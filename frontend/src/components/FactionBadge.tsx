import { factionTheme, type EmblemMotif } from '../theme/factions'

interface Props {
  factionId: string
  name: string
  /** Scenario the faction belongs to — selects the hand-tuned palette/motif. */
  scenarioId?: string
  size?: number
  className?: string
}

/**
 * A diplomatic-seal mark: a ring + a per-nation emblem motif, all drawn in that
 * nation's accent color. The motif and color come from `factionTheme`, so each
 * faction reads as visually distinct. Self-contained SVG — no image assets.
 *
 * Coordinate system is a 0..36 box centered at (18, 18); the framing ring sits
 * at r=13 and emblems are designed to live inside ~r=10.
 */
export function starPoints(cx: number, cy: number, spikes: number, outer: number, inner: number): string {
  const pts: string[] = []
  for (let i = 0; i < spikes * 2; i++) {
    const r = i % 2 === 0 ? outer : inner
    const a = (i / (spikes * 2)) * Math.PI * 2 - Math.PI / 2
    pts.push(`${(cx + r * Math.cos(a)).toFixed(2)},${(cy + r * Math.sin(a)).toFixed(2)}`)
  }
  return pts.join(' ')
}

export function Emblem({ motif, color }: { motif: EmblemMotif; color: string }) {
  const stroke = { stroke: color, strokeWidth: 1.6, fill: 'none', strokeLinejoin: 'round' as const, strokeLinecap: 'round' as const }
  switch (motif) {
    case 'star':
      return <polygon points={starPoints(18, 18, 5, 9, 3.7)} fill={color} />
    case 'sun':
      return (
        <g>
          <circle cx="18" cy="18" r="3.6" fill={color} />
          {Array.from({ length: 12 }, (_, i) => {
            const a = (i / 12) * Math.PI * 2
            return (
              <line
                key={i}
                x1={18 + 5 * Math.cos(a)}
                y1={18 + 5 * Math.sin(a)}
                x2={18 + 9 * Math.cos(a)}
                y2={18 + 9 * Math.sin(a)}
                stroke={color}
                strokeWidth="1.4"
                strokeLinecap="round"
              />
            )
          })}
        </g>
      )
    case 'chevron':
      return (
        <g>
          <path d="M10 20 L18 14 L26 20" {...stroke} />
          <path d="M10 25 L18 19 L26 25" {...stroke} />
        </g>
      )
    case 'mountain':
      return <polygon points="9,25 15,14 19,19 23,12 27,25" fill={color} />
    case 'wave':
      return (
        <g>
          <path d="M9 16 q3 -3 6 0 t6 0 t6 0" {...stroke} />
          <path d="M9 21 q3 -3 6 0 t6 0 t6 0" {...stroke} />
        </g>
      )
    case 'crescent':
      return (
        <path
          d="M22.5 11 a8 8 0 1 0 0 14 a6 6 0 1 1 0 -14 Z"
          fill={color}
        />
      )
    case 'lambda':
      return (
        <g>
          <path d="M18 11 L12 26" {...stroke} strokeWidth="2" />
          <path d="M18 11 L24 26" {...stroke} strokeWidth="2" />
        </g>
      )
    case 'cross':
      // Off-center nordic cross.
      return (
        <g fill={color}>
          <rect x="15.5" y="9" width="3" height="18" />
          <rect x="10" y="16.5" width="16" height="3" />
        </g>
      )
    case 'eye':
      return (
        <g>
          <path d="M9 18 q9 -7 18 0 q-9 7 -18 0 Z" {...stroke} />
          <circle cx="18" cy="18" r="2.6" fill={color} />
        </g>
      )
    case 'laurel':
      return (
        <g>
          <path d="M18 27 q-9 -2 -7 -16" {...stroke} />
          <path d="M18 27 q9 -2 7 -16" {...stroke} />
          <circle cx="18" cy="11" r="1.8" fill={color} />
        </g>
      )
    case 'pillar':
      return (
        <g fill={color}>
          <rect x="9" y="11" width="18" height="2.4" />
          <rect x="9" y="24" width="18" height="2.4" />
          <rect x="11" y="13.4" width="2.4" height="10.6" />
          <rect x="16.8" y="13.4" width="2.4" height="10.6" />
          <rect x="22.6" y="13.4" width="2.4" height="10.6" />
        </g>
      )
    case 'diamond':
      return (
        <g>
          <polygon points="18,8 27,18 18,28 9,18" {...stroke} strokeWidth="1.8" />
          <polygon points="18,13 22,18 18,23 14,18" fill={color} />
        </g>
      )
    case 'leaf':
      return (
        <g>
          <path d="M18 27 C 10 22 10 13 18 9 C 26 13 26 22 18 27 Z" fill={color} />
          <path d="M18 25 L18 12" stroke="#0d0d0f" strokeWidth="1" opacity="0.35" />
        </g>
      )
  }
}

export function FactionBadge({ factionId, name, scenarioId, size = 32, className }: Props) {
  const { color, emblem } = factionTheme(scenarioId, factionId)

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 36 36"
      className={className}
      role="img"
      aria-label={name}
    >
      <circle cx="18" cy="18" r="15.5" fill={color} opacity="0.12" />
      <circle cx="18" cy="18" r="13" fill="none" stroke={color} strokeWidth="1.5" />
      <Emblem motif={emblem} color={color} />
    </svg>
  )
}
