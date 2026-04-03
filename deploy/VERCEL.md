# Frontend on Vercel (API on DigitalOcean)

The Vue app (`wapow-ui`) is deployed to **Vercel**. The API stays on your Droplet at **`api.tunedin.live`** and the analytics collector at **`collector.tunedin.live`**.

## 1. Vercel project

1. Import the Git repo in [Vercel](https://vercel.com).
2. Set **Root Directory** to `wapow-ui`.
3. Framework: **Vite** (auto-detected). Build: `npm run build`, output: `dist`.

`vercel.json` adds SPA **rewrites** so Vue Router history mode works on refresh.

## 2. Environment variables (Vercel → Project → Settings → Environment Variables)

Set for **Production** (and **Preview** if you want preview deploys to hit real APIs):

| Name | Example |
|------|---------|
| `VITE_API_URL` | `https://api.tunedin.live` |
| `VITE_COLLECTOR_URL` | `https://collector.tunedin.live` |
| `VITE_AUTH0_DOMAIN` | `your-tenant.us.auth0.com` |
| `VITE_AUTH0_CLIENT_ID` | (SPA client id) |
| `VITE_AUTH0_AUDIENCE` | (same as API identifier on backend) |

Redeploy after changing env vars (they are baked in at build time).

## 3. Auth0

- **Allowed Callback URLs:** `https://tunedin.live/auth/callback`, `https://www.tunedin.live/auth/callback`, plus `https://*.vercel.app/auth/callback` for previews (if Auth0 supports wildcard; otherwise add each preview host).
- **Allowed Logout URLs:** same origins + `/login`.
- **Allowed Web Origins:** your Vercel production URL, custom domain, and preview URLs as needed.

## 4. Droplet: CORS

In `wapow-app/.env` (or compose env), set **comma-separated** origins (no spaces required, but trims are OK):

```env
CORS_ORIGINS=https://tunedin.live,https://www.tunedin.live,https://your-app.vercel.app
```

Use your real Vercel production domain and any preview URLs that should call the API. Restart containers after changing.

The same `CORS_ORIGINS` value is passed to the **collector** service in `docker-compose.prod.yml`.

## 5. DNS

- **tunedin.live** / **www** → Vercel (as in Vercel’s DNS instructions).
- **api.tunedin.live** / **collector.tunedin.live** → Droplet IP (same as today).

## 6. Optional preview deploys

Each preview gets a unique `*.vercel.app` URL. Browsers will send that as `Origin`. Either:

- Add preview URLs to `CORS_ORIGINS` when you need them, or  
- Use a stable **Preview** API subdomain and accept broader CORS only in staging (not recommended for production secrets).
