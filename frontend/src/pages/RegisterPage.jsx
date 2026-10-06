/**
 * src/pages/RegisterPage.jsx
 */
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    full_name: '',
    email: '',
    password: '',
    password_confirm: '',
  });
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
    if (!form.full_name.trim()) errs.full_name = 'Full name is required.';
    if (!form.email) errs.email = 'Email is required.';
    else if (!/\S+@\S+\.\S+/.test(form.email)) errs.email = 'Enter a valid email.';
    if (!form.password) errs.password = 'Password is required.';
    else if (form.password.length < 8) errs.password = 'Password must be at least 8 characters.';
    if (form.password !== form.password_confirm) errs.password_confirm = 'Passwords do not match.';
    return errs;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }

    setIsLoading(true);
    try {
      await register(form);
      navigate('/dashboard');
    } catch (err) {
      const data = err.response?.data;
      if (data && typeof data === 'object') {
        // Map Django field errors back to form fields
        const fieldErrors = {};
        let hasFieldError = false;
        Object.entries(data).forEach(([key, val]) => {
          fieldErrors[key] = Array.isArray(val) ? val[0] : val;
          hasFieldError = true;
        });
        if (hasFieldError) setErrors(fieldErrors);
        else setGlobalError('Registration failed. Please try again.');
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
          <h1>Land your dream job with confidence</h1>
          <p>AI-powered resume analysis, mock interviews, and personalised coaching — all in one place.</p>
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
            <h2>Create your account</h2>
            <p>Start your interview preparation journey today.</p>
          </div>

          {globalError && <div className="alert alert-error">{globalError}</div>}

          <form onSubmit={handleSubmit} noValidate>
            <div className="form-group">
              <label className="form-label" htmlFor="full_name">Full Name</label>
              <input
                id="full_name"
                name="full_name"
                type="text"
                autoComplete="name"
                className={`form-input${errors.full_name ? ' error' : ''}`}
                placeholder="Prasad Kumar"
                value={form.full_name}
                onChange={handleChange}
              />
              {errors.full_name && <div className="form-error">{errors.full_name}</div>}
            </div>

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
                autoComplete="new-password"
                className={`form-input${errors.password ? ' error' : ''}`}
                placeholder="Min. 8 characters"
                value={form.password}
                onChange={handleChange}
              />
              {errors.password && <div className="form-error">{errors.password}</div>}
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="password_confirm">Confirm Password</label>
              <input
                id="password_confirm"
                name="password_confirm"
                type="password"
                autoComplete="new-password"
                className={`form-input${errors.password_confirm ? ' error' : ''}`}
                placeholder="Repeat your password"
                value={form.password_confirm}
                onChange={handleChange}
              />
              {errors.password_confirm && <div className="form-error">{errors.password_confirm}</div>}
            </div>

            <button
              id="register-submit"
              type="submit"
              className="btn btn-primary"
              disabled={isLoading}
            >
              {isLoading ? <><div className="spinner" /> Creating account…</> : 'Create Account'}
            </button>
          </form>

          <div className="auth-switch">
            Already have an account? <Link to="/login">Sign in</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
