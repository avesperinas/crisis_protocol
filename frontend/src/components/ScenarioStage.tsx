import type { CSSProperties, ReactNode } from 'react'
import { SCENARIO_BACKDROP, scenarioTheme } from '../theme/scenarios'

/**
 * The themed surface a scenario plays on. Wrap a page's content in this and it
 * gets the scenario's accent colors (`--accent` / `--accent-secondary`),
 * backdrop wash, and procedural texture — all from `theme/scenarios.ts`, so
 * re-skinning a scenario never touches page code.
 *
 * Setting the accent vars inline makes the TS theme the single source of truth
 * (it overrides the `[data-scenario]` fallbacks in index.css); `data-texture`
 * selects the CSS overlay.
 */
export function ScenarioStage({
  scenarioId,
  children,
  className,
}: {
  scenarioId: string | undefined
  children: ReactNode
  className?: string
}) {
  const theme = scenarioTheme(scenarioId)
  const style = {
    '--accent': theme.accent,
    '--accent-secondary': theme.accentSecondary,
    background: SCENARIO_BACKDROP,
  } as CSSProperties

  return (
    <div
      className={'scenario-stage flex-1' + (className ? ' ' + className : '')}
      data-scenario={scenarioId}
      data-texture={theme.texture}
      style={style}
    >
      {children}
    </div>
  )
}
