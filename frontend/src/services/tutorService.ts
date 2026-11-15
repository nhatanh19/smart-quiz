import { apiClient } from "@/lib/apiClient";
import { ApiResponse } from "@/types";

export interface AITutorFeedback {
  version?: number;
  explanation: string;
  why_selected_wrong: string;
  study_suggestions: string[];
  model?: string;
  generated_at?: string;
}

export interface AITutorExplanationData {
  attempt_id?: string;
  question_id?: string;
  is_correct?: boolean;
  selected_options: string[];
  correct_options: string[];
  feedback: AITutorFeedback;
  cached: boolean;
  response_time_ms: number;
}

export interface ExplanationRequestParams {
  attempt_id?: string;
  question_id?: string;
  question_content?: string;
  question_type?: string;
  options?: Array<{ id: string; text: string; is_correct?: boolean }>;
  selected_options?: string[];
  correct_options?: string[];
  question_explanation?: string;
}

export interface ReviewQuestionOption {
  id: string;
  text: string;
  is_correct: boolean;
}

export interface ReviewQuestionItem {
  id: string; // maps to question_id
  question_id?: string;
  content: string;
  question_type: string;
  cognitive_level: string;
  options: ReviewQuestionOption[];
  selected_options: string[];
  correct_options: string[];
  is_correct: boolean;
  points_awarded: number;
  explanation_note?: string;
  ai_feedback?: AITutorFeedback;
  response_time_ms?: number;
  order_index?: number;
}

export interface ExamReviewData {
  attempt_id: string;
  exam_id: string;
  exam_title: string;
  student_id: string;
  student_name?: string;
  score: number;
  max_score: number;
  status: string;
  started_at?: string;
  submitted_at?: string;
  time_spent_seconds: number;
  total_questions: number;
  correct_count: number;
  incorrect_count: number;
  questions_review: Array<{
    question_id: string;
    content: string;
    question_type: string;
    cognitive_level: string;
    options: ReviewQuestionOption[];
    selected_options: string[];
    correct_options: string[];
    is_correct: boolean;
    points_awarded: number;
    explanation?: string;
    ai_tutor_feedback?: AITutorFeedback;
    order_index: number;
  }>;
}

// ==============================================================================
// ISSUE #17: KNOWLEDGE GAP DIAGNOSTIC TYPES (WBS 5.2.2)
// ==============================================================================

export interface WeakTopicItem {
  topic: string;
  wrong_count: number;
  total_questions: number;
  accuracy_percentage: number;
  question_ids: string[];
  cognitive_levels?: string[];
}

export interface ActionableStudyAdvice {
  title: string;
  description: string;
  action_type: string;
  priority: string;
  resource_hint?: string;
}

export interface KnowledgeGapData {
  attempt_id: string;
  exam_id: string;
  summary_headline: string; // e.g. "Chủ đề bạn cần củng cố: Kế thừa & Đa hình trong OOP"
  primary_weak_topic?: string;
  has_gaps: boolean;
  total_wrong: number;
  total_questions: number;
  weak_topics: WeakTopicItem[];
  advice: ActionableStudyAdvice[];
  generated_at: string;
}

export const tutorService = {
  /**
   * Request an AI Tutor explanation for a question (or retrieve cached from DB).
   * No client-side mocks: errors propagate so the UI can surface the real failure.
   */
  async getExplanation(params: ExplanationRequestParams): Promise<AITutorExplanationData> {
    const response = await apiClient.post<ApiResponse<AITutorExplanationData>>(
      "/tutor-analytics/explain",
      params
    );
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || "Không thể sinh lời giải thích từ AI Tutor.");
  },

  /**
   * Request explanation for a specific question within an attempt.
   */
  async explainAttemptQuestion(attemptId: string, questionId: string): Promise<AITutorExplanationData> {
    const response = await apiClient.post<ApiResponse<AITutorExplanationData>>(
      `/tutor-analytics/attempts/${attemptId}/questions/${questionId}/explain`
    );
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || "Failed to generate AI Tutor explanation");
  },

  /**
   * Get full review data for an attempt (Issue #15, WBS 5.1.2).
   */
  async getAttemptReview(attemptId: string): Promise<ExamReviewData> {
    const response = await apiClient.get<ApiResponse<ExamReviewData>>(`/tutor-analytics/review/${attemptId}`);
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || "Không thể tải dữ liệu xem lại bài thi.");
  },

  /**
   * Diagnose student knowledge gaps & get actionable study advice (Issue #17, WBS 5.2.2).
   */
  async getKnowledgeGaps(attemptId: string): Promise<KnowledgeGapData> {
    const response = await apiClient.get<ApiResponse<KnowledgeGapData>>(`/tutor-analytics/knowledge-gaps/${attemptId}`);
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || "Không thể tải chẩn đoán lỗ hổng kiến thức từ AI Tutor.");
  },
};
