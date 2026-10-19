// ==============================================================================
// ENUMS (Synchronized with Backend app/models/entities.py & PostgreSQL types)
// ==============================================================================

export type UserRole = "ADMIN" | "INSTRUCTOR" | "STUDENT";

export type QuestionType = "SINGLE_CHOICE" | "MULTIPLE_CHOICE" | "TRUE_FALSE";

export type CognitiveLevel = "REMEMBER" | "UNDERSTAND" | "APPLY";

export type AttemptStatus =
  | "IN_PROGRESS"
  | "SUBMITTED"
  | "LOCKED_VIOLATION"
  | "EXPIRED";

export type QuestionSource = "MANUAL" | "FILE_PARSER" | "AI_GENERATED";
export type QuestionSourceType = QuestionSource;

export type AntiCheatEventType =
  | "TAB_SWITCH"
  | "WINDOW_BLUR"
  | "COPY_PASTE_ATTEMPT"
  | "DEVTOOLS_SHORTCUT";

// ==============================================================================
// ENTITY INTERFACES (Synchronized with Backend PostgreSQL UUID Tables)
// ==============================================================================

export interface User {
  id: string; // UUID
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Category {
  id: string; // UUID
  name: string;
  description?: string | null;
  created_by: string; // UUID -> User.id
  created_at: string;
  updated_at: string;
}

export interface QuestionOption {
  id: string; // e.g. "A", "B", "C", "D"
  text: string;
  is_correct: boolean;
}

export interface Question {
  id: string; // UUID
  category_id: string; // UUID -> Category.id
  creator_id: string; // UUID -> User.id
  content: string;
  question_type: QuestionType;
  cognitive_level: CognitiveLevel;
  options: QuestionOption[];
  explanation?: string | null;
  source_type: QuestionSource;
  created_at: string;
  updated_at: string;
}

export interface ExamMatrixConfig {
  version?: number;
  total_questions?: number;
  category_ids?: string[];
  cognitive_distribution?: {
    REMEMBER?: number;
    UNDERSTAND?: number;
    APPLY?: number;
  };
  type_distribution?: {
    SINGLE_CHOICE?: number;
    MULTIPLE_CHOICE?: number;
    TRUE_FALSE?: number;
  };
}

export interface Exam {
  id: string; // UUID
  exam_code: string;
  title: string;
  description?: string | null;
  instructor_id: string; // UUID -> User.id
  duration_minutes: number;
  start_time?: string | null;
  end_time?: string | null;
  access_password_hash?: string | null;
  max_attempts: number;
  max_tab_violations: number;
  shuffle_questions: boolean;
  shuffle_options: boolean;
  matrix_config?: ExamMatrixConfig | Record<string, any> | null;
  is_published: boolean;
  created_at: string;
  updated_at: string;
}

export interface ExamQuestion {
  id: string; // UUID
  exam_id: string; // UUID -> Exam.id
  question_id: string; // UUID -> Question.id
  order_index: number;
  points: number;
  question?: Question;
}

export interface ExamAttempt {
  id: string; // UUID
  exam_id: string; // UUID -> Exam.id
  student_id: string; // UUID -> User.id
  attempt_number: number;
  started_at: string;
  expires_at: string;
  submitted_at?: string | null;
  score?: number | null;
  status: AttemptStatus;
  violation_count: number;
  question_order_snapshot: {
    version: number;
    questions: Array<{
      question_id: string;
      options_order: string[];
    }>;
  };
}

export interface AttemptAnswer {
  id: string; // UUID
  attempt_id: string; // UUID -> ExamAttempt.id
  question_id: string; // UUID -> Question.id
  selected_options: string[];
  is_correct?: boolean | null;
  points_awarded?: number | null;
  ai_tutor_feedback?: {
    version?: number;
    explanation?: string;
    why_selected_wrong?: string;
    study_suggestions?: string[];
    model?: string;
    generated_at?: string;
  } | null;
}

export interface AntiCheatLog {
  id: string; // UUID
  attempt_id: string; // UUID -> ExamAttempt.id
  event_type: string; // TAB_SWITCH, WINDOW_BLUR, COPY_PASTE_ATTEMPT, DEVTOOLS_SHORTCUT
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
  user_id: string; // UUID
}
