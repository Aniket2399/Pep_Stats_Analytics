import { useMemo, useState } from 'react'
import { useAsync } from './hooks/useAsync'
import { loadAppData } from './data/adapter'
import { refreshLive } from './api/client'
import { crestStyle } from './data/kits'
import Loading from './components/Loading'
import ErrorState from './components/ErrorState'
import Overview from './tabs/Overview'
import Standings from './tabs/Standings'
import Squad from './tabs/Squad'
import Trends from './tabs/Trends'
import SetPieces from './tabs/SetPieces'
import Compare from './tabs/Compare'
import Players from './tabs/Players'
import WcOverview from './tabs/WcOverview'
import WcTeams from './tabs/WcTeams'
import WcInsights from './tabs/WcInsights'
import WcBracket from './tabs/WcBracket'
import WcGroups from './tabs/WcGroups'

type Source = 'historic' | 'wc'
// [key, label] — labels EXACTLY match the wireframe nav.
const HISTORIC_TABS: [string, string][] = [['overview', 'Overview'], ['standings', 'Standings'], ['squad', 'Squad'], ['trends', 'Trends'], ['setpieces', 'Set Pieces'], ['compare', 'Compare'], ['players', 'Players']]
const WC_TABS: [string, string][] = [['wc_overview', 'Overview'], ['wc_teams', 'Team Metrics'], ['wc_insights', 'Insights'], ['wc_bracket', 'Bracket'], ['wc_groups', 'Groups']]
const DEFAULT_TAB: Record<Source, string> = { historic: 'overview', wc: 'wc_overview' }

export default function App() {
  const [source, setSource] = useState<Source>('historic')
  const [tab, setTab] = useState<string>('overview')
  const [club, setClub] = useState<string>('Barcelona')
  const [updating, setUpdating] = useState(false)
  const [updateError, setUpdateError] = useState<string | null>(null)
  const { data, loading, error, reload } = useAsync(() => loadAppData(), [])

  const tabs = source === 'historic' ? HISTORIC_TABS : WC_TABS
  const pick = (s: Source) => { setSource(s); setTab(DEFAULT_TAB[s]) }
  const onUpdate = async () => {
    setUpdating(true)
    setUpdateError(null)
    try {
      const res = await refreshLive()
      if (!res.ok) setUpdateError(res.error ?? 'the refresh failed for an unknown reason')
    } finally {
      setUpdating(false)
      reload()
    }
  }

  const clubs = useMemo(() => (data ? data.historic.standings.map((r) => r.team) : []), [data])
  const teamRow = data?.historic.standings.find((r) => r.team === club) ?? data?.historic.standings[0]
  const squad = (data && teamRow) ? (data.historic.squads[teamRow.team] ?? []) : []

  const badge = source === 'wc'
    ? { code: 'WC26', title: 'FIFA World Cup 2026', sub: 'USA · CANADA · MEXICO' }
    : { code: teamRow?.code ?? 'BAR', title: teamRow?.team ?? 'Barcelona', sub: 'LA LIGA · 2015/16' }

  return (
    <div className={`app${source === 'wc' ? ' wc' : ''}`} data-testid="apex-shell">
      <header className="fifa-top">
        <span className="ft-brand">PepStats</span>
        <div className="ft-links">
          <div className="srcseg">
            <button className={`srcbtn${source === 'historic' ? ' on' : ''}`} onClick={() => pick('historic')}>Historic</button>
            <button className={`srcbtn${source === 'wc' ? ' on' : ''}`} onClick={() => pick('wc')}>
              <span className="srcdot" />World Cup 2026
            </button>
          </div>
        </div>
      </header>

      <nav className="fifa-nav">
        <div className="wc-badge">
          <div className="wc-mark" style={source === 'historic' ? crestStyle(badge.code) : {
            background: 'linear-gradient(135deg,#e21d43 0%,#7a3cdc 55%,#ffc93c 130%)',
            color: '#fff', fontSize: 12, letterSpacing: '.02em', boxShadow: '0 4px 14px rgba(226,29,67,.35)',
          }}>{badge.code}</div>
          <div><div className="wc-title">{badge.title}</div><div className="wc-sub">{badge.sub}</div></div>
        </div>
        {source === 'historic' && clubs.length > 0 && (
          <label className="clubpick" title="Select club">
            <span className="clubpick-cap">CLUB</span>
            <select className="clubsel" value={club} onChange={(e) => setClub(e.target.value)}>
              {clubs.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </label>
        )}
        <div className="navtabs">
          {tabs.map(([key, label]) => (
            <button key={key} className={`tab${tab === key ? ' on' : ''}`} onClick={() => setTab(key)}>{label}</button>
          ))}
        </div>
        {source === 'wc' && (
          <button className="wc-update" onClick={onUpdate} disabled={updating}
            title="Fetch the latest scores from the live source">
            <span className="wc-update-dot" />{updating ? 'Updating…' : 'Update scores'}
          </button>
        )}
        <div className="season-tag">{source === 'historic' ? 'LA LIGA · 2015/16' : 'WORLD CUP · 2026'}</div>
      </nav>

      <main className="wrap-main">
        {source === 'wc' && updateError && (
          <div className="update-error" data-testid="update-error" role="alert">
            <strong>⚠ Couldn't update scores.</strong> The scores below are unchanged. {updateError}
          </div>
        )}
        {loading && <Loading />}
        {error && <ErrorState error={error} onRetry={reload} />}
        {data && data.source === 'sample' && <div className="sec-sub" style={{ marginBottom: 12 }}>⚠ Live data service unavailable — showing cached results.</div>}
        {data && (
          <>
            {tab === 'overview' && teamRow && <Overview team={teamRow} squad={squad} />}
            {tab === 'standings' && <Standings rows={data.historic.standings} />}
            {tab === 'squad' && <Squad squad={squad} club={teamRow?.team ?? ''} />}
            {tab === 'trends' && <Trends />}
            {tab === 'setpieces' && <SetPieces />}
            {tab === 'compare' && <Compare />}
            {tab === 'players' && <Players squad={squad} club={teamRow?.team ?? ''} />}
            {tab === 'wc_overview' && <WcOverview matches={data.world_cup_2026.matches} fixtures={data.world_cup_2026.fixtures} teams={data.world_cup_2026.team_metrics} groups={data.world_cup_2026.group_standings} />}
            {tab === 'wc_teams' && <WcTeams teams={data.world_cup_2026.team_metrics} />}
            {tab === 'wc_insights' && <WcInsights groups={data.world_cup_2026.group_standings} />}
            {tab === 'wc_bracket' && <WcBracket rounds={data.world_cup_2026.bracket} />}
            {tab === 'wc_groups' && <WcGroups groups={data.world_cup_2026.group_standings} />}
          </>
        )}
      </main>
    </div>
  )
}
