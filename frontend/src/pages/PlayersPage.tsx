import { useState } from 'react'
import { useClubs, usePlayers, usePlayer, useShots } from '../hooks'
import PlayerList from '../components/PlayerList'
import PlayerDetail from '../components/PlayerDetail'
import Loading from '../components/Loading'
import ErrorState from '../components/ErrorState'
import Empty from '../components/Empty'

const POSITIONS = ['All', 'GK', 'DEF', 'MID', 'FWD']

export default function PlayersPage() {
  const clubs = useClubs()
  const [club, setClub] = useState<number | undefined>(undefined)
  const [pos, setPos] = useState('All')
  const [playerId, setPlayerId] = useState<number | undefined>(undefined)
  const players = usePlayers(club, pos === 'All' ? undefined : pos)
  const detail = usePlayer(playerId)
  const shots = useShots(playerId)

  return (
    <div>
      <h1 className="text-2xl font-bold text-navy mb-4">Historic — Players (La Liga 2015/16)</h1>
      <div className="flex flex-wrap gap-3 mb-4">
        <select className="border rounded px-2 py-1" value={club ?? ''}
                onChange={(e) => { setClub(e.target.value ? Number(e.target.value) : undefined); setPlayerId(undefined) }}>
          <option value="">All clubs</option>
          {(clubs.data ?? []).map((c) => <option key={c.team_id} value={c.team_id}>{c.team}</option>)}
        </select>
        <select className="border rounded px-2 py-1" value={pos} onChange={(e) => setPos(e.target.value)}>
          {POSITIONS.map((p) => <option key={p} value={p}>{p}</option>)}
        </select>
      </div>

      {players.loading && <Loading />}
      {players.error && <ErrorState error={players.error} onRetry={players.reload} />}
      {players.data && (players.data.length
        ? <PlayerList players={players.data} selectedId={playerId} onSelect={setPlayerId} />
        : <Empty message="No players for this filter." />)}

      {playerId && detail.loading && <Loading />}
      {detail.data && <PlayerDetail player={detail.data} shots={shots.data ?? []} />}
    </div>
  )
}
