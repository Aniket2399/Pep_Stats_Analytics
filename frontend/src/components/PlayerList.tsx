import type { PlayerSeason } from '../api/types'

export default function PlayerList({ players, selectedId, onSelect }:
  { players: PlayerSeason[]; selectedId?: number; onSelect: (id: number) => void }) {
  return (
    <div className="overflow-x-auto rounded border">
      <table className="w-full text-sm">
        <thead className="bg-slate-100 text-slate-600">
          <tr><th className="text-left p-2">Player</th><th className="p-2">Pos</th>
          <th className="p-2">Min</th><th className="p-2">Goals</th><th className="p-2">xG</th></tr>
        </thead>
        <tbody>
          {players.map((p) => (
            <tr key={p.player_id} onClick={() => onSelect(p.player_id)}
                className={`cursor-pointer border-t hover:bg-slate-50 ${selectedId === p.player_id ? 'bg-slate-100' : ''}`}>
              <td className="p-2 font-medium">{p.player}</td>
              <td className="p-2 text-center">{p.position_group ?? p.primary_position}</td>
              <td className="p-2 text-center">{p.minutes}</td>
              <td className="p-2 text-center">{p.goals}</td>
              <td className="p-2 text-center">{Number(p.xg).toFixed(1)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
