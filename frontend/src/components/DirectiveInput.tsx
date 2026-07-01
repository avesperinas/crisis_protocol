import { useTranslation } from 'react-i18next'

interface Props {
  value: string
  onChange: (v: string) => void
  maxLength?: number
  disabled?: boolean
  placeholder?: string
}

export function DirectiveInput({ value, onChange, maxLength = 300, disabled, placeholder }: Props) {
  const { t } = useTranslation()
  return (
    <div className="space-y-2">
      <div className="flex justify-between items-baseline">
        <div className="label">{t('components.directiveInput.label')}</div>
        <div className="text-xs font-mono text-neutral-600">
          {value.length} / {maxLength}
        </div>
      </div>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value.slice(0, maxLength))}
        maxLength={maxLength}
        rows={2}
        disabled={disabled}
        placeholder={placeholder ?? t('components.directiveInput.placeholder')}
        className="input w-full resize-none"
      />
    </div>
  )
}
