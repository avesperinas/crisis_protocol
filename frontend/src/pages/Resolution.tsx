import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { Scoreboard } from '../components/Scoreboard'
import { ScenarioBanner } from '../components/ScenarioBanner'
import { ScenarioStage } from '../components/ScenarioStage'
import { useGameStore } from '../store/gameStore'
import type { FinalResultView } from '../types/game'

export function Resolution() {
  const { t } = useTranslation()
  const { gameId } = useParams<{ gameId: string }>()
  const navigate = useNavigate()
  const session = useGameStore((s) => s.session)
  const [result, setResult] = useState<FinalResultView | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (!gameId) return
    api
      .getResult(gameId)
      .then(setResult)
      .catch((e) => setError(String(e)))
  }, [gameId])

  // Unlike other pages, this one is viewable without a session — anyone with
  // the link can see a finished game's outcome (replay sharing).
  if (error) return <div className="p-8 text-red-700">{t('common.error')}: {error}</div>
  if (!result) return <div className="p-8 text-neutral-600">{t('resolution.loading')}</div>

  const share = async () => {
    await navigator.clipboard.writeText(window.location.href)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <ScenarioStage scenarioId={result.scenario_id}>
      <main className="max-w-4xl mx-auto p-8 space-y-6">
      <ScenarioBanner
        scenarioId={result.scenario_id}
        scenarioName={result.scenario_name}
        subtitle={t('resolution.title')}
        right={
          <button className="btn text-sm" onClick={share}>
            {copied ? t('resolution.copiedBtn') : t('resolution.shareBtn')}
          </button>
        }
      />

      {result.final_narrative && (
        <section className="card">
          <h3 className="mb-2">{t('resolution.finalNarrativeTitle')}</h3>
          <p className="narrative text-sm whitespace-pre-wrap">{result.final_narrative}</p>
          <div className="mt-3 text-xs text-neutral-600">
            {t('resolution.finalTension')} <span className="font-mono">{result.final_tension}</span>
          </div>
        </section>
      )}

      <Scoreboard
        entries={result.scoreboard}
        yourRoleId={session?.roleId ?? ''}
        scenarioId={result.scenario_id}
      />

      <button className="btn" onClick={() => navigate('/')}>
        {t('resolution.newGameBtn')}
      </button>
      </main>
    </ScenarioStage>
  )
}
