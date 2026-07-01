import { useEffect, useRef, useState } from 'react'

/**
 * Calls `fetcher` every `intervalMs` ms while `active`. Returns the latest result.
 * Stops on unmount or when `active` becomes false.
 */
export function usePolling<T>(
  fetcher: () => Promise<T>,
  intervalMs: number,
  active: boolean,
): { data: T | null; error: Error | null; refresh: () => Promise<void> } {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<Error | null>(null)
  const aliveRef = useRef(true)
  const fetcherRef = useRef(fetcher)
  fetcherRef.current = fetcher

  const run = async () => {
    try {
      const next = await fetcherRef.current()
      if (aliveRef.current) {
        setData(next)
        setError(null)
      }
    } catch (e) {
      if (aliveRef.current) setError(e as Error)
    }
  }

  useEffect(() => {
    aliveRef.current = true
    if (!active) return
    run()
    const handle = window.setInterval(run, intervalMs)
    return () => {
      aliveRef.current = false
      window.clearInterval(handle)
    }
  }, [active, intervalMs])

  return { data, error, refresh: run }
}
