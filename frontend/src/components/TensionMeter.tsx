import { useTranslation } from 'react-i18next'

interface Props {
  value: number
  orientation?: 'vertical' | 'horizontal' | 'strip'
  showLabel?: boolean
}

const THRESHOLDS = [20, 70, 85]

export function TensionMeter({ value, orientation = 'horizontal', showLabel = true }: Props) {
  const { t } = useTranslation()
  const v = Math.max(0, Math.min(100, value))
  const glow = v >= 85 ? 16 : v >= 70 ? 10 : v >= 20 ? 4 : 0
  const title = `${t('components.tensionMeter.label')}: ${v} / 100`

  if (orientation === 'strip') {
    // Mobile always-visible indicator: a flat 2px color band, no fill/marks.
    const band = v >= 85 ? 'bg-red-500' : v >= 70 ? 'bg-amber-500' : v < 20 ? 'bg-neutral-400' : ''
    return (
      <div
        className={`fixed top-0 inset-x-0 h-[2px] z-40 ${band}`}
        style={!band ? { backgroundColor: 'var(--accent)' } : undefined}
        title={title}
      />
    )
  }

  if (orientation === 'vertical') {
    // Threshold-coloured fill so a heating crisis reads dramatically: amber as
    // it climbs, red once it's critical.
    const fill = v >= 85 ? '#ef4444' : v >= 70 ? '#f59e0b' : 'var(--accent)'
    return (
      <div className="h-full w-4 flex flex-col items-center" title={title}>
        <div className="relative w-4 flex-1 bg-neutral-200 rounded-full overflow-hidden">
          <div
            className="absolute bottom-0 left-0 w-full rounded-full transition-all duration-700"
            style={{
              height: `${v}%`,
              backgroundColor: fill,
              boxShadow: glow ? `0 0 ${glow}px ${fill}` : undefined,
            }}
          />
          {THRESHOLDS.map((th) => (
            <div
              key={th}
              className="absolute left-0 w-full h-px bg-neutral-500"
              style={{ bottom: `${th}%` }}
            />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {showLabel && (
        <div className="flex justify-between text-sm text-neutral-600">
          <span className="label">{t('components.tensionMeter.label')}</span>
          <span className="font-mono">{v} / 100</span>
        </div>
      )}
      <div className="relative h-3 bg-neutral-200 rounded">
        <div
          className="absolute top-0 left-0 h-3 rounded transition-all duration-700"
          style={{
            width: `${v}%`,
            backgroundColor: 'var(--accent)',
            boxShadow: glow ? `0 0 ${glow}px var(--accent)` : undefined,
          }}
        />
        {THRESHOLDS.map((threshold) => (
          <div
            key={threshold}
            className="absolute top-0 h-3 w-px bg-neutral-400"
            style={{ left: `${threshold}%` }}
            title={t('components.tensionMeter.threshold', { value: threshold })}
          />
        ))}
      </div>
    </div>
  )
}
