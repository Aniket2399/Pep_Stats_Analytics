import { useCallback, useEffect, useState } from 'react'

export interface AsyncState<T> { data: T | null; loading: boolean; error: Error | null; reload: () => void }

export function useAsync<T>(
  fn: () => Promise<T>,
  deps: unknown[],
  opts: { pollMs?: number } = {},
): AsyncState<T> {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const run = useCallback(fn, deps)

  const load = useCallback(() => {
    let cancelled = false
    setLoading(true)
    run()
      .then((d) => { if (!cancelled) { setData(d); setError(null) } })
      .catch((e) => { if (!cancelled) setError(e as Error) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [run])

  useEffect(() => {
    const cancel = load()
    let timer: ReturnType<typeof setInterval> | undefined
    if (opts.pollMs) timer = setInterval(() => load(), opts.pollMs)
    return () => { cancel(); if (timer) clearInterval(timer) }
  }, [load, opts.pollMs])

  return { data, loading, error, reload: load }
}
