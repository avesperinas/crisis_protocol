import { useCallback, useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate, useParams } from 'react-router-dom'
import { api, socialApi } from '../api/client'
import { FactionBadge } from '../components/FactionBadge'
import { ScenarioBanner } from '../components/ScenarioBanner'
import { ScenarioStage } from '../components/ScenarioStage'
import { factionTheme } from '../theme/factions'
import { useGameSocket } from '../hooks/useGameSocket'
import { usePolling } from '../hooks/usePolling'
import { useAuthStore } from '../store/authStore'
import { useGameStore } from '../store/gameStore'
import type { LobbyStateView } from '../types/game'
import type { FriendEntry } from '../types/social'

export function WaitingRoom() {
  const { t } = useTranslation()
  const { gameId } = useParams<{ gameId: string }>()
  const navigate = useNavigate()
  const session = useGameStore((s) => s.session)
  const authUser = useAuthStore((s) => s.user)
  const [starting, setStarting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [friends, setFriends] = useState<FriendEntry[]>([])
  const [invited, setInvited] = useState<Set<string>>(new Set())

  const fetcher = useMemo(() => {
    if (!session || !gameId) return null
    return () => api.getLobbyState(gameId, session.roleId)
  }, [session, gameId])

  const { data: lobby, refresh } = usePolling<LobbyStateView>(
    fetcher ?? (() => Promise.reject(new Error('no session'))),
    3000,
    !!fetcher,
  )

  useGameSocket(gameId, session?.roleId, useCallback((event) => {
    if (event.type === 'lobby_updated') refresh()
    if (event.type === 'game_started') navigate(`/games/${gameId}/briefing`)
  }, [gameId, navigate, refresh]))

  useEffect(() => {
    if (lobby?.is_started) navigate(`/games/${gameId}/briefing`)
  }, [lobby, gameId, navigate])

  useEffect(() => {
    if (!session) navigate('/')
  }, [session, navigate])

  useEffect(() => {
    if (!authUser) return
    socialApi
      .getFriends()
      .then((d) => setFriends(d.friends.filter((f) => f.direction === 'mutual')))
      .catch(() => setFriends([]))
  }, [authUser])

  if (!session) {
    return null
  }

  const inviteFriend = async (friend: FriendEntry) => {
    if (!gameId || !lobby) return
    try {
      await socialApi.inviteFriend({
        to_user_id: friend.user_id,
        game_id: gameId,
        join_code: lobby.join_code,
        room_name: lobby.room_name,
        scenario_name: lobby.scenario_name,
      })
      setInvited((prev) => new Set(prev).add(friend.user_id))
    } catch (e) {
      setError(String(e))
    }
  }

  const copyCode = async () => {
    if (!lobby) return
    await navigator.clipboard.writeText(lobby.join_code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const start = async () => {
    if (!gameId || !session) return
    setStarting(true)
    setError(null)
    try {
      await api.startGame(gameId, session.roleId)
      navigate(`/games/${gameId}/briefing`)
    } catch (e) {
      setError(String(e))
      setStarting(false)
    }
  }

  return (
    <ScenarioStage scenarioId={lobby?.scenario_id}>
      <main className="max-w-2xl mx-auto p-8 space-y-6">
      <ScenarioBanner
        scenarioId={lobby?.scenario_id}
        scenarioName={lobby?.room_name || lobby?.scenario_name || t('waitingRoom.loading')}
        subtitle={lobby?.room_name ? lobby.scenario_name : t('waitingRoom.title')}
        right={
          lobby && (
            <span
              className="inline-block text-xs px-2 py-0.5 rounded"
              style={{ backgroundColor: 'var(--accent-secondary)', color: 'var(--accent)' }}
            >
              {lobby.async_mode ? t('lobby.paceAsync') : t('lobby.paceRealtime')}
            </span>
          )
        }
      />

      {lobby && (
        <>
          <section className="card space-y-3">
            <h2>{t('waitingRoom.roomCodeTitle')}</h2>
            <div className="flex items-center gap-3">
              <span className="font-mono text-3xl tracking-widest font-bold text-slate-800">
                {lobby.join_code}
              </span>
              <button className="btn text-sm" onClick={copyCode}>
                {copied ? t('waitingRoom.copiedBtn') : t('waitingRoom.copyBtn')}
              </button>
            </div>
            <p className="text-sm text-neutral-600">{t('waitingRoom.roomCodeHint')}</p>
          </section>

          <section className="card space-y-2">
            <h2>{t('waitingRoom.playersTitle')}</h2>
            <ul className="space-y-2">
              {lobby.slots.map((slot) => (
                <li
                  key={slot.role_id}
                  className="flex items-center justify-between text-sm py-1 border-b border-neutral-100 last:border-0"
                >
                  <div className="flex items-center gap-2">
                    <FactionBadge
                      factionId={slot.role_id}
                      name={slot.role_name}
                      scenarioId={lobby.scenario_id}
                      size={24}
                    />
                    <div>
                      <span
                        className="font-medium"
                        style={{ color: factionTheme(lobby.scenario_id, slot.role_id).color }}
                      >
                        {slot.role_name}
                      </span>
                      <span className="text-neutral-500 ml-2">{slot.tagline}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {lobby.connected_roles.includes(slot.role_id) && (
                      <span
                        className="w-2 h-2 rounded-full bg-green-500"
                        title={t('waitingRoom.connected')}
                      />
                    )}
                    {slot.is_taken ? (
                      <span
                        className={`text-xs px-2 py-0.5 rounded ${
                          slot.is_human
                            ? 'bg-indigo-100 text-indigo-800'
                            : 'bg-neutral-100 text-neutral-600'
                        }`}
                      >
                        {slot.is_human ? t('waitingRoom.humanBadge') : t('waitingRoom.botBadge')}
                      </span>
                    ) : (
                      <span className="text-xs text-neutral-400">{t('waitingRoom.freeBadge')}</span>
                    )}
                    {slot.role_id === session.roleId && (
                      <span className="text-xs text-slate-500">{t('waitingRoom.youTag')}</span>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </section>

          {authUser && friends.length > 0 && (
            <section className="card space-y-2">
              <h2>{t('waitingRoom.inviteFriendsTitle')}</h2>
              <ul className="space-y-2">
                {friends.map((f) => (
                  <li key={f.friendship_id} className="flex items-center justify-between text-sm">
                    <span>@{f.username}</span>
                    <button
                      className="btn text-xs"
                      disabled={invited.has(f.user_id)}
                      onClick={() => inviteFriend(f)}
                    >
                      {invited.has(f.user_id)
                        ? t('waitingRoom.invitedBtn')
                        : t('waitingRoom.inviteBtn')}
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {error && <div className="text-sm text-red-700">{error}</div>}

          {lobby.is_host ? (
            <div className="flex items-center gap-4">
              <button className="btn-primary" disabled={starting} onClick={start}>
                {starting ? t('waitingRoom.startingBtn') : t('waitingRoom.startBtn')}
              </button>
              <span className="text-sm text-neutral-600">{t('waitingRoom.freeSlotsHint')}</span>
            </div>
          ) : (
            <div className="card text-sm text-neutral-600">{t('waitingRoom.waitingHost')}</div>
          )}
        </>
      )}
      </main>
    </ScenarioStage>
  )
}
