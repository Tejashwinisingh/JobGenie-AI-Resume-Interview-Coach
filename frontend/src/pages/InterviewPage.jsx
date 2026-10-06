/**
 * src/pages/InterviewPage.jsx
 * Module 8 — AI Interview Question Generator dedicated page.
 */
import { useState, useEffect } from 'react';
import { Sidebar } from '../components/layout/Sidebar';
import { resumeApi } from '../api/resumeApi';

const CATEGORY_COLORS = {
  HR:          { bg: 'rgba(99,102,241,0.12)', text: '#a5b4fc', border: 'rgba(99,102,241,0.2)' },
  Technical:   { bg: 'rgba(14,165,233,0.12)', text: '#38bdf8', border: 'rgba(14,165,233,0.2)' },
  Resume:      { bg: 'rgba(245,158,11,0.12)', text: '#fbbf24', border: 'rgba(245,158,11,0.2)' },
  Project:     { bg: 'rgba(16,185,129,0.12)', text: '#34d399', border: 'rgba(16,185,129,0.2)' },
  Coding:      { bg: 'rgba(239,68,68,0.1)',   text: '#f87171', border: 'rgba(239,68,68,0.2)' },
  Behavioral:  { bg: 'rgba(167,139,250,0.12)', text: '#c4b5fd', border: 'rgba(167,139,250,0.2)' },
};

const CATEGORY_ICONS = {
  HR: '👤', Technical: '⚙️', Resume: '📄', Project: '🚀', Coding: '💻', Behavioral: '🤝',
};

function CategoryBadge({ category }) {
  const style = CATEGORY_COLORS[category] || CATEGORY_COLORS.Technical;
  return (
    <span
      className="interview-category-badge"
      style={{ background: style.bg, color: style.text, border: `1px solid ${style.border}` }}
    >
      {CATEGORY_ICONS[category] || '❓'} {category}
    </span>
  );
}

function QuestionCard({ question, index, isRevealed, onReveal }) {
  return (
    <div className={`question-card${isRevealed ? ' revealed' : ''}`} onClick={onReveal}>
      <div className="question-card-header">
        <span className="question-number">Q{question.id}</span>
        <CategoryBadge category={question.category} />
        {!isRevealed && <span className="question-hint">Click to reveal</span>}
      </div>
      {isRevealed ? (
        <p className="question-text">{question.question}</p>
      ) : (
        <div className="question-blurred">
          <p className="question-text blurred-text">{question.question}</p>
          <div className="question-blur-overlay">🔒 Click to reveal</div>
        </div>
      )}
    </div>
  );
}

export function InterviewPage() {
  const [resumes, setResumes] = useState([]);
  const [selectedId, setSelectedId] = useState('');
  const [loadingResumes, setLoadingResumes] = useState(true);

  const [difficulty, setDifficulty] = useState('Medium');
  const [count, setCount] = useState(10);
  const [role, setRole] = useState('');

  const [questions, setQuestions] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');

  const [revealedIds, setRevealedIds] = useState(new Set());
  const [revealAll, setRevealAll] = useState(false);
  const [activeFilter, setActiveFilter] = useState('All');
  const [copySuccess, setCopySuccess] = useState(false);

  useEffect(() => {
    resumeApi.list().then(({ data }) => {
      setResumes(data);
      if (data.length > 0) setSelectedId(String(data[0].id));
    }).catch(() => {}).finally(() => setLoadingResumes(false));
  }, []);

  const handleGenerate = async (e) => {
    e.preventDefault();
    if (!selectedId) return;
    setGenerating(true);
    setError('');
    setQuestions(null);
    setRevealedIds(new Set());
    setRevealAll(false);
    setActiveFilter('All');
    try {
      const { data } = await resumeApi.generateInterviewQuestions(selectedId, {
        difficulty,
        count,
        role: role || 'Software Developer',
      });
      setQuestions(data.data);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to generate questions. Make sure the resume is processed first.');
    } finally {
      setGenerating(false);
    }
  };

  const handleReveal = (id) => {
    setRevealedIds((prev) => new Set([...prev, id]));
  };

  const handleRevealAll = () => {
    if (questions) {
      setRevealedIds(new Set(questions.questions.map((q) => q.id)));
      setRevealAll(true);
    }
  };

  const handleCopyAll = () => {
    if (!questions) return;
    const text = questions.questions
      .map((q) => `Q${q.id} [${q.category}]: ${q.question}`)
      .join('\n\n');
    navigator.clipboard.writeText(text);
    setCopySuccess(true);
    setTimeout(() => setCopySuccess(false), 2000);
  };

  // Category filter
  const allCategories = questions
    ? ['All', ...new Set(questions.questions.map((q) => q.category))]
    : ['All'];

  const filteredQuestions = questions?.questions?.filter(
    (q) => activeFilter === 'All' || q.category === activeFilter
  ) || [];

  const categoryCount = (cat) => {
    if (!questions) return 0;
    return questions.questions.filter((q) => q.category === cat).length;
  };

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="module-main">
        {/* Header */}
        <div className="module-header">
          <div className="module-header-left">
            <div className="module-icon" style={{ background: 'linear-gradient(135deg, #f59e0b, #ef4444)' }}>🎤</div>
            <div>
              <h1 className="module-title">AI Interview Question Generator</h1>
              <p className="module-subtitle">Personalized Interview Questions from Your Resume &amp; JD Match</p>
            </div>
          </div>
          <div className="module-badge" style={{ background: '#f59e0b' }}>Question Generator</div>
        </div>

        <div className="interview-page-grid">
          {/* Config Panel */}
          <div className="interview-config-panel">
            <h3 className="panel-title">⚙️ Generate Interview Questions</h3>
            <form onSubmit={handleGenerate} className="jd-form-fields">
              {/* Resume */}
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

              {/* Role */}
              <div className="form-group">
                <label className="form-label">Target Job Role</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Backend Developer, Full Stack Engineer"
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                />
              </div>

              {/* Difficulty */}
              <div className="form-group">
                <label className="form-label">Difficulty Level</label>
                <div className="difficulty-selector">
                  {['Easy', 'Medium', 'Hard'].map((d) => (
                    <button
                      key={d}
                      type="button"
                      className={`difficulty-btn${difficulty === d ? ' active' : ''}`}
                      data-difficulty={d.toLowerCase()}
                      onClick={() => setDifficulty(d)}
                    >
                      {d === 'Easy' ? '🟢' : d === 'Medium' ? '🟡' : '🔴'} {d}
                    </button>
                  ))}
                </div>
              </div>

              {/* Count */}
              <div className="form-group">
                <label className="form-label">Number of Questions</label>
                <div className="count-selector">
                  {[5, 10, 20, 30].map((n) => (
                    <button
                      key={n}
                      type="button"
                      className={`count-btn${count === n ? ' active' : ''}`}
                      onClick={() => setCount(n)}
                    >
                      {n}
                    </button>
                  ))}
                </div>
              </div>

              {error && <div className="alert alert-error">{error}</div>}

              <button type="submit" className="btn-generate btn-orange btn-full" disabled={!selectedId || generating}>
                {generating
                  ? <><span className="spinner-sm" /> Generating {count} Questions…</>
                  : `🎤 Generate ${count} ${difficulty} Questions`}
              </button>
            </form>

            {/* Quick stats */}
            {questions && (
              <div className="interview-quick-stats">
                <div className="iqstat">
                  <span className="iqstat-val">{questions.question_count}</span>
                  <span className="iqstat-label">Total</span>
                </div>
                {Object.entries(
                  questions.questions.reduce((acc, q) => {
                    acc[q.category] = (acc[q.category] || 0) + 1;
                    return acc;
                  }, {})
                ).map(([cat, n]) => (
                  <div key={cat} className="iqstat">
                    <span className="iqstat-val" style={{ color: CATEGORY_COLORS[cat]?.text }}>
                      {n}
                    </span>
                    <span className="iqstat-label">{cat}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Questions Panel */}
          <div className="interview-questions-panel">
            {!questions && !generating ? (
              <div className="empty-module-state">
                <div className="empty-module-icon">🎤</div>
                <h3>Questions appear here</h3>
                <p>Configure your preferences and click <strong>Generate Questions</strong> to begin your mock interview prep.</p>
                <div className="interview-feature-list">
                  <div className="interview-feature">👤 HR &amp; Motivation</div>
                  <div className="interview-feature">⚙️ Technical Deep-Dives</div>
                  <div className="interview-feature">📄 Resume-Specific</div>
                  <div className="interview-feature">🚀 Project Architecture</div>
                  <div className="interview-feature">💻 Live Coding</div>
                  <div className="interview-feature">🤝 Behavioral STAR</div>
                </div>
              </div>
            ) : generating ? (
              <div className="module-loading">
                <div className="spinner" style={{ borderTopColor: '#f59e0b' }} />
                <span>AI is crafting personalized questions…</span>
              </div>
            ) : questions && (
              <>
                {/* Controls bar */}
                <div className="interview-controls-bar">
                  <div className="interview-meta">
                    <span className="interview-meta-role">🎯 {questions.job_role || role || 'Software Developer'}</span>
                    <span className={`interview-meta-diff diff-${(questions.difficulty || difficulty).toLowerCase()}`}>
                      {questions.difficulty || difficulty}
                    </span>
                    <span className="interview-meta-provider">
                      via {questions.provider || 'AI'}
                    </span>
                  </div>
                  <div className="interview-action-btns">
                    <button className="btn-outline-sm" onClick={handleRevealAll}>👁 Reveal All</button>
                    <button className="btn-outline-sm" onClick={handleCopyAll}>
                      {copySuccess ? '✓ Copied!' : '📋 Copy All'}
                    </button>
                  </div>
                </div>

                {/* Category filter tabs */}
                <div className="interview-category-tabs">
                  {allCategories.map((cat) => (
                    <button
                      key={cat}
                      className={`cat-tab-btn${activeFilter === cat ? ' active' : ''}`}
                      onClick={() => setActiveFilter(cat)}
                    >
                      {cat !== 'All' && (CATEGORY_ICONS[cat] || '')} {cat}
                      <span className="cat-count">
                        {cat === 'All' ? questions.questions.length : categoryCount(cat)}
                      </span>
                    </button>
                  ))}
                </div>

                {/* Questions list */}
                <div className="questions-list">
                  {filteredQuestions.map((q, idx) => (
                    <QuestionCard
                      key={q.id}
                      question={q}
                      index={idx}
                      isRevealed={revealAll || revealedIds.has(q.id)}
                      onReveal={() => handleReveal(q.id)}
                    />
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
