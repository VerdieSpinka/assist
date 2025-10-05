import i1n from '../i18n';
import { BASE_API_URL } from '../constants';

// --- 1. Constants ---
const ACCESS_TOKEN_KEY = 'jaaz_access_token';
const USER_INFO_KEY = 'jaaz_user_info';

// --- 2. Custom Error Class ---
export class ApiError extends Error {
  status: number;
  details: any;

  constructor(message: string, status: number, details: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

// --- 3. Interfaces ---
export interface UserInfo {
  id: number;
  username: string;
  email: string;
  role: string;
  image_url?: string; // Menambahkan field opsional untuk avatar
}

export interface AuthStatus {
  is_logged_in: boolean;
  user_info?: UserInfo;
  tokenExpired?: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user_info: UserInfo;
}

export interface RegisterPayload extends Pick<UserInfo, 'username' | 'email'> {
  password: string;
}

// --- 4. Low-Level Storage Helpers (dibuat private) ---
function saveAuthData(token: string, userInfo: UserInfo): void {
  try {
    localStorage.setItem(ACCESS_TOKEN_KEY, token);
    localStorage.setItem(USER_INFO_KEY, JSON.stringify(userInfo));
  } catch (error) {
    console.error("Failed to save auth data to localStorage:", error);
  }
}

function getAccessToken(): string | null {
  try {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  } catch (error) {
    console.error("Failed to get access token from localStorage:", error);
    return null;
  }
}

function clearAuthData(): void {
  try {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(USER_INFO_KEY);
  } catch (error) {
    console.error("Failed to clear auth data from localStorage:", error);
  }
}

// --- 5. Core API Wrappers ---
async function fetchWrapper(url: string, options: RequestInit = {}): Promise<Response> {
  const response = await fetch(url, options);

  if (!response.ok) {
    const errorDetails = await response.json().catch(() => ({ detail: 'An unknown server error occurred.' }));
    throw new ApiError(
      errorDetails.detail || 'An error occurred',
      response.status,
      errorDetails
    );
  }
  return response;
}

export async function authenticatedFetch(endpoint: string, options: RequestInit = {}): Promise<Response> {
  const token = getAccessToken();
  const headers = new Headers(options.headers || {});
  
  if (!headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  
  // Memastikan endpoint diawali dengan '/' untuk konsistensi
  const apiUrl = `${BASE_API_URL}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;
  return fetchWrapper(apiUrl, { ...options, headers });
}

// --- 6. Public API Functions ---

export async function registerUser(payload: RegisterPayload): Promise<UserInfo> {
  // Registrasi tidak terotentikasi, jadi gunakan fetchWrapper langsung
  const response = await fetchWrapper(`${BASE_API_URL}/api/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return response.json();
}

export async function loginUser(username: string, password: string): Promise<TokenResponse> {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);

  // Login tidak terotentikasi
  const response = await fetchWrapper(`${BASE_API_URL}/api/auth/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: formData,
  });

  const data: TokenResponse = await response.json();
  // Fungsi login sekarang bertanggung jawab untuk menyimpan data
  saveAuthData(data.access_token, data.user_info);
  return data;
}

export async function getAuthStatus(): Promise<AuthStatus> {
  const token = getAccessToken();
  if (!token) {
    return { is_logged_in: false };
  }

  try {
    const response = await authenticatedFetch('api/auth/me');
    const userFromServer: UserInfo = await response.json();
    
    // Segarkan info pengguna di localStorage agar tetap sinkron
    localStorage.setItem(USER_INFO_KEY, JSON.stringify(userFromServer));

    return { is_logged_in: true, user_info: userFromServer };
  } catch (error) {
    if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
      // Token tidak valid atau kedaluwarsa
      clearAuthData();
      return { is_logged_in: false, tokenExpired: true };
    }
    
    // Tangani kasus offline: asumsikan pengguna login dengan data cache
    console.warn("Could not validate token online, assuming offline but logged in.", error);
    const userInfoStr = localStorage.getItem(USER_INFO_KEY);
    try {
      if (userInfoStr) {
        const userInfo: UserInfo = JSON.parse(userInfoStr);
        return { is_logged_in: true, user_info: userInfo };
      }
    } catch {
      // Data di localStorage rusak
      clearAuthData();
      return { is_logged_in: false };
    }
    
    // Default ke logout jika semua gagal
    clearAuthData();
    return { is_logged_in: false };
  }
}

export function logoutUser(): void {
  clearAuthData();
}