import { createContext, useCallback, useContext, useEffect, useMemo, useState, ReactNode } from "react";
import { endpoints, getToken, setToken } from "../lib/api";
import type { AuthResponse, StudentProfile, User } from "../lib/types";

interface AuthState {
  user: User | null;
  student: StudentProfile | null;
  academicYear: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<User>;
  register: (payload: Record<string, unknown>) => Promise<User>;
  logout: () => void;
  refresh: () => Promise<void>;
  applyAuth: (data: AuthResponse) => void;
}

const AuthContext = createContext<AuthState>({} as AuthState);

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [student, setStudent] = useState<StudentProfile | null>(null);
  const [academicYear, setAcademicYear] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const applyAuth = useCallback((data: AuthResponse) => {
    if (data.access_token) setToken(data.access_token);
    setUser(data.user);
    setStudent(data.student ?? null);
    setAcademicYear(data.academic_year ?? null);
  }, []);

  const refresh = useCallback(async () => {
    if (!getToken()) {
      setLoading(false);
      return;
    }
    try {
      const data = await endpoints.me();
      applyAuth(data);
    } catch {
      setToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, [applyAuth]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const login = useCallback(
    async (email: string, password: string) => {
      const data = await endpoints.login(email, password);
      applyAuth(data);
      return data.user as User;
    },
    [applyAuth],
  );

  const register = useCallback(
    async (payload: Record<string, unknown>) => {
      const data = await endpoints.register(payload);
      applyAuth(data);
      return data.user as User;
    },
    [applyAuth],
  );

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    setStudent(null);
    setAcademicYear(null);
  }, []);

  const value = useMemo(
    () => ({ user, student, academicYear, loading, login, register, logout, refresh, applyAuth }),
    [user, student, academicYear, loading, login, register, logout, refresh, applyAuth],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
