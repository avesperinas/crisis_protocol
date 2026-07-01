import { useTranslation } from 'react-i18next'
import { DirectiveInput } from './DirectiveInput'
import { FactionBadge } from './FactionBadge'
import { PostureSelector } from './PostureSelector'
import { ResourceAllocator } from './ResourceAllocator'
import type { PlayerView, Posture, TokenAllocation, TurnView } from '../types/game'

interface Props {
  you: PlayerView
  scenarioId?: string
  turn: TurnView | null
  posture: Posture | null
  onPostureChange: (p: Posture) => void
  tokens: TokenAllocation
  onTokensChange: (t: TokenAllocation) => void
  directive: string
  onDirectiveChange: (d: string) => void
  budget: number
  submitting: boolean
  submitError: string | null
  canSubmit: boolean
  onSubmit: () => void
  exampleDirective?: string
  /** Stretch to fill the column height (desktop) so columns end level. */
  fill?: boolean
}

/**
 * The action form, presented as a single "sealed" card. Before submission it's
 * the live posture/tokens/directive editor; after submission it visually seals
 * shut and shows how many other players are still pending.
 */
export function DirectiveCard({
  you,
  scenarioId,
  turn,
  posture,
  onPostureChange,
  tokens,
  onTokensChange,
  directive,
  onDirectiveChange,
  budget,
  submitting,
  submitError,
  canSubmit,
  onSubmit,
  exampleDirective,
  fill,
}: Props) {
  const { t } = useTranslation()
  const sealed = !!turn && (turn.your_action_submitted || turn.status !== 'collecting')
  const fillCls = fill ? ' md:h-full' : ''

  if (sealed) {
    const showPending = turn && turn.humans_total > 1 && turn.status === 'collecting'
    return (
      <section className={'card space-y-3' + fillCls}>
        <div className="flex items-center gap-2">
          <FactionBadge
            factionId={you.role_id}
            name={you.role_name}
            scenarioId={scenarioId}
            size={28}
          />
          <h2>{t('gameRoom.yourActionTitle')}</h2>
        </div>
        <div className="text-sm text-neutral-500 border-t border-neutral-200 pt-3 space-y-1">
          <p>
            {turn?.status === 'collecting'
              ? t('gameRoom.waitingSubmitted')
              : t('gameRoom.resolvingTurn')}
          </p>
          {showPending && (
            <p className="text-xs font-mono">
              {t('gameRoom.pendingPlayers', {
                submitted: turn!.humans_submitted,
                total: turn!.humans_total,
              })}
            </p>
          )}
        </div>
      </section>
    )
  }

  return (
    <section className={'card space-y-3' + (fill ? ' md:h-full md:flex md:flex-col' : '')}>
      <div className="flex items-center gap-2">
        <FactionBadge
          factionId={you.role_id}
          name={you.role_name}
          scenarioId={scenarioId}
          size={28}
        />
        <h2>{t('gameRoom.yourActionTitle')}</h2>
      </div>
      <PostureSelector value={posture} onChange={onPostureChange} disabled={submitting} />
      <ResourceAllocator
        tokens={tokens}
        budget={budget}
        onChange={onTokensChange}
        disabled={submitting}
        persistentResources={you.resources ?? undefined}
      />
      <DirectiveInput
        value={directive}
        onChange={onDirectiveChange}
        disabled={submitting}
        placeholder={exampleDirective}
      />
      {submitError && <div className="text-sm text-red-700">{submitError}</div>}
      {/* spacer pushes the submit to the bottom when the card fills its column */}
      {fill && <div className="hidden md:block md:flex-1" />}
      <div className="flex justify-end">
        <button className="btn-primary" disabled={!canSubmit} onClick={onSubmit}>
          {submitting ? t('gameRoom.resolvingBtn') : t('gameRoom.submitBtn')}
        </button>
      </div>
    </section>
  )
}
