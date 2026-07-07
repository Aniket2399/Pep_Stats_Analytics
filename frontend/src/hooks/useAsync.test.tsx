import { renderHook, waitFor } from '@testing-library/react'
import { expect, test, vi } from 'vitest'
import { useAsync } from './useAsync'

test('resolves to data', async () => {
  const { result } = renderHook(() => useAsync(() => Promise.resolve(42), []))
  expect(result.current.loading).toBe(true)
  await waitFor(() => expect(result.current.loading).toBe(false))
  expect(result.current.data).toBe(42)
  expect(result.current.error).toBeNull()
})

test('captures error', async () => {
  const { result } = renderHook(() => useAsync(() => Promise.reject(new Error('x')), []))
  await waitFor(() => expect(result.current.error).not.toBeNull())
})

test('polls on interval', async () => {
  vi.useFakeTimers()
  const fn = vi.fn().mockResolvedValue(1)
  renderHook(() => useAsync(fn, [], { pollMs: 1000 }))
  await vi.advanceTimersByTimeAsync(0)   // initial
  await vi.advanceTimersByTimeAsync(1000) // one poll
  expect(fn.mock.calls.length).toBeGreaterThanOrEqual(2)
  vi.useRealTimers()
})
