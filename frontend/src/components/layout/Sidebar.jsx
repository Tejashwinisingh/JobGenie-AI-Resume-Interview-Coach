/**
 * src/components/layout/Sidebar.jsx
 * Shared sidebar navigation for all module pages.
 */
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { useState } from 'react';

const NAV_ITEMS = [
  {
    path: '/dashboard',
    icon: '🏠',
    label: 'Dashboard',
    desc: 'Overview',
  },
  {
    path: '/resumes',
    icon: '📄',
    label: 'My Resumes',
    desc: 'Upload & Manage',
  },
  {
    path: '/ats-score',
    icon: '🎯',
    label: 'ATS Quality Score',
    desc: 'ATS Optimizer',
  },
  {
    path: '/job-match',
    icon: '💼',
    label: 'Job Description Matcher',
    desc: 'JD Analyzer',
  },
  {
    path: '/ai-suggestions',
    icon: '🤖',
    label: 'AI Resume Suggestions',
    desc: 'Smart Feedback',
  },
  {
    path: '/interview',
    icon: '🎤',
    label: 'Interview Prep',
    desc: 'Question Generator',
  },
  {
    path: '/mock-interview',
    icon: '🎧',
    label: 'AI Mock Interview',
    desc: 'Live Simulator',
  },
];

export function Sidebar() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [loggingOut, setLoggingOut] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);

  const initials = user?.full_name
    ? user.full_name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2)
    : user?.email?.[0]?.toUpperCase() ?? '?';

  const handleLogout = async () => {
    setLoggingOut(true);
    await logout();
  };

  return (
    <aside className={`sidebar${isCollapsed ? ' sidebar--collapsed' : ''}`}>
      {/* Brand */}
      <div className="sidebar-brand">
        <div className="sidebar-brand-left">
          <div className="sidebar-brand-logo">🎯</div>
          {!isCollapsed && (
            <div>
              <div className="sidebar-brand-name">ResumeIQ</div>
              <div className="sidebar-brand-sub">AI CAREER SUITE</div>
            </div>
          )}
        </div>
        <button
          className="sidebar-collapse-btn"
          onClick={() => setIsCollapsed(!isCollapsed)}
          title={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
        >
          {isCollapsed ? '❯' : '❮'}
        </button>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        {!isCollapsed && <div className="sidebar-nav-label">CAREER SUITE</div>}
        {NAV_ITEMS.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`sidebar-nav-item${isActive ? ' active' : ''}`}
              title={isCollapsed ? item.label : undefined}
            >
              <span className="sidebar-nav-icon">{item.icon}</span>
              {!isCollapsed && (
                <div className="sidebar-nav-text">
                  <span className="sidebar-nav-label-text">{item.label}</span>
                  <span className="sidebar-nav-desc">{item.desc}</span>
                </div>
              )}
              {isActive && <div className="active-indicator-glow" />}
            </Link>
          );
        })}
      </nav>

      {/* User Footer */}
      <div className="sidebar-footer">
        <div className="sidebar-user">
          <div className="sidebar-avatar">{initials}</div>
          {!isCollapsed && (
            <div className="sidebar-user-info">
              <div className="sidebar-user-name">{user?.full_name || 'User'}</div>
              <div className="sidebar-user-email">{user?.email}</div>
            </div>
          )}
        </div>
        <button
          className="sidebar-logout-btn"
          onClick={handleLogout}
          disabled={loggingOut}
          title="Sign Out"
        >
          {isCollapsed ? '↩' : loggingOut ? '...' : '↩ Sign Out'}
        </button>
      </div>
    </aside>
  );
}
