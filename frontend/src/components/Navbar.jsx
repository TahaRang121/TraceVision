import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Eye, Search, Layers, HelpCircle } from 'lucide-react';

export default function Navbar() {
  const location = useLocation();

  return (
    <nav className="navbar">
      <div className="nav-container">
        <Link to="/" className="nav-logo">
          <div className="logo-badge">
            <Eye size={20} />
          </div>
          <span>TraceVision</span>
        </Link>

        <div className="nav-links">
          <Link 
            to="/" 
            className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}
          >
            Home
          </Link>
          <Link 
            to="/search" 
            className={`nav-link ${location.pathname.startsWith('/search') ? 'active' : ''}`}
          >
            <Search size={16} />
            <span>Search Person</span>
          </Link>
          <Link 
            to="/results/demo" 
            className={`nav-link ${location.pathname.startsWith('/results') ? 'active' : ''}`}
          >
            <Layers size={16} />
            <span>Demo Results</span>
          </Link>
        </div>
      </div>
    </nav>
  );
}
