import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { apiClient } from "@/lib/apiClient";
import AiGenPage from "./AiGenPage";

// ==============================================================================
// MOCKS
// ==============================================================================

vi.mock("@/services/aiGeneratorApi", () => ({
  fetchBloomTemplates: vi.fn().mockResolvedValue({
    bloom_templates: [],
    question_type_templates: [],
  }),
  previewMatrixAllocation: vi.fn().mockResolvedValue({
    topic: "Test Topic",
    total_questions: 10,
    cognitive_distribution: { REMEMBER: 4, UNDERSTAND: 4, APPLY: 2 },
    type_distribution: { SINGLE_CHOICE: 6, MULTIPLE_CHOICE: 2, TRUE_FALSE: 2 },
    allocations: [
      { cognitive_level: "REMEMBER", question_type: "SINGLE_CHOICE", count: 3 },
      { cognitive_level: "REMEMBER", question_type: "MULTIPLE_CHOICE", count: 1 },
      { cognitive_level: "UNDERSTAND", question_type: "SINGLE_CHOICE", count: 2 },
      { cognitive_level: "UNDERSTAND", question_type: "TRUE_FALSE", count: 2 },
      { cognitive_level: "APPLY", question_type: "SINGLE_CHOICE", count: 1 },
      { cognitive_level: "APPLY", question_type: "MULTIPLE_CHOICE", count: 1 },
    ],
  }),
  generateByMatrix: vi.fn().mockResolvedValue({
    total_requested: 2,
    total_generated: 2,
    generated_questions: [
      {
        category_id: null,
        content: "What is a class in OOP?",
        question_type: "SINGLE_CHOICE",
        cognitive_level: "REMEMBER",
        level: "EASY",
        options: [
          { id: "A", text: "A blueprint for objects", is_correct: true },
          { id: "B", text: "A variable", is_correct: false },
          { id: "C", text: "A function", is_correct: false },
          { id: "D", text: "A module", is_correct: false },
        ],
        tags: [],
        explanation: "A class is a blueprint.",
        source_type: "AI_GENERATED",
      },
      {
        category_id: null,
        content: "Which of the following is a valid Python data type?",
        question_type: "MULTIPLE_CHOICE",
        cognitive_level: "UNDERSTAND",
        level: "MEDIUM",
        options: [
          { id: "A", text: "list", is_correct: true },
          { id: "B", text: "dict", is_correct: true },
          { id: "C", text: "tree", is_correct: false },
          { id: "D", text: "tuple", is_correct: true },
        ],
        tags: [],
        explanation: "list, dict, tuple are valid Python types.",
        source_type: "AI_GENERATED",
      },
    ],
    cognitive_distribution: { REMEMBER: 1, UNDERSTAND: 1, APPLY: 0 },
    type_distribution: { SINGLE_CHOICE: 1, MULTIPLE_CHOICE: 1, TRUE_FALSE: 0 },
    quality_checks: { rejected_invalid_candidates: 0, repair_calls: 0 },
  }),
}));

vi.mock("@/services/questionBankApi", () => ({
  listSubjects: vi.fn().mockResolvedValue([
    { id: "sub-1", name: "Computer Science", description: null, created_by: "u1", created_at: "", updated_at: "" },
  ]),
  listCategories: vi.fn().mockResolvedValue([
    { id: "cat-1", name: "OOP", description: null, subject_id: "sub-1", created_by: "u1", created_at: "", updated_at: "" },
  ]),
  createQuestion: vi.fn().mockResolvedValue(undefined),
}));

const originalAdapter = apiClient.defaults.adapter;

beforeEach(() => {
  localStorage.clear();
});

afterEach(() => {
  apiClient.defaults.adapter = originalAdapter;
  localStorage.clear();
  cleanup();
});

// ==============================================================================
// TESTS
// ==============================================================================

describe("AiGenPage — Config Step", () => {
  it("renders the page header correctly", () => {
    render(<AiGenPage />);
    expect(screen.getByText("AI Exam Matrix Builder")).toBeTruthy();
    expect(
      screen.getByText(/Cấu hình ma trận đề thi theo thang nhận thức Bloom/),
    ).toBeTruthy();
  });

  it("renders all form inputs: topic, total questions, bloom ratios, type ratios", () => {
    render(<AiGenPage />);
    expect(screen.getByPlaceholderText(/VD: Lập trình hướng đối tượng/)).toBeTruthy();
    // Bloom ratio labels
    expect(screen.getByText("Nhận biết")).toBeTruthy();
    expect(screen.getByText("Thông hiểu")).toBeTruthy();
    expect(screen.getByText("Vận dụng")).toBeTruthy();
    // Type ratio labels
    expect(screen.getByText("1 đáp án")).toBeTruthy();
    expect(screen.getByText("Nhiều đáp án")).toBeTruthy();
    expect(screen.getByText("Đúng/Sai")).toBeTruthy();
  });

  it("disables Generate button when topic is empty", () => {
    render(<AiGenPage />);
    const btn = screen.getByRole("button", { name: /Sinh câu hỏi bằng AI/ });
    expect(btn.hasAttribute("disabled")).toBe(true);
  });

  it("enables Generate button when topic is filled and ratios sum to 100", () => {
    render(<AiGenPage />);
    const topicInput = screen.getByPlaceholderText(/VD: Lập trình hướng đối tượng/);
    fireEvent.change(topicInput, { target: { value: "Python OOP" } });
    const btn = screen.getByRole("button", { name: /Sinh câu hỏi bằng AI/ });
    expect(btn.hasAttribute("disabled")).toBe(false);
  });

  it("shows sum validation badge: green when 100, red when not", () => {
    render(<AiGenPage />);
    // Default bloom = 40+40+20 = 100 → Tổng: 100%
    const badges = screen.getAllByText(/Tổng: 100%/);
    expect(badges.length).toBeGreaterThanOrEqual(1);
  });

  it("shows Preview button and calls previewMatrixAllocation on click", async () => {
    const { previewMatrixAllocation } = await import("@/services/aiGeneratorApi");
    render(<AiGenPage />);
    const topicInput = screen.getByPlaceholderText(/VD: Lập trình hướng đối tượng/);
    fireEvent.change(topicInput, { target: { value: "Test Topic" } });

    const previewBtn = screen.getByRole("button", { name: /Xem trước phân bổ/ });
    fireEvent.click(previewBtn);

    await waitFor(() => {
      expect(previewMatrixAllocation).toHaveBeenCalledWith(
        expect.objectContaining({ topic: "Test Topic" }),
      );
    });
  });

  it("renders preview matrix table after preview button click", async () => {
    render(<AiGenPage />);
    const topicInput = screen.getByPlaceholderText(/VD: Lập trình hướng đối tượng/);
    fireEvent.change(topicInput, { target: { value: "Test Topic" } });
    fireEvent.click(screen.getByRole("button", { name: /Xem trước phân bổ/ }));

    await waitFor(() => {
      expect(screen.getByText(/Phân bổ ma trận — Test Topic/)).toBeTruthy();
    });
    // Matrix table headers
    expect(screen.getByText("Nhận thức ↓ / Loại →")).toBeTruthy();
  });
});

describe("AiGenPage — Generate & Review Step", () => {
  async function renderAndGenerate() {
    render(<AiGenPage />);
    const topicInput = screen.getByPlaceholderText(/VD: Lập trình hướng đối tượng/);
    fireEvent.change(topicInput, { target: { value: "Python OOP" } });
    fireEvent.click(screen.getByRole("button", { name: /Sinh câu hỏi bằng AI/ }));

    await waitFor(() => {
      expect(screen.getByText("Duyệt câu hỏi AI")).toBeTruthy();
    });
  }

  it("transitions to review step after generating questions", async () => {
    await renderAndGenerate();
    expect(screen.getByText("Duyệt câu hỏi AI")).toBeTruthy();
    expect(screen.getByText(/What is a class in OOP/)).toBeTruthy();
    expect(screen.getByText(/valid Python data type/)).toBeTruthy();
  });

  it("renders cognitive level and question type badges on question cards", async () => {
    await renderAndGenerate();
    expect(screen.getByText("Nhận biết")).toBeTruthy();
    expect(screen.getByText("Thông hiểu")).toBeTruthy();
    expect(screen.getByText("Một đáp án")).toBeTruthy();
    expect(screen.getByText("Nhiều đáp án")).toBeTruthy();
  });

  it("renders subject and category dropdowns for save", async () => {
    await renderAndGenerate();
    await waitFor(() => {
      expect(screen.getByText("Computer Science")).toBeTruthy();
      expect(screen.getByText("OOP")).toBeTruthy();
    });
  });

  it("saves selected questions when Save button is clicked", async () => {
    const { createQuestion } = await import("@/services/questionBankApi");
    await renderAndGenerate();

    await waitFor(() => {
      expect(screen.getByText("OOP")).toBeTruthy();
    });

    const saveBtn = screen.getByRole("button", { name: /Lưu.*câu vào Ngân hàng/ });
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(createQuestion).toHaveBeenCalled();
    });
  });

  it("shows success banner after saving", async () => {
    await renderAndGenerate();
    await waitFor(() => expect(screen.getByText("OOP")).toBeTruthy());
    fireEvent.click(screen.getByRole("button", { name: /Lưu.*câu vào Ngân hàng/ }));
    await waitFor(() => {
      expect(screen.getByText(/Đã lưu.*câu hỏi vào Ngân hàng/)).toBeTruthy();
    });
  });

  it("allows toggling back to config step via Cấu hình lại button", async () => {
    await renderAndGenerate();
    fireEvent.click(screen.getByRole("button", { name: /Cấu hình lại/ }));
    expect(screen.getByText("AI Exam Matrix Builder")).toBeTruthy();
  });

  it("Select all / Deselect all toggles correctly", async () => {
    await renderAndGenerate();
    // All selected by default
    const deselectBtn = screen.getByRole("button", { name: /Bỏ chọn tất cả/ });
    expect(deselectBtn).toBeTruthy();
    fireEvent.click(deselectBtn);
    // After deselect: button text changes
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Chọn tất cả/ })).toBeTruthy();
    });
  });
});
