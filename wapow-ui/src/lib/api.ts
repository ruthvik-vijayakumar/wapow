/**
 * API client for wapow-app backend.
 * Attaches Bearer token from the auth store when the user is authenticated.
 */
import { useAuthStore } from '@/stores/auth'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:3001'

export async function apiFetch(
  path: string,
  options: RequestInit = {},
): Promise<Response> {
  const authStore = useAuthStore()

  let token: string | null = null
  try {
    token = await authStore.getAccessToken()
  } catch {
    // Token retrieval failed — continue without auth
  }

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  }

  if (token) {
    ;(headers as Record<string, string>)['Authorization'] = `Bearer ${token}`
  }

  return fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })
}

export function getApiBase(): string {
  return API_BASE
}
