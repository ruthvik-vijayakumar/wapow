# Requirements Document: Article-to-Story Pipeline

## Introduction

The Article-to-Story Pipeline transforms long-form articles into digestible story-format slides optimized for mobile consumption. The system analyzes article content, extracts key information, generates concise summaries using LLM technology, and produces structured slide data compatible with the existing StoryView component. This enables users to consume full article narratives through swipeable story slides without reading the original article.

## Glossary

- **Pipeline**: The article-to-story conversion system
- **Article**: Long-form content stored in MongoDB with fields including title, description, content, images, videos, author, and category
- **Story**: A sequence of slides designed for mobile story-format consumption
- **Slide**: A single page within a story containing title, description, media, and layout type
- **StoryView**: The existing Vue 3 component that renders story slides with swipe navigation
- **Content_Analyzer**: The component that parses and extracts information from article content
- **Slide_Generator**: The component that creates slide structures from analyzed content
- **LLM_Service**: The language model service (OpenAI GPT, Claude, or open-source) used for summarization
- **Conversion_Job**: An asynchronous task that processes an article through the pipeline
- **Story_Data**: The generated slide collection stored alongside the original article in MongoDB
- **Layout_Type**: The visual arrangement of content within a slide (text-top, image-top, takeaways, standard)
- **Backend_API**: The FastAPI service that exposes pipeline endpoints
- **Conversion_Cache**: Storage mechanism to prevent re-processing of previously converted articles

## Requirements

### Requirement 1: Article Content Analysis

**User Story:** As a content consumer, I want articles to be analyzed for key information, so that the most important content is extracted for story slides.

#### Acceptance Criteria

1. WHEN an article is submitted for conversion, THE Content_Analyzer SHALL parse the article content from HTML or text format
2. WHEN parsing article content, THE Content_Analyzer SHALL extract the main title, description, and body text
3. WHEN analyzing article content, THE Content_Analyzer SHALL identify key sentences, paragraphs, and quotes
4. WHEN processing article media, THE Content_Analyzer SHALL extract all images and videos with their associated URLs
5. WHEN analyzing content structure, THE Content_Analyzer SHALL associate media elements with relevant content sections based on proximity and context
6. WHEN content analysis completes, THE Content_Analyzer SHALL return a structured data object containing extracted elements and their relationships

### Requirement 2: Slide Count Determination

**User Story:** As a content consumer, I want stories to have an appropriate number of slides, so that I can consume the content without excessive swiping or missing information.

#### Acceptance Criteria

1. WHEN determining slide count, THE Pipeline SHALL calculate the optimal number of slides based on article length and content density
2. THE Pipeline SHALL generate between 5 and 10 slides per article
3. WHEN an article contains fewer than 300 words, THE Pipeline SHALL generate a minimum of 3 slides
4. WHEN an article contains more than 2000 words, THE Pipeline SHALL generate a maximum of 10 slides
5. WHEN calculating slide count, THE Pipeline SHALL ensure each slide contains between 50 and 150 words of description text

### Requirement 3: LLM-Based Content Summarization

**User Story:** As a content consumer, I want article content to be accurately summarized, so that I understand the full story through concise slide descriptions.

#### Acceptance Criteria

1. WHEN generating slide content, THE LLM_Service SHALL create concise summaries that preserve the article's key information
2. WHEN summarizing content, THE LLM_Service SHALL generate descriptions between 50 and 150 words per slide
3. WHEN processing article sections, THE LLM_Service SHALL identify and extract key takeaways for the final slide
4. WHEN generating summaries, THE LLM_Service SHALL maintain factual accuracy with the original article content
5. WHEN creating slide text, THE LLM_Service SHALL use clear, readable language appropriate for mobile consumption
6. IF the LLM_Service returns an error or timeout, THEN THE Pipeline SHALL retry the request up to 3 times with exponential backoff

### Requirement 4: Slide Structure Generation

**User Story:** As a content consumer, I want slides to be properly structured with titles, descriptions, and media, so that each slide is self-contained and readable.

#### Acceptance Criteria

1. WHEN creating a slide, THE Slide_Generator SHALL include a title field with a maximum of 100 characters
2. WHEN creating a slide, THE Slide_Generator SHALL include a description field containing the summarized content
3. WHEN creating a slide, THE Slide_Generator SHALL include a thumbnail field with the associated media URL
4. WHEN creating a slide, THE Slide_Generator SHALL assign a layout type from the set: text-top, image-top, takeaways, or standard
5. WHEN generating the first slide, THE Slide_Generator SHALL use the standard layout with the article's main title and hero image
6. WHEN generating content slides, THE Slide_Generator SHALL alternate between text-top and image-top layouts
7. WHEN generating the final slide, THE Slide_Generator SHALL use the takeaways layout with extracted key points
8. WHEN an article section has no associated image, THE Slide_Generator SHALL reuse the most relevant previous image or use a placeholder

### Requirement 5: Story Data Storage

**User Story:** As a developer, I want generated story data to be stored with the original article, so that the system can retrieve stories without re-processing.

#### Acceptance Criteria

1. WHEN slide generation completes, THE Pipeline SHALL store the Story_Data in MongoDB within the article document
2. WHEN storing Story_Data, THE Pipeline SHALL create an ai_summary field containing a pages array
3. WHEN storing slide data, THE Pipeline SHALL include all slide fields: title, description, thumbnail, layout, and page_type
4. WHEN storing Story_Data, THE Pipeline SHALL include metadata: generation_timestamp, llm_model_used, and slide_count
5. WHEN an article already contains Story_Data, THE Pipeline SHALL not re-process the article unless explicitly requested
6. WHEN Story_Data storage fails, THE Pipeline SHALL log the error and return a failure status without corrupting the original article

### Requirement 6: Conversion API Endpoint

**User Story:** As a developer, I want to trigger article conversion through an API, so that I can integrate the pipeline into various workflows.

#### Acceptance Criteria

1. THE Backend_API SHALL expose a POST endpoint at /api/articles/:id/convert-to-story
2. WHEN receiving a conversion request, THE Backend_API SHALL validate that the article ID exists in MongoDB
3. WHEN receiving a conversion request with force parameter set to true, THE Backend_API SHALL re-process articles that already have Story_Data
4. WHEN receiving a conversion request without force parameter, THE Backend_API SHALL return existing Story_Data if available
5. WHEN starting a conversion, THE Backend_API SHALL return a 202 Accepted status with a job_id
6. WHEN conversion completes successfully, THE Backend_API SHALL return a 200 status with the generated Story_Data
7. IF the article ID does not exist, THEN THE Backend_API SHALL return a 404 status with an error message
8. IF the conversion fails, THEN THE Backend_API SHALL return a 500 status with error details

### Requirement 7: Asynchronous Processing

**User Story:** As a system administrator, I want article conversion to happen asynchronously, so that API requests do not block or timeout.

#### Acceptance Criteria

1. WHEN a conversion request is received, THE Backend_API SHALL create a Conversion_Job and process it asynchronously
2. WHEN processing a Conversion_Job, THE Pipeline SHALL update the job status to: pending, processing, completed, or failed
3. THE Backend_API SHALL expose a GET endpoint at /api/conversion-jobs/:job_id to check job status
4. WHEN a Conversion_Job completes, THE Pipeline SHALL store the result and update the job status to completed
5. WHEN a Conversion_Job fails, THE Pipeline SHALL store the error message and update the job status to failed
6. WHEN a Conversion_Job exceeds 5 minutes of processing time, THE Pipeline SHALL timeout and mark the job as failed

### Requirement 8: Batch Conversion Support

**User Story:** As a content administrator, I want to convert multiple articles at once, so that I can efficiently process large content collections.

#### Acceptance Criteria

1. THE Backend_API SHALL expose a POST endpoint at /api/articles/batch-convert-to-story
2. WHEN receiving a batch conversion request, THE Backend_API SHALL accept an array of article IDs
3. WHEN processing batch conversions, THE Pipeline SHALL process up to 50 articles per request
4. WHEN processing batch conversions, THE Pipeline SHALL create separate Conversion_Jobs for each article
5. WHEN receiving a batch request with more than 50 article IDs, THE Backend_API SHALL return a 400 status with an error message
6. WHEN batch conversion starts, THE Backend_API SHALL return a 202 status with an array of job_ids

### Requirement 9: LLM Service Configuration

**User Story:** As a system administrator, I want to configure the LLM service, so that I can control costs and switch between providers.

#### Acceptance Criteria

1. THE Pipeline SHALL support configuration of LLM provider through environment variables
2. THE Pipeline SHALL support OpenAI GPT, Anthropic Claude, and open-source models as LLM providers
3. WHEN configured with OpenAI, THE Pipeline SHALL use the model specified in the OPENAI_MODEL environment variable
4. WHEN configured with Anthropic, THE Pipeline SHALL use the model specified in the ANTHROPIC_MODEL environment variable
5. THE Pipeline SHALL read API keys from environment variables: OPENAI_API_KEY or ANTHROPIC_API_KEY
6. WHEN LLM API calls fail due to rate limiting, THE Pipeline SHALL implement exponential backoff with a maximum of 3 retries
7. THE Pipeline SHALL track LLM API usage and log token counts for cost monitoring

### Requirement 10: Conversion Quality Validation

**User Story:** As a content quality manager, I want generated stories to be validated, so that only high-quality conversions are stored.

#### Acceptance Criteria

1. WHEN slide generation completes, THE Pipeline SHALL validate that the slide count is between 3 and 10
2. WHEN validating slides, THE Pipeline SHALL verify that each slide contains a non-empty title and description
3. WHEN validating slides, THE Pipeline SHALL verify that at least 70% of slides have associated media
4. WHEN validating content, THE Pipeline SHALL verify that total slide description length is at least 30% of original article length
5. WHEN validating the final slide, THE Pipeline SHALL verify that it uses the takeaways layout
6. IF validation fails, THEN THE Pipeline SHALL mark the Conversion_Job as failed and log validation errors
7. IF validation fails, THEN THE Pipeline SHALL not store the Story_Data in MongoDB

### Requirement 11: Fallback Handling

**User Story:** As a user, I want the system to handle conversion failures gracefully, so that I can still access the original article.

#### Acceptance Criteria

1. IF the LLM_Service is unavailable, THEN THE Pipeline SHALL return an error status without corrupting existing data
2. IF article content cannot be parsed, THEN THE Pipeline SHALL log the error and mark the conversion as failed
3. IF an article has no images, THEN THE Slide_Generator SHALL use placeholder images or text-only layouts
4. WHEN the Pipeline encounters an error, THE Backend_API SHALL return the original article data with an error flag
5. WHEN displaying content in StoryView, THE Frontend SHALL fall back to showing the original article if Story_Data is missing or invalid

### Requirement 12: StoryView Component Compatibility

**User Story:** As a frontend developer, I want generated story data to work seamlessly with the existing StoryView component, so that no component changes are required.

#### Acceptance Criteria

1. WHEN generating Story_Data, THE Pipeline SHALL format the data structure to match the StoryView component's expected input
2. WHEN creating slide objects, THE Pipeline SHALL include all required fields: title, description, thumbnail, author, createdAt, and layout
3. WHEN storing Story_Data, THE Pipeline SHALL nest the pages array within an ai_summary object in the article document
4. WHEN the StoryView component requests story data, THE Backend_API SHALL return the article with the ai_summary field populated
5. FOR ALL generated Story_Data, loading it into StoryView and rendering all slides SHALL complete without errors

### Requirement 13: Conversion Trigger Options

**User Story:** As a content administrator, I want to control when articles are converted, so that I can manage processing costs and timing.

#### Acceptance Criteria

1. THE Pipeline SHALL support on-demand conversion triggered by API requests
2. THE Pipeline SHALL support automatic conversion for newly published articles when AUTO_CONVERT environment variable is set to true
3. WHEN AUTO_CONVERT is enabled and a new article is created, THE Pipeline SHALL automatically create a Conversion_Job
4. WHEN AUTO_CONVERT is disabled, THE Pipeline SHALL only convert articles when explicitly requested via API
5. THE Backend_API SHALL expose a POST endpoint at /api/articles/:id/preview-story for generating temporary story data without storage

### Requirement 14: Analytics Integration

**User Story:** As a product manager, I want to track story conversion and consumption metrics, so that I can measure feature success.

#### Acceptance Criteria

1. WHEN a Conversion_Job completes, THE Pipeline SHALL emit an analytics event with type: story_generated
2. WHEN a user views a generated story, THE Frontend SHALL emit an analytics event with type: story_viewed
3. WHEN a user completes viewing all slides, THE Frontend SHALL emit an analytics event with type: story_completed
4. WHEN analytics events are emitted, THE Pipeline SHALL include metadata: article_id, slide_count, conversion_duration, and llm_model
5. THE Pipeline SHALL log conversion success rate, average processing time, and LLM token usage for monitoring

### Requirement 15: Content Parsing and Pretty Printing

**User Story:** As a developer, I want to parse article content and format story data reliably, so that the system handles various content formats correctly.

#### Acceptance Criteria

1. WHEN parsing article content, THE Content_Analyzer SHALL handle HTML, Markdown, and plain text formats
2. WHEN parsing HTML content, THE Content_Analyzer SHALL extract text while preserving paragraph structure
3. WHEN parsing HTML content, THE Content_Analyzer SHALL remove script tags, style tags, and navigation elements
4. THE Pipeline SHALL include a Story_Formatter that converts Story_Data back to a readable format for debugging
5. FOR ALL valid Story_Data objects, parsing the article content, generating Story_Data, formatting it with Story_Formatter, and parsing again SHALL produce equivalent Story_Data structure (round-trip property)
6. WHEN formatting Story_Data, THE Story_Formatter SHALL output JSON with proper indentation and field ordering

---

## V2 Requirements: Adaptive Story Generation

### Requirement 16: User Persona Classification

**User Story:** As a user, I want the system to understand my reading preferences, so that content is presented in a way that matches my consumption style.

#### Acceptance Criteria

1. THE Pipeline SHALL support classification of users into persona types: Skimmer, Deep_Reader, Visual_Learner, Data_Driven, and Casual_Browser
2. WHEN classifying a user, THE Persona_Classifier SHALL analyze user behavior data from Neo4j including: average dwell time, completion rate, media preference, and category interests
3. WHEN a user has insufficient behavior data (fewer than 10 article interactions), THE Persona_Classifier SHALL assign the default persona: Casual_Browser
4. WHEN calculating persona, THE Persona_Classifier SHALL return a confidence score between 0.0 and 1.0
5. THE Persona_Classifier SHALL update user persona classification weekly based on recent behavior (last 30 days)
6. WHEN a user's behavior changes significantly (confidence score drops below 0.6), THE Persona_Classifier SHALL reclassify the user

### Requirement 17: Adaptive Slide Ordering

**User Story:** As a user, I want stories to start with content that matches my reading style, so that I can quickly find what I care about while still having access to full context.

#### Acceptance Criteria

1. WHEN generating a personalized story view, THE Story_Presenter SHALL reorder slides based on user persona while preserving all original content
2. WHEN the user persona is Skimmer, THE Story_Presenter SHALL place the takeaways slide first, followed by key points, then detailed content
3. WHEN the user persona is Deep_Reader, THE Story_Presenter SHALL maintain chronological/contextual order with background context first
4. WHEN the user persona is Visual_Learner, THE Story_Presenter SHALL prioritize slides with rich media (images, videos) at the beginning
5. WHEN the user persona is Data_Driven, THE Story_Presenter SHALL prioritize slides containing statistics, charts, and quantitative information
6. FOR ALL persona types, THE Story_Presenter SHALL ensure all slides from the original story are included in the reordered version
7. WHEN reordering slides, THE Story_Presenter SHALL not modify slide content, only the presentation order

### Requirement 18: Personalized Story API

**User Story:** As a frontend developer, I want to request personalized story views through the API, so that users see content optimized for their reading style.

#### Acceptance Criteria

1. THE Backend_API SHALL expose a GET endpoint at /api/articles/:id/story/personalized
2. WHEN receiving a personalized story request, THE Backend_API SHALL identify the authenticated user
3. WHEN the user is authenticated, THE Backend_API SHALL classify the user's persona using the Persona_Classifier
4. WHEN the user is not authenticated, THE Backend_API SHALL return the default story order (no personalization)
5. WHEN returning a personalized story, THE Backend_API SHALL include metadata: persona_type, confidence_score, and original_slide_order
6. THE Backend_API SHALL support an optional query parameter override_persona to test different persona views
7. WHEN override_persona is provided, THE Backend_API SHALL use the specified persona instead of the classified persona

### Requirement 19: Progressive Disclosure UI Hints

**User Story:** As a user, I want to be encouraged to read deeper into stories, so that I become better informed without feeling forced.

#### Acceptance Criteria

1. WHEN generating slides, THE Slide_Generator SHALL include UI hints for progressive disclosure
2. WHEN a slide is not the last slide, THE Slide_Generator SHALL include a hint field suggesting what comes next
3. WHEN the user persona is Skimmer and viewing early slides, THE hint field SHALL encourage exploring context: "Want the full story? Swipe for background & analysis"
4. WHEN the user has viewed fewer than 50% of slides, THE hint field SHALL include engagement prompts
5. WHEN the user reaches the final slide, THE hint field SHALL include a call-to-action: "Read Full Article" link
6. THE Slide_Generator SHALL not include hints that manipulate or mislead users (no clickbait)

### Requirement 20: Engagement Depth Analytics

**User Story:** As a product manager, I want to track how deeply users engage with stories, so that I can measure whether personalization improves information consumption.

#### Acceptance Criteria

1. WHEN a user views a personalized story, THE Frontend SHALL emit an analytics event: personalized_story_viewed
2. WHEN a user completes viewing a story, THE Frontend SHALL emit an analytics event: personalized_story_completed
3. WHEN emitting personalized story events, THE Frontend SHALL include metadata: persona_type, entry_slide_index, slides_viewed, total_slides, completion_rate, saw_context_slides, saw_analysis_slides
4. THE Pipeline SHALL track whether users viewed slides containing background context (context_viewed: boolean)
5. THE Pipeline SHALL track whether users viewed slides containing expert analysis (analysis_viewed: boolean)
6. THE Backend_API SHALL expose an analytics endpoint at /api/analytics/story-depth/:user_id to retrieve user engagement depth metrics
7. WHEN calculating engagement depth, THE Analytics_Service SHALL compute: average_completion_rate, context_consumption_rate, and analysis_consumption_rate

### Requirement 21: Persona-Based Slide Emphasis

**User Story:** As a content strategist, I want slides to be tagged with content types, so that the system can prioritize slides based on user preferences.

#### Acceptance Criteria

1. WHEN generating slides, THE Slide_Generator SHALL tag each slide with content_type from the set: summary, context, analysis, data, visual, opinion, takeaways
2. WHEN analyzing article content, THE Content_Analyzer SHALL identify sections containing: statistics, expert quotes, historical context, and visual elements
3. WHEN creating slides, THE Slide_Generator SHALL assign content_type based on the primary content of each slide
4. WHEN a slide contains multiple content types, THE Slide_Generator SHALL assign the dominant content_type
5. WHEN storing Story_Data, THE Pipeline SHALL include content_type in each slide's metadata
6. WHEN reordering slides for Visual_Learner persona, THE Story_Presenter SHALL prioritize slides with content_type: visual
7. WHEN reordering slides for Data_Driven persona, THE Story_Presenter SHALL prioritize slides with content_type: data

### Requirement 22: Adaptive Learning and Nudging

**User Story:** As a user, I want the system to gradually encourage me to read more deeply, so that I become better informed over time without feeling overwhelmed.

#### Acceptance Criteria

1. WHEN a user consistently completes fewer than 50% of story slides (over 20+ articles), THE System SHALL classify the user as a "shallow reader"
2. WHEN a user is classified as a shallow reader, THE Slide_Generator SHALL include gentle nudges in slide hints: "Readers who explored further found this surprising..."
3. WHEN a user's completion rate improves above 70% (over 10+ articles), THE System SHALL reclassify the user and reduce nudging frequency
4. WHEN generating hints, THE System SHALL not use manipulative language or clickbait tactics
5. THE System SHALL track nudge effectiveness: percentage of users who read deeper after seeing a nudge
6. WHEN a user consistently ignores nudges (no behavior change after 30 days), THE System SHALL reduce nudge frequency to avoid annoyance
7. THE System SHALL respect user preferences: if a user explicitly sets "minimal nudging" in settings, THE System SHALL honor this preference

### Requirement 23: Persona Override and Testing

**User Story:** As a developer, I want to test different persona views, so that I can verify personalization works correctly.

#### Acceptance Criteria

1. THE Backend_API SHALL support a query parameter override_persona on the personalized story endpoint
2. WHEN override_persona is provided with a valid persona type, THE Backend_API SHALL use that persona instead of the user's classified persona
3. WHEN override_persona is provided with an invalid persona type, THE Backend_API SHALL return a 400 error with valid persona types listed
4. THE Backend_API SHALL log all persona override requests for debugging purposes
5. WHEN in development or staging environments, THE Backend_API SHALL allow persona override without authentication
6. WHEN in production environment, THE Backend_API SHALL require authentication for persona override requests
7. THE Frontend SHALL include a developer mode toggle that allows testing all persona views for a single article

### Requirement 24: Personalization Performance

**User Story:** As a system administrator, I want personalized story generation to be fast, so that users don't experience delays.

#### Acceptance Criteria

1. WHEN requesting a personalized story, THE Backend_API SHALL return the response within 200ms (excluding network latency)
2. WHEN classifying a user persona, THE Persona_Classifier SHALL complete classification within 50ms
3. WHEN reordering slides, THE Story_Presenter SHALL complete reordering within 10ms
4. THE System SHALL cache persona classifications in Redis with a TTL of 7 days
5. WHEN a cached persona classification exists, THE System SHALL use the cached value instead of reclassifying
6. THE System SHALL cache reordered story views in Redis with a TTL of 24 hours, keyed by article_id and persona_type
7. WHEN a cached reordered story exists, THE Backend_API SHALL return the cached version

### Requirement 25: Backward Compatibility

**User Story:** As a developer, I want V2 personalization features to be optional, so that existing functionality continues to work without changes.

#### Acceptance Criteria

1. THE existing /api/articles/:id endpoint SHALL continue to return the default (non-personalized) story view
2. WHEN the ai_summary field exists in an article, THE Backend_API SHALL return it without requiring personalization
3. WHEN personalization features are disabled (ENABLE_PERSONALIZATION=false), THE Backend_API SHALL return default story views for all requests
4. WHEN a user is not authenticated, THE Backend_API SHALL return the default story view
5. THE Frontend SHALL gracefully handle responses from both personalized and non-personalized endpoints
6. WHEN the Persona_Classifier service is unavailable, THE Backend_API SHALL fall back to default story views without errors
7. THE System SHALL log all fallback events for monitoring purposes

