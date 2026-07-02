import { useCallback, useEffect, useMemo, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { useTranslation } from 'react-i18next'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { DirectiveCard } from '../components/DirectiveCard'
import { IntelReport } from '../components/IntelReport'
import { MessagePanel } from '../components/MessagePanel'
import { NarrativeCard } from '../components/NarrativeCard'
import { PactProposalModal } from '../components/PactProposalModal'
import { PactsActive } from '../components/PactsActive'
import { TensionMeter } from '../components/TensionMeter'
import { useGameSocket } from '../hooks/useGameSocket'
import { usePolling } from '../hooks/usePolling'
import { useGameStore } from '../store/gameStore'
import { FactionStandard } from '../components/FactionStandard'
import { Panel } from '../components/Panel'
import { PublicStateModal } from '../components/PublicStateModal'
import { HandshakeIcon, UsersIcon } from '../components/icons'
import { ScenarioBanner } from '../components/ScenarioBanner'
import { ScenarioStage } from '../components/ScenarioStage'
import { factionTheme } from '../theme/factions'
import type { Posture, TokenAllocation } from '../types/game'

const EMPTY: TokenAllocation = { MIL: 0, DIP: 0, ECO: 0, INT: 0 }

type Tab = 'state' | 'turn' | 'action' | 'messages' | 'intel'

export function GameRoom() {
  const { t } = useTranslation()
  const { gameId } = useParams<{ gameId: string }>()
  const navigate = useNavigate()
  const session = useGameStore((s) => s.session)
  const [posture, setPosture] = useState<Posture | null>(null)
  const [tokens, setTokens] = useState<TokenAllocation>(EMPTY)
  const [directive, setDirective] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [lastTurnSeen, setLastTurnSeen] = useState<number>(0)
  const [showPactModal, setShowPactModal] = useState(false)
  const [showStateModal, setShowStateModal] = useState(false)
  const [pactToast, setPactToast] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<Tab>('action')

  // Tracks which turn's narrative the player has already seen — only show the
  // NarrativeCard for turns that resolve while this page is open, not on every load.
  const [narrativeBaselineSet, setNarrativeBaselineSet] = useState(false)
  const [shownNarrativeTurn, setShownNarrativeTurn] = useState<number>(0)

  const fetcher = useMemo(() => {
    if (!session || !gameId) return null
    return () => api.getState(gameId, session.roleId)
  }, [session, gameId])

  const { data: state, error, refresh } = usePolling(
    fetcher ?? (() => Promise.reject(new Error('no session'))),
    5000,
    !!fetcher,
  )

  useGameSocket(gameId, session?.roleId, useCallback(() => {
    refresh()
  }, [refresh]))

  useEffect(() => {
    if (state?.status === 'finished') {
      navigate(`/games/${gameId}/resolution`)
    }
  }, [state, gameId, navigate])

  useEffect(() => {
    if (state && state.current_turn !== lastTurnSeen) {
      setPosture(null)
      setTokens(EMPTY)
      setDirective('')
      setSubmitError(null)
      setLastTurnSeen(state.current_turn)
      setActiveTab('action')
    }
  }, [state, lastTurnSeen])

  useEffect(() => {
    if (state && !narrativeBaselineSet) {
      setShownNarrativeTurn(state.previous_turn_view?.turn_number ?? 0)
      setNarrativeBaselineSet(true)
    }
  }, [state, narrativeBaselineSet])

  useEffect(() => {
    if (!session) navigate('/')
  }, [session, navigate])

  if (!session) {
    return null
  }
  if (error) return <div className="p-8 text-red-700">{t('common.error')}: {String(error)}</div>
  if (!state) return <div className="p-8 text-neutral-600">{t('gameRoom.loading')}</div>

  const you = state.you
  const youTheme = factionTheme(state.scenario_id, you.role_id)
  const turn = state.current_turn_view
  const budget = you.token_budget_per_turn ?? 0
  const total = tokens.MIL + tokens.DIP + tokens.ECO + tokens.INT
  const canSubmit =
    !!posture &&
    total === budget &&
    directive.trim().length > 0 &&
    !submitting &&
    turn?.status === 'collecting' &&
    !turn?.your_action_submitted

  const submit = async () => {
    if (!gameId || !session || !posture) return
    setSubmitting(true)
    setSubmitError(null)
    try {
      await api.submitAction(gameId, session.roleId, { posture, tokens, directive })
      await refresh()
    } catch (e) {
      setSubmitError(String(e))
    } finally {
      setSubmitting(false)
    }
  }

  const prev = state.previous_turn_view
  const pendingNarrative =
    narrativeBaselineSet && prev?.narrative && prev.turn_number > shownNarrativeTurn ? prev : null
  const actionNeedsAttention = turn?.status === 'collecting' && !turn.your_action_submitted

  // Mobile: show only the active tab. Desktop: always visible.
  // NOTE: the desktop class must be a LITERAL string ('md:block') — Tailwind's
  // scanner only emits CSS for class names it sees verbatim in source, so a
  // concatenated `'md:' + x` would silently never be generated.
  const tabVisibility = (tab: Tab) =>
    activeTab === tab ? 'block md:block' : 'hidden md:block'

  const TABS: { id: Tab; label: string; badge?: boolean }[] = [
    { id: 'state', label: t('gameRoom.tabState') },
    { id: 'turn', label: t('gameRoom.tabTurn') },
    { id: 'action', label: t('gameRoom.tabAction'), badge: actionNeedsAttention },
    { id: 'messages', label: t('gameRoom.tabMessages') },
    { id: 'intel', label: t('gameRoom.tabIntel') },
  ]

  return (
    <ScenarioStage scenarioId={state.scenario_id}>
      <TensionMeter value={state.tension} orientation="strip" />

      {pendingNarrative && (
        <NarrativeCard
          turnNumber={pendingNarrative.turn_number}
          narrative={pendingNarrative.narrative!}
          tensionStart={pendingNarrative.tension_at_start}
          tensionEnd={pendingNarrative.tension_at_end ?? pendingNarrative.tension_at_start}
          onDismiss={() => setShownNarrativeTurn(pendingNarrative.turn_number)}
        />
      )}

      <main className="max-w-6xl mx-auto p-4 md:p-5 pb-24 md:pb-5 space-y-2.5">
        <ScenarioBanner
          scenarioId={state.scenario_id}
          scenarioName={state.scenario_name}
          subtitle={t('gameRoom.turnLabel', { current: state.current_turn, max: state.max_turns })}
          right={
            <div className="flex items-center gap-3">
              <button
                className="inline-flex items-center gap-1.5 rounded border px-3 py-1.5 text-sm transition-colors hover:bg-white/5"
                style={{ borderColor: 'var(--accent)', color: 'var(--accent)' }}
                onClick={() => setShowStateModal(true)}
              >
                <UsersIcon size={16} />
                <span className="hidden sm:inline">{t('gameRoom.factionsBtn')}</span>
              </button>
              <div className="text-right text-sm">
                <div className="label">{t('gameRoom.yourRole')}</div>
                <div className="font-medium" style={{ color: youTheme.color }}>
                  {you.role_name}
                </div>
              </div>
              <FactionStandard
                factionId={you.role_id}
                name={you.role_name}
                scenarioId={state.scenario_id}
                size={56}
              />
            </div>
          }
        />

        <section
          className="card border-l-4 py-3 space-y-2"
          style={{ borderLeftColor: 'var(--accent)' }}
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 text-sm">
            <div className="bg-indigo-50 rounded p-2.5">
              <div className="label text-indigo-700 mb-0.5">{t('gameRoom.publicObjective')}</div>
              <p className="text-neutral-800 leading-snug">{you.public_objective_text}</p>
            </div>
            <div className="bg-amber-50 rounded p-2.5">
              <div className="label text-amber-700 mb-0.5">{t('gameRoom.hiddenObjective')}</div>
              <p className="text-neutral-800 leading-snug">{you.hidden_objective_text}</p>
            </div>
          </div>
        </section>

        {/* Command dashboard: a dramatic full-height tension column, then two
            content columns (action + diplomacy/intel/pacts). items-stretch plus
            an internal grower in each column keeps all three ending level. */}
        <div className="md:flex md:items-stretch md:gap-3">
          {/* Tension — its own dramatic, full-height column */}
          <div className="hidden md:flex md:flex-col md:items-center shrink-0 w-16 rounded border border-neutral-200 bg-neutral-100 px-2 py-3">
            <div className="label text-[10px] text-center leading-tight">
              {t('gameRoom.tensionLabel', { defaultValue: 'Tensión' })}
            </div>
            <div className="flex-1 w-full flex justify-center min-h-0 my-2">
              <TensionMeter value={state.tension} orientation="vertical" />
            </div>
            <div className="font-mono text-sm tabular-nums">{state.tension}</div>
          </div>

          {/* LEFT — primary action (fills) + what just happened (pinned below) */}
          <div className="md:flex-[1.6] min-w-0 space-y-3 md:flex md:flex-col">
            <div className={tabVisibility('action') + ' md:flex-1 md:flex md:flex-col'}>
              <DirectiveCard
                you={you}
                scenarioId={state.scenario_id}
                turn={turn}
                posture={posture}
                onPostureChange={setPosture}
                tokens={tokens}
                onTokensChange={setTokens}
                directive={directive}
                onDirectiveChange={setDirective}
                budget={budget}
                submitting={submitting}
                submitError={submitError}
                canSubmit={canSubmit}
                onSubmit={submit}
                exampleDirective={state.example_directive}
                fill
              />
            </div>

            {prev && (
              <section className={tabVisibility('turn') + ' card space-y-3'}>
                <h3>{t('gameRoom.previousTurnSummary', { n: prev.turn_number })}</h3>
                {prev.narrative && (
                  <div className="narrative text-sm text-neutral-700 italic border-l-2 border-indigo-300 pl-3">
                    <ReactMarkdown>{prev.narrative}</ReactMarkdown>
                  </div>
                )}
                {prev.resolved_actions.length > 0 && (
                  <div>
                    <div className="label mb-2">{t('gameRoom.declaredActions')}</div>
                    <div className="space-y-1">
                      {prev.resolved_actions.map((a) => (
                        <div key={a.role_id} className="flex items-start gap-2 text-sm">
                          <span
                            className="font-medium w-20 shrink-0"
                            style={{ color: factionTheme(state.scenario_id, a.role_id).color }}
                          >
                            {a.role_id}
                          </span>
                          <span
                            className={`text-xs px-1.5 py-0.5 rounded shrink-0 ${
                              a.posture === 'cooperative'
                                ? 'bg-green-100 text-green-800'
                                : a.posture === 'confrontational'
                                  ? 'bg-red-100 text-red-800'
                                  : 'bg-yellow-100 text-yellow-800'
                            }`}
                          >
                            {t(`postures.${a.posture}`)}
                          </span>
                          {a.action_type && a.action_type !== 'generic' && (
                            <span className="text-xs bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded shrink-0">
                              {a.action_type}
                              {a.target_id ? ` → ${a.target_id}` : ''}
                            </span>
                          )}
                          {a.directive && (
                            <span className="text-neutral-600 truncate" title={a.directive}>
                              {a.directive}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </section>
            )}
          </div>

          {/* RIGHT — coherent panels: diplomacy, messaging (fills), intel, pacts */}
          <div className="md:flex-1 min-w-0 space-y-3 mt-3 md:mt-0 md:flex md:flex-col">
            <div
              className={
                (activeTab === 'messages' ? 'flex' : 'hidden') +
                ' md:flex md:flex-1 md:flex-col md:min-h-0 space-y-3'
              }
            >
              <Panel
                icon={<HandshakeIcon size={15} />}
                title={t('gameRoom.diplomacyTitle')}
                action={
                  <button
                    className="btn-primary text-sm shrink-0"
                    disabled={turn?.status !== 'collecting'}
                    onClick={() => setShowPactModal(true)}
                  >
                    {t('gameRoom.proposePactBtn')}
                  </button>
                }
              >
                <div className="text-xs text-neutral-600">{t('gameRoom.diplomacyHint')}</div>
                {pactToast && <div className="text-xs text-slate-700 mt-1">{pactToast}</div>}
              </Panel>
              <MessagePanel
                gameId={state.game_id}
                roleId={state.your_role_id}
                factions={state.factions}
                messages={state.messages}
                activePacts={state.active_pacts}
                pactLabels={state.pact_type_labels}
                turnSummaries={state.turn_summaries}
                pactEvents={state.pact_events}
                promiseEvents={state.promise_events}
                currentTurn={state.current_turn}
                onSent={refresh}
                fill
              />
            </div>

            <div className={tabVisibility('intel')}>
              <IntelReport text={prev?.intel_for_you ?? null} />
            </div>

            <div className={tabVisibility('state')}>
              <PactsActive
                gameId={state.game_id}
                roleId={state.your_role_id}
                pacts={state.active_pacts}
                pactLabels={state.pact_type_labels}
                onChanged={refresh}
              />
            </div>
          </div>
        </div>

        {showPactModal && (
          <PactProposalModal
            gameId={state.game_id}
            roleId={state.your_role_id}
            factions={state.factions}
            pactLabels={state.pact_type_labels}
            onClose={() => setShowPactModal(false)}
            onDone={(res) => {
              setPactToast(
                res.status === 'pending'
                  ? t('gameRoom.pendingToast')
                  : res.status === 'accepted'
                    ? t('gameRoom.acceptedToast', { reason: res.reason || t('gameRoom.noReason') })
                    : t('gameRoom.rejectedToast', { reason: res.reason || t('gameRoom.noReason') }),
              )
              refresh()
            }}
          />
        )}

        {showStateModal && (
          <PublicStateModal
            factions={state.factions}
            scenarioId={state.scenario_id}
            yourRoleId={state.your_role_id}
            onClose={() => setShowStateModal(false)}
          />
        )}
      </main>

      {/* Mobile bottom tab bar */}
      <nav className="md:hidden fixed bottom-0 inset-x-0 z-30 bg-neutral-100 border-t border-neutral-200 flex">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`relative flex-1 py-3 text-xs font-medium transition-colors ${
              activeTab === tab.id ? 'text-neutral-900' : 'text-neutral-500'
            }`}
            style={activeTab === tab.id ? { color: 'var(--accent)' } : undefined}
          >
            {tab.label}
            {tab.badge && (
              <span
                className="absolute top-1.5 right-1/4 w-1.5 h-1.5 rounded-full"
                style={{ backgroundColor: 'var(--accent)' }}
              />
            )}
          </button>
        ))}
      </nav>
    </ScenarioStage>
  )
}
