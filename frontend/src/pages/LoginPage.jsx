/**
 * src/pages/LoginPage.jsx
 */
import { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const redirectTo = location.state?.from?.pathname || '/dashboard';

  const [form, setForm] = useState({ email: '', password: '' });
  const [errors, setErrors] = useState({});
  const [globalError, setGlobalError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    setErrors((prev) => ({ ...prev, [e.target.name]: '' }));
    setGlobalError('');
  };

  const validate = () => {
    const errs = {};
    if (!form.email) errs.email = 'Email is required.';
    if (!form.password) errs.password = 'Password is required.';
    return errs;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }

    setIsLoading(true);
    try {
      await login(form);
      navigate(redirectTo, { replace: true });
    } catch (err) {
      const data = err.response?.data;
      if (data?.non_field_errors) {
        setGlobalError(data.non_field_errors[0]);
      } else if (typeof data === 'object') {
        const msg = Object.values(data).flat()[0];
        setGlobalError(typeof msg === 'string' ? msg : 'Login failed.');
      } else {
        setGlobalError('An unexpected error occurred.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-layout">
      {/* Brand Panel */}
      <div className="auth-brand-panel">
        <div className="brand-logo">
          <div className="brand-logo-icon">🎯</div>
          <div>
            <div className="brand-name">ResumeIQ</div>
            <div className="brand-tagline">AI Interview Coach</div>
          </div>
        </div>
        <div className="brand-headline">
          <h1>Welcome back, achiever</h1>
          <p>Your AI interview coach is ready to help you practise, improve, and land the role you deserve.</p>
          <div className="brand-features">
            <div className="brand-feature"><span className="brand-feature-dot" /> ATS-optimised resume scoring</div>
            <div className="brand-feature"><span className="brand-feature-dot" /> Real-time interview simulation</div>
            <div className="brand-feature"><span className="brand-feature-dot" /> Detailed performance reports</div>
            <div className="brand-feature"><span className="brand-feature-dot" /> Personalised improvement tips</div>
          </div>
        </div>
      </div>

      {/* Form Panel */}
      <div className="auth-form-panel">
        <div className="auth-form-container">
          <div className="auth-form-header">
            <h2>Sign in to ResumeIQ</h2>
            <p>Enter your credentials to access your dashboard.</p>
          </div>

          {globalError && <div className="alert alert-error">{globalError}</div>}

          <form onSubmit={handleSubmit} noValidate>
            <div className="form-group">
              <label className="form-label" htmlFor="email">Email Address</label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                className={`form-input${errors.email ? ' error' : ''}`}
                placeholder="you@example.com"
                value={form.email}
                onChange={handleChange}
              />
              {errors.email && <div className="form-error">{errors.email}</div>}
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="password">Password</label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                className={`form-input${errors.password ? ' error' : ''}`}
                placeholder="Your password"
                value={form.password}
                onChange={handleChange}
              />
              {errors.password && <div className="form-error">{errors.password}</div>}
            </div>

            <button
              id="login-submit"
              type="submit"
              className="btn btn-primary"
              disabled={isLoading}
            >
              {isLoading ? <><div className="spinner" /> Signing in…</> : 'Sign In'}
            </button>
          </form>

          <div className="auth-switch">
            Don't have an account? <Link to="/register">Create one</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
