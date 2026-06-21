"""Utility for handling cookie consent banners and popups automatically using Playwright."""

import logging
import re
from playwright.async_api import Page

logger = logging.getLogger(__name__)

# Common CSS selectors for cookie consent dialogs and accept buttons
COOKIE_SELECTORS = [
    # OneTrust
    "#onetrust-accept-btn-handler",
    # Didomi
    "#didomi-notice-agree-button",
    # Quantcast
    ".qc-cmp2-summary-buttons button[mode='primary']",
    # TrustArc
    "#truste-consent-button",
    # Cookiebot
    "#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll",
    "#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowandDetails",
    # Cookie Law Info
    "#cookie_action_close_header",
    # Evidon
    "#evidon-accept-button",
    # Standard classes/IDs
    "#cookie-accept",
    ".cookie-accept",
    "#accept-cookies",
    ".accept-cookies",
    "[id*='cookie'] [class*='accept']",
    "[class*='cookie'] [class*='accept']",
    "[id*='consent'] [class*='accept']",
    "[class*='consent'] [class*='accept']",
]

# Regex patterns for matching common acceptance text on buttons, links, or role='button'
COOKIE_TEXT_PATTERNS = [
    r'^\s*accept\s+all\s*$',
    r'^\s*accept\s+cookies\s*$',
    r'^\s*accept\s*$',
    r'^\s*allow\s+all\s*$',
    r'^\s*allow\s+cookies\s*$',
    r'^\s*allow\s*$',
    r'^\s*agree\s*$',
    r'^\s*agree\s+&\s+close\s*$',
    r'^\s*accept\s+&\s+close\s*$',
    r'^\s*consent\s*$',
    r'^\s*i\s+accept\s*$',
    r'^\s*i\s+agree\s*$',
    r'^\s*yes,\s*i\s+agree\s*$',
    # Common European translations
    r'^\s*accepter\s*$',
    r'^\s*autoriser\s*$',
    r'^\s*aceptar\s*$',
    r'^\s*permitir\s*$',
    r'^\s*accepteren\s*$',
    r'^\s*akkoord\s*$',
    r'^\s*akzeptieren\s*$',
    r'^\s*zustimmen\s*$',
    r'^\s*erlauben\s*$'
]
COOKIE_TEXT_RE = re.compile('|'.join(COOKIE_TEXT_PATTERNS), re.IGNORECASE)


async def handle_cookie_consent(page: Page) -> bool:
    """
    Scans the page and all of its iframes for cookie consent buttons/banners
    and attempts to dismiss them by clicking.

    Args:
        page: The Playwright Page instance.

    Returns:
        True if at least one consent button was clicked, False otherwise.
    """
    clicked = False

    # Get all frames to handle iframes containing consent dialogs (e.g. Google)
    frames = page.frames

    # 1. Try to click by common selectors in all frames
    for frame in frames:
        for selector in COOKIE_SELECTORS:
            try:
                locator = frame.locator(selector)
                count = await locator.count()
                if count > 0:
                    for i in range(count):
                        btn = locator.nth(i)
                        if await btn.is_visible():
                            await btn.click(timeout=1500)
                            logger.info(
                                f"Clicked cookie consent element by selector '{selector}' "
                                f"in frame '{frame.name or 'main'}'"
                            )
                            clicked = True
                            await page.wait_for_timeout(500)
                            return True
            except Exception as e:
                logger.debug(f"Error checking cookie selector '{selector}': {e}")

    # 2. Try to click by text matching on buttons, links, or role='button'
    for frame in frames:
        try:
            elements = frame.locator("button, a, [role='button']")
            count = await elements.count()
            for i in range(count):
                el = elements.nth(i)
                if await el.is_visible():
                    text = await el.text_content()
                    if text:
                        text_clean = text.strip()
                        if COOKIE_TEXT_RE.match(text_clean):
                            await el.click(timeout=1500)
                            logger.info(
                                f"Clicked cookie consent button with text '{text_clean}' "
                                f"in frame '{frame.name or 'main'}'"
                            )
                            clicked = True
                            await page.wait_for_timeout(500)
                            return True
        except Exception as e:
            logger.debug(f"Error checking text matching in frame '{frame.name or 'main'}': {e}")

    return clicked


def clean_consent_elements(soup) -> None:
    """
    Decompose common cookie consent banners, privacy/CCPA modals,
    and opt-out overlays from the BeautifulSoup tree.
    """
    consent_selectors = [
        # OneTrust
        "#onetrust-consent-sdk",
        # Didomi
        "#didomi-host",
        # Quantcast
        "#qc-cmp2-container",
        # AdThrive CCPA modal
        "#adthrive-ccpa-modal",
        "#adthrive-ccpa-modal-language",
        # Cookiebot
        "#CybotCookiebotDialog",
        # Generic ids / classes containing cookie, consent, privacy dialogs
        "[id*='cookie-consent']",
        "[class*='cookie-consent']",
        "[id*='cookie-banner']",
        "[class*='cookie-banner']",
        "[id*='cookie-dialog']",
        "[class*='cookie-dialog']",
        "[id*='consent-modal']",
        "[class*='consent-modal']",
        "[id*='consent-banner']",
        "[class*='consent-banner']",
        "[id*='privacy-consent']",
        "[class*='privacy-consent']",
    ]
    for selector in consent_selectors:
        try:
            for el in soup.select(selector):
                el.decompose()
        except Exception as e:
            logger.debug(f"Error decomposing consent selector '{selector}': {e}")


def isolate_target_article(soup, url: str, page_title: str) -> None:
    """
    Identifies the correct article container on infinite-scroll or aggregate pages
    and decomposes all other article containers to isolate the requested article.
    """
    import re
    from urllib.parse import urlparse

    # Clean function to normalize text for comparison
    def clean_title_text(t: str) -> str:
        if not t:
            return ""
        return re.sub(r'[^a-z0-9]', '', t.lower())

    cleaned_page_title = clean_title_text(page_title)
    
    parsed_url = urlparse(url)
    url_path = parsed_url.path.rstrip('/')
    slug = url_path.split('/')[-1] if url_path and '/' in url_path else ""

    # Find potential article containers
    # 1. Start with <article> tags
    containers = soup.find_all("article")
    
    # 2. Fall back to common post/story wrappers if no <article> tags
    if len(containers) == 0:
        for cls in ['news-post', 'post', 'story', 'entry', 'card']:
            found = soup.find_all(class_=lambda c: c and cls in c.lower())
            if len(found) > 1:
                containers = found
                break

    # If we have multiple potential article containers, isolate the correct one
    if len(containers) > 1:
        target_container = None
        
        # Method A: Try to match by header title (highest precision)
        if cleaned_page_title:
            for idx, container in enumerate(containers):
                headers = container.find_all(["h1", "h2", "h3", "h4"])
                for h in headers:
                    cleaned_header = clean_title_text(h.get_text())
                    if cleaned_header and (cleaned_header in cleaned_page_title or cleaned_page_title in cleaned_header):
                        target_container = container
                        logger.info(f"Isolated target article by headline matching: '{h.get_text().strip()}'")
                        break
                if target_container:
                    break
                    
        # Method B: Fallback to matching by URL slug/path inside links
        if not target_container and slug:
            for idx, container in enumerate(containers):
                links = container.find_all("a", href=True)
                for link in links:
                    href = link["href"]
                    if url in href or url_path in href or slug in href:
                        target_container = container
                        logger.info(f"Isolated target article by URL/slug link matching: {href}")
                        break
                if target_container:
                    break

        # Decompose all other non-matching article containers
        if target_container:
            for container in containers:
                if container != target_container:
                    # CRITICAL: Only decompose if it is NOT an ancestor or descendant of the target_container
                    if container not in target_container.parents and target_container not in container.parents:
                        try:
                            container.decompose()
                        except Exception:
                            pass


