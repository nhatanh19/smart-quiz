import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import axios from "axios";
import { useAuth } from "@/contexts/AuthContext";
import { authError } from "@/lib/apiClient";
import { AttemptInfo, examGet, examPost } from "@/services/examService";
import { useAntiCheatMonitor, ViolationStatus } from "@/hooks/useAntiCheatMonitor";

type Answers = Record<string, string[]>;

export default function ExamRoom() {
  const { attemptId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [attempt, setAttempt] = useState<AttemptInfo | null>(null);
  const [answers, setAnswers] = useState<Answers>({});
  const [current, setCurrent] = useState(0);
  const [marked, setMarked] = useState<string[]>([]);
  const [offlineRecovery, setOfflineRecovery] = useState(false);
  const [remaining, setRemaining] = useState(0);
  const [error, setError] = useState("");
  const [storageError, setStorageError] = useState("");
  const [busy, setBusy] = useState(false);
  const [confirm, setConfirm] = useState(false);
  const [violationStatus, setViolationStatus] = useState<ViolationStatus | null>(null);
  const ended = useRef(false);
  const pending = useRef(false);
  const autoSubmitted = useRef(false);
  const saving = useRef(Promise.resolve());
  const key = `smart-quiz:answers:${user?.id}:${attemptId}`;
  const roomKey = `${key}:room`;
  const clockOffset = useRef(0);
  const latest = useRef(answers);
  latest.current = answers;
  const monitor = useAntiCheatMonitor({
    attemptId: attempt?.attempt_id,
    enabled: !!attempt && attempt.attempt_id === attemptId && !ended.current,
    paused: busy || remaining <= 0,
    getAnswers: () => attempt?.questions.map(q => ({ question_id: q.question_id, selected_options: latest.current[q.question_id] || [] })) || [],
    onStatus: status => {
      setViolationStatus(status);
      if (status.status !== "IN_PROGRESS") {
        ended.current = true;
        clearCache();
        navigate(`/review/${attemptId}`, { replace: true });
      }
    },
  });

  function clearCache() {
    for (const cacheKey of [key, roomKey]) {
      try { localStorage.removeItem(cacheKey); } catch { /* Server has already closed the attempt. */ }
    }
  }

  function secondsLeft(data: AttemptInfo) {
    return Math.max(0, Math.ceil((Date.parse(data.expires_at) - Date.now() - clockOffset.current) / 1000));
  }

  function persist() {
    if (ended.current) return;
    try { localStorage.setItem(key, JSON.stringify(latest.current)); }
    catch { setStorageError("Không thể lưu trên thiết bị. Hãy giữ trang mở cho đến khi nộp bài."); }
  }

  useEffect(() => {
    let live = true;
    setAttempt(null); setAnswers({}); setMarked([]); setCurrent(0); setError("");
    setStorageError(""); setOfflineRecovery(false);
    clockOffset.current = 0;
    autoSubmitted.current = false;
    ended.current = false;
    setViolationStatus(null);
    function restore(data: AttemptInfo, offline = false) {
      if (!live) return;
      if (data.status !== "IN_PROGRESS") {
        ended.current = true;
        clearCache();
        navigate(`/review/${attemptId}`, { replace: true }); return;
      }
      const recovered: Answers = { ...data.answers };
      try {
        const cached = JSON.parse(localStorage.getItem(key) || "{}");
        for (const q of data.questions) {
          const selected = cached?.[q.question_id];
          if (Array.isArray(selected)) {
            const valid = [...new Set(selected.filter((id): id is string => typeof id === "string" && q.options.some(o => o.id === id)))];
            recovered[q.question_id] = q.question_type === "MULTIPLE_CHOICE" ? valid : valid.slice(0, 1);
          }
        }
      } catch { setStorageError("Không đọc được bản lưu trên thiết bị."); }
      try {
        const room = JSON.parse(localStorage.getItem(roomKey) || "null");
        const validMarks: string[] = Array.isArray(room?.marked) ? room.marked.filter((id: unknown) => typeof id === "string" && data.questions.some(q => q.question_id === id)) : [];
        setMarked([...new Set(validMarks)]);
        const index = data.questions.findIndex(q => q.question_id === room?.currentQuestionId);
        setCurrent(index < 0 ? 0 : index);
        if (offline && typeof room?.clockOffset === "number" && Number.isFinite(room.clockOffset)) clockOffset.current = room.clockOffset;
      } catch { /* Answers can still be restored independently. */ }
      if (!offline && data.server_now && Number.isFinite(Date.parse(data.server_now))) clockOffset.current = Date.parse(data.server_now) - Date.now();
      setAnswers(recovered);
      setRemaining(secondsLeft(data));
      setAttempt(data);
      setOfflineRecovery(offline);
    }
    examGet<AttemptInfo>(`/attempts/${attemptId}`).then(data => restore(data)).catch(err => {
      if (!live) return;
      const networkError = !(axios.isAxiosError(err) && err.response) && ((axios.isAxiosError(err) && !err.response) || !navigator.onLine);
      if (networkError) {
        try {
          const cached = JSON.parse(localStorage.getItem(roomKey) || "null")?.attempt;
          if (cached?.attempt_id === attemptId && cached.status === "IN_PROGRESS" && Number.isFinite(Date.parse(cached.expires_at)) && Array.isArray(cached.questions) && cached.questions.every((q: AttemptInfo["questions"][number]) => q && typeof q.question_id === "string" && typeof q.content === "string" && Array.isArray(q.options) && q.options.every(o => o && typeof o.id === "string" && typeof o.text === "string"))) {
            restore(cached, true); return;
          }
        } catch { /* Fall through to the original request error. */ }
      }
      setError(authError(err));
    });
    return () => { live = false; };
  }, [attemptId, key, navigate]);

  useEffect(() => {
    if (!attempt || attempt.attempt_id !== attemptId || ended.current) return;
    try {
      localStorage.setItem(roomKey, JSON.stringify({ attempt, marked, currentQuestionId: attempt.questions[current]?.question_id, clockOffset: clockOffset.current }));
    } catch { setStorageError("Không thể lưu đầy đủ phòng thi trên thiết bị. Hãy giữ trang mở."); }
  }, [attempt, marked, current, roomKey]);

  useEffect(() => {
    if (!attempt || attempt.attempt_id !== attemptId) return;
    let live = true;
    const reconnect = async () => {
      try {
        const fresh = await examGet<AttemptInfo>(`/attempts/${attempt.attempt_id}`);
        if (!live) return;
        if (fresh.status !== "IN_PROGRESS") {
          ended.current = true; clearCache();
          navigate(`/review/${attempt.attempt_id}`, { replace: true }); return;
        }
        if (fresh.server_now && Number.isFinite(Date.parse(fresh.server_now))) clockOffset.current = Date.parse(fresh.server_now) - Date.now();
        setOfflineRecovery(false);
      } catch { /* Keep the local snapshot and answers until the network recovers. */ }
    };
    window.addEventListener("online", reconnect);
    return () => { live = false; window.removeEventListener("online", reconnect); };
  }, [attempt, roomKey, navigate]);

  useEffect(() => {
    if (!attempt || attempt.attempt_id !== attemptId) return;
    const timer = window.setTimeout(persist, 300);
    const flush = () => persist();
    window.addEventListener("pagehide", flush);
    return () => { window.clearTimeout(timer); window.removeEventListener("pagehide", flush); };
  }, [answers, attempt, key]);

  useEffect(() => {
    if (!attempt || attempt.attempt_id !== attemptId) return;
    const save = () => {
      if (pending.current || ended.current || secondsLeft(attempt) === 0) return;
      const payload = { answers: attempt.questions.map(q => ({ question_id: q.question_id, selected_options: latest.current[q.question_id] || [] })) };
      saving.current = saving.current.then(async () => {
        if (ended.current) return;
        await examPost(`/attempts/${attempt.attempt_id}/answers`, payload);
        setError("");
      }).catch(() => setError("Chưa đồng bộ được đáp án. Bản lưu trên thiết bị vẫn được giữ; hãy kết nối lại trước khi hết giờ."));
    };
    const timer = window.setTimeout(save, 300);
    window.addEventListener("online", save);
    return () => { window.clearTimeout(timer); window.removeEventListener("online", save); };
  }, [answers, attempt]);

  async function submit() {
    if (!attempt || attempt.attempt_id !== attemptId || pending.current || ended.current) return;
    pending.current = true; setBusy(true); setError(""); setConfirm(false);
    persist();
    try {
      await saving.current;
      if (ended.current) return;
      await examPost(`/attempts/${attempt.attempt_id}/submit`, {
        answers: attempt.questions.map(q => ({ question_id: q.question_id, selected_options: latest.current[q.question_id] || [] })),
      });
      ended.current = true;
      clearCache();
      navigate(`/review/${attempt.attempt_id}`, { replace: true });
    } catch (err) {
      // A lost response may hide a successful commit. Check before offering a retry.
      try {
        const currentAttempt = await examGet<AttemptInfo>(`/attempts/${attempt.attempt_id}`);
        if (currentAttempt.status !== "IN_PROGRESS") {
          ended.current = true;
          clearCache();
          navigate(`/review/${attempt.attempt_id}`, { replace: true });
          return;
        }
      } catch { /* Keep the original submission error and local recovery data. */ }
      setError(authError(err));
    }
    finally { pending.current = false; setBusy(false); }
  }

  useEffect(() => {
    if (!attempt || attempt.attempt_id !== attemptId) return;
    function tick() {
      const seconds = secondsLeft(attempt!);
      setRemaining(seconds);
      if (seconds === 0 && !autoSubmitted.current && !ended.current) { autoSubmitted.current = true; void submit(); }
    }
    tick();
    const timer = window.setInterval(tick, 1000);
    const online = () => { if (secondsLeft(attempt) === 0) void submit(); };
    window.addEventListener("online", online);
    return () => { window.clearInterval(timer); window.removeEventListener("online", online); };
  }, [attempt]);

  const question = attempt?.questions[current];
  const answered = attempt?.questions.filter(q => answers[q.question_id]?.length).length || 0;
  return <section className="max-w-5xl mx-auto p-6 space-y-5">
    <header className="flex justify-between items-center"><h1 className="text-2xl font-bold">Phòng thi</h1><p role="timer" aria-label="Thời gian còn lại" className={remaining <= 60 ? "text-red-700 font-bold" : "font-bold"}>{Math.floor(remaining / 60)}:{String(remaining % 60).padStart(2, "0")}</p></header>
    {error && <p role="alert" className="text-red-700">{error}</p>}
    {storageError && <p role="status">{storageError}</p>}
    {offlineRecovery && <p role="status" className="text-amber-800">Đang dùng bản lưu trên thiết bị. Hãy kết nối lại trước khi hết giờ để đồng bộ đáp án.</p>}
    {monitor.notice && <p role="status" className="text-amber-800">{monitor.notice}</p>}
    {monitor.syncError && <p role="alert" className="text-red-700">{monitor.syncError}</p>}
    {!attempt && !error && <p role="status">Đang tải bài thi…</p>}
    {attempt && <>
      <p>Đã trả lời {answered}/{attempt.questions.length} câu. Đáp án được lưu tự động trên thiết bị.</p>
      <p className="text-sm text-slate-600">✓ Đã làm · Chưa làm · ⚑ Đánh dấu ({marked.length})</p>
      <nav aria-label="Điều hướng câu hỏi" className="flex flex-wrap gap-2">{attempt.questions.map((q, i) => <button key={q.question_id} aria-label={`Câu ${i + 1}, ${answers[q.question_id]?.length ? "đã làm" : "chưa làm"}${marked.includes(q.question_id) ? ", đánh dấu" : ""}`} aria-current={i === current ? "step" : undefined} onClick={() => setCurrent(i)} className={`border rounded px-3 py-2 ${marked.includes(q.question_id) ? "border-amber-600 bg-amber-100" : answers[q.question_id]?.length ? "bg-blue-100" : "bg-white"} ${i === current ? "ring-2 ring-blue-600" : ""}`}>Câu {i + 1}{answers[q.question_id]?.length ? " ✓" : ""}{marked.includes(q.question_id) ? " ⚑" : ""}</button>)}</nav>
      {question && <button disabled={busy || remaining === 0} aria-pressed={marked.includes(question.question_id)} onClick={() => {
        const next = marked.includes(question.question_id) ? marked.filter(id => id !== question.question_id) : [...marked, question.question_id];
        setMarked(next);
        try { localStorage.setItem(roomKey, JSON.stringify({ attempt, marked: next, currentQuestionId: question.question_id, clockOffset: clockOffset.current })); }
        catch { setStorageError("Không thể lưu đánh dấu trên thiết bị."); }
      }} className="border border-amber-600 text-amber-900 rounded px-4 py-2">{marked.includes(question.question_id) ? "Bỏ đánh dấu câu hỏi" : "Đánh dấu câu hỏi"}</button>}
      {question && <fieldset disabled={busy || remaining === 0} className="bg-white border rounded-xl p-6 space-y-4"><legend className="font-bold">Câu {current + 1}</legend><p className="whitespace-pre-wrap">{question.content}</p>{question.options.map(option => <label key={option.id} className="flex gap-3 items-center"><input type={question.question_type === "MULTIPLE_CHOICE" ? "checkbox" : "radio"} name={question.question_id} checked={(answers[question.question_id] || []).includes(option.id)} onChange={e => {
        const selected = answers[question.question_id] || [];
        const next = { ...answers, [question.question_id]: question.question_type === "MULTIPLE_CHOICE" ? (e.target.checked ? [...selected, option.id] : selected.filter(id => id !== option.id)) : [option.id] };
        latest.current = next; setAnswers(next);
        // Flush each interaction as well as the debounce, so immediate reloads cannot lose answers.
        try { localStorage.setItem(key, JSON.stringify(next)); } catch { setStorageError("Không thể lưu đáp án trên thiết bị."); }
      }} />{option.text}</label>)}</fieldset>}
      <div className="flex gap-3"><button disabled={current === 0} onClick={() => setCurrent(i => i - 1)}>Câu trước</button><button disabled={current >= attempt.questions.length - 1} onClick={() => setCurrent(i => i + 1)}>Câu tiếp</button><button disabled={busy} onClick={() => remaining === 0 ? void submit() : setConfirm(true)} className="bg-blue-600 text-white px-5 py-2 rounded">{busy ? "Đang nộp…" : remaining === 0 ? "Thử nộp lại" : "Nộp bài"}</button></div>
      {confirm && <div role="dialog" aria-modal="true" aria-label="Xác nhận nộp bài" className="fixed inset-0 bg-slate-900/70 flex items-center justify-center"><div className="bg-white rounded-xl p-6 space-y-4"><p>Bạn đã trả lời {answered}/{attempt.questions.length} câu. Xác nhận nộp bài?</p><button onClick={() => setConfirm(false)} className="mr-5">Tiếp tục làm bài</button><button onClick={() => void submit()}>Xác nhận nộp</button></div></div>}
      {monitor.warning && <div role="alertdialog" aria-modal="true" aria-labelledby="violation-title" aria-describedby="violation-description" className="fixed inset-0 z-50 bg-slate-950/90 flex items-center justify-center p-6">
        <div className="bg-white rounded-xl p-8 max-w-lg space-y-5">
          <h2 id="violation-title" className="text-2xl font-bold text-red-700">Cảnh báo vi phạm quy chế thi</h2>
          <p id="violation-description">Vui lòng giữ nguyên cửa sổ làm bài và không mở công cụ phát triển. Bài thi sẽ tự khóa khi đạt ngưỡng.</p>
          <p>Số lần vi phạm được server xác nhận: <strong>{violationStatus?.violation_count ?? attempt.violation_count} / {violationStatus?.max_tab_violations ?? attempt.max_tab_violations}</strong></p>
          {monitor.syncError && <p role="status">{monitor.syncError}</p>}
          <button autoFocus onClick={monitor.dismissWarning} className="bg-blue-700 text-white px-5 py-3 rounded">Tôi đã hiểu, tiếp tục làm bài</button>
        </div>
      </div>}
    </>}
  </section>;
}
