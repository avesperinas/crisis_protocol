import { useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { useTranslation } from 'react-i18next'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { FactionStandard } from '../components/FactionStandard'
import { ScenarioBanner } from '../components/ScenarioBanner'
import { ScenarioStage } from '../components/ScenarioStage'
import { useGameStore } from '../store/gameStore'
import { factionTheme } from '../theme/factions'
import type { GameStateView } from '../types/game'

export function Briefing() {
  const { t } = useTranslation()
  const { gameId } = useParams<{ gameId: string }>()
  const navigate = useNavigate()
  const session = useGameStore((s) => s.session)
  const [state, setState] = useState<GameStateView | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!gameId || !session) return
    api
      .getState(gameId, session.roleId)
      .then(setState)
      .catch((e) => setError(String(e)))
  }, [gameId, session])

  useEffect(() => {
    if (!session) navigate('/')
  }, [session, navigate])

  if (!session) {
    return null
  }
  if (error) return <div className="p-8 text-red-700">{t('common.error')}: {error}</div>
  if (!state) return <div className="p-8 text-neutral-600">{t('briefing.loading')}</div>

  const you = state.you
  const youTheme = factionTheme(state.scenario_id, you.role_id)

  return (
    <ScenarioStage scenarioId={state.scenario_id}>
      <main className="max-w-3xl mx-auto p-8 space-y-6">
      <ScenarioBanner scenarioId={state.scenario_id} scenarioName={state.scenario_name} />

      <header className="flex items-center gap-5">
        <FactionStandard
          factionId={you.role_id}
          name={you.role_name}
          scenarioId={state.scenario_id}
          size={120}
        />
        <div className="min-w-0">
          <div className="label">{state.scenario_name}</div>
          <h1 style={{ color: youTheme.color }}>
            {you.role_name} — {you.tagline}
          </h1>
        </div>
      </header>

      <section className="card space-y-3">
        <h2>{t('briefing.title')}</h2>
        {you.briefing ? (
          <div className="narrative text-sm">
            <ReactMarkdown>{you.briefing}</ReactMarkdown>
          </div>
        ) : (
          <div className="text-neutral-600">{t('briefing.generating')}</div>
        )}
      </section>

      <section className="card">
        <h3 className="mb-2">{t('briefing.initialResources')}</h3>
        {you.resources && (
          <div className="grid grid-cols-4 gap-2 font-mono text-sm">
            <div>MIL {you.resources.MIL}</div>
            <div>DIP {you.resources.DIP}</div>
            <div>ECO {you.resources.ECO}</div>
            <div>INT {you.resources.INT}</div>
          </div>
        )}
        <div className="text-xs text-neutral-600 mt-2">
          {t('briefing.budgetPerTurn', { count: you.token_budget_per_turn })}
        </div>
      </section>

      <button className="btn-primary" onClick={() => navigate(`/games/${gameId}/game`)}>
        {t('briefing.startBtn')}
      </button>
      </main>
    </ScenarioStage>
  )
}
