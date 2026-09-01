import axios, { AxiosError } from "axios";

const baseURL = (import.meta.env.VITE_API_BASE_URL as string | undefined) || "";

export const api = axios.create({
  baseURL: `${baseURL}/api`,
  headers: { "Content-Type": "application/json" },
  timeout: 90000,
});

const TOKEN_KEY = "vidyalaya.token";

export function setToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<any>) => {
    if (error.response?.status === 401 && getToken()) {
      setToken(null);
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = "/login?expired=1";
      }
    }
    return Promise.reject(error);
  },
);

/** Turn any API/network failure into a readable sentence for a toast or error state. */
export function errorMessage(error: unknown, fallback = "Something went wrong. Please try again."): string {
  const axiosError = error as AxiosError<any>;
  const detail = axiosError?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length) return String(detail[0]?.msg ?? fallback);
  if (axiosError?.code === "ERR_NETWORK") {
    return "Cannot reach the Vidyalaya AI server. Is the backend running on port 8000?";
  }
  if (axiosError?.message) return axiosError.message;
  return fallback;
}

export const endpoints = {
  meta: () => api.get("/meta").then((r) => r.data),
  health: () => api.get("/health").then((r) => r.data),
  demoCredentials: () => api.get("/auth/demo-credentials").then((r) => r.data),

  login: (email: string, password: string) =>
    api.post("/auth/login", { email, password }).then((r) => r.data),
  register: (payload: Record<string, unknown>) =>
    api.post("/auth/register", payload).then((r) => r.data),
  me: () => api.get("/auth/me").then((r) => r.data),
  updateProfile: (payload: Record<string, unknown>) =>
    api.patch("/auth/me", payload).then((r) => r.data),
  changePassword: (current_password: string, new_password: string) =>
    api.post("/auth/change-password", { current_password, new_password }).then((r) => r.data),

  subjects: () => api.get("/subjects").then((r) => r.data),
  subject: (id: number | string) => api.get(`/subjects/${id}`).then((r) => r.data),
  chapter: (id: number | string) => api.get(`/chapters/${id}`).then((r) => r.data),
  topic: (id: number | string) => api.get(`/topics/${id}`).then((r) => r.data),
  resource: (id: number | string) => api.get(`/resources/${id}`).then((r) => r.data),
  topicQuestions: (id: number | string, limit = 8) =>
    api.get(`/topics/${id}/questions`, { params: { limit } }).then((r) => r.data),

  quizzes: (params: Record<string, unknown> = {}) =>
    api.get("/quizzes", { params }).then((r) => r.data),
  quiz: (id: number | string) => api.get(`/quiz/${id}`).then((r) => r.data),
  startAttempt: (id: number | string) => api.post(`/quiz/${id}/attempt`).then((r) => r.data),
  submitAttempt: (quizId: number | string, attemptId: number, payload: Record<string, unknown>) =>
    api.post(`/quiz/${quizId}/attempt/${attemptId}/submit`, payload).then((r) => r.data),
  attempt: (id: number | string) => api.get(`/attempts/${id}`).then((r) => r.data),

  dashboard: () => api.get("/student/dashboard").then((r) => r.data),
  progress: (academicYearId?: number) =>
    api.get("/student/progress", { params: academicYearId ? { academic_year_id: academicYearId } : {} })
      .then((r) => r.data),
  years: () => api.get("/student/years").then((r) => r.data),
  mastery: (subjectId?: number) =>
    api.get("/student/mastery", { params: subjectId ? { subject_id: subjectId } : {} }).then((r) => r.data),
  learningProfile: (recompute = false) =>
    api.get("/student/profile", { params: { recompute } }).then((r) => r.data),
  recommendations: (status = "pending", limit = 10) =>
    api.get("/student/recommendations", { params: { status, limit } }).then((r) => r.data),
  refreshRecommendations: () => api.post("/student/recommendations/refresh").then((r) => r.data),
  recommendationAction: (id: number, action: "complete" | "dismiss" | "open") =>
    api.post(`/student/recommendations/${id}/${action}`).then((r) => r.data),
  activity: (limit = 30) => api.get("/student/activity", { params: { limit } }).then((r) => r.data),
  trackActivity: (payload: Record<string, unknown>) =>
    api.post("/student/activity", payload).then((r) => r.data),
  heatmap: (days = 60) => api.get("/student/heatmap", { params: { days } }).then((r) => r.data),

  chat: (payload: Record<string, unknown>) => api.post("/chat", payload).then((r) => r.data),
  chatSessions: () => api.get("/chat/sessions").then((r) => r.data),
  chatHistory: (sessionId?: number) =>
    api.get("/chat/history", { params: sessionId ? { session_id: sessionId } : {} }).then((r) => r.data),
  deleteChatSession: (id: number) => api.delete(`/chat/sessions/${id}`).then((r) => r.data),
  chatStatus: () => api.get("/chat/status").then((r) => r.data),

  adminAnalytics: () => api.get("/admin/analytics").then((r) => r.data),
  adminStudents: (search?: string) =>
    api.get("/admin/students", { params: search ? { search } : {} }).then((r) => r.data),
  adminStudent: (id: number) => api.get(`/admin/students/${id}`).then((r) => r.data),
  adminSubjects: () => api.get("/admin/subjects").then((r) => r.data),
  adminChapters: (subjectId?: number) =>
    api.get("/admin/chapters", { params: subjectId ? { subject_id: subjectId } : {} }).then((r) => r.data),
  adminTopics: (params: Record<string, unknown> = {}) =>
    api.get("/admin/topics", { params }).then((r) => r.data),
  adminQuestions: (params: Record<string, unknown> = {}) =>
    api.get("/admin/questions", { params }).then((r) => r.data),
  adminQuizzes: (params: Record<string, unknown> = {}) =>
    api.get("/admin/quizzes", { params }).then((r) => r.data),
  adminResources: (topicId?: number) =>
    api.get("/admin/resources", { params: topicId ? { topic_id: topicId } : {} }).then((r) => r.data),
  create: (entity: string, payload: Record<string, unknown>) =>
    api.post(`/admin/${entity}`, payload).then((r) => r.data),
  update: (entity: string, id: number, payload: Record<string, unknown>) =>
    api.patch(`/admin/${entity}/${id}`, payload).then((r) => r.data),
  remove: (entity: string, id: number) => api.delete(`/admin/${entity}/${id}`).then((r) => r.data),
  reindex: () => api.post("/admin/reindex").then((r) => r.data),
};
