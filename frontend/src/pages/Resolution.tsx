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

  const nameOf = (roleId: string) =>
    result.scoreboard.find((e) => e.role_id === roleId)?.role_name ?? roleId

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

      {result.turn_summaries.length > 0 && (
        <section className="card space-y-4">
          <div>
            <h3>{t('resolution.chronicleTitle')}</h3>
            <p className="text-xs text-neutral-500 mt-1">
              {t('resolution.secretsRevealedHint')}
            </p>
          </div>
          {result.turn_summaries.map((s) => {
            const pacts = result.pact_events.filter((e) => e.turn_number === s.turn_number)
            const promises = result.promise_events.filter(
              (e) => e.turn_number === s.turn_number,
            )
            return (
              <div key={s.turn_number}>
                <div className="flex items-center gap-2 text-xs text-neutral-500 font-medium mb-1">
                  <span>
                    {t('components.messagePanel.turnHeader', { n: s.turn_number })}
                  </span>
                  {s.tension_at_end !== null && (
                    <span className="font-mono tabular-nums">
                      {s.tension_at_start} → {s.tension_at_end}
                    </span>
                  )}
                  <span className="flex-1 border-t border-neutral-200" />
                </div>
                <ul className="space-y-1 text-sm">
                  {pacts.map((e, i) => (
                    <li key={`p-${i}`} className="text-xs pl-2">
                      {e.kind === 'signed' ? '🤝 ' : '💥 '}
                      {e.kind === 'signed'
                        ? t('components.messagePanel.pactSigned', {
                            a: nameOf(e.a_role_id),
                            b: nameOf(e.b_role_id),
                            type: e.pact_type,
                          })
                        : t('components.messagePanel.pactBroken', {
                            by: nameOf(e.broken_by_role_id ?? e.a_role_id),
                            type: e.pact_type,
                          })}
                      {e.is_secret && (
                        <span className="ml-1 text-amber-700">
                          {t('components.messagePanel.secretEventTag')}
                        </span>
                      )}
                    </li>
                  ))}
                  {promises.map((e, i) => (
                    <li
                      key={`q-${i}`}
                      className={`text-xs pl-2 ${
                        e.assessment === 'kept' ? 'text-emerald-800' : 'text-red-800'
                      }`}
                    >
                      {e.assessment === 'kept' ? '✓ ' : '✗ '}
                      {t(
                        e.assessment === 'kept'
                          ? 'components.messagePanel.promiseKept'
                          : 'components.messagePanel.promiseBroken',
                        { role: nameOf(e.role_id) },
                      )}
                    </li>
                  ))}
                  {s.narrative && (
                    <li className="narrative text-sm italic text-neutral-700 border-l-2 border-indigo-300 pl-3">
                      {s.narrative}
                    </li>
                  )}
                </ul>
              </div>
            )
          })}
        </section>
      )}

      <button className="btn" onClick={() => navigate('/')}>
        {t('resolution.newGameBtn')}
      </button>
      </main>
    </ScenarioStage>
  )
}
