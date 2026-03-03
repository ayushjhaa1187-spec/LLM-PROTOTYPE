/**
 * Shared API helper: handles JWT tokens, auth headers, and API calls.
 */

const TOKEN_KEY = "far_copilot_token";
const USER_KEY = "far_copilot_user";

export function getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
}

export function getUser(): any | null {
    const raw = localStorage.getItem(USER_KEY);
    if (!raw) return null;
    try {
        return JSON.parse(raw);
    } catch {
        return null;
    }
}

export function setAuth(token: string, user: any) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearAuth() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
}

export function isAuthenticated(): boolean {
    const token = getToken();
    if (!token) return false;

    try {
        const payload = JSON.parse(atob(token.split(".")[1]));
        if (payload.exp && Date.now() >= payload.exp * 1000) {
            clearAuth();
            return false;
        }
        return true;
    } catch {
        return !!token;
    }
}

/** Authenticated fetch wrapper. Auto-adds Bearer token, handles 401. */
export async function apiFetch(
    url: string,
    options: RequestInit = {}
): Promise<Response> {
    const token = getToken();
    const headers: Record<string, string> = {
        ...(options.headers as Record<string, string> || {}),
    };

    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    // Don't set Content-Type for FormData (browser sets boundary automatically)
    if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
        headers["Content-Type"] = "application/json";
    }

    const baseUrl = import.meta.env.VITE_API_URL || "";
    const fetchUrl = url.startsWith("http") ? url : `${baseUrl}${url}`;

    const res = await fetch(fetchUrl, { ...options, headers });

    if (res.status === 401) {
        clearAuth();
        window.location.href = "/login";
    }

    return res;
}
