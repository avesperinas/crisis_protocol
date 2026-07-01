import type { CSSProperties, ReactNode } from 'react'
import { Emblem } from './FactionBadge'
import { scenarioTheme } from '../theme/scenarios'

interface Props {
  scenarioId: string | undefined
  scenarioName: string
  /** Optional line under the title (e.g. turn count, room name). */
  subtitle?: ReactNode
  /** Optional content pinned to the right (e.g. your role marker, a button). */
  right?: ReactNode
  className?: string
}

/**
 * A wide scenario header banner: the scenario seal (its sigil) + name + era,
 * over an accent-tinted gradient and the scenario's procedural texture. It
 * reuses the `.scenario-stage` texture machinery and sets its own accent vars,
 * so it's self-contained and themes itself from `scenarioId`.
 */
export function ScenarioBanner({ scenarioId, scenarioName, subtitle, right, className }: Props) {
  const theme = scenarioTheme(scenarioId)
  const style = {
    '--accent': theme.accent,
    '--accent-secondary': theme.accentSecondary,
    background: `linear-gradient(105deg, color-mix(in oklab, ${theme.accent} 26%, #141418), #141418 64%)`,
  } as CSSProperties

  return (
    <div
      className={
        'scenario-stage relative overflow-hidden rounded-lg border border-neutral-200' +
        (className ? ' ' + className : '')
      }
      data-scenario={scenarioId}
      data-texture={theme.texture}
      style={style}
    >
      <div className="flex items-center gap-4 p-4">
        {/* Scenario seal */}
        <svg width={48} height={48} viewBox="0 0 36 36" className="shrink-0" aria-hidden>
          <circle cx="18" cy="18" r="16" fill={theme.accent} opacity="0.14" />
          <circle cx="18" cy="18" r="13.5" fill="none" stroke={theme.accent} strokeWidth="1.5" />
          <Emblem motif={theme.sigil} color={theme.accent} />
        </svg>

        <div className="min-w-0 flex-1">
          <div className="label" style={{ color: theme.accent }}>
            {theme.era ? `${theme.era} · ` : ''}
            {theme.atmosphere}
          </div>
          <h1 className="truncate" style={{ color: theme.accent }}>
            {scenarioName}
          </h1>
          {subtitle && <div className="text-sm text-neutral-600 mt-0.5">{subtitle}</div>}
        </div>

        {right && <div className="shrink-0">{right}</div>}
      </div>
    </div>
  )
}
