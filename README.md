# WAPOW

A content aggregation and recommendation platform that curates articles, videos, and podcasts with personalized recommendations powered by collaborative filtering.

Built with a **Vue 3** frontend and a **FastAPI** backend, using **MongoDB** for content storage, **Neo4j** for graph-based recommendations, and **Auth0** for authentication.

## Architecture

```
wapow/
├── wapow-ui/          # Vue 3 frontend (Vite + TypeScript + Tailwind)
└── wapow-app/         # FastAPI backend (Python + MongoDB + Neo4j)
```

### Frontend — `wapow-ui/`

| Tech | Purpose |
|------|---------|
| Vue 3 (Composition API) | UI framework |
| TypeScript | Type safety |
| Vite | Dev server & build |
| Pinia | State management |
| Vue Router | Client-side routing |
| Tailwind CSS | Styling |
| Auth0 Vue SDK | Authentication |

### Backend — `wapow-app/`

| Tech | Purpose |
|------|---------|
| FastAPI | API framework |
| MongoDB 7 | Content & user storage |
| Neo4j 5 | Recommendation graph |
| PyJWT | Auth0 JWT validation |
| Poetry | Dependency management |
| Docker Compose | Local infrastructure |

## Features

### Content Browsing
- Browse articles, videos, and podcasts across categories: **Sports**, **Style**, **Technology**, **Travel**, **Wellbeing**
- Story-style vertical feed with swipe navigation (mobile-first)
- Full article reading view
- Masonry grid layout on the home page
- Pagination, search, and filtering

### Personalized Recommendations
- Neo4j collaborative filtering based on reading patterns
- Category-specific and time-of-day recommendations
- Graph model: Users, Articles, Categories, Locations, Hours with relationships (READS, INTERESTED_IN, READS_AT, etc.)

### User Accounts & Saved Content
- Auth0-based authentication (Google, GitHub, Twitter OAuth)
- User documents stored in MongoDB on sign-in
- Save/unsave articles, videos, and podcasts (embedded in user document)
- Saved content view with collection badges

### Additional
- Pin Board (Pinterest-style content board)
- Wordle game
- Profile & settings page

## Quick Start

### Prerequisites

- Node.js 20+ and npm
- Python 3.12+ and [Poetry](https://python-poetry.org/)
- MongoDB 7 (local or Docker)
- Neo4j 5 (local or Docker) — optional, for recommendations

### 1. Clone

```bash
git clone <repo-url> wapow
cd wapow
```

### 2. Start Databases (Docker)

From `wapow-app/`:

```bash
cd wapow-app
docker compose up -d mongo neo4j
```

This starts MongoDB on port `27017` and Neo4j on ports `7474` (HTTP) / `7687` (Bolt).

### 3. Backend Setup

```bash
cd wapow-app
poetry install
```

Create a `.env.dev` (or `.env`) in `wapow-app/`:

```env
MONGODB_URI=mongodb://localhost:27017/wapow-data
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=wapow-neo4j
PORT=3001

# Auth0 (optional — omit to disable auth)
AUTH0_DOMAIN=your-tenant.us.auth0.com
AUTH0_AUDIENCE=https://your-api-identifier
```

Start the API:

```bash
poetry run uvicorn api.main:app --host 0.0.0.0 --port 3001 --reload
```

API: http://localhost:3001 | Docs: http://localhost:3001/docs

### 4. Frontend Setup

```bash
cd wapow-ui
npm install
```

Create a `.env` in `wapow-ui/`:

```env
VITE_API_URL=http://localhost:3001
VITE_AUTH0_DOMAIN=your-tenant.us.auth0.com
VITE_AUTH0_CLIENT_ID=your-client-id
VITE_AUTH0_AUDIENCE=https://your-api-identifier
```

Start the dev server:

```bash
npm run dev
```

App: http://localhost:3000

### 5. Seed Recommendations (Optional)

Populate Neo4j with sample data so the recommendation engine returns results:

```bash
cd wapow-app
poetry run python -m api.scripts.seed_neo4j
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Welcome + endpoint listing |
| `GET` | `/health` | Health check (MongoDB ping) |
| `GET` | `/api/me` | Current user info (upserts user doc) |
| `GET` | `/api/{category}` | List content by category |
| `GET` | `/api/{category}/:id` | Single content item |
| `GET` | `/api/videos` | Video content |
| `GET` | `/api/podcasts` | Podcast content |
| `POST` | `/api/articles/by-ids` | Bulk fetch by IDs |
| `POST` | `/api/recommendations` | Neo4j collaborative filtering |
| `GET` | `/api/saved-articles` | List saved content |
| `GET` | `/api/saved-articles/ids` | Saved article ID set (quick lookup) |
| `POST` | `/api/saved-articles` | Save content |
| `DELETE` | `/api/saved-articles/:id` | Unsave content |

**Query params** for list endpoints: `page`, `limit`, `category`, `search`, `sortBy`, `sortOrder`.

**Metadata** sub-endpoints: `GET /api/{category}/meta/categories`, `/meta/stats`, `/meta/authors`.

## Project Structure

```
wapow-ui/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── StoryFeed.vue    # Vertical swipe feed
│   │   ├── StoryView.vue    # Article story card
│   │   ├── VerticalVideoView.vue
│   │   ├── PodcastView.vue
│   │   ├── TopBar.vue
│   │   ├── BottomNavigation.vue
│   │   └── CategoryNavigation.vue
│   ├── views/               # Route pages
│   │   ├── HomeView.vue
│   │   ├── SavedView.vue
│   │   ├── ProfileView.vue
│   │   ├── LoginView.vue
│   │   ├── ArticleView.vue
│   │   └── AuthCallbackView.vue
│   ├── stores/
│   │   ├── auth.ts          # Auth state (Pinia + Auth0)
│   │   └── videos.ts        # Content store
│   ├── lib/
│   │   ├── api.ts           # API client (auto-attaches Bearer token)
│   │   └── auth0.ts         # Auth0 configuration
│   └── router/index.ts      # Routes + auth guards

wapow-app/
├── api/
│   ├── routers/
│   │   ├── content.py       # Dynamic content routers per category
│   │   ├── articles.py      # Cross-collection article fetching
│   │   ├── recommendations.py  # Neo4j recommendation engine
│   │   └── saved_articles.py   # Save/unsave content
│   ├── services/
│   │   ├── content.py       # Content query logic
│   │   └── user.py          # User upsert + saved content management
│   ├── db/
│   │   ├── mongodb.py       # MongoDB client
│   │   └── neo4j_query.py   # Neo4j driver + query execution
│   ├── scripts/
│   │   ├── seed_neo4j.py    # Seed recommendation graph
│   │   └── migrate_saved_to_users.py
│   ├── auth.py              # Auth0 JWT validation
│   ├── config.py            # Environment config
│   └── main.py              # FastAPI app + lifespan
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml
```

## Docker (Full Stack)

Run everything with Docker Compose from `wapow-app/`:

```bash
docker compose up -d
```

Services:
- **mongo** — MongoDB 7 on port `27017`
- **neo4j** — Neo4j 5 on ports `7474` / `7687`
- **app** — FastAPI on port `3001`

## Auth0 Setup

Both the frontend and backend integrate with Auth0 for authentication. See the detailed setup guides:

- Backend: [`wapow-app/docs/AUTH0_SETUP.md`](wapow-app/docs/AUTH0_SETUP.md)
- Frontend: [`wapow-ui/docs/AUTH0_SETUP.md`](wapow-ui/docs/AUTH0_SETUP.md)

**TL;DR:**
1. Create an Auth0 tenant, SPA application, and API
2. Set `AUTH0_DOMAIN` + `AUTH0_AUDIENCE` in the backend `.env`
3. Set `VITE_AUTH0_DOMAIN` + `VITE_AUTH0_CLIENT_ID` + `VITE_AUTH0_AUDIENCE` in the frontend `.env`
4. Add `http://localhost:3000/auth/callback` to Auth0's Allowed Callback URLs

## License

Private project.
