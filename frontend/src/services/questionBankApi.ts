import axios from "axios";
import type {
  ApiResponse,
  Category,
  CognitiveLevel,
  Question,
  QuestionLevel,
  QuestionOption,
  QuestionType,
  Subject,
} from "@/types";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1",
});

api.interceptors.request.use((config) => {
  const token =
    localStorage.getItem("access_token") || localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface QuestionListParams {
  skip: number;
  limit: number;
  keyword?: string;
  subject_id?: string;
  category_id?: string;
  level?: QuestionLevel;
  cognitive_level?: CognitiveLevel;
  tag?: string;
}

export interface QuestionPayload {
  category_id: string;
  content: string;
  question_type: QuestionType;
  cognitive_level: CognitiveLevel;
  level: QuestionLevel;
  options: QuestionOption[];
  tags: string[];
  explanation: string | null;
}

async function getData<T>(path: string) {
  const response = await api.get<ApiResponse<T>>(path);
  return response.data.data ?? [];
}

export const isRequestCancelled = (error: unknown) => axios.isCancel(error);

export function listQuestions(
  params: QuestionListParams,
  signal?: AbortSignal,
): Promise<ApiResponse<Question[]>> {
  return api
    .get<ApiResponse<Question[]>>("/parser/questions", { params, signal })
    .then(({ data }) => data);
}

export async function listSubjects(): Promise<Subject[]> {
  return getData<Subject[]>("/parser/subjects");
}

export async function listCategories(): Promise<Category[]> {
  return getData<Category[]>("/parser/categories");
}

export async function createQuestion(payload: QuestionPayload): Promise<void> {
  await api.post("/parser/questions", payload);
}

export async function updateQuestion(
  questionId: string,
  payload: QuestionPayload,
): Promise<void> {
  await api.patch(`/parser/questions/${questionId}`, payload);
}

export async function deleteQuestion(questionId: string): Promise<void> {
  await api.delete(`/parser/questions/${questionId}`);
}

export async function createSubject(payload: {
  name: string;
  description: string | null;
}): Promise<ApiResponse<Subject>> {
  const response = await api.post<ApiResponse<Subject>>("/parser/subjects", payload);
  return response.data;
}

export async function createCategory(payload: {
  name: string;
  description: string | null;
  subject_id: string;
}): Promise<ApiResponse<Category>> {
  const response = await api.post<ApiResponse<Category>>(
    "/parser/categories",
    payload,
  );
  return response.data;
}

export async function assignCategorySubject(
  categoryId: string,
  subjectId: string,
): Promise<void> {
  await api.patch(`/parser/categories/${categoryId}`, { subject_id: subjectId });
}
