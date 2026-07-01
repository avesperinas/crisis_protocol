import { useTranslation } from 'react-i18next'
import { FactionBadge } from './FactionBadge'
import { factionTheme } from '../theme/factions'
import type { ScoreboardEntry } from '../types/game'

interface Props {
  entries: ScoreboardEntry[]
  yourRoleId: string
  scenarioId?: string
}

export function Scoreboard({ entries, yourRoleId, scenarioId }: Props) {
  const { t } = useTranslation()
  return (
    <div className="card">
      <h2 className="mb-3">{t('components.scoreboard.title')}</h2>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-neutral-600 border-b border-neutral-200">
            <th className="py-2">{t('components.scoreboard.colRank')}</th>
            <th>{t('components.scoreboard.colFaction')}</th>
            <th>{t('components.scoreboard.colTotal')}</th>
            <th>{t('components.scoreboard.colObjective')}</th>
            <th>{t('components.scoreboard.colEfficiency')}</th>
            <th>{t('components.scoreboard.colCapital')}</th>
            <th>{t('components.scoreboard.colDecision')}</th>
            <th>{t('components.scoreboard.colPublic')}</th>
            <th>{t('components.scoreboard.colHidden')}</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((e, i) => (
            <tr
              key={e.role_id}
              className={
                'border-b border-neutral-100 ' +
                (e.role_id === yourRoleId ? 'bg-slate-50 font-medium' : '')
              }
            >
              <td className="py-2 font-mono">{i + 1}</td>
              <td>
                <div className="flex items-center gap-2">
                  <FactionBadge
                    factionId={e.role_id}
                    name={e.role_name}
                    scenarioId={scenarioId}
                    size={20}
                  />
                  <span style={{ color: factionTheme(scenarioId, e.role_id).color }}>
                    {e.role_name}
                  </span>
                  {e.is_human ? t('components.scoreboard.youTag') : ''}
                </div>
              </td>
              <td className="font-mono">{e.score.total}</td>
              <td className="font-mono">{e.score.objective.toFixed(2)}</td>
              <td className="font-mono">{e.score.efficiency.toFixed(2)}</td>
              <td className="font-mono">{e.score.capital.toFixed(2)}</td>
              <td className="font-mono">{e.score.decision_quality.toFixed(2)}</td>
              <td>{e.public_objective_met ? '✓' : '·'}</td>
              <td>{e.hidden_objective_met ? '✓' : '·'}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="mt-3 text-xs text-neutral-600 space-y-1">
        {entries.map((e) => (
          <details key={e.role_id} className="border-l-2 border-neutral-200 pl-2">
            <summary className="cursor-pointer">
              {t('components.scoreboard.objectivesSummary', { name: e.role_name })}
            </summary>
            <div className="mt-1 ml-2">
              <div>
                {t('components.scoreboard.publicLabel')} {e.public_objective_text}{' '}
                <span className={e.public_objective_met ? 'text-green-700' : 'text-neutral-500'}>
                  ({e.public_objective_met
                    ? t('components.scoreboard.met')
                    : t('components.scoreboard.notMet')})
                </span>
              </div>
              <div>
                {t('components.scoreboard.hiddenLabel')} {e.hidden_objective_text}{' '}
                <span className={e.hidden_objective_met ? 'text-green-700' : 'text-neutral-500'}>
                  ({e.hidden_objective_met
                    ? t('components.scoreboard.met')
                    : t('components.scoreboard.notMet')})
                </span>
              </div>
            </div>
          </details>
        ))}
      </div>
    </div>
  )
}
