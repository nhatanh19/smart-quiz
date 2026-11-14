import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { authError } from "@/lib/apiClient";
import { AttemptInfo, examGet, examPost } from "@/services/examService";

type Answers = Record<string, string[]>;

export default function ExamRoom() {
  const { attemptId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [attempt, setAttempt] = useState<AttemptInfo | null>(null);
  const [answers, setAnswers] = useState<Answers>({});
  const [current, setCurrent] = useState(0);
  const [remaining, setRemaining] = useState(0);
  const [error, setError] = useState("");
  const [storageError, setStorageError] = useState("");
  const [busy, setBusy] = useState(false);
  const [confirm, setConfirm] = useState(false);
  const pending = useRef(false);
  const autoSubmitted = useRef(false);
  const saving = useRef(Promise.resolve());
  const key = `smart-quiz:answers:${user?.id}:${attemptId}`;
  const latest = useRef(answers);
  latest.current = answers;

  function persist() {
    try { localStorage.setItem(key, JSON.stringify(latest.current)); }
    catch { setStorageError("Không thể lưu trên thiết bị. Hãy giữ trang mở cho đến khi nộp bài."); }
  }

  useEffect(() => {
    let live = true;
    setAttempt(null); setAnswers({}); setCurrent(0); setError("");
    autoSubmitted.current = false;
    examGet<AttemptInfo>(`/attempts/${attemptId}`).then(data => {
      if (!live) return;
      if (data.status !== "IN_PROGRESS") { navigate(`/review/${attemptId}`, { replace: true }); return; }
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
      setAnswers(recovered);
      setRemaining(Math.max(0, Math.ceil((Date.parse(data.expires_at) - Date.now()) / 1000)));
      setAttempt(data);
    }).catch(err => { if (live) setError(authError(err)); });
    return () => { live = false; };
  }, [attemptId, key, navigate]);

  useEffect(() => {
    if (!attempt) return;
    const timer = window.setTimeout(persist, 300);
    const flush = () => persist();
    window.addEventListener("pagehide", flush);
    return () => { window.clearTimeout(timer); window.removeEventListener("pagehide", flush); };
  }, [answers, attempt, key]);

  useEffect(() => {
    if (!attempt) return;
    const save = () => {
      if (pending.current || Date.now() >= Date.parse(attempt.expires_at)) return;
      const payload = { answers: attempt.questions.map(q => ({ question_id: q.question_id, selected_options: latest.current[q.question_id] || [] })) };
      saving.current = saving.current.then(async () => {
        await examPost(`/attempts/${attempt.attempt_id}/answers`, payload);
        setError("");
      }).catch(() => setError("Chưa đồng bộ được đáp án. Bản lưu trên thiết bị vẫn được giữ; hãy kết nối lại trước khi hết giờ."));
    };
    const timer = window.setTimeout(save, 300);
    window.addEventListener("online", save);
    return () => { window.clearTimeout(timer); window.removeEventListener("online", save); };
  }, [answers, attempt]);

  async function submit() {
    if (!attempt || pending.current) return;
    pending.current = true; setBusy(true); setError(""); setConfirm(false);
    persist();
    try {
      await saving.current;
      await examPost(`/attempts/${attempt.attempt_id}/submit`, {
        answers: attempt.questions.map(q => ({ question_id: q.question_id, selected_options: latest.current[q.question_id] || [] })),
      });
      try { localStorage.removeItem(key); } catch { /* Submission already persisted on server. */ }
      navigate(`/review/${attempt.attempt_id}`, { replace: true });
    } catch (err) {
      // A lost response may hide a successful commit. Check before offering a retry.
      try {
        const currentAttempt = await examGet<AttemptInfo>(`/attempts/${attempt.attempt_id}`);
        if (currentAttempt.status !== "IN_PROGRESS") {
          try { localStorage.removeItem(key); } catch { /* Keep review available. */ }
          navigate(`/review/${attempt.attempt_id}`, { replace: true });
          return;
        }
      } catch { /* Keep the original submission error and local recovery data. */ }
      setError(authError(err));
    }
    finally { pending.current = false; setBusy(false); }
  }

  useEffect(() => {
    if (!attempt) return;
    function tick() {
      const seconds = Math.max(0, Math.ceil((Date.parse(attempt!.expires_at) - Date.now()) / 1000));
      setRemaining(seconds);
      if (seconds === 0 && !autoSubmitted.current) { autoSubmitted.current = true; void submit(); }
    }
    tick();
    const timer = window.setInterval(tick, 1000);
    const online = () => { if (Date.now() >= Date.parse(attempt.expires_at)) void submit(); };
    window.addEventListener("online", online);
    return () => { window.clearInterval(timer); window.removeEventListener("online", online); };
  }, [attempt]);

  const question = attempt?.questions[current];
  const answered = attempt?.questions.filter(q => answers[q.question_id]?.length).length || 0;
  return <section className="max-w-5xl mx-auto p-6 space-y-5">
    <header className="flex justify-between items-center"><h1 className="text-2xl font-bold">Phòng thi</h1><p role="timer" aria-label="Thời gian còn lại" className={remaining <= 60 ? "text-red-700 font-bold" : "font-bold"}>{Math.floor(remaining / 60)}:{String(remaining % 60).padStart(2, "0")}</p></header>
    {error && <p role="alert" className="text-red-700">{error}</p>}
    {storageError && <p role="status">{storageError}</p>}
    {!attempt && !error && <p role="status">Đang tải bài thi…</p>}
    {attempt && <>
      <p>Đã trả lời {answered}/{attempt.questions.length} câu. Đáp án được lưu tự động trên thiết bị.</p>
      <nav aria-label="Điều hướng câu hỏi" className="flex flex-wrap gap-2">{attempt.questions.map((q, i) => <button key={q.question_id} aria-current={i === current ? "step" : undefined} onClick={() => setCurrent(i)} className={`border rounded px-3 py-2 ${answers[q.question_id]?.length ? "bg-blue-100" : "bg-white"}`}>Câu {i + 1}{answers[q.question_id]?.length ? " ✓" : ""}</button>)}</nav>
      {question && <fieldset disabled={busy || remaining === 0} className="bg-white border rounded-xl p-6 space-y-4"><legend className="font-bold">Câu {current + 1}</legend><p className="whitespace-pre-wrap">{question.content}</p>{question.options.map(option => <label key={option.id} className="flex gap-3 items-center"><input type={question.question_type === "MULTIPLE_CHOICE" ? "checkbox" : "radio"} name={question.question_id} checked={(answers[question.question_id] || []).includes(option.id)} onChange={e => {
        const selected = answers[question.question_id] || [];
        const next = { ...answers, [question.question_id]: question.question_type === "MULTIPLE_CHOICE" ? (e.target.checked ? [...selected, option.id] : selected.filter(id => id !== option.id)) : [option.id] };
        latest.current = next; setAnswers(next);
        // Flush each interaction as well as the debounce, so immediate reloads cannot lose answers.
        try { localStorage.setItem(key, JSON.stringify(next)); } catch { setStorageError("Không thể lưu đáp án trên thiết bị."); }
      }} />{option.text}</label>)}</fieldset>}
      <div className="flex gap-3"><button disabled={current === 0} onClick={() => setCurrent(i => i - 1)}>Câu trước</button><button disabled={current >= attempt.questions.length - 1} onClick={() => setCurrent(i => i + 1)}>Câu tiếp</button><button disabled={busy} onClick={() => remaining === 0 ? void submit() : setConfirm(true)} className="bg-blue-600 text-white px-5 py-2 rounded">{busy ? "Đang nộp…" : remaining === 0 ? "Thử nộp lại" : "Nộp bài"}</button></div>
      {confirm && <div role="dialog" aria-modal="true" aria-label="Xác nhận nộp bài" className="fixed inset-0 bg-slate-900/70 flex items-center justify-center"><div className="bg-white rounded-xl p-6 space-y-4"><p>Bạn đã trả lời {answered}/{attempt.questions.length} câu. Xác nhận nộp bài?</p><button onClick={() => setConfirm(false)} className="mr-5">Tiếp tục làm bài</button><button onClick={() => void submit()}>Xác nhận nộp</button></div></div>}
    </>}
  </section>;
}
