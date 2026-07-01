/**
 * Per-faction visual identity (color + emblem motif), keyed by scenario.
 *
 * This is a *placeholder* identity system: simple, self-contained SVG motifs
 * drawn in a per-nation accent color, no external image assets or licensing.
 * The goal is that every nation reads as visually distinct at a glance — we
 * iterate toward bespoke art later without changing call sites, since the
 * lookup signature (`factionTheme`) stays the same.
 *
 * Colors are tuned to be mutually distinct *within* a scenario's roster and to
 * stay readable on the dark base (#0d0d0f). They nod to real national identity
 * where it doesn't hurt legibility, but distinctiveness wins over accuracy.
 */

export type EmblemMotif =
  | 'star'
  | 'sun'
  | 'chevron'
  | 'mountain'
  | 'wave'
  | 'crescent'
  | 'lambda'
  | 'cross'
  | 'eye'
  | 'laurel'
  | 'pillar'
  | 'diamond'
  | 'leaf'

/** Decorative fill drawn on a nation's standard/banner — pure CSS, no assets. */
export type FactionPattern = 'none' | 'stripes' | 'chevrons' | 'dots'

export interface FactionTheme {
  /** Accent color for this nation (badge, dots, identity highlights). */
  color: string
  /** Which procedural emblem to draw in the badge. */
  emblem: EmblemMotif
  /** Supporting tone (gradients, banner backing). Defaults to a darkened mix. */
  accent2?: string
  /** Decorative fill for the faction standard/banner. Defaults to 'none'. */
  pattern?: FactionPattern
}

const THEMES: Record<string, Record<string, FactionTheme>> = {
  corinth_338: {
    macedonia: { color: '#D4AF37', emblem: 'sun', pattern: 'stripes' }, // Vergina sun
    atenas: { color: '#3E7CB1', emblem: 'pillar', pattern: 'none' }, // Parthenon
    esparta: { color: '#B23A36', emblem: 'lambda', pattern: 'chevrons' }, // Λ on the shield
    tebas: { color: '#5B9E54', emblem: 'mountain', pattern: 'none' },
    corinto: { color: '#CC7A33', emblem: 'wave', pattern: 'dots' }, // maritime crossroads
    persia: { color: '#8E5BB0', emblem: 'eye', pattern: 'dots' }, // "The Shadow"
  },
  oil_crisis_1973: {
    arabia_saudi: { color: '#2E9E5B', emblem: 'crescent', pattern: 'none' },
    eeuu: { color: '#3E7CB1', emblem: 'star', pattern: 'stripes' },
    iran: { color: '#2BA89E', emblem: 'eye', pattern: 'none' },
    europa: { color: '#D9B441', emblem: 'laurel', pattern: 'dots' }, // ring of stars → laurel
    japon: { color: '#D8504F', emblem: 'sun', pattern: 'none' }, // rising sun
    urss: { color: '#9B4DA8', emblem: 'diamond', pattern: 'chevrons' },
  },
  arctic_2031: {
    rusia: { color: '#B23A36', emblem: 'diamond', pattern: 'stripes' },
    eeuu: { color: '#3E7CB1', emblem: 'chevron', pattern: 'stripes' }, // eagle
    canada: { color: '#D86A4A', emblem: 'leaf', pattern: 'none' },
    noruega: { color: '#5A52C9', emblem: 'cross', pattern: 'none' }, // nordic cross
    china: { color: '#D9A441', emblem: 'star', pattern: 'chevrons' },
    groenlandia: { color: '#4FB0C9', emblem: 'sun', pattern: 'none' }, // half-sun on flag
  },
}

/** Stable, well-distributed motif pool for unknown factions. */
const MOTIF_POOL: EmblemMotif[] = [
  'star',
  'sun',
  'chevron',
  'mountain',
  'wave',
  'crescent',
  'lambda',
  'cross',
  'eye',
  'laurel',
  'pillar',
  'diamond',
  'leaf',
]

function hashString(s: string): number {
  let h = 0
  for (let i = 0; i < s.length; i++) {
    h = (h * 31 + s.charCodeAt(i)) | 0
  }
  return Math.abs(h)
}

/**
 * Resolve a faction's theme. Falls back to a deterministic color+motif derived
 * from the id so a brand-new scenario/faction still looks intentional and stays
 * stable across renders.
 */
export function factionTheme(
  scenarioId: string | undefined,
  factionId: string,
): Required<FactionTheme> {
  const hit = scenarioId ? THEMES[scenarioId]?.[factionId] : undefined
  if (hit) {
    return {
      color: hit.color,
      emblem: hit.emblem,
      accent2: hit.accent2 ?? darken(hit.color),
      pattern: hit.pattern ?? 'none',
    }
  }

  const h = hashString(factionId)
  // Golden-angle hue stepping keeps consecutive ids far apart on the wheel.
  const hue = (h * 137.508) % 360
  const color = `hsl(${hue.toFixed(0)} 55% 58%)`
  return {
    color,
    emblem: MOTIF_POOL[h % MOTIF_POOL.length],
    accent2: darken(color),
    pattern: 'none',
  }
}

/** Darkened companion tone via CSS color-mix — works for hex or hsl() input. */
function darken(color: string): string {
  return `color-mix(in oklab, ${color} 60%, #0d0d0f)`
}

