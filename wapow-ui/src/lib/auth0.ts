/**
 * Auth0 configuration for wapow-ui.
 * Set VITE_AUTH0_DOMAIN, VITE_AUTH0_CLIENT_ID, VITE_AUTH0_AUDIENCE in .env
 */
function getRedirectUri(): string {
  const envOverride = import.meta.env.VITE_AUTH0_CALLBACK_URL as string | undefined
  if (envOverride) return envOverride
  if (typeof window === 'undefined') return ''
  let origin = window.location.origin
  // Auth0 rejects 0.0.0.0 - use localhost when bound to 0.0.0.0
  if (origin.includes('0.0.0.0')) {
    origin = origin.replace('0.0.0.0', 'localhost')
  }
  return `${origin}/auth/callback`
}

export const auth0Config = {
  domain: import.meta.env.VITE_AUTH0_DOMAIN as string,
  clientId: import.meta.env.VITE_AUTH0_CLIENT_ID as string,
  authorizationParams: {
    redirect_uri: getRedirectUri(),
    audience: import.meta.env.VITE_AUTH0_AUDIENCE as string,
    scope: 'openid profile email',
  },
  cacheLocation: 'localstorage' as const,
}

// Log redirect_uri in dev to help debug Auth0 callback URL config
if (import.meta.env.DEV && auth0Config.authorizationParams.redirect_uri) {
  console.log('[Auth0] Callback URL:', auth0Config.authorizationParams.redirect_uri, '(add this to Auth0 Allowed Callback URLs)')
}

export const isAuth0Configured = Boolean(
  auth0Config.domain && auth0Config.clientId && auth0Config.authorizationParams.audience
)
