// ==============================================================================
// ENUMS (Synchronized with Backend app/models/entities.py)
// ==============================================================================

export type UserRole = "ADMIN" | "INSTRUCTOR" | "STUDENT";

export type QuestionType = "SINGLE_CHOICE" | "MULTIPLE_CHOICE" | "TRUE_FALSE";

export type CognitiveLevel = "REMEMBER" | "UNDERSTAND" | "APPLY";

export type AttemptStatus =
  | "IN_PROGRESS"
  | "SUBMITTED"
  | "LOCKED_VIOLATION"
  | "EXPIRED";

export type QuestionSourceType = "MANUAL" | "FILE_PARSER" | "AI_GENERATED";

export type AntiCheatEventType =
  | "TAB_SWITCH"
  | "WINDOW_BLUR"
  | "COPY_PASTE_ATTEMPT";

// ==============================================================================
// ENTITY INTERFACES (Synchronized with Backend ERD Tables)
// ==============================================================================

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface Category {
  id: number;
  name: string;
  description?: string | null;
  created_by: number;
  created_at: string;
}

export interface QuestionOption {
  id: string; // e.g. "A", "B", "C", "D"
  text: string;
  is_correct: boolean;
}

export interface Question {
  id: number;
  category_id?: number | null;
  creator_id: number;
  content: string;
  question_type: QuestionType;
  cognitive_level: CognitiveLevel;
  options: QuestionOption[];
  explanation?: string | null;
  source_type: QuestionSourceType;
  created_at: string;
}

export interface ExamMatrixConfig {
  remember_ratio?: number;
  understand_ratio?: number;
  apply_ratio?: number;
  total_questions?: number;
}

export interface Exam {
  id: number;
  title: string;
  description?: string | null;
  instructor_id: number;
  duration_minutes: number;
  start_time?: string | null;
  end_time?: string | null;
  access_password?: string | null;
  max_attempts: number;
  max_tab_violations: number;
  shuffle_questions: boolean;
  shuffle_options: boolean;
  matrix_config?: ExamMatrixConfig | null;
  is_published: boolean;
  created_at: string;
}

export interface ExamQuestion {
  id: number;
  exam_id: number;
  question_id: number;
  order_index: number;
  points: number;
  question?: Question;
}

export interface ExamAttempt {
  id: number;
  exam_id: number;
  student_id: number;
  started_at: string;
  submitted_at?: string | null;
  score?: number | null;
  status: AttemptStatus;
  violation_count: number;
  question_order_snapshot?: any;
}

export interface AttemptAnswer {
  id: number;
  attempt_id: number;
  question_id: number;
  selected_options?: string[] | null;
  is_correct?: boolean | null;
  ai_tutor_feedback?: {
    explanation?: string;
    gap_analysis?: string;
    recommended_topics?: string[];
  } | null;
}

export interface AntiCheatLog {
  id: number;
  attempt_id: number;
  event_type: AntiCheatEventType;
  logged_at: string;
  metadata_info?: Record<string, any> | null;
}

// ==============================================================================
// API COMMON RESPONSES
// ==============================================================================

export interface ApiResponse<T = any> {
  success: boolean;
  message: string;
  data?: T;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  role: UserRole;
  full_name: string;
  user_id: number;
}
