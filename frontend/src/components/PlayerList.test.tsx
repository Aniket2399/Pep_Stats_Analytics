import { render, screen } from '@testing-library/react'
import { expect, test, vi } from 'vitest'
import PlayerList from './PlayerList'
import type { PlayerSeason } from '../api/types'

const players = [
  { player_id: 10, player: 'Suárez', primary_position: 'CF', minutes: 540, goals: 40, xg: 30 },
  { player_id: 11, player: 'Messi', primary_position: 'RW', minutes: 500, goals: 26, xg: 24 },
] as unknown as PlayerSeason[]

test('renders a row per player and fires onSelect', async () => {
  const onSelect = vi.fn()
  render(<PlayerList players={players} selectedId={undefined} onSelect={onSelect} />)
  expect(screen.getByText('Suárez')).toBeInTheDocument()
  expect(screen.getByText('Messi')).toBeInTheDocument()
  screen.getByText('Suárez').click()
  expect(onSelect).toHaveBeenCalledWith(10)
})
