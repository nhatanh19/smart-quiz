import { useEffect, useState, FormEvent } from "react";
import { Question } from "@/types";
import { authError } from "@/lib/apiClient";
import { listQuestions } from "@/services/questionBankApi";
import { ExamInfo, examGet, examPost } from "@/services/examService";

export default function ManageExams() {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [exams, setExams] = useState<ExamInfo[]>([]);
  const [created, setCreated] = useState<ExamInfo | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [page, setPage] = useState(0);
  const [keyword, setKeyword] = useState("");
  useEffect(() => {
    const abort = new AbortController();
    listQuestions({ skip: page * 50, limit: 50, keyword: keyword || undefined }, abort.signal)
      .then(data => setQuestions(data.data || [])).catch(err => { if (!abort.signal.aborted) setError(authError(err)); });
    return () => abort.abort();
  }, [page, keyword]);
  useEffect(() => { examGet<ExamInfo[]>("/exams").then(setExams).catch(err => setError(authError(err))); }, []);
  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setError(""); setBusy(true);
    const form = new FormData(event.currentTarget);
    try {
      if (new Date(String(form.get("end_time"))) <= new Date(String(form.get("start_time")))) {
        setError("Giờ đóng phải sau giờ mở."); return;
      }
      if (new TextEncoder().encode(String(form.get("pin") || "")).length > 72) {
        setError("PIN tối đa 72 byte UTF-8."); return;
      }
      const exam = await examPost<ExamInfo>("/exams", {
        title: form.get("title"), description: form.get("description") || null,
        start_time: new Date(String(form.get("start_time"))).toISOString(),
        end_time: new Date(String(form.get("end_time"))).toISOString(),
        duration_minutes: Number(form.get("duration_minutes")), max_attempts: Number(form.get("max_attempts")),
        pin: form.get("pin") || null, is_published: form.has("is_published"),
        shuffle_questions: form.has("shuffle_questions"), shuffle_options: form.has("shuffle_options"),
        questions: selected.map(question_id => ({ question_id, points: 1 })),
      });
      setCreated(exam); setExams(previous => [exam, ...previous]);
    } catch (err) { setError(authError(err)); } finally { setBusy(false); }
  }
  const input = "block w-full border rounded p-2 mt-1";
  return <section className="space-y-6">
    <h1 className="text-2xl font-bold">Quản lý ca thi</h1>
    {error && <p role="alert" className="text-red-700">{error}</p>}
    {created && <p role="status" className="p-4 bg-green-50">Đã tạo {created.title}. Mã phòng: <strong>{created.exam_code}</strong> — {created.is_published ? "Đã công bố" : "Bản nháp"}</p>}
    <form onSubmit={create} className="bg-white rounded-xl border p-6 space-y-4">
      <h2 className="text-xl font-semibold">Tạo ca thi</h2>
      <fieldset disabled={busy} className="space-y-4">
        <label className="block">Tên ca thi<input className={input} name="title" required maxLength={255} /></label>
        <label className="block">Hướng dẫn<textarea className={input} name="description" /></label>
        <div className="grid sm:grid-cols-2 gap-4">
          <label>Giờ mở (giờ địa phương)<input className={input} type="datetime-local" name="start_time" required /></label>
          <label>Giờ đóng (giờ địa phương)<input className={input} type="datetime-local" name="end_time" required /></label>
          <label>Thời lượng (phút)<input className={input} type="number" min={1} name="duration_minutes" defaultValue={30} required /></label>
          <label>Số lượt tối đa<input className={input} type="number" min={1} name="max_attempts" defaultValue={1} required /></label>
        </div>
        <label className="block">PIN (để trống nếu không dùng)<input className={input} type="password" name="pin" maxLength={72} autoComplete="new-password" /></label>
        <div className="flex flex-wrap gap-4">
          <label><input type="checkbox" name="shuffle_questions" defaultChecked /> Trộn câu hỏi</label>
          <label><input type="checkbox" name="shuffle_options" defaultChecked /> Trộn phương án</label>
          <label><input type="checkbox" name="is_published" defaultChecked /> Công bố ca thi</label>
        </div>
        <h3 className="font-semibold">Chọn câu hỏi ({selected.length}) — mỗi câu 1 điểm</h3>
        <label>Tìm câu hỏi<input className={input} value={keyword} onChange={e => { setKeyword(e.target.value); setPage(0); }} /></label>
        <div className="max-h-72 overflow-auto border rounded divide-y">
          {questions.map(q => <label key={q.id} className="flex gap-3 p-3"><input type="checkbox" checked={selected.includes(q.id)} onChange={e => setSelected(old => e.target.checked ? [...old, q.id] : old.filter(id => id !== q.id))} /><span>{q.content}</span></label>)}
          {!questions.length && <p className="p-3">Không có câu hỏi.</p>}
        </div>
        <div className="flex gap-4"><button type="button" disabled={!page} onClick={() => setPage(p => p-1)}>Trang trước</button><span>Trang {page+1}</span><button type="button" disabled={questions.length < 50} onClick={() => setPage(p => p+1)}>Trang sau</button></div>
        <button disabled={busy || !selected.length} className="rounded bg-blue-600 text-white px-4 py-2 disabled:opacity-50">{busy ? "Đang tạo…" : "Tạo ca thi"}</button>
      </fieldset>
    </form>
    <h2 className="text-xl font-semibold">Ca thi đã tạo</h2>
    <ul className="space-y-2">{exams.map(e => <li key={e.id} className="bg-white border rounded p-4">{e.title} — <strong>{e.exam_code}</strong> — {e.is_published ? "Đã công bố" : "Bản nháp"}<p className="text-sm text-slate-600">{new Date(e.start_time).toLocaleString("vi-VN")} → {new Date(e.end_time).toLocaleString("vi-VN")} · {e.duration_minutes} phút · {e.max_attempts} lượt</p></li>)}</ul>
  </section>;
}
