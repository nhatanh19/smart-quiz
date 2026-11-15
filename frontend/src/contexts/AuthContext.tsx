import { createContext, useCallback, useContext, useRef, useState, ReactNode } from "react";
import axios from "axios";
import { AUTH_REQUEST_TIMEOUT_MS, apiClient, authError, logoutSession } from "@/lib/apiClient";
import { ApiResponse, User } from "@/types";

interface AuthState {
  user: User | null;
  loading: boolean;
  error: string;
}

interface AuthContextValue extends AuthState {
  ensureSession: () => Promise<void>;
  login: (credentials: { email: string; password: string }) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({ user: null, loading: true, error: "" });
  const checked = useRef(false);
  const pending = useRef<Promise<void> | null>(null);
  const revision = useRef(0);

  const ensureSession = useCallback(() => {
    if (checked.current) return Promise.resolve();
    if (pending.current) return pending.current;
    const currentRevision = revision.current;
    pending.current = apiClient.get<ApiResponse<User>>("/auth/me", { timeout: AUTH_REQUEST_TIMEOUT_MS }).then(({ data }) => {
      if (currentRevision !== revision.current) return;
      checked.current = true;
      setState({ user: data.data!, loading: false, error: "" });
    }).catch(error => {
      if (currentRevision !== revision.current) return;
      const unauthorized = axios.isAxiosError(error) && error.response?.status === 401;
      checked.current = unauthorized;
      setState({ user: null, loading: false, error: unauthorized ? "" : authError(error) });
    }).finally(() => { pending.current = null; });
    return pending.current;
  }, []);

  const login = useCallback(async (credentials: { email: string; password: string }) => {
    const { data } = await apiClient.post<ApiResponse<User>>("/auth/login", credentials);
    revision.current += 1;
    checked.current = true;
    setState({ user: data.data!, loading: false, error: "" });
  }, []);

  const logout = useCallback(async () => {
    await logoutSession();
    revision.current += 1;
    checked.current = true;
    setState({ user: null, loading: false, error: "" });
  }, []);

  return <AuthContext.Provider value={{ ...state, ensureSession, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}
