import { useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { useTranslation } from 'react-i18next'

interface Props {
  turnNumber: number
  narrative: string
  tensionStart: number
  tensionEnd: number
  onDismiss: () => void
}

/**
 * Appears once when a new turn's narrative becomes available. Self-dismisses
 * after 12s, or immediately on click/tap — there is no "next turn" button.
 */
export function NarrativeCard({ turnNumber, narrative, tensionStart, tensionEnd, onDismiss }: Props) {
  const { t } = useTranslation()
  const [closing, setClosing] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => setClosing(true), 12000)
    return () => clearTimeout(timer)
  }, [])

  useEffect(() => {
    if (!closing) return
    const timer = setTimeout(onDismiss, 300)
    return () => clearTimeout(timer)
  }, [closing, onDismiss])

  return (
    <div
      className={`fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-6 cursor-pointer transition-opacity duration-300 ${
        closing ? 'opacity-0' : 'opacity-100'
      }`}
      onClick={() => setClosing(true)}
    >
      <div
        className="card max-w-lg w-full space-y-4 cursor-default"
        style={{ borderColor: 'var(--accent)' }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="label" style={{ color: 'var(--accent)' }}>
          {t('gameRoom.previousTurnSummary', { n: turnNumber })}
        </div>
        <div className="narrative text-base leading-relaxed">
          <ReactMarkdown>{narrative}</ReactMarkdown>
        </div>
        <div className="flex justify-between items-center text-xs text-neutral-500 border-t border-neutral-200 pt-3">
          <span className="font-mono">
            {tensionStart} → {tensionEnd}
          </span>
          <button className="underline" onClick={() => setClosing(true)}>
            {t('gameRoom.narrativeDismissHint')}
          </button>
        </div>
      </div>
    </div>
  )
}
