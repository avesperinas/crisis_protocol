import type { ReactNode } from 'react'

interface Props {
  /** Small line icon shown in the accent chip. */
  icon: ReactNode
  title: string
  /** Optional control pinned to the right of the header (e.g. a button). */
  action?: ReactNode
  children: ReactNode
  className?: string
  /** Wrapper class for the body, e.g. to make it a growing flex column. */
  bodyClassName?: string
}

/**
 * Shared panel chrome used by the right-rail cards (diplomacy, messaging,
 * intel, pacts) so they read as one coherent family: an accent icon chip, a
 * small-caps title, and an optional header action.
 */
export function Panel({ icon, title, action, children, className, bodyClassName }: Props) {
  return (
    <section className={'card flex flex-col' + (className ? ' ' + className : '')}>
      <div className="flex items-center gap-2 mb-2.5">
        <span
          className="flex items-center justify-center rounded-md shrink-0"
          style={{
            width: 26,
            height: 26,
            color: 'var(--accent)',
            backgroundColor: 'color-mix(in oklab, var(--accent) 16%, transparent)',
          }}
        >
          {icon}
        </span>
        <h2 className="label flex-1 min-w-0 truncate">{title}</h2>
        {action}
      </div>
      <div className={bodyClassName ?? ''}>{children}</div>
    </section>
  )
}
