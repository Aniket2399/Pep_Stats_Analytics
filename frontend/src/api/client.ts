import { API_BASE } from '../config'
import type { Club, PlayerSeason, Shot, LiveMatch, Fixture, StandingRow, Meta } from './types'

export class ApiError extends Error {
  constructor(message: string, readonly status?: number) { super(message) }
}

async function request<T>(path: string): Promise<T> {
  let res: Response
  try {
    res = await fetch(`${API_BASE}${path}`)
  } catch (e) {
    throw new ApiError(`network error: ${(e as Error).message}`)
  }
  if (!res.ok) throw new ApiError(`HTTP ${res.status} for ${path}`, res.status)
  return (await res.json()) as T
}

function qs(params: Record<string, string | number | undefined>): string {
  const parts = Object.entries(params)
    .filter(([, v]) => v !== undefined && v !== '')
    .map(([k, v]) => `${k}=${encodeURIComponent(String(v))}`)
  return parts.length ? `?${parts.join('&')}` : ''
}

export const getClubs = () => request<Club[]>('/api/clubs')
export const getPlayers = (p: { club?: number; position?: string; limit?: number } = {}) =>
  request<PlayerSeason[]>(`/api/players${qs(p)}`)
export const getPlayer = (id: number) => request<PlayerSeason>(`/api/players/${id}`)
export const getShots = (p: { club?: number; player?: number } = {}) =>
  request<Shot[]>(`/api/shots${qs(p)}`)
export const getLiveMatches = () => request<LiveMatch[]>('/api/live/matches')
export const getLiveFixtures = () => request<Fixture[]>('/api/live/fixtures')
export const getLiveStandings = () => request<StandingRow[]>('/api/live/standings')
export const getKnockout = () => request<LiveMatch[]>('/api/live/knockout')

export interface RefreshResult { ok: boolean; error?: string }

/** The endpoint answers 200 with {ok:false, log|error} when the rebuild itself
 *  fails, so a failure has to be read out of the body, not the status. */
export async function refreshLive(): Promise<RefreshResult> {
  let res: Response
  try {
    res = await fetch(`${API_BASE}/api/live/refresh`, { method: 'POST' })
  } catch (e) {
    return { ok: false, error: `network error: ${(e as Error).message}` }
  }
  if (!res.ok) return { ok: false, error: `HTTP ${res.status} from /api/live/refresh` }

  const body = (await res.json()) as { ok?: boolean; log?: string; error?: string }
  if (body.ok) return { ok: true }
  return { ok: false, error: lastLine(body.error ?? body.log) ?? 'the refresh failed for an unknown reason' }
}

/** The backend's `log` is a whole traceback; its last line carries the actual cause. */
function lastLine(text?: string): string | undefined {
  const lines = (text ?? '').split('\n').map((l) => l.trim()).filter(Boolean)
  return lines.length ? lines[lines.length - 1] : undefined
}
export const getMeta = () => request<Meta>('/api/meta')

// Historic league table (team_season). Rows are cast to the adapter's TeamSeasonRow.
export const getStandings = () => request<unknown[]>('/api/standings')

export type { LiveMatch as LiveMatchResult } from './types'
