# Environment variables: local vs production

This project has **three** places env vars show up: **local dev**, **Docker Compose**, and **Vercel (frontend prod)**. This doc maps what goes where.

## Quick reference

| Area | File / location | Purpose |
|------|-----------------|--------|
| API local (no Docker) | [`wapow-app/.env.dev`](../wapow-app/.env.dev) | Loaded by [`api/config.py`](../wapow-app/api/config.py) via `load_dotenv` |
| API in Docker (dev) | Repo **`.env`** next to [`docker-compose.yml`](../docker-compose.yml), **or** `environment:` in compose | Compose substitutes `${VAR}`; container env overrides app defaults |
| API in Docker (prod) | **`.env`** next to [`docker-compose.prod.yml`](../docker-compose.prod.yml) on the Droplet | Same; see [`deploy/env.production.example`](env.production.example) |
| UI local | [`wapow-ui/.env`](../wapow-ui/.env) (from [`.env.example`](../wapow-ui/.env.example)) | Vite `import.meta.env.VITE_*` at **build** time |
| UI production | **Vercel** project → Environment Variables | Same `VITE_*` names; set per Production / Preview |
| CI push images | [`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml) | `REGISTRY_PREFIX` from `DO_REGISTRY_NAME` secret; `DO_API_TOKEN`, etc. |

---

## Local development (no Docker for API)

```bash
cd wapow-app
poetry install
# Uses wapow-app/.env.dev (see api/config.py)
poetry run uvicorn api.main:app --host 0.0.0.0 --port 3001 --reload
```

```bash
cd wapow-ui
cp .env.example .env
npm install && npm run dev
```

Key vars: `MONGODB_URI`, `NEO4J_*`, `AUTH0_*`, `VITE_*`.

---

## Local development (Docker Compose)

From the **repository root** (where `docker-compose.yml` lives):

```bash
docker compose up -d
```

Compose automatically reads a **`.env`** file **in the same directory** as `docker-compose.yml` (if present) for variable substitution like `${MONGODB_URI:-...}`.

- **Do not** rely on `wapow-app/.env.dev` being copied into the image unless you bake it in; the **dev** [`docker-compose.yml`](../docker-compose.yml) passes `MONGODB_URI`, `NEO4J_*`, `AUTH0_*` via `environment:`.
- To override: create **repo root** `.env` (gitignored) with e.g. `NEO4J_PASSWORD=...`, or `export` variables before `docker compose up`.

Services and typical ports:

| Service | Host port (dev) |
|---------|-------------------|
| API | 3001 |
| Collector | 3002 |
| Mongo | 127.0.0.1:27017 |
| Neo4j | 127.0.0.1:7474 / 7687 |
| ClickHouse | 127.0.0.1:8123 |

---

## Production (DigitalOcean Droplet + Docker Compose)

1. Clone the **repo root** on the server (paths like `./wapow-app/migrations` and `./deploy/nginx.conf` are relative to that root).

2. Copy [`deploy/env.production.example`](env.production.example) to **`.env`** in the **same directory** as `docker-compose.prod.yml`:

   ```bash
   cp deploy/env.production.example .env
   vim .env
   ```

3. Set at minimum:

   - **`REGISTRY_PREFIX`** — full registry base, e.g. `registry.digitalocean.com/your-registry` (no trailing slash). Required for `app` / `collector` images.
   - **`MONGODB_URI`**, **`NEO4J_*`**, **`AUTH0_*`**, **`CORS_ORIGINS`** (comma-separated `https://` origins for your Vercel app + custom domain).

4. Bring the stack up:

   ```bash
   export $(grep -v '^#' .env | xargs)   # optional: load into shell
   docker compose -f docker-compose.prod.yml up -d
   ```

`docker compose` loads `.env` from the project directory for interpolation **without** needing `export` if you only use `${VAR}` in the YAML (Compose reads `.env` automatically).

---

## Production frontend (Vercel)

Vite bakes **`VITE_*`** at **build** time. In Vercel → Project → Settings → Environment Variables, set (examples):

| Variable | Example |
|----------|---------|
| `VITE_API_URL` | `https://api.tunedin.live` |
| `VITE_COLLECTOR_URL` | `https://collector.tunedin.live` |
| `VITE_AUTH0_DOMAIN` | your Auth0 domain |
| `VITE_AUTH0_CLIENT_ID` | SPA client id |
| `VITE_AUTH0_AUDIENCE` | API identifier (must match backend `AUTH0_AUDIENCE`) |

Redeploy after changing `VITE_*`. See also [`deploy/VERCEL.md`](VERCEL.md).

---

## GitHub Actions (build & push images)

Repository **Secrets** (Settings → Secrets and variables → Actions):

| Secret | Used for |
|--------|----------|
| `DO_REGISTRY_NAME` | Registry **slug** only; workflow builds `REGISTRY_PREFIX=registry.digitalocean.com/<slug>` |
| `DO_API_TOKEN` | `docker login` and Droplet pull |
| `DROPLET_IP`, `SSH_PRIVATE_KEY` | SSH deploy |
| `DEPLOY_PATH` | Optional; clone path on Droplet (default `/opt/wapow` in docs) |

The workflow does **not** push `.env` to the server; the Droplet must have its own `.env` for Compose.

---

## Security notes

- Never commit real **`.env`** files with secrets. Use `*.example` templates only.
- `wapow-app/.env.dev` in the repo may contain dev-only values; use production-specific values only on the Droplet / Vercel.
