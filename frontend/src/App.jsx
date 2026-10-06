/**
 * src/App.jsx
 * Root component with routing and AuthProvider — all 7 module pages.
 */
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { DashboardPage } from './pages/DashboardPage';
import { ResumeUploadPage } from './pages/ResumeUploadPage';
import { AtsScorePage } from './pages/AtsScorePage';
import { JobMatchPage } from './pages/JobMatchPage';
import { AiSuggestionsPage } from './pages/AiSuggestionsPage';
import { InterviewPage } from './pages/InterviewPage';
import { MockInterviewPage } from './pages/MockInterviewPage';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Protected routes */}
          <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
          <Route path="/resumes"   element={<ProtectedRoute><ResumeUploadPage /></ProtectedRoute>} />
          <Route path="/ats-score" element={<ProtectedRoute><AtsScorePage /></ProtectedRoute>} />
          <Route path="/job-match" element={<ProtectedRoute><JobMatchPage /></ProtectedRoute>} />
          <Route path="/ai-suggestions" element={<ProtectedRoute><AiSuggestionsPage /></ProtectedRoute>} />
          <Route path="/interview" element={<ProtectedRoute><InterviewPage /></ProtectedRoute>} />
          <Route path="/mock-interview" element={<ProtectedRoute><MockInterviewPage /></ProtectedRoute>} />

          {/* Default redirect */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
