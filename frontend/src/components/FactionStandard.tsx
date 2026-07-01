import { Emblem } from './FactionBadge'
import { factionTheme } from '../theme/factions'

interface Props {
  factionId: string
  name: string
  scenarioId?: string
  /** Overall height in px; width follows the banner aspect ratio. */
  size?: number
  className?: string
}

/**
 * A nation's "standard" — a hanging swallowtail banner bearing its emblem, in
 * the nation's colors, with an optional decorative pattern fill. This is the
 * larger, character-like figure (vs. the small round `FactionBadge` seal) used
 * on briefing/hero surfaces. Procedural SVG, no image assets.
 *
 * viewBox is 0..60 wide, 0..96 tall; the cloth is a rounded rectangle cut into
 * a swallowtail at the bottom.
 */
export function FactionStandard({ factionId, name, scenarioId, size = 112, className }: Props) {
  const { color, accent2, emblem, pattern } = factionTheme(scenarioId, factionId)
  const width = Math.round(size * 0.6)
  // Unique pattern id so multiple standards on one page don't collide.
  const pid = `fs-${(scenarioId ?? 'x')}-${factionId}`.replace(/[^a-zA-Z0-9_-]/g, '')
  const cloth = 'M8 6 H52 V74 L41 84 L30 76 L19 84 L8 74 Z'

  return (
    <svg
      width={width}
      height={size}
      viewBox="0 0 60 96"
      className={className}
      role="img"
      aria-label={name}
    >
      <defs>
        {pattern === 'stripes' && (
          <pattern id={pid} width="9" height="9" patternUnits="userSpaceOnUse">
            <rect width="3.2" height="9" fill={color} />
          </pattern>
        )}
        {pattern === 'chevrons' && (
          <pattern id={pid} width="11" height="9" patternUnits="userSpaceOnUse">
            <path d="M0 8 L5.5 3 L11 8" fill="none" stroke={color} strokeWidth="1.6" />
          </pattern>
        )}
        {pattern === 'dots' && (
          <pattern id={pid} width="10" height="10" patternUnits="userSpaceOnUse">
            <circle cx="5" cy="5" r="1.7" fill={color} />
          </pattern>
        )}
      </defs>

      {/* Pole */}
      <line x1="6" y1="2" x2="6" y2="92" stroke={color} strokeWidth="2" strokeLinecap="round" />
      <circle cx="6" cy="3" r="2.6" fill={color} />

      {/* Cloth */}
      <path d={cloth} fill={accent2} stroke={color} strokeWidth="2" strokeLinejoin="round" />
      {pattern !== 'none' && (
        <path d={cloth} fill={`url(#${pid})`} opacity="0.45" />
      )}

      {/* Emblem (designed for a 0..36 box centered at 18,18 → place at ~30,38). */}
      <g transform="translate(12, 20) scale(0.95)">
        <Emblem motif={emblem} color={color} />
      </g>

      {/* Accent bar under the emblem. */}
      <rect x="16" y="62" width="28" height="2.4" rx="1.2" fill={color} />
    </svg>
  )
}
