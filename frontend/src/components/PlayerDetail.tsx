import type { PlayerSeason, Shot } from '../api/types'
import RadarChart from './charts/RadarChart'
import ShotMap from './charts/ShotMap'

const RADAR: { key: keyof PlayerSeason; label: string }[] = [
  { key: 'percentile_goals_per90', label: 'Goals' }, { key: 'percentile_xg_per90', label: 'xG' },
  { key: 'percentile_assists_per90', label: 'Assists' }, { key: 'percentile_xa_per90', label: 'xA' },
  { key: 'percentile_shots_per90', label: 'Shots' }, { key: 'percentile_passes_per90', label: 'Passes' },
  { key: 'percentile_prog_passes_per90', label: 'Prog' }, { key: 'percentile_pressures_per90', label: 'Press' },
  { key: 'percentile_tackles_per90', label: 'Tackles' }, { key: 'percentile_interceptions_per90', label: 'Int' },
]

export default function PlayerDetail({ player, shots }: { player: PlayerSeason; shots: Shot[] }) {
  const metrics = RADAR.map((r) => ({ label: r.label, value: Number(player[r.key]) || 0 }))
  const tiles = [['Goals', player.goals], ['xG', Number(player.xg).toFixed(1)],
                 ['Assists', player.assists], ['xA', Number(player.xa).toFixed(1)]]
  const shotData = shots.map((s) => ({ location_x: s.location_x, location_y: s.location_y,
                                       xg: s.shot_statsbomb_xg, outcome: s.outcome }))
  return (
    <div className="mt-4">
      <h2 className="text-xl font-bold text-navy">{player.player}</h2>
      <p className="text-sm text-slate-500">{player.team} · {player.primary_position} · {player.minutes} min</p>
      <div className="grid grid-cols-4 gap-2 my-4 max-w-md">
        {tiles.map(([k, v]) => (
          <div key={k as string} className="rounded border p-2 text-center">
            <div className="text-lg font-bold text-navy">{v as string}</div>
            <div className="text-xs text-slate-500">{k as string}</div>
          </div>
        ))}
      </div>
      <div className="grid md:grid-cols-2 gap-6 items-start">
        <div><h3 className="font-semibold mb-2">Percentile radar</h3><RadarChart metrics={metrics} /></div>
        <div><h3 className="font-semibold mb-2">Shot map</h3>
          {shotData.length ? <ShotMap shots={shotData} /> : <p className="text-sm text-slate-400">No shots.</p>}</div>
      </div>
    </div>
  )
}
