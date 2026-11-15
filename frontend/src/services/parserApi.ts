import axios, { AxiosProgressEvent } from "axios";
import { apiClient } from "@/lib/apiClient";
import type {
  ApiResponse,
  CognitiveLevel,
  QuestionLevel,
  QuestionOption,
  QuestionSource,
  QuestionType,
} from "@/types";

export interface DocumentParseResult {
  filename: string;
  file_type: string;
  file_size: number;
  raw_text: string;
  character_count: number;
  word_count: number;
  page_count?: number;
}

export interface ParsedQuestionItem {
  question_number?: number | null;
  content: string;
  question_type: QuestionType;
  cognitive_level: CognitiveLevel;
  level: QuestionLevel;
  options: QuestionOption[];
  correct_option_ids: string[];
  explanation?: string | null;
  tags: string[];
  source_type: QuestionSource;
  is_valid: boolean;
  warnings: string[];
}

export interface ParseStatistics {
  total_blocks_detected: number;
  total_questions: number;
  valid_questions: number;
  questions_with_correct_answer: number;
  questions_with_explanation: number;
  warnings_count: number;
}

export interface ParsedQuestionBatchResult {
  filename?: string | null;
  questions: ParsedQuestionItem[];
  statistics: ParseStatistics;
  unmatched_answer_keys: Record<number, string[]>;
  warnings: string[];
}

export interface DocumentQuestionExtractionResult {
  document: DocumentParseResult;
  questions: ParsedQuestionItem[];
  statistics: ParseStatistics;
  unmatched_answer_keys: Record<number, string[]>;
  warnings: string[];
}

/**
 * Upload a document (.pdf, .docx, .txt) and extract its raw text content.
 * Sends multipart/form-data to POST /parser/upload via shared apiClient (HttpOnly cookies).
 */
export async function uploadAndExtractDocument(
  file: File,
  onUploadProgress?: (progressEvent: AxiosProgressEvent) => void,
): Promise<DocumentParseResult> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiClient.post<ApiResponse<DocumentParseResult>>(
    "/parser/upload",
    formData,
    {
      onUploadProgress,
    },
  );

  const payload = response.data?.data;
  if (!payload) {
    throw new Error("Không nhận được dữ liệu phản hồi hợp lệ từ máy chủ.");
  }

  const rawText =
    payload.raw_text ??
    (payload as unknown as Record<string, string | undefined>)?.extracted_text ??
    (payload as unknown as Record<string, string | undefined>)?.text ??
    "";

  return {
    filename: payload.filename || file.name,
    file_type:
      payload.file_type ||
      file.name.split(".").pop()?.toLowerCase() ||
      "",
    file_size: payload.file_size ?? file.size,
    raw_text: rawText,
    character_count: payload.character_count ?? rawText.length,
    word_count:
      payload.word_count ??
      (rawText.trim() ? rawText.trim().split(/\s+/).length : 0),
    page_count: payload.page_count,
  };
}

/**
 * Parse raw UTF-8 text into structured quiz questions via POST /parser/parse-questions.
 */
export async function parseQuestionsFromText(
  rawText: string,
  filename?: string,
): Promise<ParsedQuestionBatchResult> {
  const response = await apiClient.post<ApiResponse<ParsedQuestionBatchResult>>(
    "/parser/parse-questions",
    {
      raw_text: rawText,
      filename: filename ?? "direct_input.txt",
    },
  );

  const payload = response.data?.data;
  if (!payload) {
    throw new Error("Không nhận được dữ liệu câu hỏi chuẩn hóa từ máy chủ.");
  }
  return payload;
}

/**
 * Upload a document and extract both raw text and regex-parsed structured questions
 * via POST /parser/upload-and-parse.
 */
export async function uploadAndParseDocument(
  file: File,
  onUploadProgress?: (progressEvent: AxiosProgressEvent) => void,
): Promise<DocumentQuestionExtractionResult> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiClient.post<ApiResponse<DocumentQuestionExtractionResult>>(
    "/parser/upload-and-parse",
    formData,
    {
      onUploadProgress,
    },
  );

  const payload = response.data?.data;
  if (!payload) {
    throw new Error("Không nhận được dữ liệu bóc tách câu hỏi từ máy chủ.");
  }
  return payload;
}

/**
 * Extracts a human-friendly error message from any backend API or network error.
 * Properly parses FastAPI HTTPException details, validation errors, and HTTP status codes.
 */
export function extractUploadErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data;
    if (data) {
      if (typeof data.detail === "string") {
        return data.detail;
      }
      if (Array.isArray(data.detail)) {
        return data.detail
          .map((item: { msg?: string; message?: string }) => item.msg || item.message || JSON.stringify(item))
          .filter(Boolean)
          .join(", ");
      }
      if (typeof data.message === "string") {
        return data.message;
      }
      if (typeof data.error === "string") {
        return data.error;
      }
    }
    if (error.response?.status === 413) {
      return "Dung lượng tệp vượt quá giới hạn tối đa cho phép của máy chủ (10MB).";
    }
    if (error.response?.status === 400) {
      return (
        data?.detail ||
        data?.message ||
        "Tệp tin tải lên không hợp lệ hoặc định dạng bị lỗi."
      );
    }
    if (error.response?.status === 401) {
      return "Phiên đăng nhập đã hết hạn hoặc không hợp lệ. Vui lòng đăng nhập lại.";
    }
    if (error.response?.status === 403) {
      return "Bạn không có quyền thực hiện chức năng tải lên tài liệu.";
    }
    if (error.response?.status === 500) {
      return "Máy chủ gặp sự cố nội bộ khi xử lý tệp. Vui lòng thử lại sau.";
    }
    if (
      error.code === "ECONNABORTED" ||
      (error.message && error.message.includes("Network Error"))
    ) {
      return "Không thể kết nối máy chủ phân tích tài liệu. Vui lòng kiểm tra đường truyền mạng.";
    }
    return error.message || "Không thể kết nối máy chủ phân tích tài liệu.";
  }
  return error instanceof Error
    ? error.message
    : "Đã xảy ra lỗi không xác định khi tải lên tài liệu.";
}
