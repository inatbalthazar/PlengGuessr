import React from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import GamePlayer from './pages/GamePlayer';
import Admin from './pages/Admin';
import { Music2, Settings } from 'lucide-react';

function Navbar() {
  const loc = useLocation();
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <span className="brand-icon">🎵</span>
        <span className="brand-name">PlengGuessr</span>
      </div>
      <div className="navbar-links">
        <Link to="/" className={`nav-link ${loc.pathname === '/' ? 'active' : ''}`}>
          <Music2 size={15} />
          Home
        </Link>
        <Link to="/admin" className={`nav-link ${loc.pathname === '/admin' ? 'active' : ''}`}>
          <Settings size={15} />
          Login
        </Link>
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <div className="app">
      <Navbar />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<GamePlayer />} />
          <Route path="/admin" element={<Admin />} />
        </Routes>
      </main>
    </div>
  );
}
