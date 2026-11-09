import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { authError } from "@/lib/apiClient";
import { AttemptInfo, ExamInfo, examGet, examPost } from "@/services/examService";

export default function ExamLobby() {
  const { examId } = useParams();
  const [exam, setExam] = useState<ExamInfo | null>(null);
  const [attempt, setAttempt] = useState<AttemptInfo | null>(null);
  const [answers, setAnswers] = useState<Record<string, string[]>>({});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  useEffect(() => {
    let live = true;
    setExam(null); setAttempt(null); setAnswers({}); setError("");
    examGet<ExamInfo>(`/exams/${examId}/lobby`).then(data => { if (live) setExam(data); }).catch(err => { if (live) setError(authError(err)); });
    return () => { live = false; };
  }, [examId]);
  async function start() {
    if (busy) return;
    setBusy(true); setError("");
    try { setAttempt(await examPost<AttemptInfo>(`/exams/${examId}/start`)); }
    catch (err) { setError(authError(err)); } finally { setBusy(false); }
  }
  async function submit() {
    if (!attempt || busy) return;
    setBusy(true); setError("");
    try {
      await examPost(`/attempts/${attempt.attempt_id}/submit`, { answers: attempt.questions.map(q => ({ question_id: q.question_id, selected_options: answers[q.question_id] || [] })) });
      navigate(`/review/${attempt.attempt_id}`);
    } catch (err) { setError(authError(err)); } finally { setBusy(false); }
  }
  return <section className="max-w-3xl mx-auto space-y-5">
    <h1 className="text-2xl font-bold">{attempt ? "Làm bài thi" : "Phòng chờ"}</h1>
    {error && <p role="alert" className="text-red-700">{error}</p>}
    {!exam && !error && <p role="status">Đang tải ca thi…</p>}
    {exam && <div className="bg-white border rounded-xl p-6 space-y-2"><h2 className="text-xl font-semibold">{exam.title}</h2><p>{exam.description}</p><p>{new Date(exam.start_time).toLocaleString("vi-VN")} → {new Date(exam.end_time).toLocaleString("vi-VN")}</p><p>{exam.duration_minutes} phút · Tối đa {exam.max_attempts} lượt</p>
      {!attempt && <><p>Bấm bắt đầu khi đến giờ thi. Nếu đã có lượt đang làm, bạn sẽ tiếp tục lượt đó.</p><button disabled={busy} onClick={start} className="bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-50">Bắt đầu / Tiếp tục</button></>}
    </div>}
    {attempt && <><p>Hạn nộp: {new Date(attempt.expires_at).toLocaleString("vi-VN")}. Câu trả lời trên màn hình chưa được lưu cho đến khi nộp.</p>
      {attempt.questions.map((q, index) => <fieldset disabled={busy} key={q.question_id} className="bg-white border rounded-xl p-5 space-y-3"><legend className="font-semibold">Câu {index+1}</legend><p>{q.content}</p>{q.options.map(option => <label key={option.id} className="flex gap-3"><input type={q.question_type === "MULTIPLE_CHOICE" ? "checkbox" : "radio"} name={q.question_id} checked={(answers[q.question_id] || []).includes(option.id)} onChange={e => setAnswers(old => ({ ...old, [q.question_id]: q.question_type === "MULTIPLE_CHOICE" ? (e.target.checked ? [...(old[q.question_id] || []), option.id] : (old[q.question_id] || []).filter(id => id !== option.id)) : [option.id] }))} />{option.text}</label>)}</fieldset>)}
      <button disabled={busy} onClick={submit} className="bg-blue-600 text-white rounded px-5 py-2 disabled:opacity-50">{busy ? "Đang xử lý…" : "Nộp bài"}</button>
    </>}
    <Link to="/exam/join" className="block text-blue-700">Nhập lại mã phòng / PIN</Link>
  </section>;
}
