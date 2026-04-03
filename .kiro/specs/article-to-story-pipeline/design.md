# Technical Design Document: Article-to-Story Pipeline

## Overview

The Article-to-Story Pipeline is a content transformation system that converts long-form articles into mobile-optimized story slides. The system leverages Large Language Models (LLMs) to intelligently summarize content, extract key information, and generate structured slide data compatible with the existing StoryView component.

### Design Goals

1. **Scalability**: Handle concurrent conversion requests without blocking
2. **Reliability**: Graceful error handling with retry mechanisms and fallbacks
3. **Cost Efficiency**: Optimize LLM usage through caching and batching
4. **Maintainability**: Clean separation of concerns with modular components
5. **Extensibility**: Support multiple LLM providers and future fine-tuned models
6. **Quality**: Validate generated content to ensure high-quality output

### Architecture Decision: Integrated FastAPI Backend (Option B)

After evaluating the three architecture options, we recommend **Option B: Integrated into existing FastAPI backend** for the following reasons:

**Advantages:**
- Simplified deployment and infrastructure management
- Direct access to existing MongoDB connections and models
- Reduced operational complexity (no separate service to maintain)
- Lower latency for API calls (no network hop between services)
- Easier development and debugging in monolithic codebase
- Cost-effective for initial rollout

**Trade-offs:**
- LLM processing may impact API responsiveness (mitigated by async job queue)
- Scaling requires scaling entire backend (acceptable for current load)
- Future migration to microservice possible if needed

**Implementation Strategy:**
- Use async job queue (Redis + RQ) to prevent blocking
- Implement resource limits and timeouts
- Monitor performance and plan migration to Option A if load increases

## Architecture

### High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Vue 3)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Article View │  │  StoryView   │  │ Admin Panel  │         │
│  └──────┬───────┘  └──────▲───────┘  └──────┬───────┘         │
└─────────┼──────────────────┼──────────────────┼────────────────┘
          │                  │                  │
          │ GET /articles    │ GET /articles    │ POST /convert
          │                  │ (with ai_summary)│
          ▼                  │                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend Service                      │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    API Layer                             │  │
│  │  /api/articles/:id/convert-to-story                      │  │
│  │  /api/articles/batch-convert-to-story                    │  │
│  │  /api/conversion-jobs/:job_id                            │  │
│  │  /api/articles/:id/preview-story                         │  │
│  └────────┬─────────────────────────────────────────────────┘  │
│           │                                                     │
│           ▼                                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Conversion Orchestrator                     │  │
│  │  - Job creation and management                           │  │
│  │  - Status tracking                                       │  │
│  │  - Error handling and retries                            │  │
│  └────┬─────────────────────────────────────────────────────┘  │
│       │                                                         │
│       ▼                                                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Processing Pipeline                         │  │
│  │                                                          │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌───────────┐ │  │
│  │  │Content_Analyzer│→ │  LLM_Service   │→ │   Slide   │ │  │
│  │  │                │  │                │  │ Generator │ │  │
│  │  └────────────────┘  └────────────────┘  └───────────┘ │  │
│  │           │                  │                  │       │  │
│  │           └──────────────────┴──────────────────┘       │  │
│  │                              │                          │  │
│  │                              ▼                          │  │
│  │                    ┌──────────────────┐                │  │
│  │                    │Story_Validator   │                │  │
│  │                    └──────────────────┘                │  │
│  └──────────────────────────────┬───────────────────────────┘  │
│                                 │                               │
└─────────────────────────────────┼───────────────────────────────┘
                                  │
                                  ▼
         ┌────────────────────────────────────────────┐
         │              External Services             │
         │                                            │
         │  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
         │  │ MongoDB  │  │  Redis   │  │   LLM   │ │
         │  │          │  │  (Queue) │  │   API   │ │
         │  └──────────┘  └──────────┘  └─────────┘ │
         │                                            │
         └────────────────────────────────────────────┘
```

### Component Responsibilities

#### 1. API Layer
- Exposes REST endpoints for conversion operations
- Validates incoming requests
- Returns job IDs for async operations
- Handles authentication and authorization

#### 2. Conversion Orchestrator
- Creates and manages conversion jobs
- Tracks job status in Redis
- Implements retry logic with exponential backoff
- Coordinates pipeline components
- Handles timeouts and cancellations

#### 3. Content_Analyzer
- Parses HTML, Markdown, and plain text
- Extracts title, description, body text
- Identifies key sentences and paragraphs
- Extracts media elements (images, videos)
- Associates media with content sections
- Cleans and normalizes content

#### 4. LLM_Service
- Manages LLM provider connections (OpenAI, Anthropic)
- Implements prompt templates
- Handles structured output (JSON mode)
- Implements rate limiting and retries
- Tracks token usage for cost monitoring
- Caches responses to reduce costs

#### 5. Slide_Generator
- Determines optimal slide count
- Creates slide structures from analyzed content
- Assigns layout types (text-top, image-top, takeaways, standard)
- Associates media with slides
- Formats content for mobile consumption

#### 6. Story_Validator
- Validates slide count (3-10 slides)
- Verifies required fields present
- Checks media coverage (70% threshold)
- Validates content length ratios
- Ensures takeaways slide present

#### 7. Story_Formatter
- Converts Story_Data to readable JSON
- Supports debugging and inspection
- Implements round-trip serialization

## Components and Interfaces

### Content_Analyzer Component

**Purpose**: Parse and extract structured information from article content.

**Interface**:

```python
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class ContentFormat(Enum):
    HTML = "html"
    MARKDOWN = "markdown"
    PLAIN_TEXT = "plain_text"

@dataclass
class MediaElement:
    url: str
    type: str  # "image" or "video"
    alt_text: Optional[str] = None
    caption: Optional[str] = None
    position: int = 0  # Position in content

@dataclass
class ContentSection:
    text: str
    start_position: int
    end_position: int
    media_elements: List[MediaElement]
    is_key_section: bool = False

@dataclass
class AnalyzedContent:
    title: str
    description: str
    body_text: str
    word_count: int
    sections: List[ContentSection]
    all_media: List[MediaElement]
    key_quotes: List[str]
    format: ContentFormat

class ContentAnalyzer:
    def analyze(self, content: str, format: ContentFormat) -> AnalyzedContent:
        """
        Parse and analyze article content.
        
        Args:
            content: Raw article content
            format: Content format (HTML, Markdown, or plain text)
            
        Returns:
            AnalyzedContent object with extracted information
            
        Raises:
            ContentParsingError: If content cannot be parsed
        """
        pass
    
    def extract_key_sections(self, analyzed: AnalyzedContent, count: int) -> List[ContentSection]:
        """
        Extract the most important sections for slide generation.
        
        Args:
            analyzed: Previously analyzed content
            count: Number of sections to extract
            
        Returns:
            List of key content sections
        """
        pass
```

**Implementation Details**:

```python
from bs4 import BeautifulSoup
import re
from typing import List

class ContentAnalyzer:
    def __init__(self):
        self.min_section_words = 30
        self.max_section_words = 300
    
    def analyze(self, content: str, format: ContentFormat) -> AnalyzedContent:
        if format == ContentFormat.HTML:
            return self._analyze_html(content)
        elif format == ContentFormat.MARKDOWN:
            return self._analyze_markdown(content)
        else:
            return self._analyze_plain_text(content)
    
    def _analyze_html(self, html_content: str) -> AnalyzedContent:
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Remove unwanted elements
        for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
            tag.decompose()
        
        # Extract title
        title = soup.find('h1')
        title_text = title.get_text().strip() if title else ""
        
        # Extract description (meta or first paragraph)
        description = ""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            description = meta_desc.get('content', '')
        else:
            first_p = soup.find('p')
            if first_p:
                description = first_p.get_text().strip()[:200]
        
        # Extract body text and sections
        sections = []
        all_media = []
        body_parts = []
        
        position = 0
        for element in soup.find_all(['p', 'h2', 'h3', 'img', 'video']):
            if element.name in ['p', 'h2', 'h3']:
                text = element.get_text().strip()
                if text:
                    body_parts.append(text)
                    word_count = len(text.split())
                    
                    # Create section if substantial
                    if word_count >= self.min_section_words:
                        section_media = self._find_nearby_media(soup, element)
                        sections.append(ContentSection(
                            text=text,
                            start_position=position,
                            end_position=position + len(text),
                            media_elements=section_media
                        ))
                    position += len(text)
            
            elif element.name in ['img', 'video']:
                media = self._extract_media_element(element, position)
                if media:
                    all_media.append(media)
        
        body_text = "\n\n".join(body_parts)
        word_count = len(body_text.split())
        
        # Extract key quotes
        key_quotes = [q.get_text().strip() for q in soup.find_all('blockquote')]
        
        return AnalyzedContent(
            title=title_text,
            description=description,
            body_text=body_text,
            word_count=word_count,
            sections=sections,
            all_media=all_media,
            key_quotes=key_quotes,
            format=ContentFormat.HTML
        )
    
    def _extract_media_element(self, element, position: int) -> Optional[MediaElement]:
        if element.name == 'img':
            src = element.get('src')
            if src:
                return MediaElement(
                    url=src,
                    type="image",
                    alt_text=element.get('alt'),
                    caption=element.get('title'),
                    position=position
                )
        elif element.name == 'video':
            src = element.get('src') or (element.find('source') and element.find('source').get('src'))
            if src:
                return MediaElement(
                    url=src,
                    type="video",
                    position=position
                )
        return None
    
    def _find_nearby_media(self, soup, element) -> List[MediaElement]:
        """Find media elements near the given text element."""
        media = []
        # Look at next few siblings
        for sibling in element.find_next_siblings(limit=3):
            if sibling.name in ['img', 'video']:
                media_elem = self._extract_media_element(sibling, 0)
                if media_elem:
                    media.append(media_elem)
        return media
    
    def extract_key_sections(self, analyzed: AnalyzedContent, count: int) -> List[ContentSection]:
        """Extract key sections based on length and position."""
        # Prioritize sections with media and substantial text
        scored_sections = []
        for section in analyzed.sections:
            score = 0
            score += len(section.media_elements) * 10  # Media presence
            score += min(len(section.text.split()), 100) / 10  # Text length (capped)
            score += 5 if any(quote in section.text for quote in analyzed.key_quotes) else 0
            scored_sections.append((score, section))
        
        # Sort by score and take top N
        scored_sections.sort(reverse=True, key=lambda x: x[0])
        return [section for _, section in scored_sections[:count]]
```


### LLM_Service Component

**Purpose**: Interface with LLM providers to generate slide summaries and extract takeaways.

**Interface**:

```python
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum

class LLMProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPEN_SOURCE = "open_source"

@dataclass
class LLMConfig:
    provider: LLMProvider
    model: str
    api_key: str
    temperature: float = 0.7
    max_tokens: int = 500
    timeout: int = 30

@dataclass
class SlideSummary:
    title: str
    description: str
    key_points: List[str]
    suggested_layout: str

@dataclass
class LLMResponse:
    summaries: List[SlideSummary]
    takeaways: List[str]
    token_usage: int
    model_used: str

class LLMService:
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = self._initialize_client()
        self.cache = {}  # Simple in-memory cache
    
    def generate_slide_summaries(
        self, 
        content_sections: List[ContentSection],
        article_title: str,
        target_slide_count: int
    ) -> LLMResponse:
        """
        Generate summaries for content sections.
        
        Args:
            content_sections: Analyzed content sections
            article_title: Original article title
            target_slide_count: Desired number of content slides
            
        Returns:
            LLMResponse with generated summaries
            
        Raises:
            LLMServiceError: If LLM call fails after retries
        """
        pass
    
    def extract_takeaways(self, full_content: str, num_takeaways: int = 3) -> List[str]:
        """
        Extract key takeaways from article content.
        
        Args:
            full_content: Complete article text
            num_takeaways: Number of takeaways to extract
            
        Returns:
            List of takeaway strings
        """
        pass
```

**Prompt Templates**:

```python
class PromptTemplates:
    SYSTEM_PROMPT = """You are an expert content summarizer specializing in creating mobile-friendly story slides. 
Your task is to transform article content into concise, engaging slide descriptions.

Guidelines:
- Each slide description should be 50-150 words
- Use clear, simple language
- Preserve key facts and information
- Make each slide self-contained
- Focus on the most important points
- Use active voice and present tense when possible"""

    SLIDE_SUMMARY_PROMPT = """Given the following article section, create a concise slide summary.

Article Title: {article_title}

Section Content:
{section_content}

Generate a JSON response with:
- title: A compelling slide title (max 100 characters)
- description: A concise summary (50-150 words)
- key_points: Array of 2-3 key points from this section

Respond with valid JSON only."""

    TAKEAWAYS_PROMPT = """Analyze the following article and extract the key takeaways.

Article Title: {article_title}

Full Content:
{full_content}

Generate a JSON response with:
- takeaways: Array of {num_takeaways} key takeaways (each 15-30 words)

Focus on actionable insights and main conclusions. Respond with valid JSON only."""

    BATCH_SUMMARY_PROMPT = """Given the following article, create {num_slides} slide summaries that tell the complete story.

Article Title: {article_title}

Content Sections:
{sections}

Generate a JSON response with:
- slides: Array of {num_slides} slide objects, each containing:
  - title: Compelling slide title (max 100 characters)
  - description: Concise summary (50-150 words)
  - key_points: Array of 2-3 key points

Ensure the slides flow logically and cover the article comprehensively. Respond with valid JSON only."""
```

**Implementation**:

```python
import openai
import anthropic
import json
import hashlib
from typing import List, Dict, Any
import time

class LLMService:
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = self._initialize_client()
        self.cache = {}
        self.retry_delays = [1, 2, 4]  # Exponential backoff
    
    def _initialize_client(self):
        if self.config.provider == LLMProvider.OPENAI:
            return openai.OpenAI(api_key=self.config.api_key)
        elif self.config.provider == LLMProvider.ANTHROPIC:
            return anthropic.Anthropic(api_key=self.config.api_key)
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")
    
    def generate_slide_summaries(
        self,
        content_sections: List[ContentSection],
        article_title: str,
        target_slide_count: int
    ) -> LLMResponse:
        # Create cache key
        cache_key = self._create_cache_key(content_sections, article_title, target_slide_count)
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Prepare sections text
        sections_text = "\n\n---\n\n".join([
            f"Section {i+1}:\n{section.text}"
            for i, section in enumerate(content_sections)
        ])
        
        # Create prompt
        prompt = PromptTemplates.BATCH_SUMMARY_PROMPT.format(
            num_slides=target_slide_count,
            article_title=article_title,
            sections=sections_text
        )
        
        # Call LLM with retries
        response_data = self._call_llm_with_retry(prompt)
        
        # Parse response
        summaries = [
            SlideSummary(
                title=slide['title'],
                description=slide['description'],
                key_points=slide.get('key_points', []),
                suggested_layout='standard'
            )
            for slide in response_data['slides']
        ]
        
        result = LLMResponse(
            summaries=summaries,
            takeaways=[],
            token_usage=response_data.get('token_usage', 0),
            model_used=self.config.model
        )
        
        # Cache result
        self.cache[cache_key] = result
        
        return result
    
    def extract_takeaways(self, full_content: str, num_takeaways: int = 3) -> List[str]:
        cache_key = hashlib.md5(f"takeaways_{full_content[:100]}_{num_takeaways}".encode()).hexdigest()
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        prompt = PromptTemplates.TAKEAWAYS_PROMPT.format(
            article_title="",  # Can be added if needed
            full_content=full_content[:4000],  # Limit content length
            num_takeaways=num_takeaways
        )
        
        response_data = self._call_llm_with_retry(prompt)
        takeaways = response_data['takeaways']
        
        self.cache[cache_key] = takeaways
        return takeaways
    
    def _call_llm_with_retry(self, prompt: str) -> Dict[str, Any]:
        """Call LLM with exponential backoff retry logic."""
        last_error = None
        
        for attempt, delay in enumerate(self.retry_delays):
            try:
                if self.config.provider == LLMProvider.OPENAI:
                    return self._call_openai(prompt)
                elif self.config.provider == LLMProvider.ANTHROPIC:
                    return self._call_anthropic(prompt)
            except Exception as e:
                last_error = e
                if attempt < len(self.retry_delays) - 1:
                    time.sleep(delay)
                continue
        
        raise LLMServiceError(f"LLM call failed after {len(self.retry_delays)} attempts: {last_error}")
    
    def _call_openai(self, prompt: str) -> Dict[str, Any]:
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": PromptTemplates.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            response_format={"type": "json_object"}  # JSON mode
        )
        
        content = response.choices[0].message.content
        token_usage = response.usage.total_tokens
        
        parsed = json.loads(content)
        parsed['token_usage'] = token_usage
        
        return parsed
    
    def _call_anthropic(self, prompt: str) -> Dict[str, Any]:
        response = self.client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            system=PromptTemplates.SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        content = response.content[0].text
        token_usage = response.usage.input_tokens + response.usage.output_tokens
        
        # Extract JSON from response (Anthropic may wrap it)
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
        else:
            parsed = json.loads(content)
        
        parsed['token_usage'] = token_usage
        
        return parsed
    
    def _create_cache_key(self, content_sections: List[ContentSection], article_title: str, count: int) -> str:
        content_hash = hashlib.md5(
            f"{article_title}_{count}_{'_'.join([s.text[:50] for s in content_sections])}".encode()
        ).hexdigest()
        return content_hash

class LLMServiceError(Exception):
    pass
```

### Slide_Generator Component

**Purpose**: Create structured slide data from analyzed content and LLM summaries.

**Interface**:

```python
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class LayoutType(Enum):
    STANDARD = "standard"
    TEXT_TOP = "text-top"
    IMAGE_TOP = "image-top"
    TAKEAWAYS = "takeaways"

@dataclass
class Slide:
    title: str
    description: str
    thumbnail: str
    layout: LayoutType
    page_type: str = "content"
    author: Optional[str] = None
    created_at: Optional[str] = None

@dataclass
class StoryData:
    pages: List[Slide]
    metadata: Dict[str, Any]

class SlideGenerator:
    def __init__(self, placeholder_image_url: str = "/images/placeholder.jpg"):
        self.placeholder_image = placeholder_image_url
    
    def calculate_slide_count(self, word_count: int) -> int:
        """
        Calculate optimal slide count based on article length.
        
        Args:
            word_count: Total words in article
            
        Returns:
            Number of slides (3-10)
        """
        pass
    
    def generate_story(
        self,
        analyzed_content: AnalyzedContent,
        llm_response: LLMResponse,
        article_metadata: Dict[str, Any]
    ) -> StoryData:
        """
        Generate complete story data from analyzed content and LLM summaries.
        
        Args:
            analyzed_content: Parsed article content
            llm_response: LLM-generated summaries
            article_metadata: Original article metadata (author, date, etc.)
            
        Returns:
            Complete StoryData object
        """
        pass
```

**Implementation**:

```python
from datetime import datetime
from typing import List, Dict, Any

class SlideGenerator:
    def __init__(self, placeholder_image_url: str = "/images/placeholder.jpg"):
        self.placeholder_image = placeholder_image_url
        self.min_slides = 3
        self.max_slides = 10
        self.words_per_slide = 200  # Target average
    
    def calculate_slide_count(self, word_count: int) -> int:
        """Calculate optimal slide count based on article length."""
        if word_count < 300:
            return self.min_slides
        elif word_count > 2000:
            return self.max_slides
        else:
            # Linear interpolation between min and max
            count = self.min_slides + ((word_count - 300) / (2000 - 300)) * (self.max_slides - self.min_slides)
            return max(self.min_slides, min(self.max_slides, int(count)))
    
    def generate_story(
        self,
        analyzed_content: AnalyzedContent,
        llm_response: LLMResponse,
        article_metadata: Dict[str, Any]
    ) -> StoryData:
        slides = []
        
        # 1. Generate intro slide (standard layout)
        intro_slide = self._create_intro_slide(analyzed_content, article_metadata)
        slides.append(intro_slide)
        
        # 2. Generate content slides (alternating layouts)
        content_slides = self._create_content_slides(
            analyzed_content,
            llm_response.summaries,
            article_metadata
        )
        slides.extend(content_slides)
        
        # 3. Generate takeaways slide
        takeaways_slide = self._create_takeaways_slide(
            llm_response.takeaways,
            analyzed_content,
            article_metadata
        )
        slides.append(takeaways_slide)
        
        # Create metadata
        metadata = {
            "generation_timestamp": datetime.utcnow().isoformat(),
            "llm_model_used": llm_response.model_used,
            "slide_count": len(slides),
            "token_usage": llm_response.token_usage,
            "original_word_count": analyzed_content.word_count
        }
        
        return StoryData(pages=slides, metadata=metadata)
    
    def _create_intro_slide(
        self,
        analyzed_content: AnalyzedContent,
        article_metadata: Dict[str, Any]
    ) -> Slide:
        # Use first available image or placeholder
        thumbnail = (
            analyzed_content.all_media[0].url 
            if analyzed_content.all_media 
            else self.placeholder_image
        )
        
        return Slide(
            title=analyzed_content.title,
            description=analyzed_content.description,
            thumbnail=thumbnail,
            layout=LayoutType.STANDARD,
            page_type="intro",
            author=article_metadata.get('author'),
            created_at=article_metadata.get('created_at')
        )
    
    def _create_content_slides(
        self,
        analyzed_content: AnalyzedContent,
        summaries: List[SlideSummary],
        article_metadata: Dict[str, Any]
    ) -> List[Slide]:
        slides = []
        media_index = 1  # Start after intro slide image
        
        for i, summary in enumerate(summaries):
            # Alternate between text-top and image-top
            layout = LayoutType.TEXT_TOP if i % 2 == 0 else LayoutType.IMAGE_TOP
            
            # Get next available media or reuse last/placeholder
            if media_index < len(analyzed_content.all_media):
                thumbnail = analyzed_content.all_media[media_index].url
                media_index += 1
            elif analyzed_content.all_media:
                # Reuse last image
                thumbnail = analyzed_content.all_media[-1].url
            else:
                thumbnail = self.placeholder_image
            
            slide = Slide(
                title=summary.title,
                description=summary.description,
                thumbnail=thumbnail,
                layout=layout,
                page_type="content",
                author=article_metadata.get('author'),
                created_at=article_metadata.get('created_at')
            )
            slides.append(slide)
        
        return slides
    
    def _create_takeaways_slide(
        self,
        takeaways: List[str],
        analyzed_content: AnalyzedContent,
        article_metadata: Dict[str, Any]
    ) -> Slide:
        # Format takeaways as bullet points
        description = "Key Takeaways:\n\n" + "\n\n".join([
            f"• {takeaway}" for takeaway in takeaways
        ])
        
        # Use last image or placeholder
        thumbnail = (
            analyzed_content.all_media[-1].url 
            if analyzed_content.all_media 
            else self.placeholder_image
        )
        
        return Slide(
            title="Key Takeaways",
            description=description,
            thumbnail=thumbnail,
            layout=LayoutType.TAKEAWAYS,
            page_type="takeaways",
            author=article_metadata.get('author'),
            created_at=article_metadata.get('created_at')
        )
```


### Story_Validator Component

**Purpose**: Validate generated story data meets quality requirements.

**Interface**:

```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]

class StoryValidator:
    def __init__(self):
        self.min_slides = 3
        self.max_slides = 10
        self.min_media_coverage = 0.7  # 70%
        self.min_content_ratio = 0.3  # 30% of original
        self.min_description_words = 50
        self.max_description_words = 150
        self.max_title_length = 100
    
    def validate(self, story_data: StoryData, original_word_count: int) -> ValidationResult:
        """
        Validate generated story data.
        
        Args:
            story_data: Generated story data
            original_word_count: Word count of original article
            
        Returns:
            ValidationResult with errors and warnings
        """
        pass
```

**Implementation**:

```python
class StoryValidator:
    def __init__(self):
        self.min_slides = 3
        self.max_slides = 10
        self.min_media_coverage = 0.7
        self.min_content_ratio = 0.3
        self.min_description_words = 50
        self.max_description_words = 150
        self.max_title_length = 100
    
    def validate(self, story_data: StoryData, original_word_count: int) -> ValidationResult:
        errors = []
        warnings = []
        
        # Validate slide count
        slide_count = len(story_data.pages)
        if slide_count < self.min_slides:
            errors.append(f"Too few slides: {slide_count} (minimum: {self.min_slides})")
        elif slide_count > self.max_slides:
            errors.append(f"Too many slides: {slide_count} (maximum: {self.max_slides})")
        
        # Validate each slide
        slides_with_media = 0
        total_description_words = 0
        
        for i, slide in enumerate(story_data.pages):
            # Check required fields
            if not slide.title or not slide.title.strip():
                errors.append(f"Slide {i+1}: Missing title")
            elif len(slide.title) > self.max_title_length:
                warnings.append(f"Slide {i+1}: Title exceeds {self.max_title_length} characters")
            
            if not slide.description or not slide.description.strip():
                errors.append(f"Slide {i+1}: Missing description")
            else:
                word_count = len(slide.description.split())
                total_description_words += word_count
                
                if word_count < self.min_description_words:
                    warnings.append(f"Slide {i+1}: Description too short ({word_count} words)")
                elif word_count > self.max_description_words:
                    warnings.append(f"Slide {i+1}: Description too long ({word_count} words)")
            
            # Check media presence
            if slide.thumbnail and slide.thumbnail != "/images/placeholder.jpg":
                slides_with_media += 1
        
        # Validate media coverage
        if slide_count > 0:
            media_coverage = slides_with_media / slide_count
            if media_coverage < self.min_media_coverage:
                errors.append(
                    f"Insufficient media coverage: {media_coverage:.1%} "
                    f"(minimum: {self.min_media_coverage:.0%})"
                )
        
        # Validate content ratio
        if original_word_count > 0:
            content_ratio = total_description_words / original_word_count
            if content_ratio < self.min_content_ratio:
                warnings.append(
                    f"Low content ratio: {content_ratio:.1%} "
                    f"(recommended: {self.min_content_ratio:.0%})"
                )
        
        # Validate takeaways slide present
        has_takeaways = any(
            slide.layout == LayoutType.TAKEAWAYS or slide.page_type == "takeaways"
            for slide in story_data.pages
        )
        if not has_takeaways:
            errors.append("Missing takeaways slide")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
```

### Conversion Orchestrator

**Purpose**: Coordinate the conversion pipeline and manage job lifecycle.

**Interface**:

```python
from dataclasses import dataclass
from typing import Optional
from enum import Enum
import uuid

class JobStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ConversionJob:
    job_id: str
    article_id: str
    status: JobStatus
    created_at: str
    updated_at: str
    result: Optional[StoryData] = None
    error: Optional[str] = None
    progress: int = 0  # 0-100

class ConversionOrchestrator:
    def __init__(
        self,
        content_analyzer: ContentAnalyzer,
        llm_service: LLMService,
        slide_generator: SlideGenerator,
        validator: StoryValidator,
        job_store: 'JobStore'
    ):
        self.content_analyzer = content_analyzer
        self.llm_service = llm_service
        self.slide_generator = slide_generator
        self.validator = validator
        self.job_store = job_store
        self.timeout_seconds = 300  # 5 minutes
    
    def create_job(self, article_id: str) -> ConversionJob:
        """Create a new conversion job."""
        pass
    
    def process_job(self, job_id: str) -> ConversionJob:
        """Process a conversion job through the pipeline."""
        pass
    
    def get_job_status(self, job_id: str) -> ConversionJob:
        """Retrieve job status."""
        pass
```

**Implementation**:

```python
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ConversionOrchestrator:
    def __init__(
        self,
        content_analyzer: ContentAnalyzer,
        llm_service: LLMService,
        slide_generator: SlideGenerator,
        validator: StoryValidator,
        job_store: 'JobStore',
        article_repository: 'ArticleRepository'
    ):
        self.content_analyzer = content_analyzer
        self.llm_service = llm_service
        self.slide_generator = slide_generator
        self.validator = validator
        self.job_store = job_store
        self.article_repository = article_repository
        self.timeout_seconds = 300
    
    def create_job(self, article_id: str) -> ConversionJob:
        job = ConversionJob(
            job_id=str(uuid.uuid4()),
            article_id=article_id,
            status=JobStatus.PENDING,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        self.job_store.save(job)
        return job
    
    def process_job(self, job_id: str) -> ConversionJob:
        job = self.job_store.get(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        try:
            # Update status
            job.status = JobStatus.PROCESSING
            job.progress = 0
            self._update_job(job)
            
            # Get article
            article = self.article_repository.get_by_id(job.article_id)
            if not article:
                raise ValueError(f"Article not found: {job.article_id}")
            
            # Step 1: Analyze content (20% progress)
            logger.info(f"Job {job_id}: Analyzing content")
            analyzed_content = self.content_analyzer.analyze(
                article['content'],
                ContentFormat.HTML
            )
            job.progress = 20
            self._update_job(job)
            
            # Step 2: Calculate slide count (30% progress)
            slide_count = self.slide_generator.calculate_slide_count(
                analyzed_content.word_count
            )
            content_slide_count = slide_count - 2  # Exclude intro and takeaways
            job.progress = 30
            self._update_job(job)
            
            # Step 3: Extract key sections (40% progress)
            logger.info(f"Job {job_id}: Extracting key sections")
            key_sections = self.content_analyzer.extract_key_sections(
                analyzed_content,
                content_slide_count
            )
            job.progress = 40
            self._update_job(job)
            
            # Step 4: Generate LLM summaries (70% progress)
            logger.info(f"Job {job_id}: Generating LLM summaries")
            llm_response = self.llm_service.generate_slide_summaries(
                key_sections,
                analyzed_content.title,
                content_slide_count
            )
            job.progress = 70
            self._update_job(job)
            
            # Step 5: Extract takeaways (80% progress)
            logger.info(f"Job {job_id}: Extracting takeaways")
            takeaways = self.llm_service.extract_takeaways(
                analyzed_content.body_text,
                num_takeaways=3
            )
            llm_response.takeaways = takeaways
            job.progress = 80
            self._update_job(job)
            
            # Step 6: Generate story structure (90% progress)
            logger.info(f"Job {job_id}: Generating story structure")
            story_data = self.slide_generator.generate_story(
                analyzed_content,
                llm_response,
                {
                    'author': article.get('author'),
                    'created_at': article.get('createdAt')
                }
            )
            job.progress = 90
            self._update_job(job)
            
            # Step 7: Validate (95% progress)
            logger.info(f"Job {job_id}: Validating story data")
            validation_result = self.validator.validate(
                story_data,
                analyzed_content.word_count
            )
            
            if not validation_result.is_valid:
                raise ValidationError(
                    f"Story validation failed: {', '.join(validation_result.errors)}"
                )
            
            if validation_result.warnings:
                logger.warning(
                    f"Job {job_id}: Validation warnings: {', '.join(validation_result.warnings)}"
                )
            
            job.progress = 95
            self._update_job(job)
            
            # Step 8: Store story data (100% progress)
            logger.info(f"Job {job_id}: Storing story data")
            self.article_repository.update_story_data(
                job.article_id,
                story_data
            )
            
            # Complete job
            job.status = JobStatus.COMPLETED
            job.result = story_data
            job.progress = 100
            job.updated_at = datetime.utcnow().isoformat()
            self.job_store.save(job)
            
            logger.info(f"Job {job_id}: Completed successfully")
            return job
            
        except Exception as e:
            logger.error(f"Job {job_id}: Failed with error: {str(e)}", exc_info=True)
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.updated_at = datetime.utcnow().isoformat()
            self.job_store.save(job)
            return job
    
    def get_job_status(self, job_id: str) -> ConversionJob:
        job = self.job_store.get(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        # Check for timeout
        created_at = datetime.fromisoformat(job.created_at)
        if datetime.utcnow() - created_at > timedelta(seconds=self.timeout_seconds):
            if job.status in [JobStatus.PENDING, JobStatus.PROCESSING]:
                job.status = JobStatus.FAILED
                job.error = "Job timeout exceeded"
                self.job_store.save(job)
        
        return job
    
    def _update_job(self, job: ConversionJob):
        job.updated_at = datetime.utcnow().isoformat()
        self.job_store.save(job)

class ValidationError(Exception):
    pass
```

## Data Models

### MongoDB Schema

**Article Document** (existing, with additions):

```javascript
{
  _id: ObjectId,
  title: String,
  description: String,
  content: String,  // HTML content
  images: [String],
  videos: [String],
  author: String,
  category: String,
  createdAt: Date,
  updatedAt: Date,
  
  // NEW: AI-generated story data
  ai_summary: {
    pages: [
      {
        title: String,
        description: String,
        thumbnail: String,
        layout: String,  // "standard" | "text-top" | "image-top" | "takeaways"
        page_type: String,  // "intro" | "content" | "takeaways"
        author: String,
        createdAt: Date
      }
    ],
    metadata: {
      generation_timestamp: Date,
      llm_model_used: String,
      slide_count: Number,
      token_usage: Number,
      original_word_count: Number
    }
  }
}
```

**Conversion Job Document** (Redis or MongoDB):

```javascript
{
  job_id: String,  // UUID
  article_id: String,
  status: String,  // "pending" | "processing" | "completed" | "failed"
  progress: Number,  // 0-100
  created_at: Date,
  updated_at: Date,
  result: Object,  // StoryData (only on completion)
  error: String  // Error message (only on failure)
}
```

### Pydantic Models (FastAPI)

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class LayoutType(str, Enum):
    STANDARD = "standard"
    TEXT_TOP = "text-top"
    IMAGE_TOP = "image-top"
    TAKEAWAYS = "takeaways"

class PageType(str, Enum):
    INTRO = "intro"
    CONTENT = "content"
    TAKEAWAYS = "takeaways"

class SlideModel(BaseModel):
    title: str = Field(..., max_length=100)
    description: str = Field(..., min_length=50, max_length=500)
    thumbnail: str
    layout: LayoutType
    page_type: PageType
    author: Optional[str] = None
    createdAt: Optional[datetime] = None

class StoryMetadata(BaseModel):
    generation_timestamp: datetime
    llm_model_used: str
    slide_count: int
    token_usage: int
    original_word_count: int

class AISummary(BaseModel):
    pages: List[SlideModel]
    metadata: StoryMetadata

class ConversionRequest(BaseModel):
    force: bool = False  # Force re-conversion if story exists

class BatchConversionRequest(BaseModel):
    article_ids: List[str] = Field(..., max_items=50)
    force: bool = False

class JobStatusResponse(BaseModel):
    job_id: str
    article_id: str
    status: str
    progress: int
    created_at: datetime
    updated_at: datetime
    result: Optional[AISummary] = None
    error: Optional[str] = None

class ConversionResponse(BaseModel):
    job_id: str
    status: str
    message: str

class BatchConversionResponse(BaseModel):
    job_ids: List[str]
    message: str
```


## API Specifications

### REST Endpoints

#### 1. Convert Single Article

**Endpoint**: `POST /api/articles/:id/convert-to-story`

**Description**: Trigger conversion of a single article to story format.

**Path Parameters**:
- `id` (string, required): Article ID

**Request Body**:
```json
{
  "force": false
}
```

**Response** (202 Accepted):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Conversion job created successfully"
}
```

**Response** (200 OK - if story exists and force=false):
```json
{
  "job_id": null,
  "status": "completed",
  "message": "Story already exists",
  "data": {
    "pages": [...],
    "metadata": {...}
  }
}
```

**Error Responses**:
- `404 Not Found`: Article not found
- `500 Internal Server Error`: Conversion failed

**Example**:
```bash
curl -X POST http://localhost:8000/api/articles/507f1f77bcf86cd799439011/convert-to-story \
  -H "Content-Type: application/json" \
  -d '{"force": false}'
```

#### 2. Batch Convert Articles

**Endpoint**: `POST /api/articles/batch-convert-to-story`

**Description**: Trigger conversion of multiple articles.

**Request Body**:
```json
{
  "article_ids": [
    "507f1f77bcf86cd799439011",
    "507f1f77bcf86cd799439012",
    "507f1f77bcf86cd799439013"
  ],
  "force": false
}
```

**Response** (202 Accepted):
```json
{
  "job_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "550e8400-e29b-41d4-a716-446655440001",
    "550e8400-e29b-41d4-a716-446655440002"
  ],
  "message": "Batch conversion jobs created successfully"
}
```

**Error Responses**:
- `400 Bad Request`: Too many article IDs (>50)
- `500 Internal Server Error`: Batch creation failed

#### 3. Get Job Status

**Endpoint**: `GET /api/conversion-jobs/:job_id`

**Description**: Check the status of a conversion job.

**Path Parameters**:
- `job_id` (string, required): Job ID

**Response** (200 OK):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "article_id": "507f1f77bcf86cd799439011",
  "status": "processing",
  "progress": 70,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:31:30Z",
  "result": null,
  "error": null
}
```

**Response** (200 OK - completed):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "article_id": "507f1f77bcf86cd799439011",
  "status": "completed",
  "progress": 100,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:32:00Z",
  "result": {
    "pages": [...],
    "metadata": {...}
  },
  "error": null
}
```

**Error Responses**:
- `404 Not Found`: Job not found

#### 4. Preview Story (No Storage)

**Endpoint**: `POST /api/articles/:id/preview-story`

**Description**: Generate story data without storing it (for preview/testing).

**Path Parameters**:
- `id` (string, required): Article ID

**Response** (200 OK):
```json
{
  "pages": [
    {
      "title": "Introduction to AI",
      "description": "Artificial Intelligence is transforming...",
      "thumbnail": "https://example.com/image1.jpg",
      "layout": "standard",
      "page_type": "intro",
      "author": "John Doe",
      "createdAt": "2024-01-15T10:00:00Z"
    },
    ...
  ],
  "metadata": {
    "generation_timestamp": "2024-01-15T10:32:00Z",
    "llm_model_used": "gpt-4",
    "slide_count": 7,
    "token_usage": 1250,
    "original_word_count": 1500
  }
}
```

### FastAPI Implementation

```python
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import List
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["conversion"])

# Dependency injection
def get_orchestrator() -> ConversionOrchestrator:
    # Initialize and return orchestrator
    pass

def get_article_repository() -> 'ArticleRepository':
    # Initialize and return repository
    pass

@router.post("/articles/{article_id}/convert-to-story")
async def convert_article_to_story(
    article_id: str,
    request: ConversionRequest,
    background_tasks: BackgroundTasks,
    orchestrator: ConversionOrchestrator = Depends(get_orchestrator),
    article_repo: 'ArticleRepository' = Depends(get_article_repository)
):
    """Convert a single article to story format."""
    
    # Check if article exists
    article = article_repo.get_by_id(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Check if story already exists
    if not request.force and article.get('ai_summary'):
        return {
            "job_id": None,
            "status": "completed",
            "message": "Story already exists",
            "data": article['ai_summary']
        }
    
    # Create conversion job
    job = orchestrator.create_job(article_id)
    
    # Process in background
    background_tasks.add_task(orchestrator.process_job, job.job_id)
    
    return ConversionResponse(
        job_id=job.job_id,
        status="pending",
        message="Conversion job created successfully"
    )

@router.post("/articles/batch-convert-to-story")
async def batch_convert_articles(
    request: BatchConversionRequest,
    background_tasks: BackgroundTasks,
    orchestrator: ConversionOrchestrator = Depends(get_orchestrator),
    article_repo: 'ArticleRepository' = Depends(get_article_repository)
):
    """Convert multiple articles to story format."""
    
    if len(request.article_ids) > 50:
        raise HTTPException(
            status_code=400,
            detail="Maximum 50 articles per batch request"
        )
    
    job_ids = []
    
    for article_id in request.article_ids:
        # Check if article exists
        article = article_repo.get_by_id(article_id)
        if not article:
            logger.warning(f"Article not found: {article_id}")
            continue
        
        # Skip if story exists and force=false
        if not request.force and article.get('ai_summary'):
            logger.info(f"Skipping article {article_id}: story already exists")
            continue
        
        # Create job
        job = orchestrator.create_job(article_id)
        job_ids.append(job.job_id)
        
        # Process in background
        background_tasks.add_task(orchestrator.process_job, job.job_id)
    
    return BatchConversionResponse(
        job_ids=job_ids,
        message=f"Created {len(job_ids)} conversion jobs"
    )

@router.get("/conversion-jobs/{job_id}")
async def get_conversion_job_status(
    job_id: str,
    orchestrator: ConversionOrchestrator = Depends(get_orchestrator)
):
    """Get the status of a conversion job."""
    
    try:
        job = orchestrator.get_job_status(job_id)
        return JobStatusResponse(
            job_id=job.job_id,
            article_id=job.article_id,
            status=job.status.value,
            progress=job.progress,
            created_at=datetime.fromisoformat(job.created_at),
            updated_at=datetime.fromisoformat(job.updated_at),
            result=job.result,
            error=job.error
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/articles/{article_id}/preview-story")
async def preview_article_story(
    article_id: str,
    orchestrator: ConversionOrchestrator = Depends(get_orchestrator),
    article_repo: 'ArticleRepository' = Depends(get_article_repository)
):
    """Generate story preview without storing."""
    
    # Check if article exists
    article = article_repo.get_by_id(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    try:
        # Create temporary job (not stored)
        job_id = str(uuid.uuid4())
        
        # Process synchronously for preview
        content_analyzer = orchestrator.content_analyzer
        llm_service = orchestrator.llm_service
        slide_generator = orchestrator.slide_generator
        
        # Analyze content
        analyzed_content = content_analyzer.analyze(
            article['content'],
            ContentFormat.HTML
        )
        
        # Calculate slide count
        slide_count = slide_generator.calculate_slide_count(
            analyzed_content.word_count
        )
        content_slide_count = slide_count - 2
        
        # Extract key sections
        key_sections = content_analyzer.extract_key_sections(
            analyzed_content,
            content_slide_count
        )
        
        # Generate summaries
        llm_response = llm_service.generate_slide_summaries(
            key_sections,
            analyzed_content.title,
            content_slide_count
        )
        
        # Extract takeaways
        takeaways = llm_service.extract_takeaways(
            analyzed_content.body_text,
            num_takeaways=3
        )
        llm_response.takeaways = takeaways
        
        # Generate story
        story_data = slide_generator.generate_story(
            analyzed_content,
            llm_response,
            {
                'author': article.get('author'),
                'created_at': article.get('createdAt')
            }
        )
        
        return story_data
        
    except Exception as e:
        logger.error(f"Preview generation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Preview generation failed: {str(e)}"
        )
```

### Job Store Implementation (Redis)

```python
import redis
import json
from typing import Optional

class RedisJobStore:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url)
        self.key_prefix = "conversion_job:"
        self.ttl = 86400  # 24 hours
    
    def save(self, job: ConversionJob):
        """Save job to Redis."""
        key = f"{self.key_prefix}{job.job_id}"
        data = {
            "job_id": job.job_id,
            "article_id": job.article_id,
            "status": job.status.value,
            "progress": job.progress,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
            "error": job.error
        }
        
        # Don't store full result in Redis (too large)
        # Store only completion flag
        if job.result:
            data["has_result"] = True
        
        self.redis_client.setex(
            key,
            self.ttl,
            json.dumps(data)
        )
    
    def get(self, job_id: str) -> Optional[ConversionJob]:
        """Retrieve job from Redis."""
        key = f"{self.key_prefix}{job_id}"
        data = self.redis_client.get(key)
        
        if not data:
            return None
        
        job_data = json.loads(data)
        
        return ConversionJob(
            job_id=job_data["job_id"],
            article_id=job_data["article_id"],
            status=JobStatus(job_data["status"]),
            progress=job_data["progress"],
            created_at=job_data["created_at"],
            updated_at=job_data["updated_at"],
            error=job_data.get("error")
        )
```

### Article Repository Implementation (MongoDB)

```python
from pymongo import MongoClient
from typing import Optional, Dict, Any

class ArticleRepository:
    def __init__(self, mongo_url: str, database: str = "news_app"):
        self.client = MongoClient(mongo_url)
        self.db = self.client[database]
        self.collection = self.db["articles"]
    
    def get_by_id(self, article_id: str) -> Optional[Dict[str, Any]]:
        """Get article by ID."""
        from bson import ObjectId
        return self.collection.find_one({"_id": ObjectId(article_id)})
    
    def update_story_data(self, article_id: str, story_data: StoryData):
        """Update article with generated story data."""
        from bson import ObjectId
        
        # Convert to dict
        ai_summary = {
            "pages": [
                {
                    "title": slide.title,
                    "description": slide.description,
                    "thumbnail": slide.thumbnail,
                    "layout": slide.layout.value,
                    "page_type": slide.page_type,
                    "author": slide.author,
                    "createdAt": slide.created_at
                }
                for slide in story_data.pages
            ],
            "metadata": story_data.metadata
        }
        
        self.collection.update_one(
            {"_id": ObjectId(article_id)},
            {"$set": {"ai_summary": ai_summary}}
        )
```


## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property Reflection

Before defining properties, I analyzed the acceptance criteria to identify redundancies:

**Redundancies Identified:**
- Properties 2.2, 2.3, 2.4 can be combined into one comprehensive property about slide count bounds
- Properties 4.1, 4.2, 4.3, 4.4 can be combined into one property about required slide fields
- Properties 5.2, 5.3, 5.4 can be combined into one property about stored data structure
- Properties 6.2 and 6.7 are testing the same behavior (404 for invalid article ID)
- Properties 3.6 and 9.6 are identical (retry behavior)
- Properties 12.2 and 12.3 overlap with 5.3 (required fields in stored data)
- Properties 13.2 and 13.3 are identical (AUTO_CONVERT behavior)

**Combined Properties:**
- Slide count validation (2.2, 2.3, 2.4) → Single property with edge cases handled by generators
- Required slide fields (4.1-4.4) → Single comprehensive property
- Storage structure validation (5.2-5.4, 12.2-12.3) → Single property about complete storage format
- Retry behavior (3.6, 9.6) → Single property about LLM retry logic

### Properties

### Property 1: Content Parsing Completeness

For any article with valid HTML, Markdown, or plain text content, the Content_Analyzer should successfully parse the content and return an AnalyzedContent object with non-empty title, description, and body_text fields.

**Validates: Requirements 1.1, 1.2, 1.6**

### Property 2: Media Extraction Completeness

For any HTML content containing N img or video tags, the Content_Analyzer should extract exactly N MediaElement objects with valid URLs.

**Validates: Requirements 1.4**

### Property 3: Content Section Structure

For any analyzed content, all returned ContentSection objects should have non-empty text, valid position boundaries (start_position < end_position), and associated media elements should reference valid URLs.

**Validates: Requirements 1.3, 1.5**

### Property 4: Slide Count Bounds

For any article, the calculated slide count should be between 3 and 10 (inclusive), with articles under 300 words generating at least 3 slides and articles over 2000 words generating at most 10 slides.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

### Property 5: Slide Description Length

For any generated slide, the description field should contain between 50 and 150 words.

**Validates: Requirements 2.5, 3.2**

### Property 6: Takeaways Extraction

For any article content, the LLM_Service should return a non-empty list of takeaway strings when extract_takeaways is called.

**Validates: Requirements 3.3**

### Property 7: LLM Retry Behavior

For any LLM request that fails, the system should retry up to 3 times with exponential backoff delays (1s, 2s, 4s) before raising an error.

**Validates: Requirements 3.6, 9.6**

### Property 8: Required Slide Fields

For any generated slide, all required fields (title, description, thumbnail, layout, page_type) should be present and non-empty, with title length not exceeding 100 characters and layout being one of the valid LayoutType values.

**Validates: Requirements 4.1, 4.2, 4.3, 4.4**

### Property 9: Layout Alternation

For any generated story with N content slides (excluding intro and takeaways), content slides should alternate between TEXT_TOP and IMAGE_TOP layouts, starting with TEXT_TOP for the first content slide.

**Validates: Requirements 4.6**

### Property 10: Thumbnail Presence

For any generated slide, the thumbnail field should never be null or empty—if no media is available, it should contain the placeholder image URL.

**Validates: Requirements 4.8**

### Property 11: Storage Structure Completeness

For any successfully converted article, the stored ai_summary object should contain a pages array with all slides having required fields (title, description, thumbnail, layout, page_type) and a metadata object with required fields (generation_timestamp, llm_model_used, slide_count, token_usage, original_word_count).

**Validates: Requirements 5.1, 5.2, 5.3, 5.4, 12.2, 12.3**

### Property 12: Conversion Caching

For any article that has been successfully converted, requesting conversion again without force=true should return the existing Story_Data without re-processing (verifiable by checking that generation_timestamp remains unchanged).

**Validates: Requirements 5.5, 6.4**

### Property 13: Storage Failure Safety

For any conversion that fails during storage, the original article document should remain unchanged (no ai_summary field added or modified).

**Validates: Requirements 5.6, 11.1**

### Property 14: Invalid Article ID Handling

For any non-existent article ID, the conversion API should return a 404 status code with an error message.

**Validates: Requirements 6.2, 6.7**

### Property 15: Force Conversion Behavior

For any article with existing Story_Data, requesting conversion with force=true should create a new conversion job and generate new Story_Data with a different generation_timestamp.

**Validates: Requirements 6.3**

### Property 16: Async Job Creation

For any valid conversion request, the API should return immediately (within 1 second) with a 202 status and a valid job_id, without waiting for conversion to complete.

**Validates: Requirements 6.5, 7.1**

### Property 17: Job Status Validity

For any conversion job at any point in time, the job status should be exactly one of: pending, processing, completed, or failed.

**Validates: Requirements 7.2**

### Property 18: Completed Job Structure

For any conversion job with status=completed, the job should have a non-null result field containing valid StoryData and a null error field.

**Validates: Requirements 7.4**

### Property 19: Failed Job Structure

For any conversion job with status=failed, the job should have a non-empty error field and a null result field.

**Validates: Requirements 7.5**

### Property 20: Job Timeout Enforcement

For any conversion job that has been processing for more than 5 minutes (300 seconds), the job status should be updated to failed with a timeout error message.

**Validates: Requirements 7.6**

### Property 21: Batch Job Creation

For any batch conversion request with N valid article IDs (where N ≤ 50), the system should create exactly N conversion jobs and return N job_ids.

**Validates: Requirements 8.3, 8.4, 8.6**

### Property 22: Batch Size Limit

For any batch conversion request with more than 50 article IDs, the API should return a 400 status code with an error message.

**Validates: Requirements 8.5**

### Property 23: LLM Provider Configuration

For any valid LLM provider configuration (OpenAI, Anthropic, or open-source), the LLM_Service should initialize successfully and use the model specified in the corresponding environment variable (OPENAI_MODEL or ANTHROPIC_MODEL).

**Validates: Requirements 9.1, 9.3, 9.4, 9.5**

### Property 24: Token Usage Tracking

For any LLM request that completes successfully, the system should log the token usage count and include it in the story metadata.

**Validates: Requirements 9.7**

### Property 25: Slide Count Validation

For any generated StoryData, validation should fail if the slide count is less than 3 or greater than 10.

**Validates: Requirements 10.1**

### Property 26: Required Fields Validation

For any generated StoryData, validation should fail if any slide has an empty title or empty description.

**Validates: Requirements 10.2**

### Property 27: Media Coverage Validation

For any generated StoryData with N slides, validation should fail if fewer than 70% of slides (0.7 * N) have non-placeholder media (thumbnail not equal to placeholder URL).

**Validates: Requirements 10.3**

### Property 28: Content Ratio Validation

For any generated StoryData, if the total word count across all slide descriptions is less than 30% of the original article word count, validation should emit a warning (but not fail).

**Validates: Requirements 10.4**

### Property 29: Takeaways Slide Validation

For any generated StoryData, validation should fail if the last slide does not have layout=TAKEAWAYS or page_type=takeaways.

**Validates: Requirements 10.5**

### Property 30: Validation Failure Prevents Storage

For any conversion where StoryData validation fails, the article document should not be updated with ai_summary, and the job status should be failed with validation errors in the error field.

**Validates: Requirements 10.6, 10.7**

### Property 31: Parse Error Handling

For any article with unparseable content, the conversion should fail gracefully with status=failed and an error message, without modifying the article document.

**Validates: Requirements 11.2**

### Property 32: No-Image Fallback

For any article with zero images, the Slide_Generator should successfully generate a complete story with all slides using the placeholder image URL.

**Validates: Requirements 11.3**

### Property 33: StoryView Schema Compatibility

For any generated StoryData, all slides should conform to the StoryView expected schema (having title, description, thumbnail, layout, page_type, author, and createdAt fields with correct types).

**Validates: Requirements 12.1, 12.4, 12.5**

### Property 34: Auto-Convert Behavior

When AUTO_CONVERT environment variable is set to true, creating a new article should automatically trigger a conversion job; when set to false, no automatic job should be created.

**Validates: Requirements 13.2, 13.3, 13.4**

### Property 35: Analytics Event Emission

For any conversion job that completes (successfully or with failure), the system should emit an analytics event with type=story_generated and metadata including article_id, slide_count, conversion_duration, and llm_model.

**Validates: Requirements 14.1, 14.4**

### Property 36: Metrics Logging

For any conversion job, the system should log metrics including success/failure status, processing time, and token usage for monitoring purposes.

**Validates: Requirements 14.5**

### Property 37: Multi-Format Parsing

For any valid content in HTML, Markdown, or plain text format, the Content_Analyzer should successfully parse it and return an AnalyzedContent object with the correct format field set.

**Validates: Requirements 15.1**

### Property 38: HTML Cleaning

For any HTML content containing script, style, nav, header, or footer tags, the parsed body_text should not contain content from these tags.

**Validates: Requirements 15.3**

### Property 39: Story Data Round-Trip

For any valid StoryData object, serializing it to JSON with Story_Formatter, then parsing the JSON back, should produce an equivalent StoryData structure (all fields match).

**Validates: Requirements 15.5**

### Property 40: JSON Formatting

For any StoryData object, the Story_Formatter should output valid JSON that can be parsed by a standard JSON parser, with proper indentation (2 or 4 spaces).

**Validates: Requirements 15.6**


## Error Handling

### Error Categories and Strategies

#### 1. Content Parsing Errors

**Scenarios:**
- Malformed HTML/Markdown
- Empty or missing content
- Unsupported character encodings

**Handling:**
- Try multiple parsers (BeautifulSoup with different parsers: lxml, html.parser)
- Fall back to plain text extraction if structured parsing fails
- Log detailed error with content sample for debugging
- Mark job as failed with descriptive error message

**Example:**
```python
def _parse_with_fallback(self, content: str) -> AnalyzedContent:
    parsers = ['lxml', 'html.parser', 'html5lib']
    last_error = None
    
    for parser in parsers:
        try:
            return self._parse_html(content, parser)
        except Exception as e:
            last_error = e
            logger.warning(f"Parser {parser} failed: {e}")
            continue
    
    # Final fallback: plain text
    logger.warning("All HTML parsers failed, falling back to plain text")
    return self._parse_plain_text(content)
```

#### 2. LLM Service Errors

**Scenarios:**
- API rate limiting (429)
- API timeout
- Invalid API key (401)
- Model unavailable (503)
- Malformed response
- Token limit exceeded

**Handling:**
- Exponential backoff for rate limiting and timeouts (1s, 2s, 4s)
- Immediate failure for authentication errors (no retry)
- Parse errors: retry once, then fail
- Log token usage even on failure
- Cache successful responses to avoid re-processing

**Example:**
```python
def _call_llm_with_retry(self, prompt: str) -> Dict[str, Any]:
    retry_delays = [1, 2, 4]
    
    for attempt, delay in enumerate(retry_delays):
        try:
            return self._call_llm(prompt)
        except RateLimitError as e:
            if attempt < len(retry_delays) - 1:
                logger.warning(f"Rate limited, retrying in {delay}s")
                time.sleep(delay)
            else:
                raise LLMServiceError(f"Rate limit exceeded after {len(retry_delays)} attempts")
        except AuthenticationError as e:
            # Don't retry auth errors
            raise LLMServiceError(f"Authentication failed: {e}")
        except TimeoutError as e:
            if attempt < len(retry_delays) - 1:
                logger.warning(f"Timeout, retrying in {delay}s")
                time.sleep(delay)
            else:
                raise LLMServiceError(f"Timeout after {len(retry_delays)} attempts")
        except Exception as e:
            logger.error(f"Unexpected LLM error: {e}")
            raise LLMServiceError(f"LLM call failed: {e}")
```

#### 3. Validation Errors

**Scenarios:**
- Slide count out of bounds
- Missing required fields
- Insufficient media coverage
- Content ratio too low

**Handling:**
- Collect all validation errors before failing
- Distinguish between errors (fail) and warnings (log but continue)
- Include validation details in job error message
- Do not store invalid Story_Data

**Example:**
```python
def validate(self, story_data: StoryData, original_word_count: int) -> ValidationResult:
    errors = []
    warnings = []
    
    # Collect all issues
    if len(story_data.pages) < 3:
        errors.append("Too few slides")
    
    if media_coverage < 0.7:
        errors.append(f"Insufficient media: {media_coverage:.0%}")
    
    if content_ratio < 0.3:
        warnings.append(f"Low content ratio: {content_ratio:.0%}")
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )
```

#### 4. Storage Errors

**Scenarios:**
- MongoDB connection failure
- Write timeout
- Document size limit exceeded
- Concurrent modification

**Handling:**
- Retry storage operation once
- Use transactions where possible
- Verify write success before marking job complete
- Never corrupt original article data

**Example:**
```python
def update_story_data(self, article_id: str, story_data: StoryData):
    max_retries = 2
    
    for attempt in range(max_retries):
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(article_id)},
                {"$set": {"ai_summary": story_data.to_dict()}},
                upsert=False
            )
            
            if result.matched_count == 0:
                raise StorageError("Article not found")
            
            if result.modified_count == 0:
                logger.warning("Article not modified (may already have same data)")
            
            return
            
        except pymongo.errors.ConnectionFailure as e:
            if attempt < max_retries - 1:
                logger.warning(f"Storage failed, retrying: {e}")
                time.sleep(1)
            else:
                raise StorageError(f"Failed to store after {max_retries} attempts: {e}")
```

#### 5. Job Timeout

**Scenarios:**
- LLM taking too long
- Large article processing
- System resource constraints

**Handling:**
- Set 5-minute timeout per job
- Check timeout on job status requests
- Mark timed-out jobs as failed
- Log timeout for monitoring

**Example:**
```python
def get_job_status(self, job_id: str) -> ConversionJob:
    job = self.job_store.get(job_id)
    
    if job.status in [JobStatus.PENDING, JobStatus.PROCESSING]:
        created_at = datetime.fromisoformat(job.created_at)
        elapsed = datetime.utcnow() - created_at
        
        if elapsed.total_seconds() > self.timeout_seconds:
            job.status = JobStatus.FAILED
            job.error = f"Job timeout after {self.timeout_seconds}s"
            self.job_store.save(job)
            logger.error(f"Job {job_id} timed out")
    
    return job
```

### Error Response Format

All API errors follow consistent format:

```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Story validation failed",
    "details": [
      "Too few slides: 2 (minimum: 3)",
      "Insufficient media coverage: 50% (minimum: 70%)"
    ],
    "article_id": "507f1f77bcf86cd799439011",
    "job_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

## Testing Strategy

### Dual Testing Approach

The testing strategy combines unit tests for specific scenarios and property-based tests for comprehensive coverage:

**Unit Tests**: Focus on specific examples, edge cases, and integration points
**Property Tests**: Verify universal properties across randomized inputs

Both approaches are complementary and necessary for comprehensive coverage. Unit tests catch concrete bugs in specific scenarios, while property tests verify general correctness across a wide input space.

### Property-Based Testing Configuration

**Library Selection**: 
- Python: Use `hypothesis` library (mature, well-documented, excellent for Python)
- Minimum 100 iterations per property test (due to randomization)
- Each test references its design document property

**Test Tag Format**:
```python
@given(article_content=html_content_strategy())
@settings(max_examples=100)
def test_property_1_content_parsing_completeness(article_content):
    """
    Feature: article-to-story-pipeline
    Property 1: For any article with valid HTML, Markdown, or plain text content,
    the Content_Analyzer should successfully parse the content and return an
    AnalyzedContent object with non-empty title, description, and body_text fields.
    """
    analyzer = ContentAnalyzer()
    result = analyzer.analyze(article_content, ContentFormat.HTML)
    
    assert result.title.strip() != ""
    assert result.description.strip() != ""
    assert result.body_text.strip() != ""
```

### Test Organization

```
tests/
├── unit/
│   ├── test_content_analyzer.py
│   ├── test_llm_service.py
│   ├── test_slide_generator.py
│   ├── test_validator.py
│   └── test_api_endpoints.py
├── property/
│   ├── test_properties_content_analysis.py  # Properties 1-3
│   ├── test_properties_slide_generation.py  # Properties 4-10
│   ├── test_properties_storage.py           # Properties 11-13
│   ├── test_properties_api.py               # Properties 14-22
│   ├── test_properties_llm.py               # Properties 23-24
│   ├── test_properties_validation.py        # Properties 25-30
│   └── test_properties_misc.py              # Properties 31-40
├── integration/
│   ├── test_full_pipeline.py
│   ├── test_batch_conversion.py
│   └── test_error_scenarios.py
└── fixtures/
    ├── sample_articles.py
    ├── html_generators.py
    └── mock_llm_responses.py
```

### Property Test Examples

#### Property 1: Content Parsing Completeness

```python
from hypothesis import given, strategies as st
from hypothesis import settings
import pytest

# Custom strategy for generating HTML content
@st.composite
def html_article_strategy(draw):
    title = draw(st.text(min_size=10, max_size=100))
    paragraphs = draw(st.lists(st.text(min_size=50, max_size=200), min_size=3, max_size=10))
    
    html = f"""
    <html>
    <head><title>{title}</title></head>
    <body>
        <h1>{title}</h1>
        <p>{paragraphs[0]}</p>
        {''.join(f'<p>{p}</p>' for p in paragraphs[1:])}
    </body>
    </html>
    """
    return html

@given(content=html_article_strategy())
@settings(max_examples=100)
def test_property_1_content_parsing_completeness(content):
    """
    Feature: article-to-story-pipeline
    Property 1: For any article with valid HTML, the Content_Analyzer should
    successfully parse the content and return an AnalyzedContent object with
    non-empty title, description, and body_text fields.
    """
    analyzer = ContentAnalyzer()
    result = analyzer.analyze(content, ContentFormat.HTML)
    
    assert result.title.strip() != "", "Title should not be empty"
    assert result.description.strip() != "", "Description should not be empty"
    assert result.body_text.strip() != "", "Body text should not be empty"
    assert result.format == ContentFormat.HTML
```

#### Property 4: Slide Count Bounds

```python
@given(word_count=st.integers(min_value=100, max_value=5000))
@settings(max_examples=100)
def test_property_4_slide_count_bounds(word_count):
    """
    Feature: article-to-story-pipeline
    Property 4: For any article, the calculated slide count should be between
    3 and 10 (inclusive).
    """
    generator = SlideGenerator()
    slide_count = generator.calculate_slide_count(word_count)
    
    assert 3 <= slide_count <= 10, f"Slide count {slide_count} out of bounds for {word_count} words"
    
    # Edge cases
    if word_count < 300:
        assert slide_count >= 3, "Short articles should have at least 3 slides"
    if word_count > 2000:
        assert slide_count <= 10, "Long articles should have at most 10 slides"
```

#### Property 39: Story Data Round-Trip

```python
@st.composite
def story_data_strategy(draw):
    num_slides = draw(st.integers(min_value=3, max_value=10))
    slides = []
    
    for i in range(num_slides):
        slide = Slide(
            title=draw(st.text(min_size=10, max_size=100)),
            description=draw(st.text(min_size=50, max_size=500)),
            thumbnail=draw(st.text(min_size=10, max_size=200)),
            layout=draw(st.sampled_from(list(LayoutType))),
            page_type=draw(st.sampled_from(["intro", "content", "takeaways"]))
        )
        slides.append(slide)
    
    return StoryData(
        pages=slides,
        metadata={
            "generation_timestamp": datetime.utcnow().isoformat(),
            "llm_model_used": "gpt-4",
            "slide_count": num_slides,
            "token_usage": draw(st.integers(min_value=100, max_value=5000)),
            "original_word_count": draw(st.integers(min_value=300, max_value=3000))
        }
    )

@given(story_data=story_data_strategy())
@settings(max_examples=100)
def test_property_39_story_data_round_trip(story_data):
    """
    Feature: article-to-story-pipeline
    Property 39: For any valid StoryData object, serializing it to JSON with
    Story_Formatter, then parsing the JSON back, should produce an equivalent
    StoryData structure.
    """
    formatter = StoryFormatter()
    
    # Serialize
    json_str = formatter.format(story_data)
    
    # Deserialize
    parsed_data = formatter.parse(json_str)
    
    # Verify equivalence
    assert len(parsed_data.pages) == len(story_data.pages)
    assert parsed_data.metadata["slide_count"] == story_data.metadata["slide_count"]
    
    for original, parsed in zip(story_data.pages, parsed_data.pages):
        assert original.title == parsed.title
        assert original.description == parsed.description
        assert original.layout == parsed.layout
```

### Unit Test Examples

#### Content Analyzer Edge Cases

```python
def test_content_analyzer_empty_html():
    """Test that empty HTML is handled gracefully."""
    analyzer = ContentAnalyzer()
    result = analyzer.analyze("<html></html>", ContentFormat.HTML)
    
    assert result.title == ""
    assert result.body_text == ""
    assert len(result.sections) == 0

def test_content_analyzer_removes_scripts():
    """Test that script tags are removed from parsed content."""
    html = """
    <html>
    <body>
        <h1>Title</h1>
        <script>alert('xss')</script>
        <p>Content</p>
    </body>
    </html>
    """
    analyzer = ContentAnalyzer()
    result = analyzer.analyze(html, ContentFormat.HTML)
    
    assert "alert" not in result.body_text
    assert "xss" not in result.body_text
    assert "Content" in result.body_text

def test_content_analyzer_extracts_all_images():
    """Test that all images are extracted."""
    html = """
    <html>
    <body>
        <img src="image1.jpg" alt="First">
        <p>Text</p>
        <img src="image2.jpg" alt="Second">
    </body>
    </html>
    """
    analyzer = ContentAnalyzer()
    result = analyzer.analyze(html, ContentFormat.HTML)
    
    assert len(result.all_media) == 2
    assert result.all_media[0].url == "image1.jpg"
    assert result.all_media[1].url == "image2.jpg"
```

#### API Endpoint Tests

```python
from fastapi.testclient import TestClient

def test_convert_article_returns_job_id(client: TestClient, sample_article_id):
    """Test that conversion request returns job ID."""
    response = client.post(
        f"/api/articles/{sample_article_id}/convert-to-story",
        json={"force": False}
    )
    
    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "pending"

def test_convert_nonexistent_article_returns_404(client: TestClient):
    """Test that invalid article ID returns 404."""
    response = client.post(
        "/api/articles/000000000000000000000000/convert-to-story",
        json={"force": False}
    )
    
    assert response.status_code == 404

def test_batch_convert_exceeds_limit_returns_400(client: TestClient):
    """Test that batch with >50 articles returns 400."""
    article_ids = [f"id_{i}" for i in range(51)]
    response = client.post(
        "/api/articles/batch-convert-to-story",
        json={"article_ids": article_ids, "force": False}
    )
    
    assert response.status_code == 400
```

### Integration Tests

```python
@pytest.mark.integration
def test_full_pipeline_end_to_end(mongo_db, redis_client, mock_llm):
    """Test complete conversion pipeline."""
    # Setup
    article = create_test_article(mongo_db)
    orchestrator = create_orchestrator(mongo_db, redis_client, mock_llm)
    
    # Create and process job
    job = orchestrator.create_job(article['_id'])
    result_job = orchestrator.process_job(job.job_id)
    
    # Verify
    assert result_job.status == JobStatus.COMPLETED
    assert result_job.result is not None
    
    # Check storage
    updated_article = mongo_db.articles.find_one({"_id": article['_id']})
    assert "ai_summary" in updated_article
    assert len(updated_article["ai_summary"]["pages"]) >= 3

@pytest.mark.integration
def test_llm_failure_handling(mongo_db, redis_client, failing_llm):
    """Test that LLM failures are handled gracefully."""
    article = create_test_article(mongo_db)
    orchestrator = create_orchestrator(mongo_db, redis_client, failing_llm)
    
    job = orchestrator.create_job(article['_id'])
    result_job = orchestrator.process_job(job.job_id)
    
    assert result_job.status == JobStatus.FAILED
    assert result_job.error is not None
    
    # Verify article unchanged
    updated_article = mongo_db.articles.find_one({"_id": article['_id']})
    assert "ai_summary" not in updated_article
```

### Test Coverage Goals

- Unit test coverage: >80% of code
- Property test coverage: All 40 properties implemented
- Integration test coverage: All major workflows
- API endpoint coverage: 100% of endpoints

### Mocking Strategy

**Mock LLM Responses**: Use deterministic responses for unit/integration tests
**Mock MongoDB**: Use mongomock or test database
**Mock Redis**: Use fakeredis for job store tests
**Real LLM**: Only in manual/staging tests (cost consideration)


## Deployment Considerations

### Environment Configuration

**Required Environment Variables**:

```bash
# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=news_app

# Redis (Job Queue)
REDIS_URL=redis://localhost:6379

# LLM Configuration
LLM_PROVIDER=openai  # or "anthropic" or "open_source"
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-sonnet-20240229

# Pipeline Configuration
AUTO_CONVERT=false  # Auto-convert new articles
CONVERSION_TIMEOUT=300  # 5 minutes
MAX_BATCH_SIZE=50
PLACEHOLDER_IMAGE_URL=/images/placeholder.jpg

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Infrastructure Requirements

#### Development Environment

```yaml
services:
  - FastAPI backend (Python 3.12+)
  - MongoDB 6.0+
  - Redis 7.0+
  - LLM API access (OpenAI or Anthropic)

resources:
  cpu: 2 cores
  memory: 4GB
  storage: 20GB
```

#### Production Environment

```yaml
services:
  - FastAPI backend (multiple instances behind load balancer)
  - MongoDB cluster (replica set)
  - Redis cluster (for high availability)
  - LLM API access with rate limiting

resources:
  backend:
    cpu: 4 cores per instance
    memory: 8GB per instance
    instances: 3+ (for redundancy)
  
  mongodb:
    cpu: 4 cores
    memory: 16GB
    storage: 500GB SSD
  
  redis:
    cpu: 2 cores
    memory: 4GB
    storage: 20GB
```

### Deployment Architecture

```
                    ┌─────────────────┐
                    │  Load Balancer  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
         ┌────▼────┐    ┌────▼────┐   ┌────▼────┐
         │ FastAPI │    │ FastAPI │   │ FastAPI │
         │Instance1│    │Instance2│   │Instance3│
         └────┬────┘    └────┬────┘   └────┬────┘
              │              │              │
              └──────────────┼──────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
         ┌────▼────┐    ┌────▼────┐   ┌────▼────┐
         │ MongoDB │    │  Redis  │   │   LLM   │
         │ Cluster │    │ Cluster │   │   API   │
         └─────────┘    └─────────┘   └─────────┘
```

### Docker Configuration

**Dockerfile**:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**docker-compose.yml** (for development):

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URL=mongodb://mongodb:27017
      - REDIS_URL=redis://redis:6379
      - LLM_PROVIDER=openai
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENAI_MODEL=gpt-4-turbo-preview
      - AUTO_CONVERT=false
    depends_on:
      - mongodb
      - redis
    volumes:
      - ./:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  mongodb:
    image: mongo:6.0
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    environment:
      - MONGO_INITDB_DATABASE=news_app

  redis:
    image: redis:7.0-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  mongodb_data:
  redis_data:
```

### Monitoring and Observability

#### Metrics to Track

```python
# Prometheus metrics example
from prometheus_client import Counter, Histogram, Gauge

# Conversion metrics
conversion_requests_total = Counter(
    'conversion_requests_total',
    'Total conversion requests',
    ['status']  # success, failed, cached
)

conversion_duration_seconds = Histogram(
    'conversion_duration_seconds',
    'Time spent processing conversions',
    buckets=[1, 5, 10, 30, 60, 120, 300]
)

llm_token_usage_total = Counter(
    'llm_token_usage_total',
    'Total LLM tokens used',
    ['model', 'provider']
)

active_jobs = Gauge(
    'active_conversion_jobs',
    'Number of currently processing jobs'
)

validation_failures_total = Counter(
    'validation_failures_total',
    'Total validation failures',
    ['reason']
)
```

#### Logging Strategy

```python
import logging
import json
from datetime import datetime

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log_conversion_start(self, job_id: str, article_id: str):
        self.logger.info(json.dumps({
            "event": "conversion_started",
            "job_id": job_id,
            "article_id": article_id,
            "timestamp": datetime.utcnow().isoformat()
        }))
    
    def log_conversion_complete(self, job_id: str, duration: float, slide_count: int, token_usage: int):
        self.logger.info(json.dumps({
            "event": "conversion_completed",
            "job_id": job_id,
            "duration_seconds": duration,
            "slide_count": slide_count,
            "token_usage": token_usage,
            "timestamp": datetime.utcnow().isoformat()
        }))
    
    def log_conversion_failed(self, job_id: str, error: str, duration: float):
        self.logger.error(json.dumps({
            "event": "conversion_failed",
            "job_id": job_id,
            "error": error,
            "duration_seconds": duration,
            "timestamp": datetime.utcnow().isoformat()
        }))
```

#### Health Check Endpoint

```python
@router.get("/health")
async def health_check(
    mongo_client: MongoClient = Depends(get_mongo_client),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """Health check endpoint for load balancer."""
    health = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # Check MongoDB
    try:
        mongo_client.admin.command('ping')
        health["services"]["mongodb"] = "healthy"
    except Exception as e:
        health["services"]["mongodb"] = f"unhealthy: {str(e)}"
        health["status"] = "degraded"
    
    # Check Redis
    try:
        redis_client.ping()
        health["services"]["redis"] = "healthy"
    except Exception as e:
        health["services"]["redis"] = f"unhealthy: {str(e)}"
        health["status"] = "degraded"
    
    # Check LLM (optional, may be expensive)
    # health["services"]["llm"] = "not_checked"
    
    status_code = 200 if health["status"] == "healthy" else 503
    return JSONResponse(content=health, status_code=status_code)
```

### Scaling Considerations

#### Horizontal Scaling

- FastAPI instances can be scaled horizontally behind load balancer
- Use Redis for job state (shared across instances)
- MongoDB handles concurrent writes
- No session state in backend (stateless)

#### Vertical Scaling

- Increase memory for larger articles
- More CPU cores for parallel processing
- Consider GPU instances if using local LLM models

#### Cost Optimization

**LLM Costs**:
- Cache LLM responses aggressively (Redis with TTL)
- Use cheaper models for preview endpoint
- Batch similar articles together
- Monitor token usage per article type

**Infrastructure Costs**:
- Use spot instances for non-critical workloads
- Scale down during low-traffic periods
- Use MongoDB Atlas free tier for development
- Consider managed Redis (AWS ElastiCache, Redis Cloud)

**Example Cost Calculation**:
```
Assumptions:
- 1000 articles/day
- Average 1500 words per article
- ~500 tokens per article for summarization
- GPT-4 Turbo: $0.01 per 1K input tokens, $0.03 per 1K output tokens
- Average 300 output tokens per article

Daily LLM cost:
- Input: 1000 * 500 * $0.01 / 1000 = $5
- Output: 1000 * 300 * $0.03 / 1000 = $9
- Total: $14/day = $420/month

Infrastructure (AWS):
- EC2 (3x t3.medium): ~$75/month
- MongoDB Atlas (M10): ~$60/month
- ElastiCache (cache.t3.micro): ~$15/month
- Total: ~$150/month

Total monthly cost: ~$570
```

### Security Considerations

#### API Security

```python
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify JWT token."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/articles/{article_id}/convert-to-story")
async def convert_article(
    article_id: str,
    request: ConversionRequest,
    user: dict = Depends(verify_token)
):
    # Check user permissions
    if not user.get("can_convert_articles"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Process conversion...
```

#### Data Security

- Encrypt LLM API keys in environment
- Use TLS for all external connections
- Sanitize article content before LLM processing
- Implement rate limiting per user/IP
- Log all conversion requests for audit

#### Input Validation

```python
from pydantic import BaseModel, validator, Field

class ConversionRequest(BaseModel):
    force: bool = False
    
    @validator('force')
    def validate_force(cls, v):
        if not isinstance(v, bool):
            raise ValueError('force must be boolean')
        return v

class BatchConversionRequest(BaseModel):
    article_ids: List[str] = Field(..., max_items=50)
    force: bool = False
    
    @validator('article_ids')
    def validate_article_ids(cls, v):
        if not v:
            raise ValueError('article_ids cannot be empty')
        if len(v) > 50:
            raise ValueError('Maximum 50 articles per batch')
        for article_id in v:
            if not ObjectId.is_valid(article_id):
                raise ValueError(f'Invalid article ID: {article_id}')
        return v
```

### Migration Strategy

#### Phase 1: Development and Testing (Weeks 1-2)
- Set up development environment
- Implement core components
- Write unit and property tests
- Manual testing with sample articles

#### Phase 2: Staging Deployment (Week 3)
- Deploy to staging environment
- Test with production-like data
- Performance testing and optimization
- Security audit

#### Phase 3: Limited Production Rollout (Week 4)
- Deploy to production
- Enable for 10% of articles (feature flag)
- Monitor metrics and errors
- Gather user feedback

#### Phase 4: Full Rollout (Week 5+)
- Gradually increase to 100%
- Batch convert existing articles
- Monitor costs and performance
- Iterate based on feedback

### Rollback Plan

If issues arise in production:

1. **Immediate**: Disable AUTO_CONVERT flag
2. **Short-term**: Stop accepting new conversion requests (return 503)
3. **Medium-term**: Roll back to previous version
4. **Long-term**: Fix issues, re-test, re-deploy

### Maintenance and Operations

#### Regular Tasks

- Monitor LLM token usage and costs
- Review failed conversion logs
- Update LLM prompts based on quality feedback
- Clean up old job records from Redis (TTL)
- Optimize MongoDB indexes for ai_summary queries
- Update LLM models as new versions release

#### Backup Strategy

- MongoDB: Daily automated backups
- Redis: Not critical (job state is temporary)
- Configuration: Version controlled in Git
- LLM cache: Can be rebuilt if lost

### Performance Targets

- API response time: <100ms (job creation)
- Conversion time: <60s for average article (1500 words)
- Throughput: 100+ conversions/minute
- Success rate: >95%
- Availability: 99.9% uptime

## V2: Adaptive Story Generation

### Overview

V2 extends the base pipeline with personalized story presentation while maintaining editorial integrity. Instead of reducing content, V2 adapts the **presentation order** and **entry points** based on user personas, ensuring all users have access to full context while improving engagement.

### Design Philosophy

**Core Principle**: Same comprehensive content for everyone, personalized presentation.

- ✅ No information loss
- ✅ Publishers maintain editorial control
- ✅ Improved engagement through better UX
- ✅ Measurable "informed vs. skimmed" metrics
- ✅ No ethical concerns about filter bubbles

### User Personas

```python
from enum import Enum

class UserPersona(Enum):
    SKIMMER = "skimmer"              # Quick readers, want TL;DR first
    DEEP_READER = "deep_reader"      # Thorough readers, want context first
    VISUAL_LEARNER = "visual_learner" # Prefer images/videos
    DATA_DRIVEN = "data_driven"      # Focus on stats and facts
    CASUAL_BROWSER = "casual_browser" # Default, balanced approach

@dataclass
class PersonaClassification:
    persona: UserPersona
    confidence: float  # 0.0 to 1.0
    classified_at: datetime
    behavior_summary: Dict[str, Any]
```

### Persona Classification Component

**Purpose**: Analyze user behavior to determine reading preferences.

**Data Sources**:
- Neo4j user behavior graph (dwell time, completion rate, category interests)
- MongoDB user interaction history
- Analytics events (scroll depth, media engagement)

**Implementation**:

```python
from typing import Dict, Any
import numpy as np

class PersonaClassifier:
    def __init__(self, neo4j_client, analytics_service):
        self.neo4j = neo4j_client
        self.analytics = analytics_service
        self.min_interactions = 10  # Minimum articles for classification
    
    def classify_user(self, user_id: str) -> PersonaClassification:
        """
        Classify user based on behavior patterns.
        
        Returns PersonaClassification with confidence score.
        """
        # Get user behavior from Neo4j
        behavior = self._get_user_behavior(user_id)
        
        if behavior['interaction_count'] < self.min_interactions:
            return PersonaClassification(
                persona=UserPersona.CASUAL_BROWSER,
                confidence=0.5,
                classified_at=datetime.utcnow(),
                behavior_summary=behavior
            )
        
        # Calculate persona scores
        scores = {
            UserPersona.SKIMMER: self._calculate_skimmer_score(behavior),
            UserPersona.DEEP_READER: self._calculate_deep_reader_score(behavior),
            UserPersona.VISUAL_LEARNER: self._calculate_visual_learner_score(behavior),
            UserPersona.DATA_DRIVEN: self._calculate_data_driven_score(behavior),
            UserPersona.CASUAL_BROWSER: 0.5  # Baseline
        }
        
        # Select persona with highest score
        persona = max(scores, key=scores.get)
        confidence = scores[persona]
        
        return PersonaClassification(
            persona=persona,
            confidence=confidence,
            classified_at=datetime.utcnow(),
            behavior_summary=behavior
        )
    
    def _get_user_behavior(self, user_id: str) -> Dict[str, Any]:
        """Query Neo4j for user behavior metrics."""
        query = """
        MATCH (u:User {id: $user_id})-[r:READS]->(a:Article)
        WITH u, 
             count(r) as interaction_count,
             avg(r.dwell_time_ms) as avg_dwell_time,
             avg(r.completion_rate) as avg_completion_rate,
             sum(CASE WHEN r.viewed_media THEN 1 ELSE 0 END) * 1.0 / count(r) as media_engagement
        RETURN interaction_count, avg_dwell_time, avg_completion_rate, media_engagement
        """
        result = self.neo4j.run(query, user_id=user_id).single()
        
        return {
            'interaction_count': result['interaction_count'] if result else 0,
            'avg_dwell_time': result['avg_dwell_time'] if result else 0,
            'avg_completion_rate': result['avg_completion_rate'] if result else 0,
            'media_engagement': result['media_engagement'] if result else 0
        }
    
    def _calculate_skimmer_score(self, behavior: Dict[str, Any]) -> float:
        """Calculate likelihood user is a skimmer."""
        score = 0.0
        
        # Short dwell time (< 30 seconds average)
        if behavior['avg_dwell_time'] < 30000:
            score += 0.4
        
        # Low completion rate (< 50%)
        if behavior['avg_completion_rate'] < 0.5:
            score += 0.4
        
        # Low media engagement
        if behavior['media_engagement'] < 0.3:
            score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_deep_reader_score(self, behavior: Dict[str, Any]) -> float:
        """Calculate likelihood user is a deep reader."""
        score = 0.0
        
        # Long dwell time (> 120 seconds average)
        if behavior['avg_dwell_time'] > 120000:
            score += 0.4
        
        # High completion rate (> 80%)
        if behavior['avg_completion_rate'] > 0.8:
            score += 0.5
        
        # Moderate to high media engagement
        if behavior['media_engagement'] > 0.5:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_visual_learner_score(self, behavior: Dict[str, Any]) -> float:
        """Calculate likelihood user is a visual learner."""
        score = 0.0
        
        # High media engagement (> 70%)
        if behavior['media_engagement'] > 0.7:
            score += 0.6
        
        # Moderate dwell time
        if 40000 < behavior['avg_dwell_time'] < 90000:
            score += 0.2
        
        # Moderate completion rate
        if 0.5 < behavior['avg_completion_rate'] < 0.8:
            score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_data_driven_score(self, behavior: Dict[str, Any]) -> float:
        """Calculate likelihood user is data-driven."""
        # This would require additional analytics on which slide types
        # users engage with most (data/stats slides vs narrative slides)
        # For now, return baseline
        return 0.5
```

### Story Presenter Component

**Purpose**: Reorder slides based on persona while preserving all content.

**Implementation**:

```python
from typing import List
from dataclasses import dataclass

@dataclass
class ContentTypeTag(Enum):
    SUMMARY = "summary"
    CONTEXT = "context"
    ANALYSIS = "analysis"
    DATA = "data"
    VISUAL = "visual"
    OPINION = "opinion"
    TAKEAWAYS = "takeaways"

@dataclass
class EnhancedSlide(Slide):
    """Slide with additional metadata for personalization."""
    content_type: ContentTypeTag
    media_richness_score: float  # 0.0 to 1.0
    data_density_score: float    # 0.0 to 1.0
    hint: Optional[str] = None   # Progressive disclosure hint

class StoryPresenter:
    def __init__(self):
        self.persona_strategies = {
            UserPersona.SKIMMER: self._reorder_for_skimmer,
            UserPersona.DEEP_READER: self._reorder_for_deep_reader,
            UserPersona.VISUAL_LEARNER: self._reorder_for_visual_learner,
            UserPersona.DATA_DRIVEN: self._reorder_for_data_driven,
            UserPersona.CASUAL_BROWSER: self._default_order
        }
    
    def present_story(
        self,
        story_data: StoryData,
        persona: UserPersona,
        include_hints: bool = True
    ) -> StoryData:
        """
        Reorder slides based on persona.
        
        Args:
            story_data: Original story with all slides
            persona: User's classified persona
            include_hints: Whether to add progressive disclosure hints
            
        Returns:
            StoryData with reordered slides (same content, different order)
        """
        strategy = self.persona_strategies.get(persona, self._default_order)
        reordered_slides = strategy(story_data.pages)
        
        if include_hints:
            reordered_slides = self._add_hints(reordered_slides, persona)
        
        # Add personalization metadata
        metadata = story_data.metadata.copy()
        metadata['personalization'] = {
            'persona': persona.value,
            'original_order_preserved': False,
            'reordered_at': datetime.utcnow().isoformat()
        }
        
        return StoryData(pages=reordered_slides, metadata=metadata)
    
    def _reorder_for_skimmer(self, slides: List[EnhancedSlide]) -> List[EnhancedSlide]:
        """
        Skimmer: Takeaways first, then key points, then details.
        """
        takeaways = [s for s in slides if s.content_type == ContentTypeTag.TAKEAWAYS]
        summary = [s for s in slides if s.content_type == ContentTypeTag.SUMMARY]
        rest = [s for s in slides if s.content_type not in [ContentTypeTag.TAKEAWAYS, ContentTypeTag.SUMMARY]]
        
        return takeaways + summary + rest
    
    def _reorder_for_deep_reader(self, slides: List[EnhancedSlide]) -> List[EnhancedSlide]:
        """
        Deep Reader: Context first, then narrative flow, then takeaways.
        """
        context = [s for s in slides if s.content_type == ContentTypeTag.CONTEXT]
        content = [s for s in slides if s.content_type not in [ContentTypeTag.CONTEXT, ContentTypeTag.TAKEAWAYS]]
        takeaways = [s for s in slides if s.content_type == ContentTypeTag.TAKEAWAYS]
        
        return context + content + takeaways
    
    def _reorder_for_visual_learner(self, slides: List[EnhancedSlide]) -> List[EnhancedSlide]:
        """
        Visual Learner: Media-rich slides first, sorted by media richness.
        """
        return sorted(slides, key=lambda s: s.media_richness_score, reverse=True)
    
    def _reorder_for_data_driven(self, slides: List[EnhancedSlide]) -> List[EnhancedSlide]:
        """
        Data-Driven: Data/stats slides first, sorted by data density.
        """
        return sorted(slides, key=lambda s: s.data_density_score, reverse=True)
    
    def _default_order(self, slides: List[EnhancedSlide]) -> List[EnhancedSlide]:
        """
        Default: Keep original order.
        """
        return slides
    
    def _add_hints(self, slides: List[EnhancedSlide], persona: UserPersona) -> List[EnhancedSlide]:
        """
        Add progressive disclosure hints to slides.
        """
        for i, slide in enumerate(slides):
            if i < len(slides) - 1:  # Not the last slide
                if persona == UserPersona.SKIMMER and i < 2:
                    slide.hint = "Want the full story? Swipe for context & analysis"
                elif i == len(slides) // 2:
                    slide.hint = "You're halfway through. Keep going for the complete picture"
            else:  # Last slide
                slide.hint = "Read the full article for even more details"
        
        return slides
```

### Enhanced Slide Generation

Update `Slide_Generator` to tag slides with content types:

```python
class EnhancedSlideGenerator(SlideGenerator):
    def _create_content_slides(
        self,
        analyzed_content: AnalyzedContent,
        summaries: List[SlideSummary],
        article_metadata: Dict[str, Any]
    ) -> List[EnhancedSlide]:
        """
        Create slides with content type tags and scoring.
        """
        slides = []
        media_index = 1
        
        for i, summary in enumerate(summaries):
            # Determine content type
            content_type = self._classify_slide_content(summary, analyzed_content)
            
            # Calculate scores
            media_score = self._calculate_media_richness(summary, analyzed_content, media_index)
            data_score = self._calculate_data_density(summary.description)
            
            # Get media
            if media_index < len(analyzed_content.all_media):
                thumbnail = analyzed_content.all_media[media_index].url
                media_index += 1
            else:
                thumbnail = self.placeholder_image
            
            # Determine layout
            layout = LayoutType.TEXT_TOP if i % 2 == 0 else LayoutType.IMAGE_TOP
            
            slide = EnhancedSlide(
                title=summary.title,
                description=summary.description,
                thumbnail=thumbnail,
                layout=layout,
                page_type="content",
                author=article_metadata.get('author'),
                created_at=article_metadata.get('created_at'),
                content_type=content_type,
                media_richness_score=media_score,
                data_density_score=data_score
            )
            slides.append(slide)
        
        return slides
    
    def _classify_slide_content(
        self,
        summary: SlideSummary,
        analyzed_content: AnalyzedContent
    ) -> ContentTypeTag:
        """
        Classify slide content type based on text analysis.
        """
        text = summary.description.lower()
        
        # Check for data/stats keywords
        data_keywords = ['percent', '%', 'data', 'statistics', 'study', 'research', 'number']
        if any(keyword in text for keyword in data_keywords):
            return ContentTypeTag.DATA
        
        # Check for context keywords
        context_keywords = ['background', 'history', 'previously', 'context', 'began']
        if any(keyword in text for keyword in context_keywords):
            return ContentTypeTag.CONTEXT
        
        # Check for analysis keywords
        analysis_keywords = ['analysis', 'expert', 'opinion', 'suggests', 'indicates']
        if any(keyword in text for keyword in analysis_keywords):
            return ContentTypeTag.ANALYSIS
        
        # Default to summary
        return ContentTypeTag.SUMMARY
    
    def _calculate_media_richness(
        self,
        summary: SlideSummary,
        analyzed_content: AnalyzedContent,
        media_index: int
    ) -> float:
        """
        Calculate how media-rich this slide is (0.0 to 1.0).
        """
        score = 0.0
        
        # Has media
        if media_index < len(analyzed_content.all_media):
            score += 0.5
            
            # Video is richer than image
            media = analyzed_content.all_media[media_index]
            if media.type == "video":
                score += 0.3
            else:
                score += 0.2
        
        # Text-to-media ratio (less text = more visual)
        word_count = len(summary.description.split())
        if word_count < 60:
            score += 0.2
        elif word_count < 100:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_data_density(self, text: str) -> float:
        """
        Calculate how data-dense this slide is (0.0 to 1.0).
        """
        import re
        
        # Count numbers
        numbers = re.findall(r'\d+', text)
        number_density = len(numbers) / max(len(text.split()), 1)
        
        # Count data keywords
        data_keywords = ['percent', '%', 'data', 'statistics', 'study', 'research']
        keyword_count = sum(1 for keyword in data_keywords if keyword in text.lower())
        
        score = min(number_density * 5 + keyword_count * 0.2, 1.0)
        return score
```

### Personalized API Endpoints

```python
@router.get("/api/articles/{article_id}/story/personalized")
async def get_personalized_story(
    article_id: str,
    override_persona: Optional[str] = None,
    user: dict = Depends(get_current_user),
    persona_classifier: PersonaClassifier = Depends(get_persona_classifier),
    story_presenter: StoryPresenter = Depends(get_story_presenter),
    article_repo: ArticleRepository = Depends(get_article_repository),
    cache: redis.Redis = Depends(get_redis_client)
):
    """
    Get personalized story view based on user persona.
    
    Query Parameters:
        override_persona: Optional persona override for testing
    """
    # Get article
    article = article_repo.get_by_id(article_id)
    if not article or 'ai_summary' not in article:
        raise HTTPException(status_code=404, detail="Story not found")
    
    # Determine persona
    if override_persona:
        try:
            persona = UserPersona(override_persona)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid persona. Valid options: {[p.value for p in UserPersona]}"
            )
    else:
        # Check cache
        cache_key = f"persona:{user['id']}"
        cached_classification = cache.get(cache_key)
        
        if cached_classification:
            classification = PersonaClassification(**json.loads(cached_classification))
        else:
            # Classify user
            classification = persona_classifier.classify_user(user['id'])
            
            # Cache for 7 days
            cache.setex(
                cache_key,
                604800,  # 7 days
                json.dumps(classification.__dict__)
            )
        
        persona = classification.persona
    
    # Check cache for reordered story
    cache_key = f"story:{article_id}:persona:{persona.value}"
    cached_story = cache.get(cache_key)
    
    if cached_story:
        return json.loads(cached_story)
    
    # Load original story
    original_story = StoryData(**article['ai_summary'])
    
    # Reorder for persona
    personalized_story = story_presenter.present_story(
        original_story,
        persona,
        include_hints=True
    )
    
    # Cache for 24 hours
    cache.setex(
        cache_key,
        86400,  # 24 hours
        json.dumps(personalized_story.__dict__)
    )
    
    return personalized_story

@router.get("/api/users/{user_id}/persona")
async def get_user_persona(
    user_id: str,
    user: dict = Depends(get_current_user),
    persona_classifier: PersonaClassifier = Depends(get_persona_classifier)
):
    """
    Get user's classified persona with confidence score.
    """
    # Verify user can access this data
    if user['id'] != user_id and not user.get('is_admin'):
        raise HTTPException(status_code=403, detail="Forbidden")
    
    classification = persona_classifier.classify_user(user_id)
    
    return {
        "user_id": user_id,
        "persona": classification.persona.value,
        "confidence": classification.confidence,
        "classified_at": classification.classified_at.isoformat(),
        "behavior_summary": classification.behavior_summary
    }
```

### Analytics Integration

```python
# Frontend tracking
function trackPersonalizedStoryView(articleId, persona, entrySlideIndex) {
  tracker.track('personalized_story_viewed', {
    content_id: articleId,
    content_type: 'article',
    properties: {
      persona_type: persona,
      entry_slide_index: entrySlideIndex,
      timestamp: new Date().toISOString()
    }
  })
}

function trackPersonalizedStoryCompletion(articleId, persona, slidesViewed, totalSlides, contextViewed, analysisViewed) {
  tracker.track('personalized_story_completed', {
    content_id: articleId,
    content_type: 'article',
    properties: {
      persona_type: persona,
      slides_viewed: slidesViewed,
      total_slides: totalSlides,
      completion_rate: slidesViewed / totalSlides,
      saw_context_slides: contextViewed,
      saw_analysis_slides: analysisViewed,
      timestamp: new Date().toISOString()
    }
  })
}
```

### V2 Cost Analysis

**Additional Costs**:
- Persona classification: Negligible (Neo4j query + simple scoring)
- Slide reordering: Negligible (in-memory operation)
- Caching: Minimal (Redis storage for persona + reordered stories)

**Storage Impact**:
- No additional MongoDB storage (reordering happens at request time)
- Redis cache: ~5KB per persona classification + ~50KB per reordered story
- For 10K active users × 5 personas × 100 popular articles = ~50MB Redis

**Performance**:
- Persona classification: <50ms
- Slide reordering: <10ms
- Total overhead: <100ms (acceptable)

**Total Additional Cost**: ~$10-20/month for Redis caching

### V2 Deployment Strategy

**Phase 1: Persona Classification (Week 1)**
- Deploy PersonaClassifier
- Start classifying users based on existing behavior
- Monitor classification accuracy

**Phase 2: Slide Reordering (Week 2)**
- Deploy StoryPresenter
- Enable personalized endpoint for 10% of users (A/B test)
- Measure engagement metrics

**Phase 3: Progressive Disclosure (Week 3)**
- Add hints and nudges
- Monitor nudge effectiveness
- Iterate on hint messaging

**Phase 4: Full Rollout (Week 4)**
- Enable for 100% of users
- Monitor engagement depth metrics
- Gather user feedback

### V2 Success Metrics

**Engagement Metrics**:
- Story completion rate (target: +15%)
- Average slides viewed per story (target: +20%)
- Time spent per story (target: +25%)

**Information Consumption Metrics**:
- Context slide view rate (target: >60%)
- Analysis slide view rate (target: >50%)
- Full article click-through rate (target: +10%)

**User Satisfaction**:
- User feedback surveys
- Persona classification accuracy (target: >80% confidence)
- Nudge effectiveness (target: >30% respond positively)

## Conclusion

This design provides a comprehensive, scalable solution for converting articles to story format using LLM technology. The architecture balances simplicity (integrated backend) with robustness (async processing, error handling, validation). The dual testing approach ensures both specific correctness and general properties hold across all inputs.

**V1 Key Decisions**:
- Integrated FastAPI backend for simplicity
- Async job queue for non-blocking operations
- Comprehensive validation before storage
- Extensive error handling and retry logic
- Property-based testing for thorough coverage
- Flexible LLM provider support
- Cost-conscious caching and optimization

**V2 Key Decisions**:
- Persona-based presentation (not content reduction)
- Client-side reordering for performance
- Progressive disclosure to encourage depth
- Measurable information consumption metrics
- Backward compatible with V1
- Minimal additional cost (~$10-20/month)

The system is designed to be maintainable, testable, and ready for production deployment with clear monitoring, scaling, and security considerations. V2 enhances engagement while maintaining editorial integrity and ensuring all users have access to complete information.
