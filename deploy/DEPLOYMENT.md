## WAPOW deployment (Docker + Nginx on a VM)

### 1. Build the frontend

On your CI or directly on the server:

```bash
cd wapow-ui
cp .env.example .env  # edit for production
# Set these to your public domain, no /api suffix
# VITE_API_URL=https://wapow.example.com
# VITE_COLLECTOR_URL=https://wapow.example.com
npm ci
npm run build
```

Copy the built assets to `/var/www/wapow-ui` on the server:

```bash
sudo mkdir -p /var/www/wapow-ui
sudo rsync -av dist/ /var/www/wapow-ui/
```

### 2. Backend + databases with Docker Compose

From `wapow-app/` on the server:

```bash
cd wapow-app
cp .env.dev .env  # or create a fresh .env with prod values

# Important: set MongoDB, Neo4j, Auth0, and ClickHouse env vars
vim .env
```

For a production-style stack with Nginx and internal-only databases, use:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

This starts:

- `mongo` (no public port)
- `neo4j` (no public port; admin via SSH tunnel)
- `clickhouse` (no public port; init run from `./migrations`)
- `wapow-api` (FastAPI, internal only)
- `wapow-collector` (analytics, internal only)
- `wapow-nginx` (public, port 80 → serves UI + proxies `/api` and `/collect`)

Health checks:

- API health: `curl http://localhost/api/health` from the server
- ClickHouse: `docker exec -it wapow-clickhouse clickhouse client --query 'SELECT 1'`

### 3. Nginx

The production compose file mounts:

- Nginx config: `../deploy/nginx.conf` → `/etc/nginx/nginx.conf`
- UI assets: `/var/www/wapow-ui` → `/var/www/wapow-ui` (inside container)

`deploy/nginx.conf`:

- Serves the Vue app with SPA history fallback (`try_files $uri $uri/ /index.html`)
- Proxies `/api/` to `wapow-api:3001`
- Proxies `/collect/` to `wapow-collector:3002`

### 4. Auth0 configuration

Backend (`wapow-app/.env`):

```env
AUTH0_DOMAIN=your-tenant.us.auth0.com
AUTH0_AUDIENCE=https://api.wapow.example.com
```

Frontend (`wapow-ui/.env`):

```env
VITE_AUTH0_DOMAIN=your-tenant.us.auth0.com
VITE_AUTH0_CLIENT_ID=your-spa-client-id
VITE_AUTH0_AUDIENCE=https://api.wapow.example.com
VITE_API_URL=https://wapow.example.com
VITE_COLLECTOR_URL=https://wapow.example.com
```

Auth0 dashboard:

- Allowed Callback URLs: `https://wapow.example.com/auth/callback`
- Allowed Logout URLs: `https://wapow.example.com/login`
- Allowed Web Origins: `https://wapow.example.com`

See `wapow-app/docs/AUTH0_SETUP.md` and `wapow-ui/docs/AUTH0_SETUP.md` for full details.

### 5. Local vs production

- Use `docker-compose.yml` for local dev (databases and API exposed on localhost).
- Use `docker-compose.prod.yml` for production (only Nginx exposes 80/443).

