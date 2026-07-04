import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Trophy, Target, Radio } from 'lucide-react';
import { ENDPOINTS } from '@config/api';
import { useMatches } from '@hooks/useMatches';
import type { Match } from '@hooks/useMatchData';

interface StandingRow {
  group: string; rank: number; team: string; flag: string;
  w: number; d: number; l: number; gf: number; ga: number; pts: number;
}
interface Scorer {
  rank: number; player: string; team: string; flag: string; goals: number; assists: number;
}

function MatchRow({ m }: { m: Match }) {
  const isLive = m.status === 'LIVE';
  return (
    <Link to={`/match/${m.id}`}
      className="flex items-center justify-between bg-white rounded-lg border p-4 hover:shadow-md transition">
      <div className="flex items-center gap-2">
        <span className="text-2xl">{m.team1.flag}</span>
        <span className="font-semibold">{m.team1.name}</span>
      </div>
      <div className="text-center">
        {m.status === 'SCHEDULED'
          ? <span className="text-sm text-gray-500">{new Date(m.time).toLocaleString()}</span>
          : <span className="text-xl font-bold">{m.team1.score} - {m.team2.score}</span>}
        <div className={`text-xs ${isLive ? 'text-red-600 font-bold' : 'text-gray-400'}`}>
          {isLive ? `🔴 LIVE ${m.time}` : m.status}
        </div>
      </div>
      <div className="flex items-center gap-2">
        <span className="font-semibold">{m.team2.name}</span>
        <span className="text-2xl">{m.team2.flag}</span>
      </div>
    </Link>
  );
}

export default function TournamentPage() {
  const { live, upcoming, recent, source, loading: matchesLoading, error: matchesError } = useMatches();
  const [standings, setStandings] = useState<StandingRow[]>([]);
  const [scorers, setScorers] = useState<Scorer[]>([]);

  useEffect(() => {
    axios.get(ENDPOINTS.standings).then(r => setStandings(r.data.data)).catch(() => {});
    axios.get(ENDPOINTS.leaderboards).then(r => setScorers(r.data.data)).catch(() => {});
  }, []);

  const heroMatches = live.length > 0
    ? live
    : [...upcoming.slice(0, 1), ...recent.slice(0, 1)];

  return (
    <div className="min-h-screen bg-fifa-light">
      <div className="bg-gradient-to-r from-fifa-navy to-fifa-green py-12">
        <div className="container text-center">
          <h1 className="text-5xl font-bold text-white mb-2">🏆 FIFA WORLD CUP 2026</h1>
          <p className="text-fifa-gold font-semibold">Real-Time Tournament Analytics</p>
          {source && (
            <span className="inline-block mt-2 text-xs px-2 py-1 rounded bg-black/20 text-white">
              {source === 'mock' ? '⚠️ sample data' : `● ${source} data`}
            </span>
          )}
        </div>
      </div>

      <div className="container py-10 space-y-14">
        {/* Live / hero */}
        <section>
          <div className="flex items-center gap-3 mb-4">
            <Radio className="text-red-600" size={28} />
            <h2 className="text-2xl font-bold text-fifa-navy">
              {live.length > 0 ? 'Live Now' : 'Featured'}
            </h2>
          </div>
          {matchesLoading && <p className="text-gray-500">Loading matches…</p>}
          {matchesError && <p className="text-red-600">Could not load matches: {matchesError}</p>}
          {!matchesLoading && !matchesError && heroMatches.length === 0 && (
            <p className="text-gray-500">No matches available right now.</p>
          )}
          <div className="grid gap-3">
            {heroMatches.map(m => <MatchRow key={m.id} m={m} />)}
          </div>
        </section>

        {/* Upcoming */}
        {upcoming.length > 0 && (
          <section>
            <h2 className="text-2xl font-bold text-fifa-navy mb-4">📅 Upcoming Matches</h2>
            <div className="grid gap-3">{upcoming.map(m => <MatchRow key={m.id} m={m} />)}</div>
          </section>
        )}

        {/* Recent */}
        {recent.length > 0 && (
          <section>
            <h2 className="text-2xl font-bold text-fifa-navy mb-4">✅ Recent Results</h2>
            <div className="grid gap-3">{recent.map(m => <MatchRow key={m.id} m={m} />)}</div>
          </section>
        )}

        {/* Standings */}
        {standings.length > 0 && (
          <section>
            <div className="flex items-center gap-3 mb-4">
              <Trophy className="text-fifa-gold" size={28} />
              <h2 className="text-2xl font-bold text-fifa-navy">Standings</h2>
            </div>
            <div className="overflow-x-auto bg-white rounded-lg border">
              <table className="w-full">
                <thead>
                  <tr className="border-b-2 border-fifa-gold bg-fifa-light text-fifa-navy">
                    <th className="text-left py-2 px-3">Grp</th>
                    <th className="text-left py-2 px-3">#</th>
                    <th className="text-left py-2 px-3">Team</th>
                    <th className="py-2 px-3">W</th><th className="py-2 px-3">D</th>
                    <th className="py-2 px-3">L</th><th className="py-2 px-3">GD</th>
                    <th className="py-2 px-3 text-fifa-gold">Pts</th>
                  </tr>
                </thead>
                <tbody>
                  {standings.map((r, i) => (
                    <tr key={i} className="border-b hover:bg-fifa-light">
                      <td className="py-2 px-3 text-xs text-gray-500">{r.group?.replace('GROUP_', '')}</td>
                      <td className="py-2 px-3 font-bold">{r.rank}</td>
                      <td className="py-2 px-3"><span className="mr-2">{r.flag}</span>{r.team}</td>
                      <td className="py-2 px-3 text-center">{r.w}</td>
                      <td className="py-2 px-3 text-center">{r.d}</td>
                      <td className="py-2 px-3 text-center">{r.l}</td>
                      <td className="py-2 px-3 text-center">{r.gf - r.ga > 0 ? '+' : ''}{r.gf - r.ga}</td>
                      <td className="py-2 px-3 text-center font-bold text-fifa-gold">{r.pts}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* Top scorers */}
        {scorers.length > 0 && (
          <section>
            <div className="flex items-center gap-3 mb-4">
              <Target className="text-fifa-gold" size={28} />
              <h2 className="text-2xl font-bold text-fifa-navy">⭐ Top Scorers</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {scorers.slice(0, 8).map((p) => (
                <div key={p.rank} className="card card-gold p-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="text-3xl">{p.flag}</div>
                      <h3 className="font-bold text-fifa-navy">{p.player}</h3>
                      <p className="text-sm text-gray-600">{p.team}</p>
                    </div>
                    <div className="bg-fifa-gold text-fifa-navy font-bold rounded-full w-12 h-12 flex items-center justify-center text-xl">
                      {p.goals}
                    </div>
                  </div>
                  <span className="badge badge-navy mt-2 inline-block">Assists: {p.assists}</span>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
