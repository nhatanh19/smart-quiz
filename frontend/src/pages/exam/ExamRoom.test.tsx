import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import ExamRoom from "./ExamRoom";
import { examGet, examPost } from "@/services/examService";
vi.mock("@/services/examService", () => ({ examGet: vi.fn(), examPost: vi.fn() }));
vi.mock("@/contexts/AuthContext", () => ({ useAuth: () => ({ user: { id: "student" } }) }));
const key = "smart-quiz:answers:student:attempt";
const attempt = { attempt_id: "attempt", exam_id: "exam", status: "IN_PROGRESS", expires_at: new Date(Date.now() + 600000).toISOString(), questions: [{ question_id: "q", content: "Chọn đáp án", question_type: "SINGLE_CHOICE", options: [{ id: "A", text: "Đáp án A" }, { id: "B", text: "Đáp án B" }] }] };
function open() { return render(<MemoryRouter initialEntries={["/exam/attempt"]}><Routes><Route path="/exam/:attemptId" element={<ExamRoom />} /><Route path="/review/:attemptId" element={<p>Kết quả</p>} /></Routes></MemoryRouter>); }
beforeEach(() => { localStorage.clear(); vi.resetAllMocks(); vi.mocked(examGet).mockResolvedValue(attempt); vi.mocked(examPost).mockResolvedValue({}); });
afterEach(() => { cleanup(); vi.useRealTimers(); vi.restoreAllMocks(); });
it("restores answers on reload, submits original IDs and clears only this cache", async () => {
  const first = open();
  fireEvent.click(await screen.findByLabelText("Đáp án B"));
  expect(JSON.parse(localStorage.getItem(key)!)).toEqual({ q: ["B"] });
  first.unmount(); open();
  expect((await screen.findByLabelText("Đáp án B") as HTMLInputElement).checked).toBe(true);
  fireEvent.click(screen.getByRole("button", { name: "Nộp bài" }));
  fireEvent.click(screen.getByRole("button", { name: "Xác nhận nộp" }));
  await screen.findByText("Kết quả");
  expect(examPost).toHaveBeenLastCalledWith("/attempts/attempt/submit", { answers: [{ question_id: "q", selected_options: ["B"] }] });
  expect(localStorage.getItem(key)).toBeNull();
});
it("automatically submits an expired attempt exactly once", async () => {
  vi.mocked(examGet).mockResolvedValue({ ...attempt, expires_at: new Date(Date.now() - 1000).toISOString() });
  open(); await screen.findByText("Kết quả");
  expect(examPost).toHaveBeenCalledTimes(1);
});
it("retains answers after submission failure and permits retry", async () => {
  vi.mocked(examPost).mockRejectedValue(new Error("offline"));
  open(); fireEvent.click(await screen.findByLabelText("Đáp án A"));
  fireEvent.click(screen.getByRole("button", { name: "Nộp bài" }));
  fireEvent.click(screen.getByRole("button", { name: "Xác nhận nộp" }));
  await screen.findByRole("alert");
  expect(JSON.parse(localStorage.getItem(key)!)).toEqual({ q: ["A"] });
  expect((screen.getByRole("button", { name: "Nộp bài" }) as HTMLButtonElement).disabled).toBe(false);
});
it("ignores corrupted local cache", async () => {
  localStorage.setItem(key, "broken json"); open();
  expect((await screen.findByLabelText("Đáp án A") as HTMLInputElement).checked).toBe(false);
});
it("recovers a successful server commit when the submit response is lost", async () => {
  vi.mocked(examGet).mockResolvedValueOnce(attempt).mockResolvedValueOnce({ ...attempt, status: "SUBMITTED" });
  vi.mocked(examPost).mockRejectedValue(new Error("response lost"));
  open(); fireEvent.click(await screen.findByLabelText("Đáp án A"));
  fireEvent.click(screen.getByRole("button", { name: "Nộp bài" }));
  fireEvent.click(screen.getByRole("button", { name: "Xác nhận nộp" }));
  await screen.findByText("Kết quả");
  expect(localStorage.getItem(key)).toBeNull();
});
it("shows the server count and configured threshold in the warning modal", async () => {
  vi.mocked(examGet).mockResolvedValue({ ...attempt, violation_count: 0, max_tab_violations: 5 });
  vi.mocked(examPost).mockImplementation(async path => path.endsWith("/log-violation") ? { status: "IN_PROGRESS", violation_count: 1, max_tab_violations: 5 } : {});
  open(); await screen.findByLabelText("Đáp án A");
  fireEvent.keyDown(document, { key: "F12" });
  await screen.findByText("1 / 5");
  expect(screen.getByRole("alertdialog")).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Tôi đã hiểu, tiếp tục làm bài" }));
  expect(screen.queryByRole("alertdialog")).toBeNull();
});
it("sends current original option IDs, clears cache and opens review on lockout", async () => {
  vi.mocked(examGet).mockResolvedValue({ ...attempt, violation_count: 0, max_tab_violations: 1 });
  vi.mocked(examPost).mockImplementation(async path => path.endsWith("/log-violation") ? { status: "LOCKED_VIOLATION", violation_count: 1, max_tab_violations: 1 } : {});
  open(); fireEvent.click(await screen.findByLabelText("Đáp án B"));
  fireEvent.keyDown(document, { key: "F12" });
  await screen.findByText("Kết quả");
  expect(examPost).toHaveBeenCalledWith("/attempts/attempt/log-violation", expect.objectContaining({ answers: [{ question_id: "q", selected_options: ["B"] }] }));
  expect(localStorage.getItem(key)).toBeNull();
});
it("persists marks and the current question across reload without changing answers", async () => {
  const second = { ...attempt.questions[0], question_id: "q2", content: "Câu hỏi thứ hai" };
  vi.mocked(examGet).mockResolvedValue({ ...attempt, questions: [...attempt.questions, second] });
  const first = open();
  fireEvent.click(await screen.findByRole("button", { name: "Đánh dấu câu hỏi" }));
  expect(screen.getByRole("button", { name: "Câu 1, chưa làm, đánh dấu" })).toBeTruthy();
  fireEvent.click(screen.getByLabelText("Đáp án B"));
  expect(screen.getByRole("button", { name: "Câu 1, đã làm, đánh dấu" })).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Câu 2, chưa làm" }));
  fireEvent.click(screen.getByRole("button", { name: "Đánh dấu câu hỏi" }));
  first.unmount(); open();
  await screen.findByText("Câu hỏi thứ hai");
  expect(screen.getByRole("button", { name: "Câu 2, chưa làm, đánh dấu" }).getAttribute("aria-current")).toBe("step");
  fireEvent.click(screen.getByRole("button", { name: "Bỏ đánh dấu câu hỏi" }));
  expect(screen.getByRole("button", { name: "Câu 2, chưa làm" })).toBeTruthy();
  expect(JSON.parse(localStorage.getItem(key)!)).toEqual({ q: ["B"] });
});
it("restores cached questions, multiple selections and marks when the API is offline", async () => {
  vi.mocked(examGet).mockResolvedValue({ ...attempt, questions: [{ ...attempt.questions[0], question_type: "MULTIPLE_CHOICE" }] });
  const first = open();
  fireEvent.click(await screen.findByLabelText("Đáp án A"));
  fireEvent.click(screen.getByLabelText("Đáp án B"));
  fireEvent.click(screen.getByRole("button", { name: "Đánh dấu câu hỏi" }));
  first.unmount();
  vi.mocked(examGet).mockRejectedValue({ isAxiosError: true, message: "Network Error" });
  open();
  expect((await screen.findByLabelText("Đáp án A") as HTMLInputElement).checked).toBe(true);
  expect((screen.getByLabelText("Đáp án B") as HTMLInputElement).checked).toBe(true);
  expect(screen.getByRole("button", { name: "Câu 1, đã làm, đánh dấu" })).toBeTruthy();
  expect(screen.getByText(/Đang dùng bản lưu/)).toBeTruthy();
});
it("does not bypass a server ownership rejection with a cached room", async () => {
  const first = open(); await screen.findByLabelText("Đáp án A"); first.unmount();
  vi.mocked(examGet).mockRejectedValue({ isAxiosError: true, response: { status: 403 }, message: "Forbidden" });
  open(); await screen.findByRole("alert");
  expect(screen.queryByLabelText("Đáp án A")).toBeNull();
});
it("clears answers, marks and room snapshot together after a successful submission", async () => {
  open(); fireEvent.click(await screen.findByRole("button", { name: "Đánh dấu câu hỏi" }));
  fireEvent.click(screen.getByLabelText("Đáp án B"));
  expect(localStorage.getItem(`${key}:room`)).not.toBeNull();
  localStorage.setItem("other-attempt", "keep");
  fireEvent.click(screen.getByRole("button", { name: "Nộp bài" }));
  fireEvent.click(screen.getByRole("button", { name: "Xác nhận nộp" }));
  await screen.findByText("Kết quả");
  expect(localStorage.getItem(key)).toBeNull();
  expect(localStorage.getItem(`${key}:room`)).toBeNull();
  expect(localStorage.getItem("other-attempt")).toBe("keep");
});
it("uses server time despite client clock skew and submits once when countdown reaches zero", async () => {
  vi.useFakeTimers();
  const clientNow = new Date("2026-11-14T10:00:00Z");
  vi.setSystemTime(clientNow);
  vi.mocked(examGet).mockResolvedValue({ ...attempt, server_now: "2026-11-14T09:00:00Z", expires_at: "2026-11-14T09:00:03Z" });
  open();
  await act(async () => { await Promise.resolve(); });
  expect(screen.getByRole("timer").textContent).toBe("0:03");
  fireEvent.click(screen.getByLabelText("Đáp án B"));
  await act(async () => { await vi.advanceTimersByTimeAsync(3000); });
  expect(screen.getByText("Kết quả")).toBeTruthy();
  expect(vi.mocked(examPost).mock.calls.filter(([path]) => path.endsWith("/submit"))).toHaveLength(1);
  expect(examPost).toHaveBeenLastCalledWith("/attempts/attempt/submit", { answers: [{ question_id: "q", selected_options: ["B"] }] });
  expect(localStorage.getItem(`${key}:room`)).toBeNull();
});
