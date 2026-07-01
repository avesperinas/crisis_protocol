import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useNavigate } from 'react-router-dom'
import { socialApi } from '../api/client'
import { useAuthStore } from '../store/authStore'
import type { GameHistoryEntry, UserStats } from '../types/social'

export function Profile() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const [stats, setStats] = useState<UserStats | null>(null)
  const [games, setGames] = useState<GameHistoryEntry[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!user) return
    Promise.all([socialApi.getStats(), socialApi.getGameHistory()])
      .then(([s, g]) => {
        setStats(s)
        setGames(g)
      })
      .catch((e) => setError(String(e)))
  }, [user])

  useEffect(() => {
    if (!user) navigate('/')
  }, [user, navigate])

  if (!user) return null
  if (error) return <div className="p-8 text-red-700">{t('common.error')}: {error}</div>
  if (!stats) return <div className="p-8 text-neutral-600">{t('profile.loading')}</div>

  return (
    <main className="max-w-3xl mx-auto p-8 space-y-6">
      <header>
        <div className="label">{t('profile.title')}</div>
        <h1>@{user.username}</h1>
      </header>

      <section className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="card text-center">
          <div className="text-2xl font-mono">{stats.games_played}</div>
          <div className="label mt-1">{t('profile.gamesPlayed')}</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-mono">{stats.wins}</div>
          <div className="label mt-1">{t('profile.wins')}</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-mono">{stats.avg_decision_quality}</div>
          <div className="label mt-1">{t('profile.avgDecisionQuality')}</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-mono">{stats.avg_coherence}</div>
          <div className="label mt-1">{t('profile.avgCoherence')}</div>
        </div>
      </section>

      <section className="card grid grid-cols-2 gap-4 text-sm">
        <div>
          <div className="label mb-1">{t('profile.favoriteScenario')}</div>
          <div>{stats.favorite_scenario ?? '—'}</div>
        </div>
        <div>
          <div className="label mb-1">{t('profile.favoriteFaction')}</div>
          <div>{stats.favorite_faction ?? '—'}</div>
        </div>
        <div>
          <div className="label mb-1">{t('profile.publicObjectiveRate')}</div>
          <div>{Math.round(stats.public_objective_rate * 100)}%</div>
        </div>
        <div>
          <div className="label mb-1">{t('profile.hiddenObjectiveRate')}</div>
          <div>{Math.round(stats.hidden_objective_rate * 100)}%</div>
        </div>
      </section>

      <section className="card">
        <h2 className="mb-3">{t('profile.historyTitle')}</h2>
        {games.length === 0 ? (
          <p className="text-sm text-neutral-500 italic">{t('profile.noGames')}</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-neutral-600 border-b border-neutral-200">
                <th className="py-2">{t('profile.colScenario')}</th>
                <th>{t('profile.colFaction')}</th>
                <th>{t('profile.colRank')}</th>
                <th>{t('profile.colScore')}</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {games.map((g) => (
                <tr key={g.game_id} className="border-b border-neutral-100">
                  <td className="py-2">{g.scenario_name}</td>
                  <td>{g.role_name}</td>
                  <td className="font-mono">
                    {g.rank} / {g.player_count}
                  </td>
                  <td className="font-mono">{g.score_total}</td>
                  <td>
                    <Link
                      className="underline text-xs"
                      to={`/games/${g.game_id}/resolution`}
                    >
                      {t('profile.viewBtn')}
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </main>
  )
}
