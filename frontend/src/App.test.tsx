import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import App from './App'
import type { AppData } from './data/types'

const refreshLive = vi.fn()
vi.mock('./api/client', () => ({ refreshLive: (...a: unknown[]) => refreshLive(...a) }))

vi.mock('./data/adapter', () => ({
  loadAppData: (): Promise<AppData> => Promise.resolve({
    source: 'live',
    historic: {
      competition: 'La Liga 2015/16',
      standings: [{ pos: 1, code: 'BAR', team: 'Barcelona', team_id: 217, played: 38, won: 29, drawn: 4, lost: 5, gf: 112, ga: 29, gd: 83, points: 91, form: 'WWWDL', xg_for: 80, xg_against: 30, possession_pct: 64, ppda: 8 }],
      squads: { Barcelona: [{ number: 10, player_id: 2, player: 'Lionel Messi', position: 'RW', apps: 33, goals: 26, assists: 15, minutes: 2801, pass_pct: null, percentiles: {} }] },
    },
    world_cup_2026: { team_metrics: [], group_standings: [], bracket: [], matches: [], fixtures: [] },
  }),
}))

test('renders the PepStats shell with source toggle and tabs', () => {
  render(<App />)
  expect(screen.getByTestId('apex-shell')).toBeInTheDocument()
  expect(screen.getByText('PepStats')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Historic' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'World Cup 2026' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: /standings/i })).toBeInTheDocument()
})

test('loads data and shows the historic overview club', async () => {
  const { getAllByText } = render(<App />)
  await waitFor(() => expect(getAllByText('Barcelona').length).toBeGreaterThan(0))
})

test('shows the reason when "Update scores" fails instead of silently spinning', async () => {
  refreshLive.mockResolvedValue({ ok: false, error: "ModuleNotFoundError: No module named 'pandas'" })
  const user = userEvent.setup()
  render(<App />)

  await user.click(screen.getByRole('button', { name: /World Cup 2026/ }))
  await user.click(screen.getByRole('button', { name: /Update scores/ }))

  const err = await screen.findByTestId('update-error')
  expect(err).toHaveTextContent(/couldn't update/i)
  expect(err).toHaveTextContent(/pandas/)
})

test('shows no error banner when "Update scores" succeeds', async () => {
  refreshLive.mockResolvedValue({ ok: true })
  const user = userEvent.setup()
  render(<App />)

  await user.click(screen.getByRole('button', { name: /World Cup 2026/ }))
  await user.click(screen.getByRole('button', { name: /Update scores/ }))

  await waitFor(() => expect(screen.getByRole('button', { name: /Update scores/ })).toBeEnabled())
  expect(screen.queryByTestId('update-error')).not.toBeInTheDocument()
})
