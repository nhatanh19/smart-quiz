import { apiClient as api } from "@/lib/apiClient";
import type {
  ApiResponse,
  CognitiveLevel,
  QuestionLevel,
  QuestionOption,
  QuestionType,
} from "@/types";

// ==============================================================================
// REQUEST / RESPONSE TYPES — AI Generator (Issue #32)
// ==============================================================================

export type BloomLevel = "REMEMBER" | "UNDERSTAND" | "APPLY";

export interface CognitiveRatios {
  REMEMBER: number;
  UNDERSTAND: number;
  APPLY: number;
}

export interface TypeRatios {
  SINGLE_CHOICE: number;
  MULTIPLE_CHOICE: number;
  TRUE_FALSE: number;
}

export interface MatrixRequest {
  topic: string;
  total_questions: number;
  cognitive_ratios: CognitiveRatios;
  type_ratios: TypeRatios;
}

export interface MatrixAllocation {
  cognitive_level: BloomLevel;
  question_type: QuestionType;
  count: number;
}

export interface MatrixPreviewData {
  topic: string;
  total_questions: number;
  cognitive_distribution: Record<BloomLevel, number>;
  type_distribution: Record<QuestionType, number>;
  allocations: MatrixAllocation[];
}

export interface GeneratedQuestionItem {
  /** Null until saved — will be populated from category dropdown */
  category_id: string | null;
  content: string;
  question_type: QuestionType;
  cognitive_level: CognitiveLevel;
  level: QuestionLevel;
  options: QuestionOption[];
  tags: string[];
  explanation: string | null;
  source_type: "AI_GENERATED";
}

export interface GenerateByMatrixData {
  total_requested: number;
  total_generated: number;
  generated_questions: GeneratedQuestionItem[];
  cognitive_distribution: Record<BloomLevel, number>;
  type_distribution: Record<QuestionType, number>;
  quality_checks: {
    rejected_invalid_candidates: number;
    repair_calls: number;
  };
}

export interface BloomTemplateItem {
  cognitive_level: BloomLevel;
  system_prompt: string;
  example_topics: string[];
  question_counts_guidance: string;
}

export interface QuestionTypeTemplateItem {
  question_type: QuestionType;
  system_prompt: string;
  example_topics?: string[];
}

export interface BloomTemplatesData {
  bloom_templates: BloomTemplateItem[];
  question_type_templates: QuestionTypeTemplateItem[];
}

export interface GenerateFromContextRequest {
  raw_text: string;
  topic?: string;
  subject_name?: string;
  category_id?: string;
  total_questions: number;
  cognitive_ratios?: CognitiveRatios;
  type_ratios?: TypeRatios;
  language?: "vi" | "en";
  additional_instructions?: string;
  temperature?: number;
  chunk_size?: number;
  overlap?: number;
}

export interface GenerateFromContextData {
  topic: string;
  subject_name?: string | null;
  total_requested: number;
  total_generated: number;
  chunks_used: number;
  total_chunks: number;
  generated_questions: GeneratedQuestionItem[];
  cognitive_distribution: Record<BloomLevel, number>;
  type_distribution: Record<QuestionType, number>;
  quality_checks: {
    context_grounded?: boolean;
    exact_count_match?: boolean;
    duplicate_questions_blocked?: boolean;
    rejected_invalid_candidates: number;
    repair_calls: number;
  };
}

// ==============================================================================
// API FUNCTIONS
// ==============================================================================

const AI_GEN_PATH = "/ai-generator";

/**
 * GET /api/v1/ai-generator/bloom-templates
 * Trả về danh sách 3 Bloom templates và 3 question-type templates.
 */
export async function fetchBloomTemplates(): Promise<BloomTemplatesData> {
  const response = await api.get<ApiResponse<BloomTemplatesData>>(
    `${AI_GEN_PATH}/bloom-templates`,
  );
  const payload = response.data?.data;
  if (!payload) throw new Error("Không nhận được dữ liệu Bloom templates từ máy chủ.");
  return payload;
}

/**
 * POST /api/v1/ai-generator/bloom-templates/preview
 * Tính toán phân bổ ma trận (không gọi LLM).
 */
export async function previewMatrixAllocation(
  payload: MatrixRequest,
): Promise<MatrixPreviewData> {
  const response = await api.post<ApiResponse<MatrixPreviewData>>(
    `${AI_GEN_PATH}/bloom-templates/preview`,
    payload,
  );
  const data = response.data?.data;
  if (!data) throw new Error("Không nhận được dữ liệu preview ma trận từ máy chủ.");
  return data;
}

/**
 * POST /api/v1/ai-generator/generate-by-matrix
 * Sinh câu hỏi thực tế bằng LLM.
 */
export async function generateByMatrix(
  payload: MatrixRequest,
): Promise<GenerateByMatrixData> {
  const response = await api.post<ApiResponse<GenerateByMatrixData>>(
    `${AI_GEN_PATH}/generate-by-matrix`,
    payload,
  );
  const data = response.data?.data;
  if (!data) throw new Error("Không nhận được câu hỏi từ AI. Vui lòng thử lại.");
  return data;
}

/**
 * POST /api/v1/ai-generator/generate-from-context
 * Sinh câu hỏi bám sát tài liệu bài giảng / văn bản bằng Sliding Window Chunking và AI.
 */
export async function generateFromContext(
  payload: GenerateFromContextRequest,
): Promise<GenerateFromContextData> {
  const response = await api.post<ApiResponse<GenerateFromContextData>>(
    `${AI_GEN_PATH}/generate-from-context`,
    payload,
  );
  const data = response.data?.data;
  if (!data) throw new Error("Không nhận được câu hỏi từ tài liệu. Vui lòng thử lại.");
  return data;
}
