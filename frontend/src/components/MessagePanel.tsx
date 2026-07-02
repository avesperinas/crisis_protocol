import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { api } from '../api/client'
import { Panel } from './Panel'
import { ChatIcon } from './icons'
import type { FactionView, MessageView } from '../types/game'

interface Props {
  gameId: string
  roleId: string
  factions: FactionView[]
  messages: MessageView[]
  onSent: () => void
  /** When true, fill the parent flex column (desktop) so the chat absorbs slack
      height and the surrounding layout stays a clean rectangle. */
  fill?: boolean
}

export function MessagePanel({ gameId, roleId, factions, messages, onSent, fill }: Props) {
  const { t } = useTranslation()
  const channels = useMemo(() => {
    const others = factions.filter((f) => f.id !== roleId)
    return [
      { id: 'public' as const, label: t('components.messagePanel.publicChannel') },
      ...others.map((f) => ({ id: f.id, label: f.name })),
    ]
  }, [factions, roleId, t])
  const [active, setActive] = useState<string>('public')
  const [draft, setDraft] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const visibleMessages = messages.filter((m) => {
    if (active === 'public') return m.to_role_id === null
    const involves = (a: string, b: string | null) => a === roleId && b === active
    return (
      (m.from_role_id === roleId && m.to_role_id === active) ||
      (m.from_role_id === active && m.to_role_id === roleId) ||
      involves(m.from_role_id, m.to_role_id)
    )
  })

  const submit = async () => {
    if (!draft.trim()) return
    setBusy(true)
    setError(null)
    try {
      await api.sendMessage(gameId, roleId, draft.trim(), active === 'public' ? null : active)
      setDraft('')
      onSent()
    } catch (e) {
      setError(String(e))
    } finally {
      setBusy(false)
    }
  }

  const respondProposal = async (messageId: string, accept: boolean) => {
    setBusy(true)
    setError(null)
    try {
      await api.respondToProposal(gameId, roleId, messageId, accept)
      onSent()
    } catch (e) {
      setError(String(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Panel
      icon={<ChatIcon size={15} />}
      title={t('components.messagePanel.label')}
      className={fill ? 'md:flex-1 md:min-h-0' : ''}
      bodyClassName={fill ? 'md:flex-1 md:flex md:flex-col md:min-h-0' : ''}
    >
      <div className="flex gap-1 flex-wrap mb-2">
        {channels.map((c) => (
          <button
            key={c.id}
            onClick={() => setActive(c.id)}
            className={
              'text-xs px-2 py-1 rounded border ' +
              (active === c.id
                ? 'border-slate-700 bg-slate-50'
                : 'border-neutral-200 hover:bg-neutral-100')
            }
          >
            {c.label}
          </button>
        ))}
      </div>

      <ul
        className={
          'space-y-1 overflow-y-auto mb-3 text-sm border-t border-neutral-100 pt-2 ' +
          (fill ? 'max-h-40 md:max-h-none md:flex-1 md:min-h-[10rem]' : 'max-h-40 md:max-h-72')
        }
      >
        {visibleMessages.length === 0 ? (
          <li className="text-neutral-500 italic text-xs">
            {t('components.messagePanel.emptyChannel')}
          </li>
        ) : (
          visibleMessages.map((m) => (
            <li key={m.id} className="border-l-2 border-neutral-200 pl-2">
              <div className="text-xs text-neutral-500">
                T{m.turn_number} · <span className="font-medium">{m.from_role_id}</span>
                {m.to_role_id ? ` → ${m.to_role_id}` : ` ${t('components.messagePanel.publicTag')}`}
                {m.is_proposal && (
                  <span className="ml-2 text-amber-700">
                    {t('components.messagePanel.proposalTag', {
                      type: m.proposal_type,
                      status: m.proposal_status,
                    })}
                  </span>
                )}
              </div>
              <div className="whitespace-pre-wrap">{m.content}</div>
              {m.is_proposal && m.proposal_status === 'pending' && m.to_role_id === roleId && (
                <div className="flex gap-2 mt-1">
                  <button
                    className="text-xs px-2 py-1 rounded border border-green-300 bg-green-50 text-green-800 hover:bg-green-100"
                    disabled={busy}
                    onClick={() => respondProposal(m.id, true)}
                  >
                    {t('components.messagePanel.acceptProposal')}
                  </button>
                  <button
                    className="text-xs px-2 py-1 rounded border border-red-300 bg-red-50 text-red-800 hover:bg-red-100"
                    disabled={busy}
                    onClick={() => respondProposal(m.id, false)}
                  >
                    {t('components.messagePanel.rejectProposal')}
                  </button>
                </div>
              )}
            </li>
          ))
        )}
      </ul>

      <div className="flex gap-2">
        <input
          className="input flex-1"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={
            active === 'public'
              ? t('components.messagePanel.publicPlaceholder')
              : t('components.messagePanel.privatePlaceholder', { target: active })
          }
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) submit()
          }}
        />
        <button className="btn-primary" disabled={busy || !draft.trim()} onClick={submit}>
          {t('components.messagePanel.sendBtn')}
        </button>
      </div>
      {error && <p className="text-xs text-red-700 mt-1">{error}</p>}
    </Panel>
  )
}
