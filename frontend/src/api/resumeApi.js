/**
 * src/api/resumeApi.js
 *
 * Axios calls for the resumes, ATS score, Job Matching, and AI Suggestions modules.
 * Reuses the authenticated `api` instance from authApi.js
 */
import api from './authApi';

export const resumeApi = {
  /** GET /api/resumes/ — list the authenticated user's resumes */
  list: () => api.get('/resumes/'),

  /**
   * POST /api/resumes/ — upload a new resume.
   * @param {File} file — the File object from the input element
   */
  upload: (file) => {
    const form = new FormData();
    form.append('file', file);
    return api.post('/resumes/', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  /** DELETE /api/resumes/<id>/ — delete a specific resume. */
  delete: (id) => api.delete(`/resumes/${id}/`),

  /** PUT /api/resumes/<id>/ — replace a specific resume. */
  replace: (id, file) => {
    const form = new FormData();
    form.append('file', file);
    return api.put(`/resumes/${id}/`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  /** POST /api/resumes/<id>/process/ — trigger text extraction & cleaning. */
  process: (id) => api.post(`/resumes/${id}/process/`),

  /** GET /api/resumes/<id>/text/ — retrieve raw text, cleaned text, and metadata. */
  getText: (id) => api.get(`/resumes/${id}/text/`),

  /** POST /api/resumes/<id>/parse/ — trigger structured parsing. */
  parse: (id) => api.post(`/resumes/${id}/parse/`),

  /** GET /api/resumes/<id>/parsed/ — retrieve structured parsed resume data. */
  getParsed: (id) => api.get(`/resumes/${id}/parsed/`),

  // ── MODULE 5: ATS QUALITY SCORE ───────────────────────────────────────────
  /** GET /api/resumes/<id>/ats-score/ — retrieve ATS score report. */
  getAtsScore: (id) => api.get(`/resumes/${id}/ats-score/`),

  /** POST /api/resumes/<id>/ats-score/ — generate/refresh ATS score report. */
  generateAtsScore: (id) => api.post(`/resumes/${id}/ats-score/`),

  // ── MODULE 6: JOB DESCRIPTION MATCHING ────────────────────────────────────
  /** POST /api/job-descriptions/ — create/upload Job Description. */
  createJd: (data) => api.post('/job-descriptions/', data),

  /** GET /api/job-descriptions/ — list user's Job Descriptions. */
  listJds: () => api.get('/job-descriptions/'),

  /** POST /api/job-descriptions/<jdId>/match/<resumeId>/ — generate Job Match report. */
  matchJd: (jdId, resumeId) => api.post(`/job-descriptions/${jdId}/match/${resumeId}/`),

  /** GET /api/job-descriptions/<jdId>/match/<resumeId>/ — retrieve Job Match report. */
  getMatchJd: (jdId, resumeId) => api.get(`/job-descriptions/${jdId}/match/${resumeId}/`),

  // ── MODULE 7: AI RESUME SUGGESTIONS ───────────────────────────────────────
  /** GET /api/resumes/<id>/ai-suggestions/ — retrieve AI suggestions. */
  getAiSuggestions: (id) => api.get(`/resumes/${id}/ai-suggestions/`),

  /** POST /api/resumes/<id>/ai-suggestions/ — generate AI suggestions. */
  generateAiSuggestions: (id) => api.post(`/resumes/${id}/ai-suggestions/`),

  // ── MODULE 8: INTERVIEW QUESTION GENERATOR ─────────────────────────────────
  /**
   * POST /api/resumes/<id>/generate-questions/
   * Generate AI interview questions.
   * @param {number} id — Resume ID
   * @param {{ difficulty: string, count: number, role: string }} payload
   */
  generateInterviewQuestions: (id, payload) =>
    api.post(`/resumes/${id}/generate-questions/`, payload),

  /** GET /api/resumes/<id>/questions/list/ — list all saved question sets. */
  listInterviewQuestions: (id) => api.get(`/resumes/${id}/questions/list/`),

  /** GET /api/resumes/<id>/questions/<qsId>/ — retrieve a specific question set. */
  getInterviewQuestionSet: (id, qsId) => api.get(`/resumes/${id}/questions/${qsId}/`),

  // ── MODULE 9: AI MOCK INTERVIEW SYSTEM ─────────────────────────────────────
  /** POST /api/interviews/start/ — initialize mock interview session */
  startMockInterview: (data) => api.post('/interviews/start/', data),

  /** POST /api/interviews/<id>/answer/ — submit answer & get next question */
  submitMockAnswer: (sessionId, data) => api.post(`/interviews/${sessionId}/answer/`, data),

  /** GET /api/interviews/<id>/ — retrieve session status & progress */
  getMockSession: (sessionId) => api.get(`/interviews/${sessionId}/`),

  /** POST /api/interviews/<id>/finish/ — end interview session early */
  finishMockInterview: (sessionId) => api.post(`/interviews/${sessionId}/finish/`),

  /** GET /api/interviews/ — list candidate's mock interview sessions */
  listMockInterviews: () => api.get('/interviews/'),

  // ── MODULE 10: AI ANSWER EVALUATION & INTERVIEW ANALYSIS ENGINE ───────────
  /** POST /api/interviews/<id>/evaluate/ — generate interview evaluation report */
  evaluateMockInterview: (sessionId) => api.post(`/interviews/${sessionId}/evaluate/`),

  /** GET /api/interviews/<id>/evaluation/ — retrieve saved evaluation report */
  getMockInterviewEvaluation: (sessionId) => api.get(`/interviews/${sessionId}/evaluation/`),
};
