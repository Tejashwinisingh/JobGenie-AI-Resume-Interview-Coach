/**
 * src/hooks/useAuth.js
 * Convenience hook that reads from AuthContext.
 */
import { useContext } from 'react';
import { AuthContext } from '../context/AuthContextObject';

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used inside <AuthProvider>');
  }
  return ctx;
}
