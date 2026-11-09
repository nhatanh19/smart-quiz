import { apiClient } from "@/lib/apiClient";
import { ApiResponse } from "@/types";

export interface ExamInfo {
  id: string; title: string; exam_code: string; description: string | null;
  start_time: string; end_time: string; duration_minutes: number; max_attempts: number;
  is_published: boolean; requires_pin: boolean;
}
export interface AttemptInfo {
  attempt_id: string; exam_id: string; expires_at: string;
  questions: { question_id: string; content: string; question_type: string; options: { id: string; text: string }[] }[];
}
export async function examGet<T>(path: string): Promise<T> {
  return (await apiClient.get<ApiResponse<T>>(`/exam-engine${path}`)).data.data!;
}
export async function examPost<T>(path: string, payload?: unknown): Promise<T> {
  return (await apiClient.post<ApiResponse<T>>(`/exam-engine${path}`, payload)).data.data!;
}
