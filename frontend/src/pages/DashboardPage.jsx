import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Sidebar } from '../components/layout/Sidebar';
import { Header } from '../components/layout/Header';
import { useAuth } from '../hooks/useAuth';

const MODULES = [
  {
    icon: '📄',
    gradient: 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
    title: 'My Resumes',
    desc: 'Upload, manage, and process your PDF or DOCX resumes. Text extraction and structured parsing included.',
    badge: 'Upload & Manage',
    status: 'Ready',
    statusClass: 'status-badge--success',
    lastUsed: '10 mins ago',
    ctaText: 'Upload & Manage',
    link: '/resumes',
  },
  {
    icon: '🎯',
    gradient: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
    title: 'ATS Quality Score',
    desc: 'Check how ATS-friendly your resume is. Score across formatting, structure, keywords, skills, and more.',
    badge: 'ATS Optimizer',
    status: 'Completed',
    statusClass: 'status-badge--success',
    lastUsed: '2 mins ago',
    ctaText: 'Analyze Resume',
    link: '/ats-score',
  },
  {
    icon: '💼',
    gradient: 'linear-gradient(135deg, #0ea5e9, #06b6d4)',
    title: 'Job Description Matcher',
    desc: 'Paste any job description and get an instant compatibility score — matched skills, gaps, and recommendations.',
    badge: 'JD Analyzer',
    status: 'Ready',
    statusClass: 'status-badge--info',
    lastUsed: '1 hour ago',
    ctaText: 'Match Job',
    link: '/job-match',
  },
  {
    icon: '🤖',
    gradient: 'linear-gradient(135deg, #10b981, #06d6a0)',
    title: 'AI Resume Suggestions',
    desc: 'Get OpenAI-powered personalised suggestions — strengths, improvements, priority skills, and STAR rewrites.',
    badge: 'Smart Feedback',
    status: 'Completed',
    statusClass: 'status-badge--success',
    lastUsed: '5 mins ago',
    ctaText: 'Get AI Suggestions',
    link: '/ai-suggestions',
  },
  {
    icon: '🎤',
    gradient: 'linear-gradient(135deg, #f59e0b, #ef4444)',
    title: 'Interview Prep',
    desc: 'Generate personalized interview questions (HR, Technical, Project, Coding, Behavioral) from your resume.',
    badge: 'Question Generator',
    status: 'In Progress',
    statusClass: 'status-badge--warning',
    lastUsed: 'Yesterday',
    ctaText: 'Prep Questions',
    link: '/interview',
  },
  {
    icon: '🎧',
    gradient: 'linear-gradient(135deg, #ec4899, #8b5cf6)',
    title: 'AI Mock Interview',
    desc: 'Conduct a live, interactive mock interview session. Questions are asked one by one and responses stored.',
    badge: 'Live Simulator',
    status: 'Ready',
    statusClass: 'status-badge--purple',
    lastUsed: '15 mins ago',
    ctaText: 'Start Simulator',
    link: '/mock-interview',
  },
];

const QUICK_ACTIONS = [
  { icon: '📤', label: 'Upload Resume', link: '/resumes', color: 'btn-qa--blue' },
  { icon: '🎯', label: 'Analyze ATS', link: '/ats-score', color: 'btn-qa--indigo' },
  { icon: '🎤', label: 'Generate Questions', link: '/interview', color: 'btn-qa--amber' },
  { icon: '🎧', label: 'Start Interview', link: '/mock-interview', color: 'btn-qa--pink' },
  { icon: '🤖', label: 'View Report', link: '/ai-suggestions', color: 'btn-qa--emerald' },
];

const RECENT_ACTIVITIES = [
  { id: 1, action: 'Uploaded Resume', file: 'alex_morgan_resume.pdf', time: '10 minutes ago', icon: '📄', color: '#3b82f6' },
  { id: 2, action: 'Generated ATS Report', detail: 'Grade A · 88/100', time: '9 minutes ago', icon: '🎯', color: '#6366f1' },
  { id: 3, action: 'Started Practice Session', detail: 'Backend Engineer', time: '5 minutes ago', icon: '🎤', color: '#f59e0b' },
  { id: 4, action: 'Interview Completed', detail: 'Score 84/100 · Very Good', time: '2 minutes ago', icon: '🎧', color: '#ec4899' },
];

export function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchVal, setSearchVal] = useState('');

  const firstName = user?.full_name ? user.full_name.split(' ')[0] : 'Alex';

  return (
    <div className="app-layout app-layout--has-header">
      <Sidebar />
      <div className="main-content-wrapper">
        <Header searchVal={searchVal} setSearchVal={setSearchVal} />

        <main className="module-main dashboard-content-body">
          {/* HERO SECTION */}
          <div className="dashboard-hero-v2">
            <div className="hero-text-area">
              <div className="hero-welcome-tag">
                <span className="hero-ai-sparkle">✨</span>
                <span>AI Career Operating System</span>
              </div>
              <h1 className="hero-title">
                Welcome back, <span className="gradient-text">{firstName}</span> 👋
              </h1>
              <p className="hero-subtitle">
                Your AI Career Assistant is ready. Continue improving your resume and interview performance.
              </p>
            </div>

            {/* 4 ANIMATED STAT CARDS */}
            <div className="hero-stats-grid">
              <div className="stat-card-v2 glass-card">
                <div className="stat-v2-header">
                  <span className="stat-v2-title">ATS Score</span>
                  <span className="stat-v2-icon" style={{ background: 'rgba(99, 102, 241, 0.15)', color: '#818cf8' }}>🎯</span>
                </div>
                <div className="stat-v2-main">
                  <span className="stat-v2-value text-indigo">88%</span>
                  <span className="stat-v2-badge badge-success">Excellent</span>
                </div>
                <div className="stat-v2-bar"><div className="stat-v2-progress" style={{ width: '88%', background: '#6366f1' }} /></div>
              </div>

              <div className="stat-card-v2 glass-card">
                <div className="stat-v2-header">
                  <span className="stat-v2-title">Job Match</span>
                  <span className="stat-v2-icon" style={{ background: 'rgba(14, 165, 233, 0.15)', color: '#38bdf8' }}>💼</span>
                </div>
                <div className="stat-v2-main">
                  <span className="stat-v2-value text-sky">76%</span>
                  <span className="stat-v2-badge badge-sky">Strong Match</span>
                </div>
                <div className="stat-v2-bar"><div className="stat-v2-progress" style={{ width: '76%', background: '#0ea5e9' }} /></div>
              </div>

              <div className="stat-card-v2 glass-card">
                <div className="stat-v2-header">
                  <span className="stat-v2-title">Interview Score</span>
                  <span className="stat-v2-icon" style={{ background: 'rgba(236, 72, 153, 0.15)', color: '#f472b6' }}>🎧</span>
                </div>
                <div className="stat-v2-main">
                  <span className="stat-v2-value text-pink">84%</span>
                  <span className="stat-v2-badge badge-pink">Very Good</span>
                </div>
                <div className="stat-v2-bar"><div className="stat-v2-progress" style={{ width: '84%', background: '#ec4899' }} /></div>
              </div>

              <div className="stat-card-v2 glass-card">
                <div className="stat-v2-header">
                  <span className="stat-v2-title">Total Resumes</span>
                  <span className="stat-v2-icon" style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa' }}>📄</span>
                </div>
                <div className="stat-v2-main">
                  <span className="stat-v2-value text-blue">5</span>
                  <span className="stat-v2-badge badge-blue">Uploaded</span>
                </div>
                <div className="stat-v2-bar"><div className="stat-v2-progress" style={{ width: '100%', background: '#3b82f6' }} /></div>
              </div>
            </div>
          </div>

          {/* QUICK ACTION BAR */}
          <div className="quick-actions-bar glass-panel">
            <div className="qa-header-label">
              <span>⚡ QUICK ACTIONS</span>
            </div>
            <div className="qa-buttons-list">
              {QUICK_ACTIONS.map((qa) => (
                <button
                  key={qa.label}
                  className={`qa-btn ${qa.color}`}
                  onClick={() => navigate(qa.link)}
                >
                  <span className="qa-btn-icon">{qa.icon}</span>
                  <span>{qa.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* 2-COLUMN FEATURE CARDS GRID */}
          <div className="dashboard-section-header">
            <h3>🤖 AI Career Tools</h3>
            <span className="section-subtitle">Click any module to launch AI features</span>
          </div>

          <div className="dashboard-modules-grid">
            {MODULES.map((m) => (
              <div key={m.title} className="dash-module-card glass-card-hover" onClick={() => navigate(m.link)}>
                <div className="dash-card-top">
                  <div className="dash-module-icon" style={{ background: m.gradient }}>
                    {m.icon}
                  </div>
                  <div className="dash-card-meta">
                    <span className={`status-badge ${m.statusClass}`}>● {m.status}</span>
                    <span className="last-used-tag">⏱ {m.lastUsed}</span>
                  </div>
                </div>

                <div className="dash-module-content">
                  <div className="dash-module-badge">{m.badge}</div>
                  <h3 className="dash-module-title">{m.title}</h3>
                  <p className="dash-module-desc">{m.desc}</p>
                </div>

                <div className="dash-card-footer">
                  <button className="dash-card-cta-btn">
                    <span>{m.ctaText}</span>
                    <span className="cta-arrow">→</span>
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* AI INSIGHTS & ACTIVITY GRID */}
          <div className="dashboard-split-grid">
            {/* ChatGPT-Style AI Insights Card */}
            <div className="ai-insights-card glass-card">
              <div className="ai-insights-header">
                <div className="ai-insights-title">
                  <span className="ai-insights-sparkle">✨</span>
                  <h3>AI Insights &amp; Recommendation</h3>
                </div>
                <span className="badge-ai-model">GPT-4o Engine</span>
              </div>

              <div className="ai-insights-content">
                <div className="ai-callout-box">
                  <span className="callout-icon">📈</span>
                  <div className="callout-text">
                    <strong>ATS Score Increased by +9%!</strong>
                    <p>Your latest resume draft matches 88% of technical requirements for Senior Engineer roles.</p>
                  </div>
                </div>

                <div className="skill-gaps-section">
                  <div className="skill-gaps-title">⚡ Missing Priority Skills Identified:</div>
                  <div className="skill-gaps-tags">
                    <span className="skill-gap-pill">Docker</span>
                    <span className="skill-gap-pill">AWS</span>
                    <span className="skill-gap-pill">Redis</span>
                  </div>
                </div>

                <div className="ai-recommendation-box">
                  <div className="recommendation-header">
                    <span>🤖 AI Recommendation</span>
                  </div>
                  <p>Practice answering System Design &amp; Microservices architecture questions to boost your interview score.</p>
                  <button className="btn-ai-action" onClick={() => navigate('/mock-interview')}>
                    <span>🎤 Start Mock Interview</span>
                    <span>→</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Recent Activity Timeline & Progress Analytics */}
            <div className="analytics-activity-column">
              {/* Activity Timeline */}
              <div className="activity-card glass-card">
                <div className="card-header-flex">
                  <h3>🕒 Recent Activity</h3>
                  <span className="text-muted-xs">Live Feed</span>
                </div>
                <div className="activity-timeline">
                  {RECENT_ACTIVITIES.map((act) => (
                    <div key={act.id} className="timeline-row">
                      <div className="timeline-icon-dot" style={{ background: act.color }}>
                        {act.icon}
                      </div>
                      <div className="timeline-details">
                        <div className="timeline-title-text">{act.action}</div>
                        {act.file && <div className="timeline-sub-text">{act.file}</div>}
                        {act.detail && <div className="timeline-sub-text">{act.detail}</div>}
                      </div>
                      <span className="timeline-time">{act.time}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Progress Analytics */}
              <div className="progress-analytics-card glass-card">
                <div className="card-header-flex">
                  <h3>📊 Performance Analytics</h3>
                  <span className="badge-ai-sm">Live Trends</span>
                </div>
                <div className="analytics-meters">
                  <div className="meter-group">
                    <div className="meter-header">
                      <span>ATS Compatibility</span>
                      <span className="meter-val text-indigo">88%</span>
                    </div>
                    <div className="meter-track"><div className="meter-fill" style={{ width: '88%', background: 'linear-gradient(90deg, #6366f1, #8b5cf6)' }} /></div>
                  </div>

                  <div className="meter-group">
                    <div className="meter-header">
                      <span>Job Match Score</span>
                      <span className="meter-val text-sky">76%</span>
                    </div>
                    <div className="meter-track"><div className="meter-fill" style={{ width: '76%', background: 'linear-gradient(90deg, #0ea5e9, #06b6d4)' }} /></div>
                  </div>

                  <div className="meter-group">
                    <div className="meter-header">
                      <span>Interview Confidence</span>
                      <span className="meter-val text-pink">84%</span>
                    </div>
                    <div className="meter-track"><div className="meter-fill" style={{ width: '84%', background: 'linear-gradient(90deg, #ec4899, #f43f5e)' }} /></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

