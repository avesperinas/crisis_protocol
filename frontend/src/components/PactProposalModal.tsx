import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { api } from '../api/client'
import type { FactionView, PactType, PactTypeLabels } from '../types/game'

interface Props {
  gameId: string
  roleId: string
  factions: FactionView[]
  pactLabels: PactTypeLabels
  onClose: () => void
  onDone: (result: { status: 'accepted' | 'rejected' | 'pending'; reason: string }) => void
}

const PACT_TYPES: PactType[] = ['alliance', 'non_aggression', 'trade', 'intel_share']

export function PactProposalModal({ gameId, roleId, factions, pactLabels, onClose, onDone }: Props) {
  const { t } = useTranslation()
  const others = factions.filter((f) => f.id !== roleId)
  const [target, setTarget] = useState<string>(others[0]?.id ?? '')
  const [pactType, setPactType] = useState<PactType>('alliance')
  const [isSecret, setIsSecret] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submit = async () => {
    if (!target) return
    setBusy(true)
    setError(null)
    try {
      const res = await api.proposePact(gameId, roleId, target, pactType, isSecret)
      onDone({ status: res.status, reason: res.reason })
      onClose()
    } catch (e) {
      setError(String(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div
      className="fixed inset-0 bg-black/60 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div className="card max-w-md w-full space-y-4" onClick={(e) => e.stopPropagation()}>
        <h2>{t('components.pactProposalModal.title')}</h2>

        <div>
          <label className="label block mb-1">{t('components.pactProposalModal.targetLabel')}</label>
          <select
            className="input w-full"
            value={target}
            onChange={(e) => setTarget(e.target.value)}
          >
            {others.map((f) => (
              <option key={f.id} value={f.id}>
                {f.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="label block mb-1">{t('components.pactProposalModal.typeLabel')}</label>
          <div className="space-y-1">
            {PACT_TYPES.map((type) => (
              <label
                key={type}
                className={
                  'block p-2 rounded border cursor-pointer transition-colors ' +
                  (pactType === type
                    ? 'border-slate-700 bg-slate-50'
                    : 'border-neutral-200 hover:bg-neutral-50')
                }
              >
                <input
                  type="radio"
                  className="mr-2"
                  checked={pactType === type}
                  onChange={() => setPactType(type)}
                />
                <span className="font-medium text-sm">{pactLabels[type].label}</span>
                <span className="text-xs text-neutral-600 block ml-5">
                  {pactLabels[type].help}
                </span>
              </label>
            ))}
          </div>
        </div>

        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={isSecret}
            onChange={(e) => setIsSecret(e.target.checked)}
          />
          {t('components.pactProposalModal.secretLabel')}
        </label>

        {error && <p className="text-xs text-red-700">{error}</p>}

        <div className="flex justify-end gap-2">
          <button className="btn" disabled={busy} onClick={onClose}>
            {t('common.cancel')}
          </button>
          <button className="btn-primary" disabled={busy} onClick={submit}>
            {busy
              ? t('components.pactProposalModal.sendingBtn')
              : t('components.pactProposalModal.proposeBtn')}
          </button>
        </div>
      </div>
    </div>
  )
}
