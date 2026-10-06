/**
 * src/pages/AtsScorePage.jsx
 * Module 5 — ATS Quality Score dedicated page.
 */
import { useState, useEffect, useCallback } from 'react';
import { Sidebar } from '../components/layout/Sidebar';
import { resumeApi } from '../api/resumeApi';

function ScoreRing({ score }) {
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  const getColor = (s) => {
    if (s >= 85) return '#10b981';
    if (s >= 70) return '#6366f1';
    if (s >= 55) return '#f59e0b';
    return '#ef4444';
  };
  const color = getColor(score);

  return (
    <div className="score-ring-wrapper">
      <svg width="140" height="140" viewBox="0 0 140 140">
        <circle cx="70" cy="70" r={radius} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="12" />
        <circle
          cx="70" cy="70" r={radius}
          fill="none"
          stroke={color}
          strokeWidth="12"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 70 70)"
          style={{ transition: 'stroke-dashoffset 1s ease' }}
        />
      </svg>
      <div className="score-ring-inner">
        <span className="score-ring-number" style={{ color }}>{score}</span>
        <span className="score-ring-label">/ 100</span>
      </div>
    </div>
  );
}

const CATEGORY_CONFIG = {
  formatting:  { icon: '🖊', label: 'Formatting',   max: 15, color: '#6366f1' },
  contact:     { icon: '📞', label: 'Contact Info',  max: 10, color: '#0ea5e9' },
  structure:   { icon: '🏗', label: 'Structure',     max: 10, color: '#8b5cf6' },
  keywords:    { icon: '🔑', label: 'Keywords',      max: 25, color: '#f59e0b' },
  skills:      { icon: '🛠', label: 'Skills',        max: 15, color: '#10b981' },
  education:   { icon: '🎓', label: 'Education',     max: 10, color: '#06b6d4' },
  experience:  { icon: '💼', label: 'Experience',    max: 10, color: '#a78bfa' },
  projects:    { icon: '🚀', label: 'Projects',      max: 5,  color: '#f472b6' },
};

export function AtsScorePage() {
  const [resumes, setResumes] = useState([]);
  const [selectedId, setSelectedId] = useState('');
  const [atsData, setAtsData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');
  const [loadingResumes, setLoadingResumes] = useState(true);

  // Fetch resumes for selector
  useEffect(() => {
    resumeApi.list().then(({ data }) => {
      setResumes(data);
      if (data.length > 0) setSelectedId(String(data[0].id));
    }).catch(() => {}).finally(() => setLoadingResumes(false));
  }, []);

  // Auto-fetch ATS score when resume changes
  const fetchAts = useCallback(async (id) => {
    if (!id) return;
    setLoading(true);
    setError('');
    setAtsData(null);
    try {
      const { data } = await resumeApi.getAtsScore(id);
      setAtsData(data);
    } catch {
      setError('No ATS report yet. Click "Generate ATS Report" below.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedId) fetchAts(selectedId);
  }, [selectedId, fetchAts]);

  const handleGenerate = async () => {
    if (!selectedId) return;
    setGenerating(true);
    setError('');
    try {
      const { data } = await resumeApi.generateAtsScore(selectedId);
      setAtsData(data);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to generate ATS report. Make sure the resume text is extracted first.');
    } finally {
      setGenerating(false);
    }
  };

  const score = atsData?.ats_score ?? 0;
  const grade = atsData?.grade ?? 'N/A';
  const breakdown = atsData?.breakdown ?? {};
  const analysis = atsData?.analysis ?? {};

  const getGradeColor = (g) => {
    if (g === 'A+' || g === 'A') return '#10b981';
    if (g === 'B') return '#6366f1';
    if (g === 'C') return '#f59e0b';
    return '#ef4444';
  };

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="module-main">
        {/* Page Header */}
        <div className="module-header">
          <div className="module-header-left">
            <div className="module-icon" style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}>🎯</div>
            <div>
              <h1 className="module-title">ATS Quality Score</h1>
              <p className="module-subtitle">Applicant Tracking System Compatibility Analysis</p>
            </div>
          </div>
          <div className="module-badge" style={{ background: '#6366f1' }}>Quality Check</div>
        </div>

        {/* Resume Selector */}
        <div className="selector-bar">
          <label className="selector-label">📄 Analyze Resume:</label>
          {loadingResumes ? (
            <span className="text-muted">Loading resumes…</span>
          ) : resumes.length === 0 ? (
            <span className="alert-inline alert-inline--warn">⚠ No resumes found. Upload a resume first from <strong>My Resumes</strong>.</span>
          ) : (
            <select
              className="resume-selector"
              value={selectedId}
              onChange={(e) => setSelectedId(e.target.value)}
            >
              {resumes.map((r) => (
                <option key={r.id} value={r.id}>{r.original_filename}</option>
              ))}
            </select>
          )}
          <button
            className="btn-generate"
            onClick={handleGenerate}
            disabled={!selectedId || generating}
          >
            {generating ? <><span className="spinner-sm" /> Analyzing…</> : '⚡ Generate ATS Report'}
          </button>
        </div>

        {error && <div className="alert alert-warn">{error}</div>}

        {loading ? (
          <div className="module-loading">
            <div className="spinner" />
            <span>Loading ATS report…</span>
          </div>
        ) : atsData ? (
          <div className="ats-page-grid">
            {/* Score Card */}
            <div className="ats-score-card">
              <ScoreRing score={score} />
              <div className="ats-score-meta">
                <div className="ats-grade-pill" style={{ background: getGradeColor(grade) }}>
                  Grade {grade}
                </div>
                <div className="ats-grade-label">{atsData.grade_label}</div>
                <p className="ats-summary-text">{atsData.summary}</p>
              </div>
            </div>

            {/* Breakdown Grid */}
            <div className="breakdown-card">
              <h3 className="card-section-title">📊 Score Breakdown</h3>
              <div className="breakdown-list">
                {Object.entries(CATEGORY_CONFIG).map(([key, cfg]) => {
                  const val = breakdown[key] ?? 0;
                  const pct = Math.round((val / cfg.max) * 100);
                  return (
                    <div key={key} className="breakdown-row">
                      <div className="breakdown-row-header">
                        <span className="breakdown-cat-icon">{cfg.icon}</span>
                        <span className="breakdown-cat-name">{cfg.label}</span>
                        <span className="breakdown-cat-score" style={{ color: cfg.color }}>{val}/{cfg.max}</span>
                      </div>
                      <div className="breakdown-bar-bg">
                        <div
                          className="breakdown-bar-fill"
                          style={{ width: `${pct}%`, background: cfg.color }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Keywords Card */}
            <div className="detail-card">
              <h3 className="card-section-title">🔑 Keywords Detected ({analysis.keyword_count ?? 0})</h3>
              {analysis.technical_keywords_found?.length > 0 ? (
                <div className="pill-grid">
                  {analysis.technical_keywords_found.map((kw, i) => (
                    <span key={i} className="pill pill--green">{kw}</span>
                  ))}
                </div>
              ) : (
                <p className="text-muted">No technical keywords detected in this resume.</p>
              )}
            </div>

            {/* Warnings Card */}
            <div className="detail-card">
              <h3 className="card-section-title" style={{ color: '#f87171' }}>⚠️ Actionable Warnings</h3>
              {analysis.warnings?.length > 0 ? (
                <ul className="warning-list">
                  {analysis.warnings.map((w, i) => (
                    <li key={i} className="warning-item">
                      <span className="warning-dot" />
                      {w}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-muted">✅ No critical issues found!</p>
              )}
            </div>
          </div>
        ) : !loading && !error && selectedId ? (
          <div className="empty-module-state">
            <div className="empty-module-icon">🎯</div>
            <h3>No ATS Report Yet</h3>
            <p>Click <strong>"Generate ATS Report"</strong> above to analyze your resume.</p>
          </div>
        ) : null}
      </main>
    </div>
  );
}
