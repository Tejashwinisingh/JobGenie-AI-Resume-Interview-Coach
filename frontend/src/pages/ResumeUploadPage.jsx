/**
 * src/pages/ResumeUploadPage.jsx
 *
 * Modules 2, 3, 4, 5, 6 & 7 – Resume Upload, Management, Extraction, Parsing,
 * ATS Quality Scoring, Job Description Matching, and AI Resume Suggestions.
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../hooks/useAuth';
import { resumeApi } from '../api/resumeApi';
import { Sidebar } from '../components/layout/Sidebar';

// ─── Constants ────────────────────────────────────────────────────────────────

const MAX_SIZE_BYTES = 5 * 1024 * 1024; // 5 MB
const ALLOWED_EXTENSIONS = ['.pdf', '.docx'];

// ─── Helper Utilities ─────────────────────────────────────────────────────────

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
}

function formatDate(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleDateString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

function validateFile(file) {
  if (!file) return 'No file selected.';
  const ext = '.' + file.name.split('.').pop().toLowerCase();
  if (!ALLOWED_EXTENSIONS.includes(ext)) {
    return `Invalid file type "${ext}". Only PDF and DOCX files are accepted.`;
  }
  if (file.size > MAX_SIZE_BYTES) {
    return `File too large (${formatBytes(file.size)}). Maximum allowed size is 5 MB.`;
  }
  return null;
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function TypeBadge({ type }) {
  return (
    <span className={`resume-badge resume-badge--${type}`}>
      {type?.toUpperCase() || 'FILE'}
    </span>
  );
}

function ProcessingStatusBadge({ status }) {
  const labelMap = {
    completed: '✓ Extracted',
    processing: '⚡ Processing…',
    pending: '⏳ Pending',
    failed: '⚠ Failed',
  };
  return (
    <span className={`status-badge status-badge--${status || 'pending'}`}>
      {labelMap[status] || status}
    </span>
  );
}

// ─── MODAL 1: Text Viewer Modal ────────────────────────────────────────────────
function TextViewerModal({ isOpen, onClose, resumeText, isLoading, error }) {
  const [activeTab, setActiveTab] = useState('cleaned');
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const currentText = activeTab === 'cleaned'
    ? (resumeText?.cleaned_text || 'No cleaned text available.')
    : (resumeText?.raw_text || 'No raw text available.');

  const handleCopy = () => {
    if (currentText) {
      navigator.clipboard.writeText(currentText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-area">
            <h3>{resumeText?.original_filename || 'Extracted Text'}</h3>
            {resumeText && (
              <div className="modal-meta-row">
                <TypeBadge type={resumeText.file_type} />
                <ProcessingStatusBadge status={resumeText.processing_status} />
                <span className="modal-stat">{resumeText.word_count || 0} words</span>
                <span className="modal-stat">{resumeText.character_count || 0} characters</span>
              </div>
            )}
          </div>
          <button className="btn-modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          {isLoading ? (
            <div className="modal-loading">
              <div className="spinner" style={{ borderTopColor: 'var(--color-primary)' }} />
              <span>Loading extracted text…</span>
            </div>
          ) : error ? (
            <div className="alert alert-error">{error}</div>
          ) : (
            <>
              <div className="modal-toolbar">
                <div className="modal-tabs">
                  <button
                    className={`tab-btn${activeTab === 'cleaned' ? ' active' : ''}`}
                    onClick={() => setActiveTab('cleaned')}
                  >
                    Cleaned Text (Formatted)
                  </button>
                  <button
                    className={`tab-btn${activeTab === 'raw' ? ' active' : ''}`}
                    onClick={() => setActiveTab('raw')}
                  >
                    Raw Extracted Text
                  </button>
                </div>
                <button className="btn-copy" onClick={handleCopy}>
                  {copied ? '✓ Copied!' : '📋 Copy Text'}
                </button>
              </div>

              <div className="text-display-container">
                <pre className="text-display-content">{currentText}</pre>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── MODAL 2: Parsed Data Modal ────────────────────────────────────────────────
function ParsedDataModal({ isOpen, onClose, parsedData, isLoading, error }) {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-content modal-content--wide" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-area">
            <h3>Structured Resume Profile</h3>
            <p className="modal-subtitle">Extracted contact info, skills, education, experience, and projects</p>
          </div>
          <button className="btn-modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body modal-body--scrollable">
          {isLoading ? (
            <div className="modal-loading">
              <div className="spinner" style={{ borderTopColor: 'var(--color-primary)' }} />
              <span>Parsing resume into structured data…</span>
            </div>
          ) : error ? (
            <div className="alert alert-error">{error}</div>
          ) : parsedData ? (
            <div className="parsed-profile-grid">
              {/* Header Info */}
              <div className="profile-card profile-card--main">
                <div className="profile-avatar-large">
                  {parsedData.name ? parsedData.name[0].toUpperCase() : '👤'}
                </div>
                <div>
                  <h4 className="profile-name">{parsedData.name || 'Name Not Found'}</h4>
                  <div className="profile-contact-row">
                    {parsedData.email && <span className="contact-item">✉ {parsedData.email}</span>}
                    {parsedData.phone && <span className="contact-item">📞 {parsedData.phone}</span>}
                    {parsedData.linkedin && (
                      <a className="contact-item link-item" href={parsedData.linkedin.startsWith('http') ? parsedData.linkedin : `https://${parsedData.linkedin}`} target="_blank" rel="noreferrer">
                        🔗 LinkedIn
                      </a>
                    )}
                    {parsedData.github && (
                      <a className="contact-item link-item" href={parsedData.github.startsWith('http') ? parsedData.github : `https://${parsedData.github}`} target="_blank" rel="noreferrer">
                        💻 GitHub
                      </a>
                    )}
                  </div>
                </div>
              </div>

              {/* Skills */}
              <div className="profile-card">
                <h5>🛠 Technical Skills ({parsedData.skills?.length || 0})</h5>
                {parsedData.skills?.length > 0 ? (
                  <div className="skills-pill-container">
                    {parsedData.skills.map((skill, idx) => (
                      <span key={idx} className="skill-pill">{skill}</span>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted">No technical skills detected.</p>
                )}
              </div>

              {/* Work Experience */}
              <div className="profile-card">
                <h5>💼 Work Experience</h5>
                {parsedData.experience?.length > 0 ? (
                  <div className="timeline-list">
                    {parsedData.experience.map((exp, idx) => (
                      <div key={idx} className="timeline-item">
                        <div className="timeline-title">{exp.title || 'Role'} {exp.company && `@ ${exp.company}`}</div>
                        {exp.date && <div className="timeline-date">{exp.date}</div>}
                        {exp.bullets?.length > 0 && (
                          <ul className="timeline-bullets">
                            {exp.bullets.map((b, bIdx) => <li key={bIdx}>{b}</li>)}
                          </ul>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted">No work experience entries detected.</p>
                )}
              </div>

              {/* Education */}
              <div className="profile-card">
                <h5>🎓 Education</h5>
                {parsedData.education?.length > 0 ? (
                  <div className="timeline-list">
                    {parsedData.education.map((edu, idx) => (
                      <div key={idx} className="timeline-item">
                        <div className="timeline-title">{edu.degree || 'Degree'}</div>
                        {edu.institution && <div className="timeline-sub">{edu.institution}</div>}
                        {edu.date && <div className="timeline-date">{edu.date}</div>}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted">No education entries detected.</p>
                )}
              </div>

              {/* Projects */}
              <div className="profile-card">
                <h5>🚀 Key Projects</h5>
                {parsedData.projects?.length > 0 ? (
                  <div className="timeline-list">
                    {parsedData.projects.map((proj, idx) => (
                      <div key={idx} className="timeline-item">
                        <div className="timeline-title">{proj.title || 'Project'}</div>
                        {proj.description && <p className="timeline-desc">{proj.description}</p>}
                        {proj.technologies?.length > 0 && (
                          <div className="skills-pill-container" style={{ marginTop: '0.4rem' }}>
                            {proj.technologies.map((t, tIdx) => (
                              <span key={tIdx} className="skill-pill skill-pill--sm">{t}</span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted">No project entries detected.</p>
                )}
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

// ─── MODAL 3: ATS Score Modal (Module 5) ──────────────────────────────────────
function AtsScoreModal({ isOpen, onClose, atsData, isLoading, error }) {
  if (!isOpen) return null;

  const score = atsData?.ats_score ?? 0;
  const grade = atsData?.grade ?? 'N/A';
  const label = atsData?.grade_label ?? '';
  const breakdown = atsData?.breakdown ?? {};
  const analysis = atsData?.analysis ?? {};

  const getScoreColor = (val) => {
    if (val >= 80) return '#10b981';
    if (val >= 70) return '#6366f1';
    if (val >= 60) return '#f59e0b';
    return '#ef4444';
  };

  return (
    <div className="modal-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-content modal-content--wide" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-area">
            <h3>🎯 ATS Quality Assessment Report</h3>
            <p className="modal-subtitle">Applicant Tracking System Parsability &amp; Formatting Analysis</p>
          </div>
          <button className="btn-modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body modal-body--scrollable">
          {isLoading ? (
            <div className="modal-loading">
              <div className="spinner" style={{ borderTopColor: 'var(--color-primary)' }} />
              <span>Analyzing resume for ATS compatibility…</span>
            </div>
          ) : error ? (
            <div className="alert alert-error">{error}</div>
          ) : atsData ? (
            <div className="ats-report-grid">
              {/* Score Header Card */}
              <div className="ats-score-hero" style={{ borderColor: getScoreColor(score) }}>
                <div className="ats-score-circle" style={{ backgroundColor: getScoreColor(score) }}>
                  <span className="ats-number">{score}</span>
                  <span className="ats-denom">/100</span>
                </div>
                <div className="ats-hero-details">
                  <div className="ats-grade-badge" style={{ backgroundColor: getScoreColor(score) }}>
                    Grade {grade} · {label}
                  </div>
                  <p className="ats-summary-text">{atsData.summary}</p>
                </div>
              </div>

              {/* Score Breakdown Bars */}
              <div className="profile-card">
                <h5>📊 Category Score Breakdown</h5>
                <div className="ats-breakdown-list" style={{ display: 'grid', gap: '0.8rem', marginTop: '0.8rem' }}>
                  {Object.entries(breakdown).map(([cat, val]) => (
                    <div key={cat} className="ats-bar-item">
                      <div className="ats-bar-label" style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', fontWeight: 600, textTransform: 'capitalize' }}>
                        <span>{cat}</span>
                        <span>{val} pts</span>
                      </div>
                      <div className="ats-bar-bg" style={{ height: '8px', background: '#e2e8f0', borderRadius: '4px', overflow: 'hidden', marginTop: '4px' }}>
                        <div className="ats-bar-fill" style={{ width: `${(val / 25) * 100}%`, height: '100%', background: getScoreColor(score) }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Keywords & Warnings */}
              <div className="profile-card">
                <h5>🔍 Technical Keywords Detected ({analysis.keyword_count || 0})</h5>
                {analysis.technical_keywords_found?.length > 0 ? (
                  <div className="skills-pill-container" style={{ marginTop: '0.5rem' }}>
                    {analysis.technical_keywords_found.map((kw, i) => (
                      <span key={i} className="skill-pill skill-pill--sm">{kw}</span>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted">No technical keywords detected.</p>
                )}

                {analysis.warnings?.length > 0 && (
                  <div style={{ marginTop: '1rem' }}>
                    <h5 style={{ color: '#dc2626' }}>⚠️ Actionable Warnings</h5>
                    <ul className="timeline-bullets" style={{ marginTop: '0.4rem', color: '#b91c1c' }}>
                      {analysis.warnings.map((w, i) => <li key={i}>{w}</li>)}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

// ─── MODAL 4: AI Suggestions Modal (Module 7) ──────────────────────────────────
function AiSuggestionsModal({ isOpen, onClose, aiData, isLoading, error }) {
  const [copied, setCopied] = useState(false);
  if (!isOpen) return null;

  const handleCopyCode = () => {
    if (aiData?.improved_project_description) {
      navigator.clipboard.writeText(aiData.improved_project_description);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-content modal-content--wide" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-area">
            <h3>🤖 AI Resume Improvement Engine</h3>
            <p className="modal-subtitle">OpenAI Personalised Resume Analysis &amp; Rewriting Roadmap</p>
          </div>
          <button className="btn-modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body modal-body--scrollable">
          {isLoading ? (
            <div className="modal-loading">
              <div className="spinner" style={{ borderTopColor: 'var(--color-primary)' }} />
              <span>Generating AI suggestions & project rewrites…</span>
            </div>
          ) : error ? (
            <div className="alert alert-error">{error}</div>
          ) : aiData ? (
            <div className="ai-report-grid" style={{ display: 'grid', gap: '1rem' }}>
              {/* Summary Box */}
              <div className="profile-card" style={{ background: 'linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%)', borderColor: '#0284c7' }}>
                <h5 style={{ color: '#0369a1' }}>💡 AI Executive Assessment</h5>
                <p style={{ marginTop: '0.4rem', color: '#0c4a6e', fontWeight: 500 }}>{aiData.summary}</p>
              </div>

              {/* Strengths & Weaknesses */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="profile-card" style={{ borderColor: '#86efac' }}>
                  <h5 style={{ color: '#15803d' }}>✅ Strengths</h5>
                  <ul className="timeline-bullets" style={{ marginTop: '0.5rem', color: '#166534' }}>
                    {aiData.strengths?.map((s, i) => <li key={i}>{s}</li>)}
                  </ul>
                </div>
                <div className="profile-card" style={{ borderColor: '#fca5a5' }}>
                  <h5 style={{ color: '#b91c1c' }}>⚠️ Areas for Improvement</h5>
                  <ul className="timeline-bullets" style={{ marginTop: '0.5rem', color: '#991b1b' }}>
                    {aiData.weaknesses?.map((w, i) => <li key={i}>{w}</li>)}
                  </ul>
                </div>
              </div>

              {/* Actionable Suggestions */}
              <div className="profile-card">
                <h5>📋 Actionable Suggestions</h5>
                <ul className="timeline-bullets" style={{ marginTop: '0.5rem' }}>
                  {aiData.suggestions?.map((s, i) => <li key={i}>{s}</li>)}
                </ul>
              </div>

              {/* Priority Skills to Learn */}
              <div className="profile-card">
                <h5>🎯 Priority Skills to Learn / Highlight</h5>
                <div className="skills-pill-container" style={{ marginTop: '0.5rem' }}>
                  {aiData.priority_skills?.map((sk, i) => (
                    <span key={i} className="skill-pill" style={{ background: '#e0e7ff', color: '#3730a3', fontWeight: 600 }}>{sk}</span>
                  ))}
                </div>
              </div>

              {/* Improved STAR Project Description */}
              {aiData.improved_project_description && (
                <div className="profile-card" style={{ background: '#faf5ff', borderColor: '#c084fc' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h5 style={{ color: '#7e22ce' }}>✨ Rewritten STAR-Method Project Description</h5>
                    <button className="btn-copy" onClick={handleCopyCode}>
                      {copied ? '✓ Copied!' : '📋 Copy Text'}
                    </button>
                  </div>
                  <pre className="text-display-content" style={{ marginTop: '0.6rem', whiteSpace: 'pre-wrap', background: '#ffffff', padding: '0.8rem', borderRadius: '6px', fontSize: '0.85rem' }}>
                    {aiData.improved_project_description}
                  </pre>
                </div>
              )}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

// ─── MODAL 5: Job Match Modal (Module 6) ───────────────────────────────────────
function JobMatchModal({ isOpen, onClose, resume, onMatch, matchData, isLoading, error }) {
  const [jdText, setJdText] = useState('');
  const [jdTitle, setJdTitle] = useState('');
  const [jdCompany, setJdCompany] = useState('');

  if (!isOpen) return null;

  const handleMatchSubmit = (e) => {
    e.preventDefault();
    if (!jdText.strip && !jdTitle) return;
    onMatch(resume.id, { title: jdTitle || 'Job Role', company: jdCompany, description: jdText });
  };

  return (
    <div className="modal-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-content modal-content--wide" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-area">
            <h3>💼 Job Description Match Engine</h3>
            <p className="modal-subtitle">Match candidate skills, experience &amp; degree against any Job Description</p>
          </div>
          <button className="btn-modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body modal-body--scrollable">
          {/* Input Form */}
          <form onSubmit={handleMatchSubmit} className="jd-form" style={{ marginBottom: '1.2rem' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.8rem', marginBottom: '0.8rem' }}>
              <input
                type="text"
                placeholder="Job Title (e.g. Senior Backend Developer)"
                value={jdTitle}
                onChange={(e) => setJdTitle(e.target.value)}
                style={{ padding: '0.6rem', borderRadius: '6px', border: '1px solid #cbd5e1' }}
              />
              <input
                type="text"
                placeholder="Company Name (Optional)"
                value={jdCompany}
                onChange={(e) => setJdCompany(e.target.value)}
                style={{ padding: '0.6rem', borderRadius: '6px', border: '1px solid #cbd5e1' }}
              />
            </div>
            <textarea
              rows={4}
              placeholder="Paste Job Description text requirements here (skills, experience, degree)..."
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              style={{ width: '100%', padding: '0.6rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontFamily: 'inherit' }}
            />
            <button type="submit" className="btn-upload" style={{ marginTop: '0.6rem', width: 'auto' }} disabled={isLoading}>
              {isLoading ? '⚡ Calculating Match…' : '🔍 Analyze Job Match'}
            </button>
          </form>

          {/* Results Display */}
          {error && <div className="alert alert-error">{error}</div>}

          {matchData && (
            <div className="match-report-grid" style={{ display: 'grid', gap: '1rem' }}>
              <div className="ats-score-hero" style={{ background: '#f8fafc', borderColor: '#3b82f6' }}>
                <div className="ats-score-circle" style={{ backgroundColor: '#3b82f6' }}>
                  <span className="ats-number">{matchData.match_score}</span>
                  <span className="ats-denom">%</span>
                </div>
                <div className="ats-hero-details">
                  <div className="ats-grade-badge" style={{ backgroundColor: '#3b82f6' }}>
                    {matchData.grade}
                  </div>
                  <p style={{ marginTop: '0.4rem', color: '#475569' }}>
                    Skill Match: {matchData.breakdown?.skills ?? 0}/50 pts | Experience: {matchData.experience_match ?? 0}/20 pts
                  </p>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.8rem' }}>
                <div className="profile-card" style={{ borderColor: '#86efac' }}>
                  <h5 style={{ color: '#15803d' }}>✅ Matched Skills</h5>
                  <div className="skills-pill-container" style={{ marginTop: '0.4rem' }}>
                    {matchData.matched_skills?.map((sk, i) => (
                      <span key={i} className="skill-pill" style={{ background: '#dcfce7', color: '#166534' }}>{sk}</span>
                    ))}
                  </div>
                </div>
                <div className="profile-card" style={{ borderColor: '#fca5a5' }}>
                  <h5 style={{ color: '#b91c1c' }}>❌ Missing Skills</h5>
                  <div className="skills-pill-container" style={{ marginTop: '0.4rem' }}>
                    {matchData.missing_skills?.map((sk, i) => (
                      <span key={i} className="skill-pill" style={{ background: '#fee2e2', color: '#991b1b' }}>{sk}</span>
                    ))}
                  </div>
                </div>
                <div className="profile-card" style={{ borderColor: '#93c5fd' }}>
                  <h5 style={{ color: '#1d4ed8' }}>💡 Extra Skills</h5>
                  <div className="skills-pill-container" style={{ marginTop: '0.4rem' }}>
                    {matchData.extra_skills?.map((sk, i) => (
                      <span key={i} className="skill-pill" style={{ background: '#dbeafe', color: '#1e40af' }}>{sk}</span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── RESUME CARD ─────────────────────────────────────────────────────────────
function ResumeCard({
  resume,
  onDelete,
  onReplace,
  onProcess,
  onViewText,
  onViewParsed,
  onViewAts,
  onViewAi,
  onViewMatch,
  isDeleting,
  isReplacing,
  isProcessing,
  isParsing,
}) {
  const replaceFileRef = useRef(null);

  const handleReplaceClick = (e) => {
    e.stopPropagation();
    replaceFileRef.current?.click();
  };

  const handleFileChange = (e) => {
    if (e.target.files?.[0]) {
      onReplace(resume.id, e.target.files[0]);
    }
  };

  return (
    <div className="resume-card">
      <input
        ref={replaceFileRef}
        type="file"
        accept=".pdf,.docx"
        style={{ display: 'none' }}
        onChange={handleFileChange}
      />

      <div className="resume-card-header">
        <div className="resume-card-icon">
          {resume.file_type === 'pdf' ? '🔴' : '🔵'}
        </div>
        <div className="resume-card-meta">
          <h4 className="resume-card-title">{resume.original_filename}</h4>
          <div className="resume-card-sub">
            <TypeBadge type={resume.file_type} />
            <span>{formatBytes(resume.file_size)}</span>
            <span>Uploaded {formatDate(resume.upload_date)}</span>
          </div>
        </div>
        <ProcessingStatusBadge status={resume.processing_status} />
      </div>

      <div className="resume-card-actions">
        {resume.has_extracted_text ? (
          <>
            <button
              className="btn-resume-action btn-view-text"
              onClick={() => onViewText(resume)}
              title="View Extracted Text"
            >
              📄 View Text
            </button>
            <button
              className="btn-resume-action btn-view-parsed"
              onClick={() => onViewParsed(resume)}
              disabled={isParsing}
              title="View Parsed Structured Profile"
            >
              {isParsing ? <span className="spinner-sm" /> : '👤 Structured Profile'}
            </button>
            <button
              className="btn-resume-action"
              style={{ background: '#e0e7ff', color: '#3730a3', borderColor: '#c7d2fe', fontWeight: 600 }}
              onClick={() => onViewAts(resume)}
              title="Module 5 — ATS Quality Score"
            >
              🎯 ATS Score
            </button>
            <button
              className="btn-resume-action"
              style={{ background: '#f0fdf4', color: '#166534', borderColor: '#bbf7d0', fontWeight: 600 }}
              onClick={() => onViewAi(resume)}
              title="Module 7 — AI Resume Suggestions"
            >
              🤖 AI Feedback
            </button>
            <button
              className="btn-resume-action"
              style={{ background: '#eff6ff', color: '#1e40af', borderColor: '#bfdbfe', fontWeight: 600 }}
              onClick={() => onViewMatch(resume)}
              title="Module 6 — Job Match"
            >
              💼 Job Match
            </button>
          </>
        ) : (
          <button
            className="btn-resume-action btn-process"
            onClick={() => onProcess(resume.id)}
            disabled={isProcessing || isDeleting || isReplacing || isParsing}
            title="Process and extract text"
          >
            {isProcessing ? <span className="spinner-sm" /> : '⚡ Extract Text'}
          </button>
        )}

        <button
          className="btn-resume-action btn-replace"
          onClick={handleReplaceClick}
          disabled={isReplacing || isDeleting || isProcessing || isParsing}
          title="Replace this resume"
        >
          {isReplacing ? <span className="spinner-sm" /> : '↩ Replace'}
        </button>
        <button
          className="btn-resume-action btn-delete"
          onClick={() => onDelete(resume.id)}
          disabled={isDeleting || isReplacing || isProcessing || isParsing}
          title="Delete this resume"
        >
          {isDeleting ? <span className="spinner-sm" /> : '✕ Delete'}
        </button>
      </div>
    </div>
  );
}

// ─── Main Page Component ──────────────────────────────────────────────────────

export function ResumeUploadPage() {
  const { user } = useAuth();

  // Resumes list state
  const [resumes, setResumes] = useState([]);
  const [loadingList, setLoadingList] = useState(true);
  const [listError, setListError] = useState('');

  // Upload state
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadError, setUploadError] = useState('');
  const [uploadSuccess, setUploadSuccess] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);

  // Action states
  const [deletingId, setDeletingId] = useState(null);
  const [replacingId, setReplacingId] = useState(null);
  const [processingId, setProcessingId] = useState(null);
  const [parsingId, setParsingId] = useState(null);
  const [actionError, setActionError] = useState('');

  // Modals state
  const [isTextModalOpen, setIsTextModalOpen] = useState(false);
  const [modalResumeText, setModalResumeText] = useState(null);
  const [loadingModalText, setLoadingModalText] = useState(false);
  const [modalTextError, setModalTextError] = useState('');

  const [isParsedModalOpen, setIsParsedModalOpen] = useState(false);
  const [modalParsedData, setModalParsedData] = useState(null);
  const [loadingParsedData, setLoadingParsedData] = useState(false);
  const [parsedDataError, setParsedDataError] = useState('');

  // Module 5 ATS Modal
  const [isAtsModalOpen, setIsAtsModalOpen] = useState(false);
  const [atsData, setAtsData] = useState(null);
  const [loadingAts, setLoadingAts] = useState(false);
  const [atsError, setAtsError] = useState('');

  // Module 7 AI Suggestions Modal
  const [isAiModalOpen, setIsAiModalOpen] = useState(false);
  const [aiData, setAiData] = useState(null);
  const [loadingAi, setLoadingAi] = useState(false);
  const [aiError, setAiError] = useState('');

  // Module 6 Job Match Modal
  const [isMatchModalOpen, setIsMatchModalOpen] = useState(false);
  const [matchResume, setMatchResume] = useState(null);
  const [matchData, setMatchData] = useState(null);
  const [loadingMatch, setLoadingMatch] = useState(false);
  const [matchError, setMatchError] = useState('');

  // ── Fetch resumes ──────────────────────────────────────────────────────────
  const fetchResumes = useCallback(async () => {
    setLoadingList(true);
    setListError('');
    try {
      const { data } = await resumeApi.list();
      setResumes(data);
    } catch {
      setListError('Failed to load your resumes. Please refresh the page.');
    } finally {
      setLoadingList(false);
    }
  }, []);

  useEffect(() => { fetchResumes(); }, [fetchResumes]);

  // ── Handlers ───────────────────────────────────────────────────────────────
  const pickFile = (file) => {
    setUploadError('');
    setUploadSuccess('');
    const err = validateFile(file);
    if (err) { setUploadError(err); setSelectedFile(null); return; }
    setSelectedFile(file);
  };

  const handleFileChange = (e) => {
    if (e.target.files?.[0]) pickFile(e.target.files[0]);
  };

  const handleDragOver = (e) => { e.preventDefault(); setIsDragOver(true); };
  const handleDragLeave = () => setIsDragOver(false);
  const handleDrop = (e) => {
    e.preventDefault(); setIsDragOver(false);
    if (e.dataTransfer.files?.[0]) pickFile(e.dataTransfer.files[0]);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setIsUploading(true);
    setUploadError('');
    setUploadSuccess('');
    try {
      const { data } = await resumeApi.upload(selectedFile);
      setResumes((prev) => [data.resume, ...prev]);
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      setUploadSuccess(`"${data.resume.original_filename}" uploaded & parsed successfully!`);
    } catch (err) {
      setUploadError('Upload failed. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleProcess = async (id) => {
    setProcessingId(id);
    setActionError('');
    try {
      const { data } = await resumeApi.process(id);
      setResumes((prev) => prev.map((r) => (r.id === id ? {
        ...r,
        processing_status: data.data.processing_status,
        has_extracted_text: true,
        has_parsed_data: true,
      } : r)));
    } catch (err) {
      setActionError('Text processing failed.');
    } finally {
      setProcessingId(null);
    }
  };

  const handleViewText = async (resume) => {
    setIsTextModalOpen(true); setModalResumeText(null); setLoadingModalText(true); setModalTextError('');
    try {
      const { data } = await resumeApi.getText(resume.id);
      setModalResumeText(data);
    } catch {
      setModalTextError('Failed to load text.');
    } finally {
      setLoadingModalText(false);
    }
  };

  const handleViewParsed = async (resume) => {
    setIsParsedModalOpen(true); setModalParsedData(null); setLoadingParsedData(true); setParsedDataError('');
    try {
      const { data } = await resumeApi.getParsed(resume.id);
      setModalParsedData(data);
    } catch {
      setParsedDataError('Failed to load parsed profile.');
    } finally {
      setLoadingParsedData(false);
    }
  };

  // Module 5 Handler
  const handleViewAts = async (resume) => {
    setIsAtsModalOpen(true); setAtsData(null); setLoadingAts(true); setAtsError('');
    try {
      const { data } = await resumeApi.getAtsScore(resume.id);
      setAtsData(data);
    } catch {
      setAtsError('Failed to load ATS Score.');
    } finally {
      setLoadingAts(false);
    }
  };

  // Module 7 Handler
  const handleViewAi = async (resume) => {
    setIsAiModalOpen(true); setAiData(null); setLoadingAi(true); setAiError('');
    try {
      const { data } = await resumeApi.getAiSuggestions(resume.id);
      setAiData(data);
    } catch {
      setAiError('Failed to load AI suggestions.');
    } finally {
      setLoadingAi(false);
    }
  };

  // Module 6 Handler
  const handleViewMatch = (resume) => {
    setIsMatchModalOpen(true); setMatchResume(resume); setMatchData(null); setMatchError('');
  };

  const handleMatchSubmit = async (resumeId, jdPayload) => {
    setLoadingMatch(true); setMatchError('');
    try {
      const { data: jdData } = await resumeApi.createJd(jdPayload);
      const jdId = jdData.data.id;
      const { data: mData } = await resumeApi.matchJd(jdId, resumeId);
      setMatchData(mData);
    } catch (err) {
      setMatchError('Job Description match failed.');
    } finally {
      setLoadingMatch(false);
    }
  };

  const handleDelete = async (id) => {
    setDeletingId(id); setActionError('');
    try {
      await resumeApi.delete(id);
      setResumes((prev) => prev.filter((r) => r.id !== id));
    } catch {
      setActionError('Failed to delete resume.');
    } finally {
      setDeletingId(null);
    }
  };

  const handleReplace = async (id, file) => {
    setActionError('');
    const err = validateFile(file);
    if (err) { setActionError(err); return; }
    setReplacingId(id);
    try {
      const { data } = await resumeApi.replace(id, file);
      setResumes((prev) => prev.map((r) => (r.id === id ? data.resume : r)));
    } catch {
      setActionError('Replace failed.');
    } finally {
      setReplacingId(null);
    }
  };

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="module-main">
        <div className="module-header">
          <div className="module-header-left">
            <div className="module-icon" style={{ background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)' }}>📄</div>
            <div>
              <h1 className="module-title">My Resumes</h1>
              <p className="module-subtitle">Upload, Extract Text &amp; Parse Structured Profile</p>
            </div>
          </div>
          <div className="module-badge" style={{ background: '#3b82f6' }}>Upload &amp; Manage</div>
        </div>

        {/* Upload Zone */}
        <section className="upload-section">
          <div
            id="upload-zone"
            className={`upload-zone${isDragOver ? ' upload-zone--active' : ''}${selectedFile ? ' upload-zone--selected' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx"
              style={{ display: 'none' }}
              onChange={handleFileChange}
            />
            <div className="upload-zone-icon">{isDragOver ? '📂' : '⬆'}</div>
            {selectedFile ? (
              <>
                <div className="upload-zone-filename">{selectedFile.name}</div>
                <div className="upload-zone-size">{formatBytes(selectedFile.size)}</div>
              </>
            ) : (
              <>
                <div className="upload-zone-title">Drag & drop your resume</div>
                <div className="upload-zone-subtitle">or <span className="upload-zone-link">browse files</span></div>
                <div className="upload-zone-hint">PDF or DOCX · max 5 MB</div>
              </>
            )}
          </div>

          {uploadError && <div className="alert alert-error">{uploadError}</div>}
          {uploadSuccess && <div className="alert alert-success">{uploadSuccess}</div>}

          <button
            className="btn-upload"
            onClick={handleUpload}
            disabled={!selectedFile || isUploading}
          >
            {isUploading ? <><span className="spinner-sm" /> Uploading & Analyzing…</> : 'Upload Resume'}
          </button>
        </section>

        {/* Resumes List */}
        <section className="resume-list-section">
          <div className="resume-list-header">
            <h2>Your Uploaded Resumes</h2>
            <span className="resume-count">{resumes.length} file{resumes.length !== 1 ? 's' : ''}</span>
          </div>

          {actionError && <div className="alert alert-error">{actionError}</div>}

          {loadingList ? (
            <div className="resume-list-loading">
              <div className="spinner" style={{ borderTopColor: 'var(--color-primary)' }} />
              <span>Loading resumes…</span>
            </div>
          ) : listError ? (
            <div className="alert alert-error">{listError}</div>
          ) : resumes.length === 0 ? (
            <div className="resume-empty">
              <div className="resume-empty-icon">📁</div>
              <div className="resume-empty-title">No resumes uploaded yet</div>
              <div className="resume-empty-sub">Upload a PDF or DOCX above to get started.</div>
            </div>
          ) : (
            <div className="resume-list">
              {resumes.map((resume) => (
                <ResumeCard
                  key={resume.id}
                  resume={resume}
                  onDelete={handleDelete}
                  onReplace={handleReplace}
                  onProcess={handleProcess}
                  onViewText={handleViewText}
                  onViewParsed={handleViewParsed}
                  onViewAts={handleViewAts}
                  onViewAi={handleViewAi}
                  onViewMatch={handleViewMatch}
                  isDeleting={deletingId === resume.id}
                  isReplacing={replacingId === resume.id}
                  isProcessing={processingId === resume.id}
                  isParsing={parsingId === resume.id}
                />
              ))}
            </div>
          )}
        </section>
      </main>

      {/* Modals */}
      <TextViewerModal
        isOpen={isTextModalOpen}
        onClose={() => setIsTextModalOpen(false)}
        resumeText={modalResumeText}
        isLoading={loadingModalText}
        error={modalTextError}
      />
      <ParsedDataModal
        isOpen={isParsedModalOpen}
        onClose={() => setIsParsedModalOpen(false)}
        parsedData={modalParsedData}
        isLoading={loadingParsedData}
        error={parsedDataError}
      />
    </div>
  );
}
