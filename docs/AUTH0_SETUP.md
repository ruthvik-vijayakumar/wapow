# Auth0 install and configuration

This guide gets Auth0 installed and configured so your WAPOW API can validate JWT access tokens and protect routes.

## 1. Install dependencies

From the project root:

```bash
poetry install
```

This installs `pyjwt[crypto]` (already in `pyproject.toml`) for JWT RS256 validation against Auth0’s JWKS.

## 2. Create an Auth0 account and tenant

1. Go to [auth0.com](https://auth0.com) and sign up (or log in).
2. Create a **tenant** if you don’t have one (e.g. `wapow` → domain `wapow.us.auth0.com`).
3. Note your **Domain** (e.g. `wapow.us.auth0.com`) — no `https://`, no trailing slash. This is `AUTH0_DOMAIN`.

## 3. Create an API in Auth0

The API represents your WAPOW backend; its **Identifier** is the audience your tokens will use.

1. In the Auth0 Dashboard, go to **Applications** → **APIs** → **Create API**.
2. **Name:** e.g. `WAPOW API`.
3. **Identifier:** e.g. `https://api.wapow.example.com` or `https://wapow-api`.  
   - Must be a URI-like string. This is `AUTH0_AUDIENCE` — clients request access tokens for this audience.
4. **Signing Algorithm:** RS256 (default).
5. Click **Create**.

Copy the **Identifier**; that’s your `AUTH0_AUDIENCE`.

## 4. Create an Application (for testing or your frontend)

So you can get access tokens to call your API:

1. **Applications** → **Applications** → **Create Application**.
2. **Name:** e.g. `WAPOW Test` or your frontend app name.
3. **Type:** e.g. **Single Page Application** (for a web frontend) or **Machine to Machine** (for scripts/backends).
4. Create.

### Single Page Application (SPA)

- **Settings** → **Application URIs**
  - Allowed Callback URLs: `http://localhost:3000/callback` (or your app URL).
  - Allowed Logout URLs: `http://localhost:3000`.
  - Allowed Web Origins: `http://localhost:3000`.
- **Settings** → **Advanced Settings** → **Grant Types:** ensure **Authorization Code** (and **Refresh Token** if you want refresh).
- Save.

### Machine to Machine (M2M) – for scripts or backend-only

1. **APIs** → select your **WAPOW API** → **Machine to Machine Applications**.
2. Authorize your test application and choose the right scope (e.g. `read:articles` if you defined it).
3. Use **Applications** → your app → **Settings** → **Client ID** and **Client Secret** to get tokens (e.g. via `curl` or a small script).

## 5. Configure your app

### Local / Docker

Create or edit `.env` in the project root (copy from `.env.example`):

```env
# Auth0 (required for protected routes)
AUTH0_DOMAIN=your-tenant.us.auth0.com
AUTH0_AUDIENCE=https://api.wapow.example.com
```

Replace with your **Domain** and API **Identifier** from steps 2 and 3.

### Docker Compose

Same variables; Compose passes them through. Either:

- Put `AUTH0_DOMAIN` and `AUTH0_AUDIENCE` in `.env` next to `docker-compose.yml`, or  
- Set them in the shell before `docker compose up`:

```bash
export AUTH0_DOMAIN=your-tenant.us.auth0.com
export AUTH0_AUDIENCE=https://api.wapow.example.com
docker compose up -d
```

## 6. Verify

1. Start the API (e.g. `poetry run uvicorn api.main:app --host 0.0.0.0 --port 3001` or `docker compose up -d`).
2. **Without token:**  
   `GET /api/me` → **401** (missing/invalid token) or **501** (auth not configured).
3. **With valid token:**  
   Get an access token for your API (Audience = `AUTH0_AUDIENCE`) from Auth0 (e.g. SPA login or M2M client credentials), then:

   ```bash
   curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" http://localhost:3001/api/me
   ```

   You should get JSON with `user_id`, `sub`, etc.

## 7. Protect more routes

In any router or `main.py`:

```python
from api.auth import get_current_user, UserClaims

@router.get("/protected")
async def protected(user: UserClaims = Depends(get_current_user)):
    return {"user_id": user.user_id}
```

Optional auth (e.g. personalize if logged in, else anonymous):

```python
from api.auth import get_current_user_optional

@router.get("/optional")
async def optional(user: UserClaims | None = Depends(get_current_user_optional)):
    if user:
        return {"user_id": user.user_id}
    return {"user_id": None}
```

## Summary

| Step | What you do |
|------|-------------|
| 1 | `poetry install` |
| 2 | Auth0 tenant → note **Domain** → `AUTH0_DOMAIN` |
| 3 | Create API → note **Identifier** → `AUTH0_AUDIENCE` |
| 4 | Create Application (SPA or M2M) for getting tokens |
| 5 | Set `AUTH0_DOMAIN` and `AUTH0_AUDIENCE` in `.env` (and/or Docker env) |
| 6 | Call `GET /api/me` with `Authorization: Bearer <token>` |
| 7 | Use `Depends(get_current_user)` on any route to protect it |

If `AUTH0_DOMAIN` or `AUTH0_AUDIENCE` is missing, the app runs without auth and protected routes return 501 until you set them.
