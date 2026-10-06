/**
 * src/pages/JobMatchPage.jsx
 * Module 6 — Job Description Matching dedicated page.
 */
import { useState, useEffect } from 'react';
import { Sidebar } from '../components/layout/Sidebar';
import { resumeApi } from '../api/resumeApi';

function MatchScoreCircle({ score }) {
  const getColor = (s) => {
    if (s >= 80) return '#10b981';
    if (s >= 60) return '#6366f1';
    if (s >= 40) return '#f59e0b';
    return '#ef4444';
  };
  const color = getColor(score);
  const radius = 54;
  const circ = 2 * Math.PI * radius;
  const offset = circ - (score / 100) * circ;

  return (
    <div className="score-ring-wrapper">
      <svg width="140" height="140" viewBox="0 0 140 140">
        <circle cx="70" cy="70" r={radius} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="12" />
        <circle
          cx="70" cy="70" r={radius}
          fill="none" stroke={color} strokeWidth="12"
          strokeDasharray={circ} strokeDashoffset={offset}
          strokeLinecap="round" transform="rotate(-90 70 70)"
          style={{ transition: 'stroke-dashoffset 1s ease' }}
        />
      </svg>
      <div className="score-ring-inner">
        <span className="score-ring-number" style={{ color }}>{score}</span>
        <span className="score-ring-label">%</span>
      </div>
    </div>
  );
}

export function JobMatchPage() {
  const [resumes, setResumes] = useState([]);
  const [selectedId, setSelectedId] = useState('');
  const [loadingResumes, setLoadingResumes] = useState(true);
  const [jdTitle, setJdTitle] = useState('');
  const [jdCompany, setJdCompany] = useState('');
  const [jdText, setJdText] = useState('');
  const [matchData, setMatchData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    resumeApi.list().then(({ data }) => {
      setResumes(data);
      if (data.length > 0) setSelectedId(String(data[0].id));
    }).catch(() => {}).finally(() => setLoadingResumes(false));
  }, []);

  const handleMatch = async (e) => {
    e.preventDefault();
    if (!selectedId || !jdText.trim()) return;
    setLoading(true);
    setError('');
    setMatchData(null);
    try {
      const { data: jdData } = await resumeApi.createJd({
        title: jdTitle || 'Job Role',
        company: jdCompany || '',
        description: jdText,
      });
      const jdId = jdData.data.id;
      const { data: mData } = await resumeApi.matchJd(jdId, selectedId);
      setMatchData(mData);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to match resume. Make sure the resume is processed first.');
    } finally {
      setLoading(false);
    }
  };

  const getGradeColor = (g) => {
    if (!g) return '#6366f1';
    const gl = g.toLowerCase();
    if (gl.includes('excellent')) return '#10b981';
    if (gl.includes('good') || gl.includes('strong')) return '#6366f1';
    if (gl.includes('moderate') || gl.includes('partial')) return '#f59e0b';
    return '#ef4444';
  };

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="module-main">
        {/* Header */}
        <div className="module-header">
          <div className="module-header-left">
            <div className="module-icon" style={{ background: 'linear-gradient(135deg, #0ea5e9, #06b6d4)' }}>💼</div>
            <div>
              <h1 className="module-title">Job Description Matcher</h1>
              <p className="module-subtitle">Resume vs. Job Description Compatibility Engine</p>
            </div>
          </div>
          <div className="module-badge" style={{ background: '#0ea5e9' }}>JD Analyzer</div>
        </div>

        <div className="jd-page-grid">
          {/* Input Panel */}
          <div className="jd-input-panel">
            <h3 className="panel-title">📝 Job Description Input</h3>
            <form onSubmit={handleMatch} className="jd-form-fields">
              {/* Resume selector */}
              <div className="form-group">
                <label className="form-label">Select Resume</label>
                {loadingResumes ? (
                  <span className="text-muted">Loading…</span>
                ) : resumes.length === 0 ? (
                  <span className="alert-inline alert-inline--warn">No resumes found.</span>
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
              </div>

              <div className="form-row-2">
                <div className="form-group">
                  <label className="form-label">Job Title</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. Senior Backend Developer"
                    value={jdTitle}
                    onChange={(e) => setJdTitle(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Company Name</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. Google (optional)"
                    value={jdCompany}
                    onChange={(e) => setJdCompany(e.target.value)}
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Job Description *</label>
                <textarea
                  className="form-textarea"
                  rows={10}
                  placeholder="Paste the full job description here — skills, requirements, experience, degree, certifications…"
                  value={jdText}
                  onChange={(e) => setJdText(e.target.value)}
                  required
                />
              </div>

              {error && <div className="alert alert-error">{error}</div>}

              <button type="submit" className="btn-generate btn-full" disabled={loading || !jdText.trim()}>
                {loading ? <><span className="spinner-sm" /> Calculating Match…</> : '🔍 Analyze Job Match'}
              </button>
            </form>
          </div>

          {/* Results Panel */}
          <div className="jd-result-panel">
            {!matchData && !loading ? (
              <div className="empty-module-state">
                <div className="empty-module-icon">💼</div>
                <h3>Results appear here</h3>
                <p>Paste a job description and click <strong>Analyze Job Match</strong> to see how well your resume fits.</p>
              </div>
            ) : loading ? (
              <div className="module-loading">
                <div className="spinner" />
                <span>Calculating compatibility…</span>
              </div>
            ) : matchData && (
              <div className="match-results-grid">
                {/* Score */}
                <div className="match-score-card">
                  <MatchScoreCircle score={matchData.match_score ?? 0} />
                  <div className="ats-score-meta">
                    <div className="ats-grade-pill" style={{ background: getGradeColor(matchData.grade) }}>
                      {matchData.grade}
                    </div>
                    <p className="text-secondary" style={{ fontSize: '0.875rem', marginTop: '0.4rem' }}>
                      Overall compatibility with this job posting
                    </p>
                  </div>
                </div>

                {/* Breakdown */}
                <div className="breakdown-card">
                  <h3 className="card-section-title">📊 Match Breakdown</h3>
                  <div className="breakdown-list">
                    {[
                      { label: 'Skills Match', val: matchData.breakdown?.skills ?? 0, max: 50, color: '#6366f1' },
                      { label: 'Experience', val: matchData.experience_match ?? 0, max: 20, color: '#0ea5e9' },
                      { label: 'Education', val: matchData.education_match ?? 0, max: 15, color: '#10b981' },
                      { label: 'Keywords', val: matchData.breakdown?.keywords ?? 0, max: 10, color: '#f59e0b' },
                      { label: 'Certifications', val: matchData.certification_match ?? 0, max: 5, color: '#a78bfa' },
                    ].map((row) => (
                      <div key={row.label} className="breakdown-row">
                        <div className="breakdown-row-header">
                          <span className="breakdown-cat-name">{row.label}</span>
                          <span className="breakdown-cat-score" style={{ color: row.color }}>{row.val}/{row.max}</span>
                        </div>
                        <div className="breakdown-bar-bg">
                          <div className="breakdown-bar-fill" style={{ width: `${(row.val / row.max) * 100}%`, background: row.color }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Skill Pills */}
                <div className="skills-three-col">
                  <div className="detail-card">
                    <h3 className="card-section-title" style={{ color: '#10b981' }}>✅ Matched Skills</h3>
                    <div className="pill-grid">
                      {matchData.matched_skills?.length > 0
                        ? matchData.matched_skills.map((s, i) => <span key={i} className="pill pill--green">{s}</span>)
                        : <span className="text-muted">None</span>}
                    </div>
                  </div>
                  <div className="detail-card">
                    <h3 className="card-section-title" style={{ color: '#f87171' }}>❌ Missing Skills</h3>
                    <div className="pill-grid">
                      {matchData.missing_skills?.length > 0
                        ? matchData.missing_skills.map((s, i) => <span key={i} className="pill pill--red">{s}</span>)
                        : <span className="text-muted" style={{ color: '#10b981' }}>✅ None missing!</span>}
                    </div>
                  </div>
                  <div className="detail-card">
                    <h3 className="card-section-title" style={{ color: '#60a5fa' }}>💡 Extra Skills</h3>
                    <div className="pill-grid">
                      {matchData.extra_skills?.length > 0
                        ? matchData.extra_skills.map((s, i) => <span key={i} className="pill pill--blue">{s}</span>)
                        : <span className="text-muted">None</span>}
                    </div>
                  </div>
                </div>

                {/* Recommendation */}
                {matchData.recommendation && (
                  <div className="detail-card" style={{ gridColumn: '1 / -1', borderColor: '#0ea5e9' }}>
                    <h3 className="card-section-title">💡 Recommendation</h3>
                    <p style={{ color: '#94a3b8', lineHeight: 1.7 }}>{matchData.recommendation}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
