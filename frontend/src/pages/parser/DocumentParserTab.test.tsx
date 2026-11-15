import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from "axios";
import { apiClient } from "@/lib/apiClient";
import { parseQuestionsFromText, uploadAndParseDocument } from "@/services/parserApi";
import DocumentParserTab from "./DocumentParserTab";
import ParserPlaceholder from "./ParserPlaceholder";

vi.mock("@/services/questionBankApi", () => ({
  assignCategorySubject: vi.fn(),
  createCategory: vi.fn(),
  createQuestion: vi.fn(),
  createSubject: vi.fn(),
  deleteQuestion: vi.fn(),
  isRequestCancelled: () => false,
  listCategories: vi.fn().mockResolvedValue([]),
  listQuestions: vi.fn().mockResolvedValue({ success: true, message: "", data: [] }),
  listSubjects: vi.fn().mockResolvedValue([]),
  updateQuestion: vi.fn(),
}));

const originalAdapter = apiClient.defaults.adapter;

beforeEach(() => {
  localStorage.clear();
  localStorage.setItem("access_token", "stale-localstorage-token");
  localStorage.setItem("token", "stale-localstorage-token");
});

afterEach(() => {
  apiClient.defaults.adapter = originalAdapter;
  localStorage.clear();
  cleanup();
});

function makeResponse(
  config: InternalAxiosRequestConfig,
  data: unknown,
  status = 200,
): AxiosResponse {
  return { data, status, statusText: "", headers: {}, config };
}

describe("DocumentParserTab & parserApi", () => {
  it("renders upload dropzone with allowed formats and size limit", () => {
    render(<DocumentParserTab />);
    expect(screen.getByText("Tải lên & Bóc tách văn bản thô")).toBeTruthy();
    expect(screen.getAllByText(".PDF").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(".DOCX").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(".TXT").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Dung lượng tối đa: 10MB/)).toBeTruthy();
  });

  it("rejects unsupported extension, 0-byte, and >10MB files client-side without calling API", () => {
    const adapterSpy = vi.fn();
    apiClient.defaults.adapter = adapterSpy;

    render(<DocumentParserTab />);
    const input = screen.getByLabelText("Chọn tệp tài liệu tải lên") as HTMLInputElement;

    const badExt = new File(["binary"], "malware.pdf.exe", { type: "application/octet-stream" });
    fireEvent.change(input, { target: { files: [badExt] } });
    expect(screen.getByRole("alert").textContent).toContain("không được hỗ trợ");

    const emptyFile = new File([], "empty.txt", { type: "text/plain" });
    fireEvent.change(input, { target: { files: [emptyFile] } });
    expect(screen.getByRole("alert").textContent).toContain("0 bytes");

    const oversized = new File(["a"], "big.pdf", { type: "application/pdf" });
    Object.defineProperty(oversized, "size", { value: 10 * 1024 * 1024 + 1 });
    fireEvent.change(input, { target: { files: [oversized] } });
    expect(screen.getByRole("alert").textContent).toContain("vượt quá 10MB");

    expect(adapterSpy).not.toHaveBeenCalled();
  });

  it("uploads valid file using HttpOnly cookie apiClient (no localStorage Bearer) and displays extracted Vietnamese text", async () => {
    let capturedConfig: InternalAxiosRequestConfig | undefined;
    apiClient.defaults.adapter = async (config) => {
      capturedConfig = config;
      return makeResponse(config, {
        success: true,
        message: "File parsed successfully",
        data: {
          filename: "de_thi.pdf",
          file_type: "pdf",
          file_size: 2048,
          character_count: 42,
          word_count: 9,
          page_count: 2,
          raw_text: "Câu 1: Quản trị dự án phần mềm là gì?",
        },
      });
    };

    render(<DocumentParserTab />);
    const input = screen.getByLabelText("Chọn tệp tài liệu tải lên") as HTMLInputElement;
    const pdfFile = new File(["%PDF-1.4 content"], "de_thi.pdf", { type: "application/pdf" });

    fireEvent.change(input, { target: { files: [pdfFile] } });
    expect(screen.getByText("de_thi.pdf")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: /Bắt đầu bóc tách/ }));

    await screen.findByText("Bóc tách thành công");
    expect(screen.getByText("Câu 1: Quản trị dự án phần mềm là gì?")).toBeTruthy();
    expect(screen.getByText("2 trang")).toBeTruthy();
    expect(screen.getByText("9 từ")).toBeTruthy();
    expect(screen.getByText("42 ký tự")).toBeTruthy();

    expect(capturedConfig?.url).toBe("/parser/upload");
    expect(capturedConfig?.withCredentials).toBe(true);
    expect(capturedConfig?.data).toBeInstanceOf(FormData);
    expect(capturedConfig?.headers?.Authorization).toBeUndefined();

    fireEvent.click(screen.getByRole("button", { name: /Bóc tách tệp khác/ }));
    expect(screen.getByText("Kéo & thả tệp tài liệu vào đây")).toBeTruthy();
  });

  it("shows server error details when upload fails with 400 or 403", async () => {
    apiClient.defaults.adapter = async (config) => {
      throw new AxiosError(
        "Forbidden",
        "ERR_BAD_REQUEST",
        config,
        undefined,
        makeResponse(config, { detail: "Access forbidden" }, 403),
      );
    };

    render(<DocumentParserTab />);
    const input = screen.getByLabelText("Chọn tệp tài liệu tải lên") as HTMLInputElement;
    fireEvent.change(input, {
      target: { files: [new File(["hello"], "note.txt", { type: "text/plain" })] },
    });
    fireEvent.click(screen.getByRole("button", { name: /Bắt đầu bóc tách/ }));

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("Access forbidden");
  });
});

describe("ParserPlaceholder tab integration", () => {
  it("defaults to parser tab and switches to question bank tab", async () => {
    render(<ParserPlaceholder />);
    expect(screen.getByText("Tải lên & Bóc tách văn bản thô")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: /Ngân hàng câu hỏi/ }));
    await waitFor(() =>
      expect(screen.getByRole("heading", { name: "Ngân hàng câu hỏi" })).toBeTruthy(),
    );
  });
});

describe("Regex question parser API helpers (Issue #6)", () => {
  it("calls POST /parser/parse-questions with HttpOnly cookies and returns normalized questions", async () => {
    let capturedConfig: InternalAxiosRequestConfig | undefined;
    apiClient.defaults.adapter = async (config) => {
      capturedConfig = config;
      return makeResponse(config, {
        success: true,
        message: "Đã nhận diện 1 câu hỏi từ văn bản.",
        data: {
          filename: "de_mau.txt",
          questions: [
            {
              question_number: 1,
              content: "WBS là gì?",
              question_type: "SINGLE_CHOICE",
              cognitive_level: "REMEMBER",
              level: "MEDIUM",
              options: [
                { id: "A", text: "Work Breakdown Structure", is_correct: true },
                { id: "B", text: "Work Budget Schedule", is_correct: false },
              ],
              correct_option_ids: ["A"],
              explanation: "Cấu trúc phân rã công việc.",
              tags: [],
              source_type: "FILE_PARSER",
              is_valid: true,
              warnings: [],
            },
          ],
          statistics: {
            total_blocks_detected: 1,
            total_questions: 1,
            valid_questions: 1,
            questions_with_correct_answer: 1,
            questions_with_explanation: 1,
            warnings_count: 0,
          },
          unmatched_answer_keys: {},
          warnings: [],
        },
      });
    };

    const result = await parseQuestionsFromText("Câu 1: WBS là gì?\n*A. WBS\nB. Schedule", "de_mau.txt");
    expect(capturedConfig?.url).toBe("/parser/parse-questions");
    expect(capturedConfig?.withCredentials).toBe(true);
    expect(capturedConfig?.headers?.Authorization).toBeUndefined();
    expect(result.statistics.total_questions).toBe(1);
    expect(result.questions[0].correct_option_ids).toEqual(["A"]);
    expect(result.questions[0].source_type).toBe("FILE_PARSER");
  });

  it("calls POST /parser/upload-and-parse with multipart FormData", async () => {
    let capturedConfig: InternalAxiosRequestConfig | undefined;
    apiClient.defaults.adapter = async (config) => {
      capturedConfig = config;
      return makeResponse(config, {
        success: true,
        message: "Đã bóc tách văn bản và nhận diện 1 câu hỏi.",
        data: {
          document: {
            filename: "sample.docx",
            file_type: "docx",
            file_size: 1024,
            character_count: 80,
            word_count: 15,
            raw_text: "Câu 1: ...",
          },
          questions: [],
          statistics: {
            total_blocks_detected: 0,
            total_questions: 0,
            valid_questions: 0,
            questions_with_correct_answer: 0,
            questions_with_explanation: 0,
            warnings_count: 0,
          },
          unmatched_answer_keys: {},
          warnings: [],
        },
      });
    };

    const file = new File(["docx"], "sample.docx", {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });
    const res = await uploadAndParseDocument(file);
    expect(capturedConfig?.url).toBe("/parser/upload-and-parse");
    expect(capturedConfig?.withCredentials).toBe(true);
    expect(capturedConfig?.data).toBeInstanceOf(FormData);
    expect(res.document.filename).toBe("sample.docx");
  });
});
