import axios from 'axios';
import { Platform } from 'react-native';

const normalizeApiBaseURL = (rawUrl: string) => {
  const cleaned = rawUrl.trim().replace(/\/+$/, '');
  if (cleaned.endsWith('/api')) {
    return cleaned;
  }
  return `${cleaned}/api`;
};

export const getApiBaseURL = () => {
  if (process.env.EXPO_PUBLIC_API_URL) {
    return normalizeApiBaseURL(process.env.EXPO_PUBLIC_API_URL);
  }
  return Platform.OS === 'android' ? 'http://10.0.2.2:8000/api' : 'http://localhost:8000/api';
};

export const getApiOrigin = () => getApiBaseURL().replace(/\/api$/, '');

const getBaseURL = () => {
  return getApiBaseURL();
};

const api = axios.create({
  baseURL: getBaseURL(),
  headers: {
    'Content-Type': 'application/json',
  },
});

let handlingUnauthorized = false;
let refreshPromise: Promise<string | null> | null = null;

const isAuthEndpoint = (url?: string) =>
  !!url &&
  (url.includes('/users/login/') ||
    url.includes('/users/register/') ||
    url.includes('/users/refresh-token/'));

const TOKEN_KEY = 'bomoko_token';
const REFRESH_KEY = 'bomoko_refresh';

let SecureStore: any = null;
let isInitialized = false;

const ensureInitialized = async () => {
  if (isInitialized) return;
  if (Platform.OS !== 'web') {
    try {
      SecureStore = await import('expo-secure-store');
    } catch {}
  }
  isInitialized = true;
};

const getWebStorage = (): Storage | null => {
  if (typeof window === 'undefined') return null;
  try {
    return window.sessionStorage;
  } catch {
    try {
      return window.localStorage;
    } catch {
      return null;
    }
  }
};

export const getAuthToken = async (): Promise<string | null> => {
  await ensureInitialized();
  if (Platform.OS !== 'web' && SecureStore) {
    return await SecureStore.getItemAsync(TOKEN_KEY);
  }
  return getWebStorage()?.getItem(TOKEN_KEY) ?? null;
};

export const getRefreshToken = async (): Promise<string | null> => {
  await ensureInitialized();
  if (Platform.OS !== 'web' && SecureStore) {
    return await SecureStore.getItemAsync(REFRESH_KEY);
  }
  return getWebStorage()?.getItem(REFRESH_KEY) ?? null;
};

export const setAuthToken = async (token: string | null) => {
  await ensureInitialized();
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common['Authorization'];
  }

  if (Platform.OS !== 'web' && SecureStore) {
    if (token) await SecureStore.setItemAsync(TOKEN_KEY, token);
    else await SecureStore.deleteItemAsync(TOKEN_KEY);
  } else {
    const storage = getWebStorage();
    if (!storage) return;
    if (token) storage.setItem(TOKEN_KEY, token);
    else storage.removeItem(TOKEN_KEY);
  }
};

export const setRefreshToken = async (token: string | null) => {
  await ensureInitialized();
  if (Platform.OS !== 'web' && SecureStore) {
    if (token) await SecureStore.setItemAsync(REFRESH_KEY, token);
    else await SecureStore.deleteItemAsync(REFRESH_KEY);
  } else {
    const storage = getWebStorage();
    if (!storage) return;
    if (token) storage.setItem(REFRESH_KEY, token);
    else storage.removeItem(REFRESH_KEY);
  }
};

export const clearAllTokens = async () => {
  await setAuthToken(null);
  await setRefreshToken(null);
};

const redirectToWelcome = () => {
  if (Platform.OS === 'web' && typeof window !== 'undefined') {
    window.location.replace('/(auth)/welcome');
  }
};

const refreshAccessToken = async (): Promise<string | null> => {
  const refresh = await getRefreshToken();
  if (!refresh) {
    return null;
  }

  try {
    const response = await axios.post(`${getBaseURL()}/users/refresh-token/`, { refresh }, {
      headers: { 'Content-Type': 'application/json' },
    });
    const nextAccess = response.data?.access ?? null;
    if (!nextAccess) {
      return null;
    }
    await setAuthToken(nextAccess);
    if (response.data?.refresh) {
      await setRefreshToken(response.data.refresh);
    }
    return nextAccess;
  } catch {
    return null;
  }
};

api.interceptors.request.use(async (config) => {
  const token = await getAuthToken();
  config.headers = config.headers ?? {};
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  } else if ('Authorization' in config.headers) {
    delete config.headers.Authorization;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const status = error?.response?.status;
    const requestUrl: string | undefined = error?.config?.url;
    const originalRequest = error?.config;

    if (
      status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      !isAuthEndpoint(requestUrl)
    ) {
      originalRequest._retry = true;
      refreshPromise = refreshPromise ?? refreshAccessToken();
      const nextAccess = await refreshPromise;
      refreshPromise = null;

      if (nextAccess) {
        originalRequest.headers = originalRequest.headers ?? {};
        originalRequest.headers.Authorization = `Bearer ${nextAccess}`;
        return api(originalRequest);
      }
    }

    if (status === 401 && !isAuthEndpoint(requestUrl) && !handlingUnauthorized) {
      handlingUnauthorized = true;
      await clearAllTokens();
      redirectToWelcome();
      handlingUnauthorized = false;
    }

    return Promise.reject(error);
  }
);

const initializeAuth = async () => {
  const token = await getAuthToken();
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }
};

initializeAuth();

export default api;
