import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { authError } from "@/lib/apiClient";
import { ExamInfo, examPost } from "@/services/examService";

export default function JoinExam() {
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function join(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (busy) return;
    setBusy(true); setError("");
    const form = new FormData(event.currentTarget);
    try {
      const exam = await examPost<ExamInfo>("/exams/join", { exam_code: String(form.get("exam_code")).trim().toUpperCase(), pin: form.get("pin") });
      navigate(`/exam/lobby/${exam.id}`);
    } catch (err) { setError(authError(err)); } finally { setBusy(false); }
  }
  return <section className="max-w-lg mx-auto bg-white border rounded-xl p-6 space-y-4">
    <h1 className="text-2xl font-bold">Vào phòng thi</h1>
    {error && <p role="alert" className="text-red-700">{error}</p>}
    <form onSubmit={join}><fieldset disabled={busy} className="space-y-4">
      <label className="block">Mã phòng<input name="exam_code" required maxLength={12} className="block w-full border p-2 rounded uppercase" /></label>
      <label className="block">PIN<input name="pin" type="password" maxLength={72} className="block w-full border p-2 rounded" /></label>
      <button className="bg-blue-600 text-white rounded px-4 py-2">{busy ? "Đang kiểm tra…" : "Vào phòng chờ"}</button>
    </fieldset></form>
  </section>;
}
