import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import ManageExams from "./ManageExams";
import JoinExam from "./JoinExam";
import ExamLobby from "./ExamLobby";
import { examGet, examPost } from "@/services/examService";
import { listQuestions } from "@/services/questionBankApi";

vi.mock("@/services/examService", () => ({ examGet: vi.fn(), examPost: vi.fn() }));
vi.mock("@/services/questionBankApi", () => ({ listQuestions: vi.fn() }));
const exam = { id: "exam-id", title: "Ca thi thử", exam_code: "ABCD1234", start_time: "2026-11-09T01:00:00Z", end_time: "2026-11-09T03:00:00Z", duration_minutes: 30, max_attempts: 1, is_published: true };
const attempt = { attempt_id: "attempt-id", expires_at: exam.end_time, questions: [{ question_id: "q-id", content: "Chọn đáp án", question_type: "SINGLE_CHOICE", options: [{ id: "A", text: "Phương án A" }, { id: "B", text: "Phương án B" }] }] };
beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(examGet).mockResolvedValue(exam);
  vi.mocked(listQuestions).mockResolvedValue({ success: true, message: "", data: [{ id: "q-id", content: "Câu hỏi ngân hàng" }] } as never);
});
afterEach(cleanup);

it("creates a published room with selected questions and local dates converted to UTC", async () => {
  vi.mocked(examGet).mockResolvedValue([]);
  vi.mocked(examPost).mockResolvedValue(exam);
  render(<MemoryRouter><ManageExams /></MemoryRouter>);
  fireEvent.change(screen.getByLabelText("Tên ca thi"), { target: { value: "Ca thi thử" } });
  fireEvent.change(screen.getByLabelText("Giờ mở (giờ địa phương)"), { target: { value: "2026-11-09T08:00" } });
  fireEvent.change(screen.getByLabelText("Giờ đóng (giờ địa phương)"), { target: { value: "2026-11-09T10:00" } });
  fireEvent.click(await screen.findByLabelText("Câu hỏi ngân hàng"));
  fireEvent.click(screen.getByRole("button", { name: "Tạo ca thi" }));
  await screen.findByRole("status");
  expect(examPost).toHaveBeenCalledWith("/exams", expect.objectContaining({ title: exam.title, questions: [{ question_id: "q-id", points: 1 }], is_published: true, start_time: new Date("2026-11-09T08:00").toISOString() }));
  expect(screen.getAllByText("ABCD1234").length).toBeGreaterThan(0);
});

it("enters lobby only after a successful code/PIN check", async () => {
  vi.mocked(examPost).mockResolvedValue(exam);
  render(<MemoryRouter initialEntries={["/join"]}><Routes><Route path="/join" element={<JoinExam />} /><Route path="/exam/lobby/:examId" element={<p>Đã vào phòng chờ</p>} /></Routes></MemoryRouter>);
  fireEvent.change(screen.getByLabelText("Mã phòng"), { target: { value: "abcd1234" } });
  fireEvent.change(screen.getByLabelText("PIN"), { target: { value: "123456" } });
  fireEvent.click(screen.getByRole("button"));
  await screen.findByText("Đã vào phòng chờ");
  expect(examPost).toHaveBeenCalledWith("/exams/join", { exam_code: "ABCD1234", pin: "123456" });
});

it("shows join failure and does not navigate", async () => {
  vi.mocked(examPost).mockRejectedValue(new Error("denied"));
  render(<MemoryRouter><JoinExam /></MemoryRouter>);
  fireEvent.change(screen.getByLabelText("Mã phòng"), { target: { value: "BAD" } });
  fireEvent.click(screen.getByRole("button"));
  await screen.findByRole("alert");
  expect(screen.getByRole("heading", { name: "Vào phòng thi" })).toBeTruthy();
});

it("starts/resumes and submits original option IDs then opens review", async () => {
  vi.mocked(examPost).mockResolvedValueOnce(attempt).mockResolvedValueOnce({ score: 10 });
  render(<MemoryRouter initialEntries={["/exam/lobby/exam-id"]}><Routes><Route path="/exam/lobby/:examId" element={<ExamLobby />} /><Route path="/review/:attemptId" element={<p>Kết quả bài thi</p>} /></Routes></MemoryRouter>);
  fireEvent.click(await screen.findByRole("button", { name: "Bắt đầu / Tiếp tục" }));
  fireEvent.click(await screen.findByLabelText("Phương án B"));
  fireEvent.click(screen.getByRole("button", { name: "Nộp bài" }));
  await screen.findByText("Kết quả bài thi");
  expect(examPost).toHaveBeenLastCalledWith("/attempts/attempt-id/submit", { answers: [{ question_id: "q-id", selected_options: ["B"] }] });
});

it("shows backend start rejection while staying in the lobby", async () => {
  vi.mocked(examPost).mockRejectedValue(new Error("not open"));
  render(<MemoryRouter initialEntries={["/exam/lobby/exam-id"]}><Routes><Route path="/exam/lobby/:examId" element={<ExamLobby />} /></Routes></MemoryRouter>);
  fireEvent.click(await screen.findByRole("button", { name: "Bắt đầu / Tiếp tục" }));
  await screen.findByRole("alert");
  expect(screen.queryByText("Nộp bài")).toBeNull();
});
