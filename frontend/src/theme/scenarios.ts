/**
 * Scenario-level theming — the customizable "stage" each scenario plays on.
 *
 * This is the base set of standard slots that define a scenario's look. To
 * re-skin a scenario you only touch the entry here; to add a scenario, add an
 * entry keyed by its backend id. Per-*nation* identity (color + emblem) lives
 * separately in `./factions`.
 *
 * Slots:
 *   accent / accentSecondary  primary + supporting color (drive `--accent`,
 *                             tension meter, buttons, section borders…)
 *   texture                   a procedural surface overlay (see index.css
 *                             `.scenario-stage[data-texture=...]`)
 *   atmosphere                short design-intent descriptor (also a tooltip)
 *
 * Everything is procedural/CSS — no external image assets — so it stays light
 * and we iterate toward richer art without changing call sites.
 */

import type { EmblemMotif } from './factions'

export type ScenarioTexture = 'marble' | 'industrial' | 'ice' | 'none'

export interface ScenarioTheme {
  accent: string
  accentSecondary: string
  texture: ScenarioTexture
  atmosphere: string
  /** Emblem motif for the scenario itself (banner seal). Reuses the faction
      motif vocabulary so a single renderer covers both. */
  sigil: EmblemMotif
  /** Short era/date label for the banner (e.g. "338 a.C."). */
  era: string
}

const DEFAULT_THEME: ScenarioTheme = {
  accent: '#5b8dbf',
  accentSecondary: '#2e4a66',
  texture: 'none',
  atmosphere: '',
  sigil: 'star',
  era: '',
}

const SCENARIO_THEMES: Record<string, ScenarioTheme> = {
  corinth_338: {
    accent: '#c9a84c', // oro bronce
    accentSecondary: '#8b6914',
    texture: 'marble',
    atmosphere: 'Antigüedad, mármol, poder',
    sigil: 'laurel',
    era: '338 a.C.',
  },
  oil_crisis_1973: {
    accent: '#d4691e', // ámbar petróleo
    accentSecondary: '#8a3a0e',
    texture: 'industrial',
    atmosphere: 'Años 70, urgencia industrial',
    sigil: 'wave',
    era: '1973',
  },
  arctic_2031: {
    accent: '#4a9ebf', // azul ártico
    accentSecondary: '#1a5f7a',
    texture: 'ice',
    atmosphere: 'Frío, tecnológico, silencio',
    sigil: 'diamond',
    era: '2031',
  },
}

export function scenarioTheme(id: string | undefined): ScenarioTheme {
  return (id ? SCENARIO_THEMES[id] : undefined) ?? DEFAULT_THEME
}

/**
 * Faint accent-tinted radial wash anchored top-center. Uses `var(--accent)`,
 * which `ScenarioStage` sets, so it always matches the active scenario.
 */
export const SCENARIO_BACKDROP =
  'radial-gradient(120% 60% at 50% -10%, color-mix(in oklab, var(--accent) 14%, transparent), transparent 70%),' +
  ' radial-gradient(80% 50% at 100% 0%, color-mix(in oklab, var(--accent) 7%, transparent), transparent 60%)'
