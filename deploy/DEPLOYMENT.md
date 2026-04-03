## WAPOW deployment (Docker + Nginx on a VM)

### 1. Frontend (Vercel)

The UI is deployed to **Vercel** (not on the Droplet). See **[deploy/VERCEL.md](VERCEL.md)** for project root directory, env vars (`VITE_API_URL`, `VITE_COLLECTOR_URL`, Auth0), and DNS.

### 2. Backend + databases with Docker Compose

On the server, clone the **repository root** (not only `wapow-app/`) so paths like `wapow-app/migrations` and `deploy/nginx.conf` resolve. Example:

```bash
sudo mkdir -p /opt && sudo git clone <your-repo-url> /opt/wapow
cd /opt/wapow
```

Create `wapow-app/.env` with MongoDB, Neo4j, Auth0, **`CORS_ORIGINS`** (comma-separated Vercel + custom domains), and server settings:

```bash
cp wapow-app/.env.dev wapow-app/.env   # or create a fresh .env
vim wapow-app/.env
```

For a production-style stack with Nginx and internal-only databases, set **`REGISTRY_PREFIX`** to your DigitalOcean registry base (same value GitHub Actions uses: `registry.digitalocean.com/<registry-name>`), then:

```bash
export REGISTRY_PREFIX=registry.digitalocean.com/your-registry-name
docker compose -f docker-compose.prod.yml up -d
```

CI builds and pushes `wapow-app` and `wapow-collector` images; the compose file uses those images (no local `build` for those services).

This starts:

- `mongo` (no public port)
- `neo4j` (no public port; admin via SSH tunnel)
- `clickhouse` (no public port; init run from `wapow-app/migrations`)
- `wapow-api` (FastAPI, internal only)
- `wapow-collector` (analytics, internal only)
- `wapow-nginx` (public, port 80 → serves UI + proxies `/api` and `/collect`)

Health checks:

- API health: `curl http://localhost/api/health` from the server
- ClickHouse: `docker exec -it wapow-clickhouse clickhouse client --query 'SELECT 1'`

### 3. Nginx (Droplet)

The production compose file mounts only `deploy/nginx.conf`. The UI is on **Vercel**.

`deploy/nginx.conf`:

- **`api.tunedin.live`** → FastAPI (`app:3001`)
- **`collector.tunedin.live`** → collector (`collector:3002`)
- **Default server** → short text (SPA is not served here)

### 4. Auth0 configuration

Backend (`wapow-app/.env`):

```env
AUTH0_DOMAIN=your-tenant.us.auth0.com
AUTH0_AUDIENCE=https://api.wapow.example.com
CORS_ORIGINS=https://tunedin.live,https://www.tunedin.live,https://your-app.vercel.app
```

Frontend: set the same Auth0 values in **Vercel** env vars (see [VERCEL.md](VERCEL.md)):

```text
VITE_AUTH0_DOMAIN=...
VITE_AUTH0_CLIENT_ID=...
VITE_AUTH0_AUDIENCE=...
VITE_API_URL=https://api.tunedin.live
VITE_COLLECTOR_URL=https://collector.tunedin.live
```

Auth0 dashboard:

- Allowed Callback URLs: your Vercel / custom domain (e.g. `https://tunedin.live/auth/callback`)
- Allowed Logout URLs: same origins + `/login`
- Allowed Web Origins: production + preview URLs as needed

See `wapow-app/docs/AUTH0_SETUP.md` and `wapow-ui/docs/AUTH0_SETUP.md` for full details.

### 5. Local vs production

- Use `docker-compose.yml` for local dev (databases and API exposed on localhost).
- Use `docker-compose.prod.yml` for production (only Nginx exposes 80/443).

