import { useTranslation } from 'react-i18next'
import { PostureIcon, POSTURE_COLOR } from './icons'
import type { Posture } from '../types/game'

interface Props {
  value: Posture | null
  onChange: (p: Posture) => void
  disabled?: boolean
}

const OPTIONS: Posture[] = ['confrontational', 'cooperative', 'ambiguous']

export function PostureSelector({ value, onChange, disabled }: Props) {
  const { t } = useTranslation()
  return (
    <div className="space-y-2">
      <div className="label">{t('components.postureSelector.label')}</div>
      <div className="grid grid-cols-3 gap-2">
        {OPTIONS.map((opt) => {
          const active = value === opt
          const color = POSTURE_COLOR[opt]
          return (
            <button
              key={opt}
              disabled={disabled}
              onClick={() => onChange(opt)}
              className={
                'rounded-lg border p-2.5 text-left transition-colors ' +
                (active ? '' : 'border-neutral-200 hover:bg-neutral-200/40') +
                (disabled ? ' opacity-50 cursor-not-allowed' : '')
              }
              style={
                active
                  ? {
                      borderColor: color,
                      backgroundColor: `color-mix(in oklab, ${color} 14%, transparent)`,
                    }
                  : undefined
              }
            >
              <div className="flex items-center gap-1.5">
                <PostureIcon posture={opt} size={18} style={{ color }} />
                <span className="text-xs font-semibold tracking-wide">
                  {t(`components.postureSelector.${opt}`)}
                </span>
              </div>
              <div className="text-[11px] text-neutral-600 mt-1 leading-tight">
                {t(`components.postureSelector.${opt}Help`)}
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
