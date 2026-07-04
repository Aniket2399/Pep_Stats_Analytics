import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Nav from '@components/Nav';
import TournamentPage from '@pages/TournamentPage';
import LiveMatchPage from '@pages/LiveMatchPage';
import TeamsPage from '@pages/TeamsPage';
import '@styles/globals.css';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-white">
        <Nav />
        <Routes>
          <Route path="/" element={<TournamentPage />} />
          <Route path="/match/:id" element={<LiveMatchPage />} />
          <Route path="/teams" element={<TeamsPage />} />
          <Route path="/players" element={<TeamsPage />} />
          <Route path="/predictions" element={<TeamsPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
