export const AUTH_TOKEN_KEY = 'chilan_token';
export const AUTH_USER_ID_KEY = 'chilan_user_id';
export const AUTH_USER_EMAIL_KEY = 'chilan_user_email';

function decodeJwtPayload(token) {
  try {
    const [, payload] = token.split('.');
    if (!payload) return null;
    const normalized = payload.replace(/-/g, '+').replace(/_/g, '/');
    const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, '=');
    return JSON.parse(window.atob(padded));
  } catch {
    return null;
  }
}

export function clearAuthStorage() {
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(AUTH_USER_ID_KEY);
  localStorage.removeItem(AUTH_USER_EMAIL_KEY);
}

export function isTokenExpired(token, skewSeconds = 30) {
  if (!token) return true;
  const payload = decodeJwtPayload(token);
  if (!payload || !payload.exp) return false;
  const now = Math.floor(Date.now() / 1000);
  return payload.exp <= now + skewSeconds;
}

export function getValidToken() {
  const token = localStorage.getItem(AUTH_TOKEN_KEY);
  if (!token) return null;
  if (isTokenExpired(token)) {
    clearAuthStorage();
    return null;
  }
  return token;
}

export function getAuthState() {
  const token = getValidToken();
  return {
    token,
    isLoggedIn: !!token,
    userId: token ? localStorage.getItem(AUTH_USER_ID_KEY) : null,
    userEmail: token ? localStorage.getItem(AUTH_USER_EMAIL_KEY) : null,
  };
}
