/**
 * src/pages/MockInterviewPage.jsx
 * Module 9 — AI Mock Interview System with Immersive Voice & Orb Interface.
 *
 * Features:
 * - Setup view (select resume, job role, difficulty, interview type, count)
 * - Immersive 3D/Glassmorphism AI Voice Orb Interface
 * - Interactive States: Idle, Speaking (AI TTS), Listening (Mic STT), Thinking (AI API call)
 * - Canvas Background Particle System
 * - Real-time Voice Audio Visualizer
 * - Live Transcript & Animated Question display
 * - Timer, Progress, Keyboard shortcuts (Space = Toggle Mic, Esc = End)
 * - Fallback text input drawer
 * - Session completion summary & full transcript
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { Sidebar } from '../components/layout/Sidebar';
import { resumeApi } from '../api/resumeApi';

// ─── Constants & Utility Colors ─────────────────────────────────────────────

const CATEGORY_COLORS = {
  HR:          { bg: 'rgba(99,102,241,0.15)', text: '#a5b4fc', border: 'rgba(99,102,241,0.3)' },
  Technical:   { bg: 'rgba(14,165,233,0.15)', text: '#38bdf8', border: 'rgba(14,165,233,0.3)' },
  Resume:      { bg: 'rgba(245,158,11,0.15)', text: '#fbbf24', border: 'rgba(245,158,11,0.3)' },
  Project:     { bg: 'rgba(16,185,129,0.15)', text: '#34d399', border: 'rgba(16,185,129,0.3)' },
  Coding:      { bg: 'rgba(239,68,68,0.12)',  text: '#f87171', border: 'rgba(239,68,68,0.3)' },
  Behavioral:  { bg: 'rgba(167,139,250,0.15)', text: '#c4b5fd', border: 'rgba(167,139,250,0.3)' },
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

// ─── Particle Canvas Background Component ───────────────────────────────────

function ParticleBackground() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animationFrameId;

    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    const particles = Array.from({ length: 45 }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      radius: Math.random() * 2 + 0.8,
      dx: (Math.random() - 0.5) * 0.4,
      dy: (Math.random() - 0.5) * 0.4,
      alpha: Math.random() * 0.5 + 0.1,
    }));

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      particles.forEach((p) => {
        p.x += p.dx;
        p.y += p.dy;
        if (p.x < 0) p.x = canvas.width;
        if (p.x > canvas.width) p.x = 0;
        if (p.y < 0) p.y = canvas.height;
        if (p.y > canvas.height) p.y = 0;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(56, 189, 248, ${p.alpha})`;
        ctx.shadowBlur = 12;
        ctx.shadowColor = 'rgba(56, 189, 248, 0.6)';
        ctx.fill();
      });
      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return <canvas ref={canvasRef} className="orb-particle-canvas" />;
}

// ─── Main MockInterviewPage Component ───────────────────────────────────────

export function MockInterviewPage() {
  const [resumes, setResumes] = useState([]);
  const [jds, setJds] = useState([]);
  const [selectedResumeId, setSelectedResumeId] = useState('');
  const [selectedJdId, setSelectedJdId] = useState('');
  const [loadingInitial, setLoadingInitial] = useState(true);

  // Configuration form state
  const [role, setRole] = useState('Backend Engineer');
  const [difficulty, setDifficulty] = useState('Medium');
  const [interviewType, setInterviewType] = useState('Mixed');
  const [questionCount, setQuestionCount] = useState(10);

  // Active Session & Evaluation state
  const [session, setSession] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [isStarting, setIsStarting] = useState(false);
  const [error, setError] = useState('');
  const [history, setHistory] = useState([]);
  const [evaluation, setEvaluation] = useState(null);
  const [isEvaluating, setIsEvaluating] = useState(false);

  // Voice & Orb States: 'idle' | 'speaking' | 'listening' | 'thinking'
  const [orbState, setOrbState] = useState('idle');
  const [transcript, setTranscript] = useState('');
  const [isMicMuted, setIsMicMuted] = useState(false);
  const [textDrawerOpen, setTextDrawerOpen] = useState(false);
  const [manualText, setManualText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Timer state
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const timerRef = useRef(null);

  // Speech Recognition & Synthesis references
  const recognitionRef = useRef(null);
  const speechSynthRef = useRef(window.speechSynthesis || null);

  // Load initial data
  useEffect(() => {
    Promise.all([resumeApi.list(), resumeApi.listJds()])
      .then(([resumesRes, jdsRes]) => {
        setResumes(resumesRes.data || []);
        setJds(jdsRes.data?.data || jdsRes.data || []);
        if (resumesRes.data?.length > 0) {
          setSelectedResumeId(String(resumesRes.data[0].id));
        }
      })
      .catch(() => {})
      .finally(() => setLoadingInitial(false));
  }, []);

  // Timer effect when interview is active
  useEffect(() => {
    if (session && session.status === 'in_progress') {
      timerRef.current = setInterval(() => {
        setElapsedSeconds((prev) => prev + 1);
      }, 1000);
    } else {
      clearInterval(timerRef.current);
    }
    return () => clearInterval(timerRef.current);
  }, [session]);

  // Format seconds to HH:MM:SS
  const formatTimer = (totalSec) => {
    const hrs = Math.floor(totalSec / 3600);
    const mins = Math.floor((totalSec % 3600) / 60);
    const secs = totalSec % 60;
    const pad = (n) => String(n).padStart(2, '0');
    return hrs > 0 ? `${pad(hrs)}:${pad(mins)}:${pad(secs)}` : `${pad(mins)}:${pad(secs)}`;
  };

  // ── Text-to-Speech (AI Speaking Question) ──────────────────────────────────
  const speakQuestionText = useCallback((text) => {
    if (!speechSynthRef.current) return;
    speechSynthRef.current.cancel(); // Stop prior speech

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    utterance.onstart = () => {
      setOrbState('speaking');
    };

    utterance.onend = () => {
      setOrbState('listening');
      startListening();
    };

    utterance.onerror = () => {
      setOrbState('listening');
      startListening();
    };

    speechSynthRef.current.speak(utterance);
  }, []);

  // ── Speech-to-Text (Microphone STT) ────────────────────────────────────────
  const startListening = useCallback(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn('Web Speech API STT not supported in this browser.');
      return;
    }

    try {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }

      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onstart = () => {
        setOrbState('listening');
      };

      recognition.onresult = (event) => {
        let currentTranscript = '';
        for (let i = 0; i < event.results.length; i++) {
          currentTranscript += event.results[i][0].transcript;
        }
        setTranscript(currentTranscript);
      };

      recognition.onerror = (err) => {
        console.warn('Speech recognition notice:', err.error);
      };

      recognition.onend = () => {
        // Keep listening unless state was explicitly changed to thinking
      };

      recognition.start();
      recognitionRef.current = recognition;
    } catch (e) {
      console.warn('Failed to start speech recognition:', e);
    }
  }, []);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {}
      recognitionRef.current = null;
    }
  }, []);

  // Speak question whenever a new question is loaded
  useEffect(() => {
    if (currentQuestion && session?.status === 'in_progress') {
      speakQuestionText(currentQuestion.question);
    }
  }, [currentQuestion, session?.status, speakQuestionText]);

  // Handle Keyboard Shortcuts (Space = Toggle Mic, Esc = Finish)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

      if (e.code === 'Space') {
        e.preventDefault();
        setIsMicMuted((prev) => {
          const next = !prev;
          if (next) {
            stopListening();
            setOrbState('idle');
          } else {
            startListening();
          }
          return next;
        });
      } else if (e.code === 'Escape' && session && session.status === 'in_progress') {
        e.preventDefault();
        handleFinishEarly();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [session, startListening, stopListening]);

  // ── API Actions ────────────────────────────────────────────────────────────

  const handleStartInterview = async (e) => {
    e.preventDefault();
    if (!selectedResumeId) return;
    setIsStarting(true);
    setError('');
    setSession(null);
    setHistory([]);
    setTranscript('');
    setManualText('');
    setElapsedSeconds(0);
    setCurrentQuestion(null);

    try {
      const payload = {
        resume_id: parseInt(selectedResumeId),
        job_description_id: selectedJdId ? parseInt(selectedJdId) : null,
        role: role || 'Python Developer',
        difficulty,
        interview_type: interviewType,
        question_count: parseInt(questionCount),
      };

      const { data } = await resumeApi.startMockInterview(payload);
      setSession({
        id: data.session_id,
        role: role || 'Python Developer',
        difficulty,
        interview_type: interviewType,
        status: 'in_progress',
        current_question: data.question_number,
        total_questions: data.total_questions,
        completed_questions: 0,
      });
      setCurrentQuestion({
        question_number: data.question_number,
        category: data.category,
        question: data.question,
      });
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to start interview session. Ensure resume is uploaded.');
    } finally {
      setIsStarting(false);
    }
  };

  const handleSendAnswer = async (answerTextOverride) => {
    const finalAnswer = (answerTextOverride || transcript || manualText || '').trim();
    if (!finalAnswer || !session || isSubmitting) return;

    if (speechSynthRef.current) speechSynthRef.current.cancel();
    stopListening();
    setOrbState('thinking');
    setIsSubmitting(true);
    setError('');

    const submittedQ = currentQuestion;

    try {
      const { data } = await resumeApi.submitMockAnswer(session.id, {
        answer: finalAnswer,
      });

      // Update transcript history
      setHistory((prev) => [
        ...prev,
        {
          question_number: submittedQ.question_number,
          category: submittedQ.category,
          question: submittedQ.question,
          user_answer: finalAnswer,
        },
      ]);

      setTranscript('');
      setManualText('');
      setTextDrawerOpen(false);

      if (data.is_completed) {
        setSession((prev) => ({
          ...prev,
          status: 'completed',
          completed_questions: data.completed_questions,
          total_questions: data.total_questions,
        }));
        setCurrentQuestion(null);
        setOrbState('idle');
      } else {
        setSession((prev) => ({
          ...prev,
          current_question: data.question_number,
          completed_questions: data.completed_questions,
        }));
        setCurrentQuestion({
          question_number: data.question_number,
          category: data.category,
          question: data.question,
        });
      }
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to submit answer.');
      setOrbState('listening');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFinishEarly = async () => {
    if (!session || session.status === 'completed') return;
    if (speechSynthRef.current) speechSynthRef.current.cancel();
    stopListening();
    try {
      await resumeApi.finishMockInterview(session.id);
      setSession((prev) => ({ ...prev, status: 'completed' }));
      setCurrentQuestion(null);
      setOrbState('idle');
    } catch (err) {
      setError('Failed to finish interview.');
    }
  };

  const handleGenerateEvaluation = async () => {
    if (!session || isEvaluating) return;
    setIsEvaluating(true);
    setError('');
    try {
      const { data } = await resumeApi.evaluateMockInterview(session.id);
      setEvaluation(data);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to generate AI evaluation report.');
    } finally {
      setIsEvaluating(false);
    }
  };

  const progressPct = session ? Math.round((session.completed_questions / session.total_questions) * 100) : 0;

  return (
    <div className={`app-layout ${session && session.status === 'in_progress' ? 'fullscreen-voice-mode' : ''}`}>
      {/* Show Sidebar only when NOT in active full-screen voice interview */}
      {(!session || session.status !== 'in_progress') && <Sidebar />}

      <main className={`module-main ${session && session.status === 'in_progress' ? 'voice-main' : ''}`}>
        {/* Page Header (hidden in voice mode) */}
        {(!session || session.status !== 'in_progress') && (
          <div className="module-header">
            <div className="module-header-left">
              <div className="module-icon" style={{ background: 'linear-gradient(135deg, #ec4899, #8b5cf6)' }}>🎧</div>
              <div>
                <h1 className="module-title">AI Mock Interview System</h1>
                <p className="module-subtitle">Immersive Voice &amp; AI Orb Interview Simulator</p>
              </div>
            </div>
            <div className="module-badge" style={{ background: '#ec4899' }}>Live Simulator</div>
          </div>
        )}

        {/* ── STEP 1: CONFIGURATION SCREEN ── */}
        {!session && (
          <div className="mock-config-container">
            <div className="mock-config-card">
              <h3 className="panel-title">🎯 Configure Your Voice Mock Interview</h3>
              <form onSubmit={handleStartInterview} className="mock-form">
                <div className="form-row-2">
                  <div className="form-group">
                    <label className="form-label">Select Resume *</label>
                    {loadingInitial ? (
                      <span className="text-muted">Loading resumes…</span>
                    ) : resumes.length === 0 ? (
                      <span className="alert-inline alert-inline--warn">Upload a resume first in <strong>My Resumes</strong>.</span>
                    ) : (
                      <select
                        className="resume-selector"
                        value={selectedResumeId}
                        onChange={(e) => setSelectedResumeId(e.target.value)}
                      >
                        {resumes.map((r) => (
                          <option key={r.id} value={r.id}>{r.original_filename}</option>
                        ))}
                      </select>
                    )}
                  </div>

                  <div className="form-group">
                    <label className="form-label">Target Job Description (Optional)</label>
                    <select
                      className="resume-selector"
                      value={selectedJdId}
                      onChange={(e) => setSelectedJdId(e.target.value)}
                    >
                      <option value="">-- General Role Interview --</option>
                      {jds.map((jd) => (
                        <option key={jd.id} value={jd.id}>{jd.title} ({jd.company || 'Company'})</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="form-row-2">
                  <div className="form-group">
                    <label className="form-label">Target Job Role *</label>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="e.g. Python Developer, Full Stack Engineer"
                      value={role}
                      onChange={(e) => setRole(e.target.value)}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Interview Type</label>
                    <select
                      className="form-input"
                      value={interviewType}
                      onChange={(e) => setInterviewType(e.target.value)}
                    >
                      <option value="Mixed">Mixed Interview (All Categories)</option>
                      <option value="HR">HR Interview</option>
                      <option value="Technical">Technical Deep-Dive</option>
                      <option value="Behavioral">Behavioral (STAR Method)</option>
                      <option value="Coding">Coding &amp; Algorithm</option>
                      <option value="Project Discussion">Project Architecture</option>
                    </select>
                  </div>
                </div>

                <div className="form-row-2">
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

                  <div className="form-group">
                    <label className="form-label">Number of Questions</label>
                    <div className="count-selector">
                      {[5, 10, 15, 20].map((n) => (
                        <button
                          key={n}
                          type="button"
                          className={`count-btn${questionCount === n ? ' active' : ''}`}
                          onClick={() => setQuestionCount(n)}
                        >
                          {n} Questions
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {error && <div className="alert alert-error">{error}</div>}

                <button
                  type="submit"
                  className="btn-generate btn-pink btn-full"
                  disabled={!selectedResumeId || isStarting}
                >
                  {isStarting
                    ? <><span className="spinner-sm" /> Initializing Voice Orb…</>
                    : `🎙️ Launch Voice Mock Interview (${role} · ${difficulty})`}
                </button>
              </form>
            </div>
          </div>
        )}

        {/* ── STEP 2: IMMERSIVE FULL-SCREEN VOICE ORB INTERFACE ── */}
        {session && session.status === 'in_progress' && currentQuestion && (
          <div className="voice-stage">
            <ParticleBackground />

            {/* Top Bar Header */}
            <header className="voice-header">
              <div className="voice-header-top">
                <span className="voice-brand">ResumeIQ AI Interview</span>
                <span className="voice-subtitle">{session.role} · {session.difficulty}</span>
              </div>

              <div className="voice-status-pill">
                {orbState === 'speaking' && <span className="status-dot dot-speaking">🔵 Speaking</span>}
                {orbState === 'listening' && <span className="status-dot dot-listening">🟢 Listening</span>}
                {orbState === 'thinking' && <span className="status-dot dot-thinking">🟡 Thinking…</span>}
                {orbState === 'idle' && <span className="status-dot dot-idle">⚪ Muted</span>}
              </div>

              {/* Progress Line */}
              <div className="voice-progress-wrapper">
                <div className="voice-progress-label">
                  Question {currentQuestion.question_number} of {session.total_questions} ({progressPct}%)
                </div>
                <div className="voice-progress-track">
                  <div className="voice-progress-fill" style={{ width: `${progressPct}%` }} />
                </div>
              </div>
            </header>

            {/* Question Text Display */}
            <div className="voice-question-area">
              <CategoryBadge category={currentQuestion.category} />
              <h2 className="voice-question-text">{currentQuestion.question}</h2>
            </div>

            {/* Central Animated AI Orb */}
            <div className={`ai-orb-container state-${orbState}`}>
              <div className="orb-wave-rings">
                <div className="ring ring-1" />
                <div className="ring ring-2" />
                <div className="ring ring-3" />
              </div>
              <div className="ai-orb-core">
                <div className="orb-inner-glow" />
                <div className="orb-specular" />
              </div>
              {/* Timer under orb */}
              <div className="voice-timer">⏱️ {formatTimer(elapsedSeconds)}</div>
            </div>

            {/* Live Transcript Display */}
            <div className="voice-transcript-container">
              {transcript ? (
                <p className="voice-transcript-text">"{transcript}"</p>
              ) : (
                <p className="voice-transcript-placeholder">
                  {orbState === 'listening' ? '🎙️ Speak your answer... (or use Spacebar to toggle mic)' : 'AI is speaking the question...'}
                </p>
              )}
            </div>

            {/* Bottom Floating Control Bar */}
            <div className="voice-controls-bar">
              {/* Left: Keyboard input fallback toggle */}
              <button
                className={`voice-btn btn-glass ${textDrawerOpen ? 'active' : ''}`}
                onClick={() => setTextDrawerOpen(!textDrawerOpen)}
                title="Keyboard Input (Text Fallback)"
              >
                ⌨️
              </button>

              {/* Center: Main Mic / Submit Action */}
              <button
                className={`voice-btn btn-mic ${orbState === 'listening' ? 'mic-active' : 'mic-muted'}`}
                onClick={() => {
                  if (transcript.trim()) {
                    handleSendAnswer();
                  } else {
                    setIsMicMuted(!isMicMuted);
                    if (isMicMuted) startListening(); else stopListening();
                  }
                }}
                title={transcript.trim() ? "Submit Response" : "Toggle Microphone (Space)"}
              >
                {transcript.trim() ? '🚀' : isMicMuted ? '🔇' : '🎙️'}
              </button>

              {/* Right: End Interview */}
              <button
                className="voice-btn btn-end"
                onClick={handleFinishEarly}
                title="End Interview (Esc)"
              >
                ⏹️
              </button>
            </div>

            {/* Text Drawer Fallback Modal */}
            {textDrawerOpen && (
              <div className="voice-drawer-modal">
                <div className="drawer-content">
                  <div className="drawer-header">
                    <h4>⌨️ Type Response Manually</h4>
                    <button className="drawer-close" onClick={() => setTextDrawerOpen(false)}>✕</button>
                  </div>
                  <textarea
                    className="form-textarea drawer-input"
                    rows={4}
                    placeholder="Type your response here..."
                    value={manualText}
                    onChange={(e) => setManualText(e.target.value)}
                  />
                  <button
                    className="btn-generate btn-pink btn-full"
                    onClick={() => handleSendAnswer(manualText)}
                    disabled={!manualText.trim() || isSubmitting}
                  >
                    Submit Response
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── STEP 3: SESSION COMPLETED SUMMARY & AI EVALUATION REPORT (MODULE 10) ── */}
        {session && session.status === 'completed' && (
          <div className="mock-completed-card">
            <div className="completed-hero">
              <div className="completed-icon">🎉</div>
              <h2>Voice Mock Interview Completed!</h2>
              <p>You completed <strong>{session.total_questions}</strong> questions for the <strong>{session.role}</strong> position in <strong>{formatTimer(elapsedSeconds)}</strong>.</p>
              
              {!evaluation && (
                <div style={{ marginTop: '1.5rem' }}>
                  <button
                    className="btn-generate btn-cyan btn-lg"
                    onClick={handleGenerateEvaluation}
                    disabled={isEvaluating}
                  >
                    {isEvaluating ? '⏳ Generating AI Evaluation Report...' : '📊 Generate Senior AI Evaluation Report (Module 10)'}
                  </button>
                </div>
              )}
            </div>

            {/* ── MODULE 10: AI EVALUATION REPORT DISPLAY ── */}
            {evaluation && (
              <div className="eval-report-card">
                <div className="eval-header-banner">
                  <div className="eval-score-ring">
                    <span className="eval-score-num">{evaluation.overall_score}</span>
                    <span className="eval-score-denom">/100</span>
                  </div>
                  <div className="eval-title-block">
                    <span className={`eval-rec-badge rec-${(evaluation.hiring_recommendation || '').toLowerCase().replace(/\s+/g, '-')}`}>
                      🏆 {evaluation.hiring_recommendation}
                    </span>
                    <h3>Senior Interviewer Executive Summary</h3>
                    <p className="eval-summary-text">{evaluation.summary}</p>
                  </div>
                </div>

                {/* Score Breakdown Grid */}
                <h4 className="eval-section-heading">📈 Candidate Skill Breakdown</h4>
                <div className="eval-metrics-grid">
                  <div className="eval-metric-box">
                    <span className="metric-label">Technical Depth</span>
                    <span className="metric-val">{evaluation.technical_score}/100</span>
                  </div>
                  <div className="eval-metric-box">
                    <span className="metric-label">Communication</span>
                    <span className="metric-val">{evaluation.communication_score}/100</span>
                  </div>
                  <div className="eval-metric-box">
                    <span className="metric-label">Confidence</span>
                    <span className="metric-val">{evaluation.confidence_score}/100</span>
                  </div>
                  <div className="eval-metric-box">
                    <span className="metric-label">Grammar &amp; Vocabulary</span>
                    <span className="metric-val">{evaluation.grammar_score}/100</span>
                  </div>
                  <div className="eval-metric-box">
                    <span className="metric-label">Problem Solving</span>
                    <span className="metric-val">{evaluation.problem_solving_score}/100</span>
                  </div>
                  <div className="eval-metric-box">
                    <span className="metric-label">Professionalism</span>
                    <span className="metric-val">{evaluation.professionalism_score}/100</span>
                  </div>
                </div>

                {/* Strengths & Weaknesses */}
                <div className="eval-row-2">
                  <div className="eval-box eval-box--strengths">
                    <h4>✅ Identified Strengths</h4>
                    <ul>
                      {(evaluation.strengths || []).map((s, idx) => (
                        <li key={idx}>{s}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="eval-box eval-box--weaknesses">
                    <h4>⚠️ Areas for Improvement</h4>
                    <ul>
                      {(evaluation.weaknesses || []).map((w, idx) => (
                        <li key={idx}>{w}</li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* Recommended Study Topics */}
                {evaluation.recommended_topics && evaluation.recommended_topics.length > 0 && (
                  <div className="eval-box eval-box--topics">
                    <h4>📚 Recommended Study Topics for Next Round</h4>
                    <div className="topic-tags">
                      {evaluation.recommended_topics.map((topic, idx) => (
                        <span key={idx} className="topic-tag">📌 {topic}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Complete Transcript */}
            <div className="completed-transcript" style={{ marginTop: '2rem' }}>
              <h3 className="card-section-title">📋 Complete Session Transcript ({history.length} Q&amp;A Pairs)</h3>
              <div className="history-list">
                {history.map((h, i) => {
                  const evalQA = evaluation?.question_analysis?.find((q) => q.question_number === h.question_number);
                  return (
                    <div key={i} className="history-item">
                      <div className="history-item-header">
                        <span className="history-q-num">Q{h.question_number}</span>
                        <CategoryBadge category={h.category} />
                        {evalQA && (
                          <span className="history-eval-score">Overall Score: {evalQA.overall}/10</span>
                        )}
                      </div>
                      <p className="history-q-text">{h.question}</p>
                      <div className="history-ans-box">
                        <span className="history-ans-label">Your Answer:</span>
                        <p className="history-ans-text">{h.user_answer}</p>
                      </div>
                      {evalQA && (
                        <div className="history-qa-feedback">
                          <span className="feedback-label">💡 AI Feedback:</span>
                          <p className="feedback-text">{evalQA.feedback}</p>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="completed-actions">
              <button
                className="btn-generate btn-pink"
                onClick={() => { setSession(null); setHistory([]); setCurrentQuestion(null); setEvaluation(null); setOrbState('idle'); }}
              >
                🔄 Start New Voice Interview
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
