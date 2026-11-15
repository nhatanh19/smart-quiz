import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { FOCUS_MERGE_MS, useAntiCheatMonitor, ViolationStatus } from "./useAntiCheatMonitor";
import { examPost } from "@/services/examService";
vi.mock("@/services/examService", () => ({ examPost: vi.fn() }));
const status = { status: "IN_PROGRESS", violation_count: 1, max_tab_violations: 3 };
const onStatus = vi.fn();
function Harness({ enabled = true }: { enabled?: boolean }) {
  const monitor = useAntiCheatMonitor({ attemptId: "attempt", enabled, getAnswers: () => [{ question_id: "q", selected_options: ["B"] }], onStatus });
  return <>{monitor.warning && <p>Warning</p>}{monitor.notice && <p>{monitor.notice}</p>}{monitor.syncError && <p role="alert">{monitor.syncError}</p>}</>;
}
beforeEach(() => { vi.resetAllMocks(); vi.mocked(examPost).mockResolvedValue(status); });
afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.useRealTimers(); });

it.each(["blur-first", "visibility-first"])("merges focus events in either order: %s", async order => {
  vi.spyOn(document, "visibilityState", "get").mockReturnValue("hidden");
  render(<Harness />);
  act(() => {
    if (order === "blur-first") { fireEvent.blur(window); fireEvent(document, new Event("visibilitychange")); }
    else { fireEvent(document, new Event("visibilitychange")); fireEvent.blur(window); }
  });
  await waitFor(() => expect(onStatus).toHaveBeenCalledTimes(1));
  expect(examPost).toHaveBeenCalledTimes(1);
  expect(examPost).toHaveBeenCalledWith("/attempts/attempt/log-violation", expect.objectContaining({
    event_type: order === "blur-first" ? "WINDOW_BLUR" : "TAB_SWITCH",
    answers: [{ question_id: "q", selected_options: ["B"] }],
  }));
  expect(screen.getByText("Warning")).toBeTruthy();
});

it("counts separate departures after the merge interval", async () => {
  const clock = vi.spyOn(performance, "now").mockReturnValue(0);
  render(<Harness />); fireEvent.blur(window);
  await waitFor(() => expect(onStatus).toHaveBeenCalledTimes(1));
  clock.mockReturnValue(FOCUS_MERGE_MS + 1); fireEvent.blur(window);
  await waitFor(() => expect(onStatus).toHaveBeenCalledTimes(2));
});

it.each(["copy", "paste", "cut", "contextmenu"])("prevents %s with a light warning", async type => {
  render(<Harness />);
  const event = new Event(type, { bubbles: true, cancelable: true });
  fireEvent(document, event);
  expect(event.defaultPrevented).toBe(true);
  await waitFor(() => expect(onStatus).toHaveBeenCalled());
  expect(examPost).toHaveBeenCalledWith(expect.any(String), expect.objectContaining({ event_type: "COPY_PASTE_ATTEMPT" }));
  expect(screen.queryByText("Warning")).toBeNull();
});

it.each([
  ["F12", false, false, "DEVTOOLS_SHORTCUT"],
  ["I", true, true, "DEVTOOLS_SHORTCUT"],
  ["c", true, false, "COPY_PASTE_ATTEMPT"],
  ["v", true, false, "COPY_PASTE_ATTEMPT"],
])("blocks keyboard shortcut %s", async (key, ctrlKey, shiftKey, event_type) => {
  render(<Harness />);
  const event = new KeyboardEvent("keydown", { key: key as string, ctrlKey: ctrlKey as boolean, shiftKey: shiftKey as boolean, bubbles: true, cancelable: true });
  fireEvent(document, event);
  expect(event.defaultPrevented).toBe(true);
  await waitFor(() => expect(onStatus).toHaveBeenCalled());
  expect(examPost).toHaveBeenCalledWith(expect.any(String), expect.objectContaining({ event_type }));
});

it("does not count held F12 repeatedly or a return to the visible tab", () => {
  render(<Harness />);
  fireEvent.keyDown(document, { key: "F12", repeat: true });
  vi.spyOn(document, "visibilityState", "get").mockReturnValue("visible");
  fireEvent(document, new Event("visibilitychange"));
  expect(examPost).not.toHaveBeenCalled();
});

it("retries a failed event with the same event ID on reconnect", async () => {
  vi.mocked(examPost).mockRejectedValueOnce(new Error("offline")).mockResolvedValueOnce(status);
  render(<Harness />); fireEvent.blur(window);
  await screen.findByRole("alert");
  const first = vi.mocked(examPost).mock.calls[0][1];
  fireEvent(window, new Event("online"));
  await waitFor(() => expect(onStatus).toHaveBeenCalledTimes(1));
  expect(vi.mocked(examPost).mock.calls[1][1]).toEqual(first);
});

it("stops reporting after a terminal server response", async () => {
  vi.mocked(examPost).mockResolvedValue({ ...status, status: "LOCKED_VIOLATION" } satisfies ViolationStatus);
  render(<Harness />); fireEvent.keyDown(document, { key: "F12" });
  await waitFor(() => expect(onStatus).toHaveBeenCalledTimes(1));
  fireEvent.keyDown(document, { key: "F12" });
  expect(examPost).toHaveBeenCalledTimes(1);
});

it("removes listeners on unmount and stays disabled outside an active attempt", () => {
  const first = render(<Harness />); first.unmount();
  fireEvent.blur(window); expect(examPost).not.toHaveBeenCalled();
  render(<Harness enabled={false} />); fireEvent.blur(window);
  expect(examPost).not.toHaveBeenCalled();
});

it("ignores blur and visibilitychange emitted during beforeunload/pagehide reload", () => {
  vi.spyOn(document, "visibilityState", "get").mockReturnValue("hidden");
  render(<Harness />);
  act(() => {
    fireEvent(window, new Event("beforeunload"));
    fireEvent.blur(window);
    fireEvent(document, new Event("visibilitychange"));
  });
  expect(examPost).not.toHaveBeenCalled();
  expect(screen.queryByText("Warning")).toBeNull();
});

it("ignores blur after pagehide without logging violations", () => {
  render(<Harness />);
  act(() => {
    fireEvent(window, new Event("pagehide"));
    fireEvent.blur(window);
  });
  expect(examPost).not.toHaveBeenCalled();
});
