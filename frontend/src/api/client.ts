import { useAuthStore } from '../store/authStore'
import type { AuthUser, TokenResponse } from '../types/auth'
import type {
  ActionSubmission,
  ActionSubmittedResponse,
  FinalResultView,
  GameCreatedResponse,
  GameStateView,
  LobbyStateView,
  PactBreakResult,
  PactProposalResult,
  PactType,
  ScenarioInfo,
} from '../types/game'
import type {
  FriendsListView,
  GameHistoryEntry,
  UserSearchResult,
  UserStats,
} from '../types/social'

// 127.0.0.1, not "localhost" — on machines where localhost resolves to ::1
// first, uvicorn's IPv4-only default bind makes "localhost" silently
// unreachable from the browser. In the production Docker build VITE_API_BASE
// is set to "" so calls go out as relative /api/... paths, which nginx then
// proxies to the backend container — see frontend/nginx.conf.
const BASE = import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8000'

class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function rawRequest<T>(
  path: string,
  init: RequestInit | undefined,
  token: string | null,
): Promise<T> {
  const r = await fetch(BASE + path, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers ?? {}),
    },
  })
  if (!r.ok) {
    const text = await r.text()
    throw new ApiError(r.status, `${r.status} ${r.statusText}: ${text}`)
  }
  return r.json() as Promise<T>
}

/** Attaches the access token automatically and retries once via refresh on 401. */
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const { accessToken, refreshToken, setAuth, clearAuth } = useAuthStore.getState()
  try {
    return await rawRequest<T>(path, init, accessToken)
  } catch (e) {
    const isAuthRoute = path.startsWith('/api/auth/')
    if (e instanceof ApiError && e.status === 401 && refreshToken && !isAuthRoute) {
      try {
        const refreshed = await rawRequest<TokenResponse>(
          '/api/auth/refresh',
          { method: 'POST', body: JSON.stringify({ refresh_token: refreshToken }) },
          null,
        )
        setAuth(
          { access_token: refreshed.access_token, refresh_token: refreshed.refresh_token },
          refreshed.user,
        )
        return await rawRequest<T>(path, init, refreshed.access_token)
      } catch {
        clearAuth()
        throw e
      }
    }
    throw e
  }
}

export const authApi = {
  register: (email: string, username: string, password: string, locale: string) =>
    request<TokenResponse>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, username, password, locale }),
    }),

  login: (email: string, password: string) =>
    request<TokenResponse>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  logout: (refresh_token: string) =>
    request<{ ok: boolean }>('/api/auth/logout', {
      method: 'POST',
      body: JSON.stringify({ refresh_token }),
    }),

  me: () => request<AuthUser>('/api/auth/me'),
}

export const api = {
  listScenarios: () => request<ScenarioInfo[]>('/api/scenarios'),

  createGame: (
    scenario_id: string,
    human_role_id: string,
    mode: 'solo' | 'multiplayer' = 'solo',
    room_name?: string,
    async_mode = false,
  ) =>
    request<GameCreatedResponse>('/api/games', {
      method: 'POST',
      body: JSON.stringify({
        scenario_id,
        human_role_id,
        mode,
        room_name: room_name || null,
        async_mode,
      }),
    }),

  joinGame: (join_code: string, role_id: string) =>
    request<GameCreatedResponse>('/api/games/join', {
      method: 'POST',
      body: JSON.stringify({ join_code, role_id }),
    }),

  getLobbyByCode: (joinCode: string) =>
    request<LobbyStateView>(`/api/games/by-code/${encodeURIComponent(joinCode)}`),

  getLobbyState: (gameId: string, roleId: string) =>
    request<LobbyStateView>(
      `/api/games/${gameId}/lobby?role_id=${encodeURIComponent(roleId)}`,
    ),

  startGame: (gameId: string, roleId: string) =>
    request<{ ok: boolean }>(
      `/api/games/${gameId}/start?role_id=${encodeURIComponent(roleId)}`,
      { method: 'POST' },
    ),

  getState: (gameId: string, roleId: string) =>
    request<GameStateView>(
      `/api/games/${gameId}/state?role_id=${encodeURIComponent(roleId)}`,
    ),

  submitAction: (gameId: string, roleId: string, action: ActionSubmission) =>
    request<ActionSubmittedResponse>(
      `/api/games/${gameId}/actions?role_id=${encodeURIComponent(roleId)}`,
      { method: 'POST', body: JSON.stringify(action) },
    ),

  getResult: (gameId: string) => request<FinalResultView>(`/api/games/${gameId}/result`),

  proposePact: (
    gameId: string,
    roleId: string,
    targetRoleId: string,
    pactType: PactType,
    isSecret = false,
  ) =>
    request<PactProposalResult>(
      `/api/games/${gameId}/pacts/propose?role_id=${encodeURIComponent(roleId)}`,
      {
        method: 'POST',
        body: JSON.stringify({
          target_role_id: targetRoleId,
          pact_type: pactType,
          is_secret: isSecret,
        }),
      },
    ),

  breakPact: (gameId: string, roleId: string, pactId: string) =>
    request<PactBreakResult>(
      `/api/games/${gameId}/pacts/${pactId}/break?role_id=${encodeURIComponent(roleId)}`,
      { method: 'POST' },
    ),

  sendMessage: (
    gameId: string,
    roleId: string,
    content: string,
    toRoleId: string | null = null,
  ) =>
    request<{ message_id: string }>(
      `/api/games/${gameId}/messages?role_id=${encodeURIComponent(roleId)}`,
      {
        method: 'POST',
        body: JSON.stringify({ to_role_id: toRoleId, content }),
      },
    ),
}

export const socialApi = {
  searchUsers: (q: string) =>
    request<UserSearchResult[]>(`/api/users/search?q=${encodeURIComponent(q)}`),

  getFriends: () => request<FriendsListView>('/api/friends'),

  sendFriendRequest: (username: string) =>
    request<{ ok: boolean }>('/api/friends/request', {
      method: 'POST',
      body: JSON.stringify({ username }),
    }),

  acceptFriend: (friendshipId: string) =>
    request<{ ok: boolean }>(`/api/friends/${friendshipId}/accept`, { method: 'POST' }),

  removeFriend: (friendshipId: string) =>
    request<{ ok: boolean }>(`/api/friends/${friendshipId}`, { method: 'DELETE' }),

  inviteFriend: (params: {
    to_user_id: string
    game_id: string
    join_code: string
    room_name: string | null
    scenario_name: string
  }) =>
    request<{ ok: boolean }>('/api/friends/invite', {
      method: 'POST',
      body: JSON.stringify(params),
    }),

  dismissInvite: (inviteId: string) =>
    request<{ ok: boolean }>(`/api/friends/invites/${inviteId}`, { method: 'DELETE' }),

  getStats: () => request<UserStats>('/api/users/me/stats'),

  getGameHistory: () => request<GameHistoryEntry[]>('/api/users/me/games'),
}
