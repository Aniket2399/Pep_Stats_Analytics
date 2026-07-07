import { useAsync } from './useAsync'
import * as client from '../api/client'

const POLL = 45000

export const useClubs = () => useAsync(() => client.getClubs(), [])
export const usePlayers = (club?: number, position?: string) =>
  useAsync(() => client.getPlayers({ club, position }), [club, position])
export const usePlayer = (id?: number) =>
  useAsync(() => (id ? client.getPlayer(id) : Promise.resolve(null)), [id])
export const useShots = (player?: number) =>
  useAsync(() => (player ? client.getShots({ player }) : Promise.resolve([])), [player])
export const useLiveMatches = () => useAsync(() => client.getLiveMatches(), [], { pollMs: POLL })
export const useLiveFixtures = () => useAsync(() => client.getLiveFixtures(), [], { pollMs: POLL })
export const useLiveStandings = () => useAsync(() => client.getLiveStandings(), [], { pollMs: POLL })
