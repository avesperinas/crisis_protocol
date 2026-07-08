import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { api } from '../api/client'
import { Panel } from './Panel'
import { ChatIcon } from './icons'
import type {
  FactionView,
  MessageView,
  PactEventView,
  PactType,
  PactTypeLabels,
  PactView,
  PromiseEventView,
  TurnSummaryView,
} from '../types/game'

interface Props {
  gameId: string
  roleId: string
  factions: FactionView[]
  messages: MessageView[]
  activePacts: PactView[]
  pactLabels: PactTypeLabels
  turnSummaries: TurnSummaryView[]
  pactEvents: PactEventView[]
  promiseEvents: PromiseEventView[]
  currentTurn: number
  onSent: () => void
  /** When true, fill the parent flex column (desktop) so the chat absorbs slack
      height and the surrounding layout stays a clean rectangle. */
  fill?: boolean
}

/**
 * The diplomacy panel (Phase E): a unified timeline channel — narrative, public
 * statements, pact signings/breaks and promise verdicts grouped by turn — plus
 * one private thread per faction with a relationship header (credibility and
 * shared pacts).
 */
export function MessagePanel({
  gameId,
  roleId,
  factions,
  messages,
  activePacts,
  pactLabels,
  turnSummaries,
  pactEvents,
  promiseEvents,
  currentTurn,
  onSent,
  fill,
}: Props) {
  const { t } = useTranslation()
  const channels = useMemo(() => {
    const others = factions.filter((f) => f.id !== roleId)
    return [
      { id: 'feed' as const, label: t('components.messagePanel.feedChannel') },
      ...others.map((f) => ({ id: f.id, label: f.name })),
    ]
  }, [factions, roleId, t])
  const [active, setActive] = useState<string>('feed')
  const [draft, setDraft] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const nameOf = (id: string) => factions.find((f) => f.id === id)?.name ?? id
  const typeLabel = (type: string) =>
    (pactLabels as Record<string, { label: string }>)[type]?.label ?? type

  const summaryByTurn = useMemo(
    () => new Map(turnSummaries.map((s) => [s.turn_number, s])),
    [turnSummaries],
  )

  // Every turn with anything to show, newest first.
  const feedTurns = useMemo(() => {
    const numbers = new Set<number>()
    for (const m of messages) if (m.to_role_id === null) numbers.add(m.turn_number)
    for (const e of pactEvents) numbers.add(e.turn_number)
    for (const e of promiseEvents) numbers.add(e.turn_number)
    for (const s of turnSummaries) numbers.add(s.turn_number)
    if (currentTurn > 0) numbers.add(currentTurn)
    return [...numbers].sort((a, b) => b - a)
  }, [messages, pactEvents, promiseEvents, turnSummaries, currentTurn])

  const threadMessages = (factionId: string) =>
    messages.filter(
      (m) =>
        (m.from_role_id === roleId && m.to_role_id === factionId) ||
        (m.from_role_id === factionId && m.to_role_id === roleId),
    )

  const submit = async () => {
    if (!draft.trim()) return
    setBusy(true)
    setError(null)
    try {
      await api.sendMessage(gameId, roleId, draft.trim(), active === 'feed' ? null : active)
      setDraft('')
      onSent()
    } catch (e) {
      setError(String(e))
    } finally {
      setBusy(false)
    }
  }

  const respondProposal = async (messageId: string, accept: boolean) => {
    setBusy(true)
    setError(null)
    try {
      await api.respondToProposal(gameId, roleId, messageId, accept)
      onSent()
    } catch (e) {
      setError(String(e))
    } finally {
      setBusy(false)
    }
  }

  const renderMessage = (m: MessageView, showRecipient: boolean) => (
    <li key={m.id} className="border-l-2 border-neutral-200 pl-2">
      <div className="text-xs text-neutral-500">
        <span className="font-medium">{nameOf(m.from_role_id)}</span>
        {showRecipient &&
          (m.to_role_id
            ? ` → ${nameOf(m.to_role_id)}`
            : ` ${t('components.messagePanel.publicTag')}`)}
        {m.is_proposal && (
          <span className="ml-2 text-amber-700">
            {t('components.messagePanel.proposalTag', {
              type: typeLabel(m.proposal_type ?? ''),
              status: m.proposal_status,
            })}
          </span>
        )}
      </div>
      <div className="whitespace-pre-wrap text-sm">{m.content}</div>
      {m.is_proposal && m.proposal_status === 'pending' && m.to_role_id === roleId && (
        <div className="flex gap-2 mt-1">
          <button
            className="text-xs px-2 py-1 rounded border border-green-300 bg-green-50 text-green-800 hover:bg-green-100"
            disabled={busy}
            onClick={() => respondProposal(m.id, true)}
          >
            {t('components.messagePanel.acceptProposal')}
          </button>
          <button
            className="text-xs px-2 py-1 rounded border border-red-300 bg-red-50 text-red-800 hover:bg-red-100"
            disabled={busy}
            onClick={() => respondProposal(m.id, false)}
          >
            {t('components.messagePanel.rejectProposal')}
          </button>
        </div>
      )}
    </li>
  )

  const renderPactEvent = (e: PactEventView, i: number) => (
    <li key={`pact-${i}`} className="text-xs pl-2 flex items-start gap-1.5">
      <span aria-hidden>{e.kind === 'signed' ? '🤝' : '💥'}</span>
      <span className={e.kind === 'signed' ? 'text-emerald-800' : 'text-red-800'}>
        {e.kind === 'signed'
          ? t('components.messagePanel.pactSigned', {
              a: nameOf(e.a_role_id),
              b: nameOf(e.b_role_id),
              type: typeLabel(e.pact_type),
            })
          : t('components.messagePanel.pactBroken', {
              by: nameOf(e.broken_by_role_id ?? e.a_role_id),
              type: typeLabel(e.pact_type),
            })}
        {e.is_secret && (
          <span className="ml-1 text-amber-700">
            {t('components.messagePanel.secretEventTag')}
          </span>
        )}
      </span>
    </li>
  )

  const renderPromiseEvent = (e: PromiseEventView, i: number) => (
    <li key={`promise-${i}`} className="text-xs pl-2 flex items-start gap-1.5">
      <span aria-hidden>{e.assessment === 'kept' ? '✓' : '✗'}</span>
      <span className={e.assessment === 'kept' ? 'text-emerald-800' : 'text-red-800'}>
        {t(
          e.assessment === 'kept'
            ? 'components.messagePanel.promiseKept'
            : 'components.messagePanel.promiseBroken',
          { role: nameOf(e.role_id) },
        )}
      </span>
    </li>
  )

  const feed = (
    <ul
      className={
        'space-y-2 overflow-y-auto mb-3 border-t border-neutral-100 pt-2 ' +
        (fill ? 'max-h-64 md:max-h-[26rem] md:flex-1 md:min-h-[10rem]' : 'max-h-64 md:max-h-72')
      }
    >
      {feedTurns.length === 0 ? (
        <li className="text-neutral-500 italic text-xs">
          {t('components.messagePanel.emptyChannel')}
        </li>
      ) : (
        feedTurns.map((n) => {
          const summary = summaryByTurn.get(n)
          const turnMessages = messages.filter(
            (m) => m.to_role_id === null && m.turn_number === n,
          )
          const turnPacts = pactEvents.filter((e) => e.turn_number === n)
          const turnPromises = promiseEvents.filter((e) => e.turn_number === n)
          return (
            <li key={n}>
              <div className="flex items-center gap-2 text-xs text-neutral-500 font-medium mb-1">
                <span>{t('components.messagePanel.turnHeader', { n })}</span>
                {summary && summary.tension_at_end !== null && (
                  <span className="font-mono tabular-nums">
                    {summary.tension_at_start} → {summary.tension_at_end}
                  </span>
                )}
                <span className="flex-1 border-t border-neutral-200" />
              </div>
              <ul className="space-y-1">
                {turnMessages.map((m) => renderMessage(m, false))}
                {turnPacts.map(renderPactEvent)}
                {turnPromises.map(renderPromiseEvent)}
                {summary?.narrative && (
                  <li className="narrative text-xs italic text-neutral-600 border-l-2 border-indigo-300 pl-2">
                    {summary.narrative}
                  </li>
                )}
              </ul>
            </li>
          )
        })
      )}
    </ul>
  )

  const activeFaction = active === 'feed' ? null : factions.find((f) => f.id === active)
  const sharedPacts = activeFaction
    ? activePacts.filter(
        (p) =>
          p.is_active &&
          ((p.player_a_id === roleId && p.player_b_id === activeFaction.id) ||
            (p.player_b_id === roleId && p.player_a_id === activeFaction.id)),
      )
    : []

  const thread = activeFaction && (
    <>
      {/* Relationship header: who you're talking to and what binds you. */}
      <div className="flex items-center gap-2 flex-wrap text-xs bg-neutral-100 rounded px-2 py-1.5 mb-2">
        <span className="label">{t('gameRoom.credibilityLabel')}</span>
        <div className="w-16 h-1.5 rounded bg-neutral-200 overflow-hidden">
          <div
            className={`h-full ${
              activeFaction.credibility >= 60
                ? 'bg-green-500'
                : activeFaction.credibility >= 40
                  ? 'bg-yellow-500'
                  : 'bg-red-500'
            }`}
            style={{ width: `${activeFaction.credibility}%` }}
          />
        </div>
        <span className="font-mono tabular-nums text-neutral-600">
          {activeFaction.credibility}
        </span>
        <span className="text-neutral-300">·</span>
        {sharedPacts.length === 0 ? (
          <span className="text-neutral-500">
            {t('components.messagePanel.noSharedPacts')}
          </span>
        ) : (
          sharedPacts.map((p) => (
            <span
              key={p.id}
              className="px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200"
            >
              {typeLabel(p.type as PactType)}
              {p.is_secret && ` ${t('components.messagePanel.secretEventTag')}`}
            </span>
          ))
        )}
      </div>
      <ul
        className={
          'space-y-1 overflow-y-auto mb-3 text-sm border-t border-neutral-100 pt-2 ' +
          (fill ? 'max-h-40 md:max-h-[26rem] md:flex-1 md:min-h-[10rem]' : 'max-h-40 md:max-h-72')
        }
      >
        {threadMessages(activeFaction.id).length === 0 ? (
          <li className="text-neutral-500 italic text-xs">
            {t('components.messagePanel.emptyChannel')}
          </li>
        ) : (
          threadMessages(activeFaction.id).map((m) => renderMessage(m, false))
        )}
      </ul>
    </>
  )

  return (
    <Panel
      icon={<ChatIcon size={15} />}
      title={t('components.messagePanel.label')}
      className={fill ? 'md:flex-1 md:min-h-0' : ''}
      bodyClassName={fill ? 'md:flex-1 md:flex md:flex-col md:min-h-0' : ''}
    >
      <div className="flex gap-1 flex-wrap mb-2">
        {channels.map((c) => (
          <button
            key={c.id}
            onClick={() => setActive(c.id)}
            className={
              'text-xs px-2 py-1 rounded border ' +
              (active === c.id
                ? 'border-slate-700 bg-slate-50'
                : 'border-neutral-200 hover:bg-neutral-100')
            }
          >
            {c.label}
          </button>
        ))}
      </div>

      {active === 'feed' ? feed : thread}

      <div className="flex gap-2">
        <input
          className="input flex-1"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={
            active === 'feed'
              ? t('components.messagePanel.publicPlaceholder')
              : t('components.messagePanel.privatePlaceholder', {
                  target: activeFaction?.name ?? active,
                })
          }
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) submit()
          }}
        />
        <button className="btn-primary" disabled={busy || !draft.trim()} onClick={submit}>
          {t('components.messagePanel.sendBtn')}
        </button>
      </div>
      {error && <p className="text-xs text-red-700 mt-1">{error}</p>}
    </Panel>
  )
}
