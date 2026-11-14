import { useEffect, useRef, useState } from "react";
import axios from "axios";
import { examPost } from "@/services/examService";

export type ViolationType = "TAB_SWITCH" | "WINDOW_BLUR" | "COPY_PASTE_ATTEMPT" | "DEVTOOLS_SHORTCUT";
export interface ViolationStatus {
  status: string;
  violation_count: number;
  max_tab_violations: number;
}
interface ViolationPayload {
  event_id: string;
  event_type: ViolationType;
  metadata_info: Record<string, unknown>;
  answers: { question_id: string; selected_options: string[] }[];
}
interface Options {
  attemptId?: string;
  enabled: boolean;
  paused?: boolean;
  getAnswers: () => ViolationPayload["answers"];
  onStatus: (status: ViolationStatus) => void;
}

// Merge the two browser events from the same departure, in either event order.
export const FOCUS_MERGE_MS = 750;

export function useAntiCheatMonitor(options: Options) {
  const latest = useRef(options);
  latest.current = options;
  const [warning, setWarning] = useState(false);
  const [notice, setNotice] = useState("");
  const [syncError, setSyncError] = useState("");

  useEffect(() => {
    if (!options.enabled || !options.attemptId) return;
    let active = true;
    let lastFocusEvent = -Infinity;
    const queue: ViolationPayload[] = [];
    let sending = false;
    let stopped = false;
    let retry: ReturnType<typeof setTimeout> | undefined;
    let noticeTimer: ReturnType<typeof setTimeout> | undefined;

    async function drain() {
      if (sending || stopped || !active) return;
      if (retry) { clearTimeout(retry); retry = undefined; }
      sending = true;
      try {
        while (active && queue.length && !stopped) {
          try {
            const status = await examPost<ViolationStatus>(`/attempts/${options.attemptId}/log-violation`, queue[0]);
            if (!active) return;
            queue.shift();
            setSyncError("");
            if (status.status !== "IN_PROGRESS") { stopped = true; queue.length = 0; }
            latest.current.onStatus(status);
          } catch (error) {
            if (!active) return;
            const code = axios.isAxiosError(error) ? error.response?.status : undefined;
            if (code && code < 500) {
              stopped = true;
              setSyncError("Không ghi nhận được sự kiện. Vui lòng tải lại phòng thi để kiểm tra trạng thái bài.");
            } else {
              setSyncError("Chưa gửi được nhật ký vi phạm. Hệ thống sẽ thử lại khi có mạng; hãy giữ trang mở.");
              retry = setTimeout(() => { void drain(); }, 3000);
            }
            break;
          }
        }
      } finally { sending = false; }
    }

    function report(event_type: ViolationType, source: string) {
      if (stopped || !active || latest.current.paused) return;
      if (event_type === "TAB_SWITCH" || event_type === "WINDOW_BLUR") {
        const timestamp = performance.now();
        if (timestamp - lastFocusEvent < FOCUS_MERGE_MS) return;
        lastFocusEvent = timestamp;
      }
      if (event_type === "COPY_PASTE_ATTEMPT") {
        setNotice("Thao tác sao chép/dán hoặc chuột phải đã bị chặn. Sự kiện này không tăng số lần vi phạm.");
        if (noticeTimer) clearTimeout(noticeTimer);
        noticeTimer = setTimeout(() => setNotice(""), 4000);
      } else { setWarning(true); }
      queue.push({
        event_id: crypto.randomUUID(), event_type,
        metadata_info: { client_ts: new Date().toISOString(), visibility_state: document.visibilityState, source },
        answers: latest.current.getAnswers().map(a => ({ ...a, selected_options: [...a.selected_options] })),
      });
      void drain();
    }

    const visibility = () => { if (document.visibilityState === "hidden") report("TAB_SWITCH", "visibilitychange"); };
    const blur = () => report("WINDOW_BLUR", "blur");
    const clipboard = (event: Event) => { event.preventDefault(); report("COPY_PASTE_ATTEMPT", event.type); };
    const keydown = (event: KeyboardEvent) => {
      const key = event.key.toLowerCase();
      const devtools = key === "f12" || ((event.ctrlKey || event.metaKey) && event.shiftKey && ["i", "j", "c"].includes(key));
      const copyPaste = (event.ctrlKey || event.metaKey) && ["c", "v", "x"].includes(key);
      if (!devtools && !copyPaste) return;
      event.preventDefault();
      if (!event.repeat) report(devtools ? "DEVTOOLS_SHORTCUT" : "COPY_PASTE_ATTEMPT", event.key);
    };
    const online = () => { void drain(); };
    document.addEventListener("visibilitychange", visibility);
    window.addEventListener("blur", blur);
    document.addEventListener("keydown", keydown, true);
    for (const type of ["copy", "paste", "cut", "contextmenu"]) document.addEventListener(type, clipboard, true);
    window.addEventListener("online", online);
    return () => {
      active = false;
      if (retry) clearTimeout(retry);
      if (noticeTimer) clearTimeout(noticeTimer);
      document.removeEventListener("visibilitychange", visibility);
      window.removeEventListener("blur", blur);
      document.removeEventListener("keydown", keydown, true);
      for (const type of ["copy", "paste", "cut", "contextmenu"]) document.removeEventListener(type, clipboard, true);
      window.removeEventListener("online", online);
    };
  }, [options.enabled, options.attemptId]);

  return { warning, dismissWarning: () => setWarning(false), notice, syncError };
}
