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

// ==============================================================================
// ISSUE #36: LEARNING ANALYTICS & SCORE DISTRIBUTION TYPES (WBS 5.3)
// ==============================================================================

export interface StudentScoreTrendItem {
  attempt_id: string;
  exam_id: string;
  exam_title: string;
  attempt_number: number;
  score: number;
  started_at?: string;
  submitted_at?: string;
  time_spent_seconds: number;
  violation_count: number;
  status: string;
}

export interface TopicMasteryItem {
  category_id?: string;
  category_name: string;
  total_questions: number;
  correct_count: number;
  incorrect_count: number;
  accuracy_percentage: number;
  mastery_level: "EXCELLENT" | "GOOD" | "AVERAGE" | "NEEDS_IMPROVEMENT" | string;
}

export interface StudentKnowledgeGap {
  category_name: string;
  incorrect_count: number;
  accuracy_percentage: number;
  advice: string;
}

export interface StudentAnalyticsSummary {
  total_attempts: number;
  total_exams: number;
  average_score: number;
  highest_score: number;
  lowest_score: number;
  pass_rate: number;
}

export interface StudentAnalyticsData {
  student_id: string;
  student_name: string;
  student_email: string;
  summary: StudentAnalyticsSummary;
  trends: StudentScoreTrendItem[];
  topics_mastery: TopicMasteryItem[];
  knowledge_gaps: StudentKnowledgeGap[];
}

export interface ScoreDistributionBin {
  bin_label: string;
  min_score: number;
  max_score: number;
  count: number;
  percentage: number;
}

export interface DifficultQuestionItem {
  question_id: string;
  content: string;
  question_type: string;
  category_name?: string;
  total_responses: number;
  wrong_count: number;
  correct_count: number;
  incorrect_rate: number;
}

export interface StudentScoreRecord {
  student_id: string;
  student_name: string;
  student_email: string;
  attempt_id: string;
  attempt_number: number;
  score: number;
  submitted_at?: string;
  time_spent_seconds: number;
  violation_count: number;
  status: string;
}

export interface ExamAnalyticsSummary {
  total_attempts: number;
  total_students: number;
  min_score: number;
  max_score: number;
  avg_score: number;
  median_score: number;
  pass_count: number;
  fail_count: number;
  pass_rate: number;
  standard_deviation: number;
}

export interface ExamAnalyticsData {
  exam_id: string;
  exam_code: string;
  exam_title: string;
  duration_minutes: number;
  total_questions: number;
  summary: ExamAnalyticsSummary;
  score_distribution: ScoreDistributionBin[];
  grade_distribution: ScoreDistributionBin[];
  difficult_questions: DifficultQuestionItem[];
  student_scores: StudentScoreRecord[];
}

export interface AccessibleExam {
  id: string;
  exam_code: string;
  title: string;
  duration_minutes: number;
  created_at?: string;
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
   * Get student learning progress and topic mastery analytics (Issue #36, WBS 5.3.1).
   */
  async getStudentAnalytics(studentId: string = "me"): Promise<StudentAnalyticsData> {
    const response = await apiClient.get<ApiResponse<StudentAnalyticsData>>(
      `/tutor-analytics/analytics/student/${studentId}`
    );
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || "Không thể tải dữ liệu phân tích học tập sinh viên.");
  },

  /**
   * Get exam score distribution, histogram, and student scores (Issue #36, WBS 5.3.2).
   */
  async getExamAnalytics(examId: string): Promise<ExamAnalyticsData> {
    const response = await apiClient.get<ApiResponse<ExamAnalyticsData>>(
      `/tutor-analytics/analytics/exam/${examId}`
    );
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || "Không thể tải dữ liệu phổ điểm đề thi.");
  },

  /**
   * List accessible exams for the instructor selector.
   */
  async getInstructorExams(): Promise<AccessibleExam[]> {
    const response = await apiClient.get<ApiResponse<AccessibleExam[]>>(
      "/tutor-analytics/analytics/instructor/exams"
    );
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    return [];
  },

  /**
   * Trigger CSV download for an exam scoresheet.
   */
  async downloadExamCsv(examId: string, examCode: string = "exam"): Promise<void> {
    try {
      const response = await apiClient.get(`/tutor-analytics/analytics/exam/${examId}/csv`, {
        responseType: "blob",
      });
      const blob = new Blob([response.data], { type: "text/csv;charset=utf-8;" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `bang_diem_${examCode}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      throw new Error("Không thể tải xuống tệp CSV bảng điểm.");
    }
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
