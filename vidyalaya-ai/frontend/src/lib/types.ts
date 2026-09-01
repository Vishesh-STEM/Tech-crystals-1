export type Role = "student" | "teacher" | "admin";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: Role;
  avatar_emoji?: string;
  theme?: string;
  is_active: boolean;
}

export interface StudentProfile {
  id: number;
  class_level: string;
  stream?: string;
  school?: string;
  roll_number?: string;
  guardian_name?: string;
  phone?: string;
  daily_goal_minutes?: number;
  current_academic_year_id?: number | null;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
  student?: StudentProfile | null;
  academic_year?: string | null;
}

export interface SubjectProgress {
  subject_id: number;
  subject_name: string;
  subject_slug: string;
  icon: string;
  color: string;
  mastery: number;
  topics_total: number;
  topics_started: number;
  topics_mastered: number;
  weak_topics: number;
  study_minutes: number;
  last_activity_at?: string | null;
}

export interface TopicMastery {
  topic_id: number;
  topic_name: string;
  chapter_id: number;
  chapter_name: string;
  subject_id: number;
  subject_name: string;
  mastery: number;
  attempts: number;
  last_score?: number | null;
  average_score?: number | null;
  trend: number;
  is_weak: boolean;
  weakness_confidence: string;
  weakness_reason: string;
  last_activity_at?: string | null;
}

export interface Recommendation {
  id: number;
  kind: string;
  title: string;
  reason: string;
  priority: number;
  estimated_minutes: number;
  action_label: string;
  action_url: string;
  status: string;
  subject_id?: number | null;
  topic_id?: number | null;
  quiz_id?: number | null;
  created_at: string;
}

export interface LearningProfile {
  text_effectiveness: number;
  visual_effectiveness: number;
  audio_effectiveness: number;
  practice_effectiveness: number;
  samples: Record<string, number>;
  strongest_format: string;
  weakest_format: string;
  preferred_difficulty: string;
  average_session_minutes: number;
  study_streak_days: number;
  note?: string;
  evidence?: Record<string, any>;
  student?: Record<string, any>;
}

export interface Dashboard {
  greeting: string;
  student_name: string;
  academic_year: string;
  overall_mastery: number;
  subjects: SubjectProgress[];
  needs_attention: TopicMastery[];
  recommended_today: Recommendation[];
  continue_learning: any[];
  stats: Record<string, number>;
  learning_profile: LearningProfile;
  monthly_progress: { period: string; label: string; mastery: number }[];
  ai_status: { mode: string; detail: string };
}

export interface QuizQuestion {
  id: number;
  topic_id: number;
  chapter_id: number;
  subject_id: number;
  type: string;
  difficulty: string;
  text: string;
  options: string[];
  marks: number;
  concept_tag: string;
}

export interface AttemptResult {
  attempt_id: number;
  quiz_id: number;
  quiz_title: string;
  attempt_number: number;
  score: number;
  max_score: number;
  accuracy: number;
  passed: boolean;
  duration_seconds: number;
  topic_breakdown: Record<string, any>;
  difficulty_breakdown: Record<string, any>;
  answers: any[];
  mastery_updates: any[];
  new_recommendations: any[];
}

export interface ChatMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  mode?: string;
  model?: string;
  sources?: any[];
  topic_id?: number | null;
  created_at: string;
}

export interface ChatResponse {
  session_id: number;
  message: ChatMessage;
  sources: any[];
  mode: string;
  model: string;
  detected_subject?: string | null;
  detected_topic?: string | null;
  suggestions: string[];
  latency_ms: number;
}
