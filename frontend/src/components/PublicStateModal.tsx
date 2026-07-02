import { useTranslation } from 'react-i18next'
import { FactionBadge } from './FactionBadge'
import { factionTheme } from '../theme/factions'
import type { FactionView } from '../types/game'

interface Props {
  factions: FactionView[]
  scenarioId: string
  yourRoleId: string
  onClose: () => void
}

/**
 * The public board state, surfaced from the scenario banner: every faction with
 * its emblem, tagline and — since they are public knowledge — declared public
 * objective. Lives in a modal so it doesn't crowd the play columns.
 */
export function PublicStateModal({ factions, scenarioId, yourRoleId, onClose }: Props) {
  const { t } = useTranslation()
  return (
    <div
      className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="card max-w-lg w-full max-h-[85vh] overflow-y-auto space-y-3"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between gap-2">
          <h2>{t('gameRoom.publicStateTitle')}</h2>
          <button className="btn text-sm" onClick={onClose}>
            {t('common.close', { defaultValue: 'Cerrar' })}
          </button>
        </div>

        <ul className="space-y-2.5">
          {factions.map((f) => {
            const color = factionTheme(scenarioId, f.id).color
            const you = f.id === yourRoleId
            return (
              <li
                key={f.id}
                className="rounded border border-neutral-200 p-3"
                style={{ borderLeft: `3px solid ${color}` }}
              >
                <div className="flex items-center gap-2">
                  <FactionBadge factionId={f.id} name={f.name} scenarioId={scenarioId} size={24} />
                  <span className="font-semibold" style={{ color }}>
                    {f.name}
                  </span>
                  {you && (
                    <span className="text-xs text-neutral-500">
                      {t('waitingRoom.youTag', { defaultValue: '(tú)' })}
                    </span>
                  )}
                  <span className="text-neutral-500 text-sm truncate">— {f.tagline}</span>
                </div>
                <div className="mt-2 ml-1 flex items-center gap-2" title={t('gameRoom.credibilityHint')}>
                  <span className="label">{t('gameRoom.credibilityLabel')}</span>
                  <div className="flex-1 h-1.5 rounded bg-neutral-200 overflow-hidden max-w-[10rem]">
                    <div
                      className={`h-full ${
                        f.credibility >= 60
                          ? 'bg-green-500'
                          : f.credibility >= 40
                            ? 'bg-yellow-500'
                            : 'bg-red-500'
                      }`}
                      style={{ width: `${f.credibility}%` }}
                    />
                  </div>
                  <span className="text-xs font-mono tabular-nums text-neutral-600">
                    {f.credibility}
                  </span>
                </div>
                <div className="mt-2 ml-1">
                  <div className="label text-indigo-700 mb-0.5">
                    {t('gameRoom.publicObjective')}
                  </div>
                  <p className="text-sm text-neutral-800 leading-snug">{f.public_objective}</p>
                </div>
              </li>
            )
          })}
        </ul>
      </div>
    </div>
  )
}
