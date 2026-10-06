/**
 * src/components/layout/Header.jsx
 * Top navigation header bar for ResumeIQ AI SaaS Platform.
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

export function Header({ searchVal, setSearchVal }) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [showNotifications, setShowNotifications] = useState(false);
  const [unreadCount, setUnreadCount] = useState(3);

  const notifications = [
    { id: 1, title: '✨ AI Resume Report Ready', desc: 'Your ATS score improved by +9%', time: '2m ago', icon: '🤖' },
    { id: 2, title: '🎯 New Skill Gap Identified', desc: 'Docker & AWS recommended for Senior roles', time: '1h ago', icon: '💡' },
    { id: 3, title: '🎤 Interview Performance Stored', desc: '84% score recorded in Voice Simulator', time: '3h ago', icon: '🎧' },
  ];

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (!searchVal) return;
    const query = searchVal.toLowerCase();
    if (query.includes('ats') || query.includes('score')) navigate('/ats-score');
    else if (query.includes('job') || query.includes('match') || query.includes('jd')) navigate('/job-match');
    else if (query.includes('suggest') || query.includes('ai')) navigate('/ai-suggestions');
    else if (query.includes('prep') || query.includes('question')) navigate('/interview');
    else if (query.includes('mock') || query.includes('voice')) navigate('/mock-interview');
    else navigate('/resumes');
  };

  const initials = user?.full_name
    ? user.full_name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2)
    : user?.email?.[0]?.toUpperCase() ?? 'IQ';

  return (
    <header className="top-header">
      {/* Global Search Bar */}
      <form onSubmit={handleSearchSubmit} className="header-search-form">
        <div className="header-search-wrapper">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            className="header-search-input"
            placeholder="Search AI features, resumes, interview prep... (Ctrl + K)"
            value={searchVal || ''}
            onChange={(e) => setSearchVal && setSearchVal(e.target.value)}
          />
          <kbd className="search-kbd">⌘K</kbd>
        </div>
      </form>

      {/* Header Right Actions */}
      <div className="header-actions">
        {/* AI Status Badge */}
        <div className="header-ai-badge">
          <span className="ai-pulse-dot" />
          <span className="ai-badge-text">🤖 AI Coach Active</span>
        </div>

        {/* Theme Indicator */}
        <button className="header-action-btn" title="Dark Mode Active" aria-label="Theme toggle">
          🌙
        </button>

        {/* Notifications Popover Toggle */}
        <div className="notifications-wrapper">
          <button
            className="header-action-btn notification-btn"
            onClick={() => setShowNotifications(!showNotifications)}
            title="Notifications"
            aria-label="Notifications"
          >
            🔔
            {unreadCount > 0 && <span className="notification-badge">{unreadCount}</span>}
          </button>

          {showNotifications && (
            <div className="notifications-dropdown">
              <div className="notifications-header">
                <h4>Notifications</h4>
                <button
                  className="btn-text-sm"
                  onClick={() => setUnreadCount(0)}
                >
                  Mark all as read
                </button>
              </div>
              <div className="notifications-list">
                {notifications.map((n) => (
                  <div key={n.id} className="notification-item">
                    <span className="notification-item-icon">{n.icon}</span>
                    <div className="notification-item-content">
                      <div className="notification-item-title">{n.title}</div>
                      <div className="notification-item-desc">{n.desc}</div>
                      <div className="notification-item-time">{n.time}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* User Profile */}
        <div className="header-user-profile" onClick={() => navigate('/resumes')}>
          <div className="header-avatar">{initials}</div>
          <div className="header-user-details">
            <span className="header-user-name">{user?.full_name || 'Alex Morgan'}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
