/**
 * src/context/AuthContext.jsx
 * Global authentication state using React Context.
 * Provides: user, isAuthenticated, isLoading, login, register, logout, updateProfile
 */
import { useState, useEffect, useCallback } from 'react';
import { AuthContext } from './AuthContextObject';
import { authApi } from '../api/authApi';
import { tokenStorage } from '../utils/tokenStorage';

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true); // true until initial auth check completes

  // ── Restore session on mount ───────────────────────────────────────────────
  useEffect(() => {
    const restoreSession = async () => {
      if (tokenStorage.hasTokens()) {
        try {
          const { data } = await authApi.getProfile();
          setUser(data);
        } catch {
          tokenStorage.clearTokens();
        }
      }
      setIsLoading(false);
    };
    restoreSession();
  }, []);

  // ── Auth actions ───────────────────────────────────────────────────────────
  const register = useCallback(async (formData) => {
    const { data } = await authApi.register(formData);
    tokenStorage.setTokens(data.tokens);
    setUser(data.user);
    return data;
  }, []);

  const login = useCallback(async (credentials) => {
    const { data } = await authApi.login(credentials);
    tokenStorage.setTokens(data.tokens);
    setUser(data.user);
    return data;
  }, []);

  const logout = useCallback(async () => {
    const refresh = tokenStorage.getRefresh();
    try {
      if (refresh) await authApi.logout(refresh);
    } catch {
      // Proceed even if blacklist call fails
    } finally {
      tokenStorage.clearTokens();
      setUser(null);
    }
  }, []);

  const updateProfile = useCallback(async (profileData) => {
    const { data } = await authApi.updateProfile(profileData);
    setUser(data.user);
    return data;
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
        updateProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
