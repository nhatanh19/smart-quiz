import axios from "axios";
import { apiClient as api } from "@/lib/apiClient";
import type {
  ApiResponse,
  Category,
  CognitiveLevel,
  Question,
  QuestionLevel,
  QuestionOption,
  QuestionSource,
  QuestionType,
  Subject,
} from "@/types";

const questionBankPath = "/ai-generator/question-bank";

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
  source_type?: QuestionSource;
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
    .get<ApiResponse<Question[]>>(`${questionBankPath}/questions`, { params, signal })
    .then(({ data }) => data);
}

export async function listSubjects(): Promise<Subject[]> {
  return getData<Subject[]>(`${questionBankPath}/subjects`);
}

export async function listCategories(): Promise<Category[]> {
  return getData<Category[]>(`${questionBankPath}/categories`);
}

export async function createQuestion(payload: QuestionPayload): Promise<void> {
  await api.post(`${questionBankPath}/questions`, payload);
}

export async function updateQuestion(
  questionId: string,
  payload: QuestionPayload,
): Promise<void> {
  await api.patch(`${questionBankPath}/questions/${questionId}`, payload);
}

export async function deleteQuestion(questionId: string): Promise<void> {
  await api.delete(`${questionBankPath}/questions/${questionId}`);
}

export async function createSubject(payload: {
  name: string;
  description: string | null;
}): Promise<ApiResponse<Subject>> {
  const response = await api.post<ApiResponse<Subject>>(
    `${questionBankPath}/subjects`,
    payload,
  );
  return response.data;
}

export async function createCategory(payload: {
  name: string;
  description: string | null;
  subject_id: string;
}): Promise<ApiResponse<Category>> {
  const response = await api.post<ApiResponse<Category>>(
    `${questionBankPath}/categories`,
    payload,
  );
  return response.data;
}

export async function assignCategorySubject(
  categoryId: string,
  subjectId: string,
): Promise<void> {
  await api.patch(`${questionBankPath}/categories/${categoryId}`, {
    subject_id: subjectId,
  });
}
