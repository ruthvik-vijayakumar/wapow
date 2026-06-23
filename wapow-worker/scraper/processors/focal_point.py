"""Focal point detection for article images using Gemini Vision.

Analyzes images to find the primary subject's position, allowing the frontend
to intelligently crop/pan images in vertical story containers without losing the subject.
"""

from __future__ import annotations

import json
import logging
import os
import struct
import urllib.request
import urllib.error
from typing import Any, Optional

import aiohttp

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# Minimum aspect ratio (width/height) before we bother detecting focal point.
# Images that are already close to vertical don't need focal point adjustment.
MIN_ASPECT_RATIO_FOR_DETECTION = 1.4


async def get_image_dimensions(url: str, timeout: int = 10) -> Optional[dict[str, int]]:
    """
    Fetch image dimensions without downloading the full image.
    Reads just enough bytes to parse the header for JPEG/PNG/WebP/GIF.
    
    Returns:
        dict with 'width' and 'height', or None if unable to determine.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=timeout),
                headers={"User-Agent": "WAPOWBot/1.0", "Range": "bytes=0-32767"},
            ) as resp:
                if resp.status not in (200, 206):
                    return None
                data = await resp.read()
                return _parse_image_dimensions(data)
    except Exception as e:
        logger.debug(f"Could not fetch image dimensions for {url}: {e}")
        return None


def _parse_image_dimensions(data: bytes) -> Optional[dict[str, int]]:
    """Parse image dimensions from raw bytes (supports JPEG, PNG, GIF, WebP)."""
    if len(data) < 24:
        return None

    # PNG
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        w = struct.unpack('>I', data[16:20])[0]
        h = struct.unpack('>I', data[20:24])[0]
        return {"width": w, "height": h}

    # GIF
    if data[:6] in (b'GIF87a', b'GIF89a'):
        w = struct.unpack('<H', data[6:8])[0]
        h = struct.unpack('<H', data[8:10])[0]
        return {"width": w, "height": h}

    # JPEG
    if data[:2] == b'\xff\xd8':
        return _parse_jpeg_dimensions(data)

    # WebP
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        if data[12:16] == b'VP8 ' and len(data) > 29:
            w = struct.unpack('<H', data[26:28])[0] & 0x3FFF
            h = struct.unpack('<H', data[28:30])[0] & 0x3FFF
            return {"width": w, "height": h}
        elif data[12:16] == b'VP8L' and len(data) > 25:
            bits = struct.unpack('<I', data[21:25])[0]
            w = (bits & 0x3FFF) + 1
            h = ((bits >> 14) & 0x3FFF) + 1
            return {"width": w, "height": h}
        elif data[12:16] == b'VP8X' and len(data) > 29:
            w = struct.unpack('<I', data[24:27] + b'\x00')[0] + 1
            h = struct.unpack('<I', data[27:30] + b'\x00')[0] + 1
            return {"width": w, "height": h}

    return None


def _parse_jpeg_dimensions(data: bytes) -> Optional[dict[str, int]]:
    """Parse JPEG dimensions by scanning for SOF markers."""
    i = 2
    while i < len(data) - 9:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        # SOF0-SOF3, SOF5-SOF7, SOF9-SOF11, SOF13-SOF15
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                      0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            h = struct.unpack('>H', data[i + 5:i + 7])[0]
            w = struct.unpack('>H', data[i + 7:i + 9])[0]
            return {"width": w, "height": h}
        # Skip marker segment
        if marker == 0xD9:  # EOI
            break
        if marker in (0xD0, 0xD1, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0x01):
            i += 2
            continue
        if i + 3 < len(data):
            seg_len = struct.unpack('>H', data[i + 2:i + 4])[0]
            i += 2 + seg_len
        else:
            break
    return None


async def detect_focal_point(image_url: str) -> Optional[dict[str, Any]]:
    """
    Detect the focal point of an image using Gemini Vision.
    
    Returns a dict with:
        - focal_x: float 0-1 (0=left, 1=right)
        - focal_y: float 0-1 (0=top, 1=bottom)
        - width: int (original image width)
        - height: int (original image height)
        - aspect_ratio: float (width/height)
        - display_mode: "focal_crop" | "contain" (recommended display strategy)
    
    Returns None if detection fails or image doesn't need focal point (already vertical).
    """
    if not GEMINI_API_KEY:
        logger.debug("No GEMINI_API_KEY set, skipping focal point detection")
        return None

    if not image_url or not image_url.startswith("http"):
        return None

    # Step 1: Get image dimensions
    dims = await get_image_dimensions(image_url)
    if not dims:
        logger.debug(f"Could not determine dimensions for {image_url}")
        return None

    width = dims["width"]
    height = dims["height"]
    aspect_ratio = width / height if height > 0 else 1.0

    # Skip if image is already vertical or near-square
    if aspect_ratio < MIN_ASPECT_RATIO_FOR_DETECTION:
        return {
            "focal_x": 0.5,
            "focal_y": 0.5,
            "width": width,
            "height": height,
            "aspect_ratio": round(aspect_ratio, 3),
            "display_mode": "focal_crop",
        }

    # Step 2: Ask Gemini for the focal point
    focal = await _gemini_detect_focal(image_url)

    # Determine display mode based on aspect ratio extremity
    # If the image is extremely wide (e.g. 3:1 panoramic), suggest showing it full-width
    display_mode = "contain" if aspect_ratio > 2.5 else "focal_crop"

    if focal:
        return {
            "focal_x": focal["x"],
            "focal_y": focal["y"],
            "width": width,
            "height": height,
            "aspect_ratio": round(aspect_ratio, 3),
            "display_mode": display_mode,
        }

    # Fallback: center crop
    return {
        "focal_x": 0.5,
        "focal_y": 0.5,
        "width": width,
        "height": height,
        "aspect_ratio": round(aspect_ratio, 3),
        "display_mode": display_mode,
    }


async def _gemini_detect_focal(image_url: str) -> Optional[dict[str, float]]:
    """
    Call Gemini Vision to identify the main subject position in an image.
    Returns {"x": 0-1, "y": 0-1} or None on failure.
    """
    import base64

    # Download the image (limited to 4MB) for inline submission
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                image_url,
                timeout=aiohttp.ClientTimeout(total=12),
                headers={"User-Agent": "WAPOWBot/1.0"},
            ) as resp:
                if resp.status != 200:
                    return None
                content_type = resp.headers.get("Content-Type", "image/jpeg")
                # Limit to 4MB
                image_data = await resp.content.read(4 * 1024 * 1024)
    except Exception as e:
        logger.debug(f"Failed to download image for focal point: {e}")
        return None

    if not image_data or len(image_data) < 100:
        return None

    # Determine MIME type
    mime_type = "image/jpeg"
    if "png" in content_type:
        mime_type = "image/png"
    elif "webp" in content_type:
        mime_type = "image/webp"
    elif "gif" in content_type:
        mime_type = "image/gif"

    b64_image = base64.b64encode(image_data).decode("utf-8")

    prompt = (
        "You are an image analysis tool. Look at this image and identify the main subject "
        "(person, object, or focal point of interest). Return ONLY a JSON object with the "
        "normalized x and y coordinates of the center of the main subject, where (0,0) is "
        "the top-left corner and (1,1) is the bottom-right corner. "
        'Format: {"x": 0.35, "y": 0.45}'
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": b64_image,
                        }
                    },
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.1,
        },
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

    try:
        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=req_data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = json.loads(resp.read().decode("utf-8"))

        candidates = raw.get("candidates") or []
        if not candidates:
            return None

        text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        if not text:
            return None

        # Parse the JSON response
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        result = json.loads(cleaned)
        x = float(result.get("x", 0.5))
        y = float(result.get("y", 0.5))

        # Clamp to valid range
        x = max(0.0, min(1.0, x))
        y = max(0.0, min(1.0, y))

        return {"x": round(x, 3), "y": round(y, 3)}

    except Exception as e:
        logger.warning(f"Gemini focal point detection failed: {e}")
        return None


async def enrich_document_with_focal_points(doc: dict[str, Any]) -> dict[str, Any]:
    """
    Enrich a normalized MongoDB document with focal point data for all images.
    
    Adds focal_point data to:
    - promo_items.basic (the hero/promo image)
    - content_elements[] where type == "image"
    
    Returns the enriched document (mutated in place).
    """
    # Process promo image
    promo = doc.get("promo_items") or {}
    basic = promo.get("basic") or {}
    promo_url = basic.get("url") if isinstance(basic, dict) else None

    if promo_url:
        fp = await detect_focal_point(promo_url)
        if fp:
            if "promo_items" not in doc:
                doc["promo_items"] = {}
            if "basic" not in doc["promo_items"]:
                doc["promo_items"]["basic"] = {"url": promo_url}
            doc["promo_items"]["basic"]["focal_point"] = fp

    # Process content element images
    content_elements = doc.get("content_elements") or []
    for element in content_elements:
        if not isinstance(element, dict):
            continue
        if element.get("type") != "image":
            continue
        img_url = element.get("url")
        if img_url:
            fp = await detect_focal_point(img_url)
            if fp:
                element["focal_point"] = fp

    return doc
