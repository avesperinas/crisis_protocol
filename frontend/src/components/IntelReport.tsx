import ReactMarkdown from 'react-markdown'
import { useTranslation } from 'react-i18next'
import { Panel } from './Panel'
import { EyeIcon } from './icons'

interface Props {
  text: string | null
  /** Fill the parent flex column (desktop) so the rail bottom aligns. */
  fill?: boolean
}

export function IntelReport({ text, fill }: Props) {
  const { t } = useTranslation()
  return (
    <Panel
      icon={<EyeIcon size={15} />}
      title={t('components.intelReport.label')}
      className={fill ? 'md:flex-1' : ''}
    >
      {text ? (
        <div className="narrative text-sm">
          <ReactMarkdown>{text}</ReactMarkdown>
        </div>
      ) : (
        <p className="text-sm text-neutral-500 italic">{t('components.intelReport.empty')}</p>
      )}
    </Panel>
  )
}
