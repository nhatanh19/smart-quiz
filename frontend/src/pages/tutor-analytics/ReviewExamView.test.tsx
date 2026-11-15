import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from "axios";
import ReviewExamView from "./ReviewExamView";

vi.mock("@/services/tutorService", () => ({
  tutorService: {
    getExplanation: vi.fn().mockResolvedValue({
      is_correct: false,
      selected_options: ["B"],
      correct_options: ["A"],
      cached: false,
      response_time_ms: 420,
      feedback: {
        version: 1,
        explanation: "Hàm ảo cho phép đa hình động lúc runtime.",
        why_selected_wrong: "Phương án B thuộc về tính đóng gói, không phải đa hình.",
        study_suggestions: ["Ôn lại virtual function", "Ôn bảng vtable"],
        model: "cx/gpt-6-luna",
      },
    }),
    getAttemptReview: vi.fn(),
    getKnowledgeGaps: vi.fn(),
  },
}));

function renderSampleReview() {
  return render(
    <MemoryRouter initialEntries={["/review"]}>
      <Routes>
        <Route path="/review" element={<ReviewExamView />} />
        <Route path="/review/:attemptId" element={<ReviewExamView />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("ReviewExamView AI Tutor integration (Issue #51)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it("omits non-UUID sample ids when requesting AI explanation on /review", async () => {
    const { tutorService } = await import("@/services/tutorService");
    renderSampleReview();

    const explainButtons = screen.getAllByRole("button", { name: /Giải thích bằng AI/ });
    fireEvent.click(explainButtons[0]);

    await waitFor(() => {
      expect(tutorService.getExplanation).toHaveBeenCalledWith(
        expect.objectContaining({
          attempt_id: undefined,
          question_id: undefined,
          selected_options: ["B"],
          correct_options: ["A"],
        }),
      );
    });

    await screen.findByText(/Hàm ảo cho phép đa hình động lúc runtime/);
  });

  it("formats FastAPI 422 array errors cleanly without showing [object Object]", async () => {
    const { tutorService } = await import("@/services/tutorService");
    vi.mocked(tutorService.getExplanation).mockRejectedValueOnce(
      new AxiosError(
        "Request failed with status code 422",
        "ERR_BAD_REQUEST",
        {} as InternalAxiosRequestConfig,
        undefined,
        {
          data: {
            detail: [
              {
                type: "uuid_parsing",
                loc: ["body", "question_id"],
                msg: "Input should be a valid UUID",
              },
            ],
          },
          status: 422,
          statusText: "Unprocessable Entity",
          headers: {},
          config: {} as InternalAxiosRequestConfig,
        } as AxiosResponse,
      ),
    );

    renderSampleReview();
    const explainButtons = screen.getAllByRole("button", { name: /Giải thích bằng AI/ });
    fireEvent.click(explainButtons[0]);

    await screen.findByText("Input should be a valid UUID");
    expect(screen.queryByText(/\[object Object\]/)).toBeNull();
  });
});
