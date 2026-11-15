import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import ExamRoom from "./ExamRoom";
import { examGet, examPost } from "@/services/examService";
vi.mock("@/services/examService", () => ({ examGet: vi.fn(), examPost: vi.fn() }));
vi.mock("@/contexts/AuthContext", () => ({ useAuth: () => ({ user: { id: "student" } }) }));
const key = "smart-quiz:answers:student:attempt";
const attempt = { attempt_id: "attempt", exam_id: "exam", status: "IN_PROGRESS", expires_at: new Date(Date.now() + 600000).toISOString(), questions: [{ question_id: "q", content: "Chọn đáp án", question_type: "SINGLE_CHOICE", options: [{ id: "A", text: "Đáp án A" }, { id: "B", text: "Đáp án B" }] }] };
function open() { return render(<MemoryRouter initialEntries={["/exam/attempt"]}><Routes><Route path="/exam/:attemptId" element={<ExamRoom />} /><Route path="/review/:attemptId" element={<p>Kết quả</p>} /></Routes></MemoryRouter>); }
beforeEach(() => { localStorage.clear(); vi.resetAllMocks(); vi.mocked(examGet).mockResolvedValue(attempt); vi.mocked(examPost).mockResolvedValue({}); });
afterEach(cleanup);
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
