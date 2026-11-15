import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from "axios";
import { apiClient } from "@/lib/apiClient";
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
