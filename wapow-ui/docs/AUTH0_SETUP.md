# Auth0 Setup for wapow-ui

This guide configures Auth0 for the wapow-ui frontend. The backend (wapow-app) validates JWT tokens; the frontend uses Auth0 to log users in and obtain access tokens.

## 1. Auth0 Dashboard Setup

Follow [wapow-app/docs/AUTH0_SETUP.md](../../wapow-app/docs/AUTH0_SETUP.md) to create:

- Auth0 tenant (note **Domain**)
- API with Identifier = `AUTH0_AUDIENCE` (e.g. `https://api.wapow.example.com` or `http://localhost:3001`)
- **Single Page Application** for the frontend

## 2. SPA Application Settings

In your SPA application (Auth0 Dashboard → Applications → your app → Settings):

- **Allowed Callback URLs:** `http://localhost:3000/auth/callback` (add production URL when deployed)
- **Allowed Logout URLs:** `http://localhost:3000/login` (add production `/login` URL when deployed)
- **Allowed Web Origins:** `http://localhost:3000`
- **Application Type:** Single Page Application

## 3. Authorize the API

In Auth0 Dashboard → APIs → your WAPOW API → Machine to Machine Applications (or APIs tab):

- Ensure your SPA is authorized to access the API (if using M2M; for SPA, the user logs in and requests an access token with the API as audience)

For SPA with Authorization Code + PKCE, the `audience` in `authorizationParams` ensures the access token is issued for your API.

## 4. Environment Variables

Create `.env` in wapow-ui root (copy from `.env.example`):

```env
VITE_AUTH0_DOMAIN=your-tenant.us.auth0.com
VITE_AUTH0_CLIENT_ID=your-spa-client-id
VITE_AUTH0_AUDIENCE=https://api.wapow.example.com
VITE_API_URL=http://localhost:3001
```

Values must match the backend's `AUTH0_DOMAIN` and `AUTH0_AUDIENCE`.

## 5. Usage

- `useAuth()` – sign in, sign out, get user, get access token
- `apiFetch('/api/me')` – automatically attaches Bearer token for authenticated API calls
- Protected backend routes (e.g. `GET /api/me`) require `Authorization: Bearer <token>`

## 6. Verify

1. Start wapow-app: `cd wapow-app && poetry run uvicorn api.main:app --port 3001`
2. Start wapow-ui: `cd wapow-ui && yarn dev`
3. Open `http://localhost:3000`, click Login, complete Auth0 flow
4. Call `GET /api/me` with the token – backend should return user claims
