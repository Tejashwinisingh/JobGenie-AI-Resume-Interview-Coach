/**
 * src/utils/tokenStorage.js
 * Centralised helpers for JWT token persistence in localStorage.
 */

const ACCESS_KEY = 'resumeiq_access';
const REFRESH_KEY = 'resumeiq_refresh';

export const tokenStorage = {
  getAccess: () => localStorage.getItem(ACCESS_KEY),
  getRefresh: () => localStorage.getItem(REFRESH_KEY),

  setTokens: ({ access, refresh }) => {
    localStorage.setItem(ACCESS_KEY, access);
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
  },

  clearTokens: () => {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },

  hasTokens: () => !!localStorage.getItem(ACCESS_KEY),
};
