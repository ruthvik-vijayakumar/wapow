# WAPOW API

Combined FastAPI app: **MongoDB** content API (translated from the Node.js wapow-app) + **Neo4j** recommendations (from grapow).

- **Package manager:** Poetry  
- **Framework:** FastAPI  
- **Databases:** MongoDB (content), Neo4j (recommendations)

## Setup

From the project root (`wapow-app/`):

```bash
poetry install
```

## Environment

Create a `.env` in the project root (or set env vars):

```env
# MongoDB (default: mongodb://localhost:27017/wapow-data)
MONGODB_URI=mongodb://localhost:27017/wapow-data
# or MONGODB_LOCAL_URI

# Neo4j (for recommendations)
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password

# Server port (default: 3001)
PORT=3001
```

## Run

```bash
poetry run uvicorn api.main:app --host 0.0.0.0 --port 3001 --reload
```

Or:

```bash
poetry run python -m api.main
```

- API: http://localhost:3001  
- OpenAPI: http://localhost:3001/docs  

## Docker (like Node.js project)

From the project root:

```bash
# Build and start MongoDB, Neo4j, and app
docker compose up -d

# Or build only
docker compose build

# Logs
docker compose logs -f app
```

- **mongo:** `mongo:7`, port `27017`, volume `mongo_data`, healthcheck.
- **neo4j:** `neo4j:5`, HTTP `7474`, Bolt `7687`, volume `neo4j_data`. Default auth: user `neo4j`, password `wapow-neo4j` (override with `NEO4J_PASSWORD` in `.env`).
- **app:** builds from `Dockerfile`, port `3001`. In Docker, `MONGODB_URI` defaults to `mongodb://mongo:27017/wapow-data` and `NEO4J_URI` to `neo4j://neo4j:7687`; `NEO4J_PASSWORD` defaults to `wapow-neo4j`. Override any of these in `.env` if needed.

Stop:

```bash
docker compose down
```  

## Neo4j seed data (for recommendations)

Recommendations return empty until Neo4j has graph data (Users, Articles, Categories, READ, etc.). Seed minimal data from the project root:

```bash
poetry run python -m api.scripts.seed_neo4j
```

Or with Docker Neo4j running and app running locally:

```bash
# NEO4J_URI=neo4j://localhost:7687 and NEO4J_PASSWORD=wapow-neo4j (default in config)
poetry run python -m api.scripts.seed_neo4j
```

Then call `POST /api/recommendations` with e.g. `{"user_id": "1", "category": "sports"}`. The seed creates user id `"1"` and sample users/articles so collaborative filtering returns results.

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Welcome + endpoint list |
| `GET /health` | Health check (MongoDB ping) |
| `GET /api/sports`, `/api/style`, `/api/technology`, `/api/travel`, `/api/wellbeing` | Content list, pagination, filters, `/:id`, `GET /meta/categories`, `GET /meta/stats`, `GET /meta/authors`, `POST /by-ids` |
| `GET /api/videos`, `GET /api/podcasts` | Same pattern for videos and podcasts |
| `POST /api/articles/by-ids` | Body: `{"ids": ["id1", "id2"]}` — fetch across all collections |
| `GET /api/recommendations` | Returns endpoint info. |
| `POST /api/recommendations` | Body: `{"user_id": "...", "category": "technology", "current_hour": 14, "limit": 10}` — Neo4j collaborative filtering |

Query params for list endpoints: `page`, `limit`, `category`, `search`, `sortBy`, `sortOrder`.

---

## Auth (optional – offload to Auth0)

To protect routes with JWT-based auth, use **Auth0** (or any OIDC/JWT issuer) and validate tokens in the API.

### Install and configure Auth0

1. **Install dependencies** (includes JWT validation):
   ```bash
   poetry install
   ```
2. **Follow the step-by-step guide:** [docs/AUTH0_SETUP.md](docs/AUTH0_SETUP.md) — create tenant, API, application, then set `AUTH0_DOMAIN` and `AUTH0_AUDIENCE` in `.env`.
3. **Restart the app** so it picks up the new env vars. `GET /` will show `"auth": "enabled"` when Auth0 is configured.

### Why Auth0

- **Managed:** No password storage or session DB in your app.
- **OIDC/JWT:** Standard Bearer tokens; easy to validate in FastAPI.
- **Free tier:** Enough for many apps; upgrade as you grow.
- **Alternatives:** Clerk (great DX), Okta, Keycloak (self-hosted), AWS Cognito (if on AWS).

### Setup Auth0

1. Sign up at [auth0.com](https://auth0.com).
2. Create an **Application** (e.g. SPA or Native) for your frontend; get **Client ID** and **Domain**.
3. Create an **API** in the dashboard; set the **Identifier** (e.g. `https://api.wapow.example.com`) – this is `AUTH0_AUDIENCE`.
4. In your app’s `.env`:
   ```env
   AUTH0_DOMAIN=your-tenant.us.auth0.com
   AUTH0_AUDIENCE=https://api.wapow.example.com
   ```
5. Frontend: use Auth0 SDK (e.g. `@auth0/auth0-react`) to log in and get an **access token** for your API audience.
6. Call the API with `Authorization: Bearer <access_token>`.

### Integration in this app

- **Config:** `api/config.py` reads `AUTH0_DOMAIN` and `AUTH0_AUDIENCE`. If both are set, auth is enabled.
- **Validation:** `api/auth.py` uses PyJWT + Auth0’s JWKS to verify the Bearer token and expose claims.
- **Protected route example:** `GET /api/me` uses `Depends(get_current_user)` – it returns 401 when the token is missing/invalid, and 501 when auth is not configured.
- **Protecting more routes:** Add `user: UserClaims = Depends(get_current_user)` to any route; optionally use `get_current_user_optional` for “auth if present” behavior.

```python
from api.auth import get_current_user, UserClaims

@router.get("/protected")
async def protected(user: UserClaims = Depends(get_current_user)):
    return {"user_id": user.user_id}
```

- **Dependency:** `pyjwt[crypto]` is used for RS256 verification; add `poetry add 'pyjwt[crypto]'` if not already in `pyproject.toml`.
