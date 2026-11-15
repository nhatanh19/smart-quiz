import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { listCategories, listQuestions, listSubjects } from "@/services/questionBankApi";
import ParserPlaceholder from "./ParserPlaceholder";

vi.mock("@/services/questionBankApi", () => ({
  assignCategorySubject: vi.fn(),
  createCategory: vi.fn(),
  createQuestion: vi.fn(),
  createSubject: vi.fn(),
  deleteQuestion: vi.fn(),
  isRequestCancelled: () => false,
  listCategories: vi.fn(),
  listQuestions: vi.fn(),
  listSubjects: vi.fn(),
  updateQuestion: vi.fn(),
}));

beforeEach(() => {
  localStorage.clear();
  vi.mocked(listSubjects).mockResolvedValue([
    {
      id: "sub-1",
      name: "Mạng máy tính",
      description: null,
      created_by: "u-1",
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    },
  ]);
  vi.mocked(listCategories).mockResolvedValue([
    {
      id: "cat-1",
      name: "Tầng Giao vận",
      description: null,
      subject_id: "sub-1",
      created_by: "u-1",
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    },
  ]);
  vi.mocked(listQuestions).mockResolvedValue({
    success: true,
    message: "OK",
    data: [
      {
        id: "q-1",
        category_id: "cat-1",
        creator_id: "u-1",
        content: "Giao thức TCP hoạt động ở tầng nào?",
        question_type: "SINGLE_CHOICE",
        cognitive_level: "REMEMBER",
        level: "EASY",
        options: [
          { id: "A", text: "Transport", is_correct: true },
          { id: "B", text: "Network", is_correct: false },
        ],
        tags: ["tcp"],
        explanation: "TCP thuộc tầng Giao vận.",
        source_type: "MANUAL",
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
      },
    ],
  });
});

afterEach(() => {
  localStorage.clear();
  vi.clearAllMocks();
  cleanup();
});

describe("ParserPlaceholder Question Bank cookie auth (Issue #49)", () => {
  it("loads taxonomy and questions without localStorage JWT and enables creating questions", async () => {
    render(<ParserPlaceholder />);

    fireEvent.click(screen.getByRole("button", { name: /Ngân hàng câu hỏi/ }));

    await waitFor(() => {
      expect(listSubjects).toHaveBeenCalledTimes(1);
      expect(listCategories).toHaveBeenCalledTimes(1);
      expect(listQuestions).toHaveBeenCalledTimes(1);
    });

    expect(screen.queryByText(/Cần JWT giảng viên hoặc quản trị viên/)).toBeNull();
    expect(screen.queryByLabelText("JWT access token")).toBeNull();
    expect(await screen.findByText("Giao thức TCP hoạt động ở tầng nào?")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: /Thêm câu hỏi/ }));
    const submitBtn = screen.getByRole("button", { name: "Tạo câu hỏi" }) as HTMLButtonElement;
    expect(submitBtn.disabled).toBe(false);
  });
});
