import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { socialApi } from '../api/client'
import { useAuthStore } from '../store/authStore'
import type { FriendsListView, UserSearchResult } from '../types/social'

export function Friends() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const [data, setData] = useState<FriendsListView | null>(null)
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<UserSearchResult[]>([])
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState<string | null>(null)

  const refresh = () => {
    socialApi.getFriends().then(setData).catch((e) => setError(String(e)))
  }

  useEffect(() => {
    if (user) refresh()
  }, [user])

  useEffect(() => {
    if (!user) navigate('/')
  }, [user, navigate])

  useEffect(() => {
    if (!query.trim()) {
      setResults([])
      return
    }
    const handle = setTimeout(() => {
      socialApi.searchUsers(query.trim()).then(setResults).catch(() => setResults([]))
    }, 300)
    return () => clearTimeout(handle)
  }, [query])

  if (!user) return null

  const sendRequest = async (username: string) => {
    setBusy(username)
    setError(null)
    try {
      await socialApi.sendFriendRequest(username)
      setQuery('')
      setResults([])
      refresh()
    } catch (e) {
      setError(String(e))
    } finally {
      setBusy(null)
    }
  }

  const accept = async (friendshipId: string) => {
    setBusy(friendshipId)
    try {
      await socialApi.acceptFriend(friendshipId)
      refresh()
    } catch (e) {
      setError(String(e))
    } finally {
      setBusy(null)
    }
  }

  const remove = async (friendshipId: string) => {
    setBusy(friendshipId)
    try {
      await socialApi.removeFriend(friendshipId)
      refresh()
    } catch (e) {
      setError(String(e))
    } finally {
      setBusy(null)
    }
  }

  const dismissInvite = async (inviteId: string) => {
    setBusy(inviteId)
    try {
      await socialApi.dismissInvite(inviteId)
      refresh()
    } catch (e) {
      setError(String(e))
    } finally {
      setBusy(null)
    }
  }

  const friends = data?.friends ?? []
  const mutual = friends.filter((f) => f.direction === 'mutual')
  const incoming = friends.filter((f) => f.direction === 'incoming')
  const outgoing = friends.filter((f) => f.direction === 'outgoing')
  const invites = data?.invites ?? []

  return (
    <main className="max-w-2xl mx-auto p-8 space-y-6">
      <header>
        <h1>{t('friends.title')}</h1>
      </header>

      <section className="card space-y-3">
        <h2>{t('friends.searchTitle')}</h2>
        <input
          className="input w-full"
          placeholder={t('friends.searchPlaceholder')}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        {results.length > 0 && (
          <ul className="space-y-1">
            {results.map((r) => (
              <li key={r.id} className="flex items-center justify-between text-sm">
                <span>@{r.username}</span>
                <button
                  className="btn text-xs"
                  disabled={busy === r.username}
                  onClick={() => sendRequest(r.username)}
                >
                  {t('friends.addBtn')}
                </button>
              </li>
            ))}
          </ul>
        )}
        {error && <p className="text-xs text-red-700">{error}</p>}
      </section>

      {invites.length > 0 && (
        <section className="card space-y-2">
          <h2>{t('friends.invitesTitle')}</h2>
          <ul className="space-y-2">
            {invites.map((inv) => (
              <li key={inv.id} className="flex items-center justify-between text-sm">
                <span>
                  {t('friends.inviteFrom', { username: inv.from_username })}{' '}
                  <span className="text-neutral-500">
                    {inv.room_name || inv.scenario_name}
                  </span>
                </span>
                <div className="flex gap-2 shrink-0 ml-2">
                  <button
                    className="btn-primary text-xs"
                    onClick={() => navigate(`/?join=${inv.join_code}`)}
                  >
                    {t('friends.joinBtn')}
                  </button>
                  <button
                    className="btn text-xs"
                    disabled={busy === inv.id}
                    onClick={() => dismissInvite(inv.id)}
                  >
                    {t('friends.dismissBtn')}
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}

      {incoming.length > 0 && (
        <section className="card space-y-2">
          <h2>{t('friends.incomingTitle')}</h2>
          <ul className="space-y-2">
            {incoming.map((f) => (
              <li key={f.friendship_id} className="flex items-center justify-between text-sm">
                <span>@{f.username}</span>
                <div className="flex gap-2">
                  <button
                    className="btn-primary text-xs"
                    disabled={busy === f.friendship_id}
                    onClick={() => accept(f.friendship_id)}
                  >
                    {t('friends.acceptBtn')}
                  </button>
                  <button
                    className="btn text-xs"
                    disabled={busy === f.friendship_id}
                    onClick={() => remove(f.friendship_id)}
                  >
                    {t('friends.declineBtn')}
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="card space-y-2">
        <h2>{t('friends.listTitle')}</h2>
        {mutual.length === 0 ? (
          <p className="text-sm text-neutral-500 italic">{t('friends.noFriends')}</p>
        ) : (
          <ul className="space-y-2">
            {mutual.map((f) => (
              <li key={f.friendship_id} className="flex items-center justify-between text-sm">
                <span>@{f.username}</span>
                <button
                  className="btn text-xs"
                  disabled={busy === f.friendship_id}
                  onClick={() => remove(f.friendship_id)}
                >
                  {t('friends.removeBtn')}
                </button>
              </li>
            ))}
          </ul>
        )}
        {outgoing.length > 0 && (
          <>
            <div className="label mt-3">{t('friends.outgoingTitle')}</div>
            <ul className="space-y-1">
              {outgoing.map((f) => (
                <li key={f.friendship_id} className="text-sm text-neutral-500">
                  @{f.username} — {t('friends.pendingLabel')}
                </li>
              ))}
            </ul>
          </>
        )}
      </section>
    </main>
  )
}
