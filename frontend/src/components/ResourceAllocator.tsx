import { useTranslation } from 'react-i18next'
import { DomainIcon, DOMAIN_COLOR } from './icons'
import type { Domain, TokenAllocation } from '../types/game'

interface Props {
  tokens: TokenAllocation
  budget: number
  onChange: (next: TokenAllocation) => void
  disabled?: boolean
  persistentResources?: TokenAllocation
}

const DOMAINS: Domain[] = ['MIL', 'DIP', 'ECO', 'INT']
const DOMAIN_KEY: Record<Domain, string> = {
  MIL: 'domainMil',
  DIP: 'domainDip',
  ECO: 'domainEco',
  INT: 'domainInt',
}

export function ResourceAllocator({
  tokens,
  budget,
  onChange,
  disabled,
  persistentResources,
}: Props) {
  const { t } = useTranslation()
  const total = tokens.MIL + tokens.DIP + tokens.ECO + tokens.INT
  // Tokens are drawn from the persistent reserve, so a domain can never be
  // allocated more than the pool holds (nor more than the per-turn budget).
  const domainMax = (d: Domain) =>
    persistentResources ? Math.min(budget, persistentResources[d]) : budget
  const setDomain = (d: Domain, raw: number) => {
    const clamped = Math.max(0, Math.min(domainMax(d), raw))
    onChange({ ...tokens, [d]: clamped })
  }
  const over = total > budget
  return (
    <div className="space-y-2">
      <div className="flex justify-between items-baseline">
        <div className="label">{t('components.resourceAllocator.label')}</div>
        <div className={'text-sm font-mono ' + (over ? 'text-red-600 font-semibold' : '')}>
          {total} / {budget}
        </div>
      </div>
      <div className="grid grid-cols-2 gap-2">
        {DOMAINS.map((d) => {
          const color = DOMAIN_COLOR[d]
          const has = tokens[d] > 0
          return (
            <label
              key={d}
              title={t(`components.resourceAllocator.${DOMAIN_KEY[d]}Help`)}
              className={
                'rounded-lg border p-2.5 block transition-colors ' +
                (has ? '' : 'border-neutral-200') +
                (disabled ? ' opacity-50 cursor-not-allowed' : ' cursor-pointer')
              }
              style={
                has ? { borderColor: `color-mix(in oklab, ${color} 55%, transparent)` } : undefined
              }
            >
              <div className="flex items-center gap-2">
                <span
                  className="flex items-center justify-center rounded-md shrink-0"
                  style={{
                    width: 28,
                    height: 28,
                    color,
                    backgroundColor: `color-mix(in oklab, ${color} 16%, transparent)`,
                  }}
                >
                  <DomainIcon domain={d} size={16} />
                </span>
                <span className="font-medium text-sm flex-1 min-w-0">
                  {t(`components.resourceAllocator.${DOMAIN_KEY[d]}`)}
                </span>
                <span
                  className="font-mono text-lg leading-none tabular-nums"
                  style={has ? { color } : undefined}
                >
                  {tokens[d]}
                </span>
              </div>
              <input
                type="range"
                min={0}
                max={domainMax(d)}
                value={tokens[d]}
                onChange={(e) => setDomain(d, parseInt(e.target.value || '0', 10))}
                disabled={disabled}
                className="w-full mt-2 cursor-pointer"
                style={{ accentColor: color }}
              />
              {persistentResources && (
                <div className="text-[11px] text-neutral-500 font-mono mt-0.5">
                  {t('components.resourceAllocator.reserveHint', {
                    current: persistentResources[d],
                    after: Math.max(0, persistentResources[d] - tokens[d]),
                  })}
                </div>
              )}
            </label>
          )
        })}
      </div>
      {over && (
        <div className="text-sm text-red-600">
          {t('components.resourceAllocator.overBudget', { total, budget })}
        </div>
      )}
    </div>
  )
}
