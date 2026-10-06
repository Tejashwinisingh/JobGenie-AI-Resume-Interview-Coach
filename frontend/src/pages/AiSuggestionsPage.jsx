/**
 * src/pages/AiSuggestionsPage.jsx
 * Module 7 — AI Resume Improvement Suggestions dedicated page.
 */
import { useState, useEffect } from 'react';
import { Sidebar } from '../components/layout/Sidebar';
import { resumeApi } from '../api/resumeApi';

export function AiSuggestionsPage() {
  const [resumes, setResumes] = useState([]);
  const [selectedId, setSelectedId] = useState('');
  const [loadingResumes, setLoadingResumes] = useState(true);
  const [aiData, setAiData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    resumeApi.list().then(({ data }) => {
      setResumes(data);
      if (data.length > 0) setSelectedId(String(data[0].id));
    }).catch(() => {}).finally(() => setLoadingResumes(false));
  }, []);

  const fetchSuggestions = async (id) => {
    if (!id) return;
    setLoading(true);
    setError('');
    setAiData(null);
    try {
      const { data } = await resumeApi.getAiSuggestions(id);
      setAiData(data);
    } catch {
      setError('No AI report yet. Click "Generate AI Suggestions" below.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedId) fetchSuggestions(selectedId);
  }, [selectedId]);

  const handleGenerate = async () => {
    if (!selectedId) return;
    setGenerating(true);
    setError('');
    try {
      const { data } = await resumeApi.generateAiSuggestions(selectedId);
      setAiData(data);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to generate suggestions. Make sure resume is processed first.');
    } finally {
      setGenerating(false);
    }
  };

  const handleCopy = () => {
    if (aiData?.improved_project_description) {
      navigator.clipboard.writeText(aiData.improved_project_description);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="module-main">
        {/* Header */}
        <div className="module-header">
          <div className="module-header-left">
            <div className="module-icon" style={{ background: 'linear-gradient(135deg, #10b981, #06d6a0)' }}>🤖</div>
            <div>
              <h1 className="module-title">AI Resume Suggestions</h1>
              <p className="module-subtitle">Personalised AI-Powered Resume Analysis & Rewriting Engine</p>
            </div>
          </div>
          <div className="module-badge" style={{ background: '#10b981' }}>Smart Feedback</div>
        </div>

        {/* Resume Selector */}
        <div className="selector-bar">
          <label className="selector-label">📄 Analyze Resume:</label>
          {loadingResumes ? (
            <span className="text-muted">Loading resumes…</span>
          ) : resumes.length === 0 ? (
            <span className="alert-inline alert-inline--warn">⚠ Upload a resume first from <strong>My Resumes</strong>.</span>
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
            className="btn-generate btn-green"
            onClick={handleGenerate}
            disabled={!selectedId || generating}
          >
            {generating ? <><span className="spinner-sm" /> Generating…</> : '🤖 Generate AI Suggestions'}
          </button>
        </div>

        {error && <div className="alert alert-warn">{error}</div>}

        {loading ? (
          <div className="module-loading">
            <div className="spinner" style={{ borderTopColor: '#10b981' }} />
            <span>Loading AI suggestions…</span>
          </div>
        ) : aiData ? (
          <div className="ai-page-grid">
            {/* Executive Summary */}
            <div className="ai-summary-card">
              <div className="ai-summary-icon">💡</div>
              <div>
                <h3 className="card-section-title" style={{ color: '#10b981', marginBottom: '0.4rem' }}>AI Executive Assessment</h3>
                <p className="ai-summary-text">{aiData.summary}</p>
              </div>
            </div>

            {/* Strengths */}
            <div className="detail-card strengths-card">
              <h3 className="card-section-title" style={{ color: '#10b981' }}>✅ Strengths</h3>
              <ul className="ai-list">
                {aiData.strengths?.map((s, i) => (
                  <li key={i} className="ai-list-item ai-list-item--green">
                    <span className="ai-list-dot" style={{ background: '#10b981' }} />
                    {s}
                  </li>
                ))}
              </ul>
            </div>

            {/* Weaknesses */}
            <div className="detail-card weaknesses-card">
              <h3 className="card-section-title" style={{ color: '#f87171' }}>⚠️ Areas to Improve</h3>
              <ul className="ai-list">
                {aiData.weaknesses?.map((w, i) => (
                  <li key={i} className="ai-list-item ai-list-item--red">
                    <span className="ai-list-dot" style={{ background: '#f87171' }} />
                    {w}
                  </li>
                ))}
              </ul>
            </div>

            {/* Suggestions */}
            <div className="detail-card" style={{ gridColumn: '1 / -1' }}>
              <h3 className="card-section-title">📋 Actionable Suggestions</h3>
              <div className="suggestions-grid">
                {aiData.suggestions?.map((s, i) => (
                  <div key={i} className="suggestion-card">
                    <div className="suggestion-number">{i + 1}</div>
                    <p className="suggestion-text">{s}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Priority Skills */}
            <div className="detail-card">
              <h3 className="card-section-title">🎯 Priority Skills to Learn / Highlight</h3>
              <div className="pill-grid" style={{ marginTop: '0.8rem' }}>
                {aiData.priority_skills?.map((sk, i) => (
                  <span key={i} className="pill pill--purple">{sk}</span>
                ))}
              </div>
            </div>

            {/* Rewritten Project Description */}
            {aiData.improved_project_description && (
              <div className="detail-card star-card">
                <div className="star-card-header">
                  <h3 className="card-section-title" style={{ color: '#a78bfa' }}>✨ Rewritten STAR-Method Project Description</h3>
                  <button className="btn-copy" onClick={handleCopy}>
                    {copied ? '✓ Copied!' : '📋 Copy Text'}
                  </button>
                </div>
                <pre className="star-text">{aiData.improved_project_description}</pre>
              </div>
            )}
          </div>
        ) : !loading && !error && selectedId ? (
          <div className="empty-module-state">
            <div className="empty-module-icon">🤖</div>
            <h3>No AI Report Yet</h3>
            <p>Click <strong>"Generate AI Suggestions"</strong> above to get personalised resume feedback.</p>
          </div>
        ) : null}
      </main>
    </div>
  );
}
