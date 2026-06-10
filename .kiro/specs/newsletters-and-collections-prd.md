# Product Requirements Document (PRD): Curated Newsletters & Personalized Collections

## 1. Introduction & Objectives

### 1.1 Background
TunedIn is a shortform, personalized, multimodal news application. Initially, it focused on single-article conversions into swipeable stories, giving users the tools to explore and curate their own feeds. However, user feedback indicates high cognitive load and decision fatigue: readers want relevant content curated *for* them, presenting cohesive narratives rather than separate articles they have to piece together themselves.

### 1.2 Objective
We aim to shift the app's focus from individual article ingestion to **curated editions and personalized collections** that weave multiple articles into engaging, flowing narratives. This will be achieved by introducing a unified **"For You"** hub containing standard scheduled newsletters (*The Morning*, *The 7*) and dynamically generated cross-category user digests (*Tech in Sports*, *Wellbeing in Travel*) alongside regular recommended articles, videos, and podcasts.

---

## 2. Target Audience & User Stories

### 2.1 User Personas
*   **The Busy Professional (Alex):** Wants a quick, reliable summary of the world at start-of-day. Doesn't have time to browse categories. Needs a cohesive morning briefing.
*   **The Focused Enthusiast (Taylor):** Interested in specific intersections of topics (e.g., how AI/tech is transforming athletics and sports). Wants curated digests that bridge their top interests without manual searching.

### 2.2 User Stories
*   **As a user opening the app in the morning,** I want to see *The Morning* newsletter featured first so I can catch up on the day's main events immediately.
*   **As a user with mixed interests (e.g., Tech and Sports),** I want the app to automatically present a curated story called *Tech in Sports* so I can enjoy narrative-driven content tailored specifically to me.
*   **As a user reading a newsletter story slide,** I want an easy way to read the full source article if a particular summary grabs my attention.
*   **As a product owner,** I want personalized collections to be cached for 24 hours so we don't make redundant, expensive LLM calls while keeping content daily-fresh.

---

## 3. Product Features & Requirements

### 3.1 Feature 1: The "For You" Feed Hub
*   **Description:** A default landing tab on the Home/Discover screen (replacing the initial static category landing) that serves as the user's primary entrance point.
*   **Requirements:**
    *   **Tab Placement:** Rendered as the first/default tab (e.g., `/for-you`).
    *   **Feed Composition:** Mixes Curated Newsletters, Personalized Collections, Videos, Articles, and Podcasts.
    *   **Time-Appropriate Ranking:**
        *   **AM Hours (5:00 AM - 11:59 AM):** The latest *The Morning* newsletter edition is pinned to position #1.
        *   **PM Hours (5:00 PM - 11:59 PM):** The latest *The 7* newsletter edition is pinned to position #1.
        *   **Other Hours:** Feeds fall back to recent personalized collections or top recommended single-article stories.

### 3.2 Feature 2: Engaging Narrative Curation (Gemini)
*   **Description:** Moving away from disjointed article summaries. The LLM acts as an editor/anchor, synthesizing multiple source articles into a single, cohesive narrative visual story.
*   **Requirements:**
    *   **Flowing Editorial Transitions:** Slides must transition smoothly (e.g., *"First, a major upset in the NBA... Speaking of competition, AI companies are fighting for market share..."*).
    *   **Source Citation:** Each content slide must be linked to its source article ID and URL.
    *   **Visual Preservation:** Gemini matches slide text with the most relevant image from the source articles' image libraries, ensuring at most one unique image use per slide.
    *   **Layout Adaptability:** Alternates between text-top, image-top, and text-only layouts based on image availability.

### 3.3 Feature 3: Dynamic Personalized Collections
*   **Description:** User-specific newsletters blending their top two interest categories (e.g., Sports and Tech) into a combined thematic digest.
*   **Requirements:**
    *   **Interest Mining (Neo4j):** Extracts top categories by analyzing the user's graph-based reading history.
    *   **AI-Generated Branding:** Gemini dynamically invents the collection's title and description based on the categories combined (e.g., *Tech in Sports*, *Wellbeing in Travel*, *Style in Tech*).
    *   **24-Hour Cache:** Checking if a collection for the user's top interest pair was generated today. If yes, retrieve from MongoDB. If no, generate, cache, and insert.

### 3.4 Feature 4: In-Slide Navigation (Read Story)
*   **Description:** A direct connection between the high-level narrative slides and the detailed long-form content.
*   **Requirements:**
    *   An elegant, clean floating button/link (e.g., "Read Story") appears on each content slide.
    *   Tapping it opens the standard long-form reading view (`/article/:url/:title`) for that slide's specific source article.

---

## 4. UI/UX & Visual Requirements

*   **Masonry Integration:** Newsletters and collections render directly within the home screen's responsive masonry grid.
*   **Visual Distinction:** Newsletter cards must use distinct design assets:
    *   Harmonious HSL gradients as card backgrounds/headers.
    *   Glassmorphism category badges (e.g., `DAILY EDITION` or `PERSONALIZED FOR YOU`).
    *   Subtle visual outlines or double-card stacked outlines to denote a "multi-page story container".
*   **Featured Hero Layout:** Top-ranked editions (like *The Morning* in the AM) can expand into a full-width hero header card or a horizontal carousel at the top of the feed to draw immediate visual focus.

---

## 5. Technical Specifications & Architecture

### 5.1 Data Model
Newsletters will be stored in a new `newsletters` collection in MongoDB, structured to mirror the Article schema:
```json
{
  "_id": "ObjectId",
  "tag": "the-morning | the-7 | personalized-sports-tech",
  "user_id": "user_id_string | null",
  "headlines": { "basic": "The Morning: AI Shifts & Climate Tech" },
  "description": { "basic": "Curated morning news narrative." },
  "promo_items": {
    "basic": { "url": "https://images.unsplash.com/..." }
  },
  "credits": { "by": [{ "name": "TunedIn Editorial" }] },
  "publish_date": "ISO-8601-Timestamp",
  "category": "newsletters",
  "ai_summary": {
    "pages": [
      {
        "page_type": "content",
        "content": [
          { "type": "text", "content": "Narrative text slide..." },
          { "type": "image", "content_url": "https://..." }
        ],
        "layout": "text-top | image-top | text-only",
        "article_url": "https://...",
        "source_article_id": "article_id"
      }
    ]
  }
}
```

### 5.2 Retrieval & Interleaving Logic
The backend `/api/content/for-you` route executes:
1.  **Read user context:** `user_id` and `current_hour` from request.
2.  **Evaluate Pinned Edition:** If `current_hour` matches AM/PM, query the daily locked standard newsletter (e.g. *The Morning*, *The 7*).
3.  **Evaluate Persona-Based Collection:**
    *   Query Neo4j for the user's top 2 categories (e.g., `sports` and `technology`).
    *   Check MongoDB for a pre-generated newsletter matching this category pair (e.g. `tag: "sports_technology"`) created within the last 24 hours.
    *   If missing, pull 5-8 top articles from both categories, call Gemini to generate the cohort-wide newsletter (e.g. *Tech in Sports*), save it to MongoDB for all users of this cohort, and include it.
4.  **Fetch Granular & User-Specific Recommendations:** 
    *   Pull recommended articles, videos, and podcasts from Neo4j for this specific `user_id`.
    *   This dynamically retrieves and ranks articles matching their fine-tuned interests (e.g., specific teams like the *Seattle Seahawks*) to be displayed in their feed.
5.  **Assemble Feed:** Interleave the standard pinned newsletter at the top, the persona-based newsletter card below it, followed by the user-specific media tiles matching their granular interests, returning a unified payload.

---

## 6. Success Metrics & KPIs

*   **Engagement/Depth:** Average completion rate of newsletter slides (swipes to the final Takeaways slide).
*   **Click-Through Rate (CTR):** Percentage of users clicking "Read Story" on newsletter slides to read long-form articles.
*   **Retention:** Increase in Daily Active Users (DAU) returning in both morning and evening slots.
*   **Latency:** Feed retrieval time must be < 300ms for cached hits, and < 3s for cold-start dynamic generation.
