import { create } from 'zustand'

interface Session {
  gameId: string
  roleId: string
  userToken: string
}

const STORAGE_KEY = 'crisis-protocol-session'

function loadSession(): Session | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as Session) : null
  } catch {
    return null
  }
}

function saveSession(s: Session | null): void {
  if (s) sessionStorage.setItem(STORAGE_KEY, JSON.stringify(s))
  else sessionStorage.removeItem(STORAGE_KEY)
}

interface GameStore {
  session: Session | null
  setSession: (s: Session | null) => void
}

export const useGameStore = create<GameStore>((set) => ({
  session: loadSession(),
  setSession: (s) => {
    saveSession(s)
    set({ session: s })
  },
}))
