import { create } from 'zustand'
import type { AuthUser } from '../types/auth'

const STORAGE_KEY = 'crisis-protocol-auth'

interface Persisted {
  accessToken: string
  refreshToken: string
  user: AuthUser
}

function loadAuth(): Persisted | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as Persisted) : null
  } catch {
    return null
  }
}

function saveAuth(p: Persisted | null): void {
  if (p) localStorage.setItem(STORAGE_KEY, JSON.stringify(p))
  else localStorage.removeItem(STORAGE_KEY)
}

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  user: AuthUser | null
  setAuth: (tokens: { access_token: string; refresh_token: string }, user: AuthUser) => void
  setAccessToken: (token: string) => void
  clearAuth: () => void
}

const initial = loadAuth()

export const useAuthStore = create<AuthState>((set, get) => ({
  accessToken: initial?.accessToken ?? null,
  refreshToken: initial?.refreshToken ?? null,
  user: initial?.user ?? null,

  setAuth: (tokens, user) => {
    const next = { accessToken: tokens.access_token, refreshToken: tokens.refresh_token, user }
    saveAuth(next)
    set(next)
  },

  setAccessToken: (token) => {
    set({ accessToken: token })
    const { refreshToken, user } = get()
    if (refreshToken && user) saveAuth({ accessToken: token, refreshToken, user })
  },

  clearAuth: () => {
    saveAuth(null)
    set({ accessToken: null, refreshToken: null, user: null })
  },
}))
