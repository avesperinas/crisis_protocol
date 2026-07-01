import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { api } from '../api/client'
import { Panel } from './Panel'
import { LinkIcon } from './icons'
import type { PactTypeLabels, PactView } from '../types/game'

interface Props {
  gameId: string
  roleId: string
  pacts: PactView[]
  pactLabels: PactTypeLabels
  onChanged: () => void
}

export function PactsActive({ gameId, roleId, pacts, pactLabels, onChanged }: Props) {
  const { t } = useTranslation()
  const [busy, setBusy] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const breakPact = async (pactId: string) => {
    setBusy(pactId)
    setError(null)
    try {
      await api.breakPact(gameId, roleId, pactId)
      onChanged()
    } catch (e) {
      setError(String(e))
    } finally {
      setBusy(null)
    }
  }

  return (
    <Panel icon={<LinkIcon size={15} />} title={t('components.pactsActive.label')}>
      {pacts.length === 0 ? (
        <p className="text-sm text-neutral-500 italic">{t('components.pactsActive.empty')}</p>
      ) : (
        <ul className="space-y-2">
          {pacts.map((p) => {
            const youIn = p.player_a_id === roleId || p.player_b_id === roleId
            return (
              <li
                key={p.id}
                className="text-sm flex justify-between items-center gap-2 rounded border border-neutral-200 px-2.5 py-1.5"
                style={{ borderLeft: '3px solid var(--accent)' }}
              >
                <div className="min-w-0">
                  <div className="font-medium">{pactLabels[p.type].label}</div>
                  <div className="text-xs text-neutral-600 truncate">
                    {p.player_a_id} ↔ {p.player_b_id}
                    {p.is_secret && (
                      <span className="ml-1.5 text-amber-700">
                        {t('components.pactsActive.secretTag')}
                      </span>
                    )}
                  </div>
                </div>
                {youIn && (
                  <button
                    className="btn text-xs shrink-0"
                    disabled={busy === p.id}
                    onClick={() => breakPact(p.id)}
                  >
                    {busy === p.id
                      ? t('components.pactsActive.breakingBtn')
                      : t('components.pactsActive.breakBtn')}
                  </button>
                )}
              </li>
            )
          })}
        </ul>
      )}
      {error && <p className="text-xs text-red-700 mt-2">{error}</p>}
    </Panel>
  )
}
