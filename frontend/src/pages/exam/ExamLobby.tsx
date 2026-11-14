import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { authError } from "@/lib/apiClient";
import { AttemptInfo, ExamInfo, examGet, examPost } from "@/services/examService";

export default function ExamLobby() {
  const { examId } = useParams();
  const [exam, setExam] = useState<ExamInfo | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  useEffect(() => {
    let live = true;
    setExam(null); setError("");
    examGet<ExamInfo>(`/exams/${examId}/lobby`).then(data => { if (live) setExam(data); }).catch(err => { if (live) setError(authError(err)); });
    return () => { live = false; };
  }, [examId]);
  async function start() {
    if (busy) return;
    setBusy(true); setError("");
    try {
      const attempt = await examPost<AttemptInfo>(`/exams/${examId}/start`);
      navigate(`/exam/${attempt.attempt_id}`);
    } catch (err) { setError(authError(err)); } finally { setBusy(false); }
  }
  return <section className="max-w-3xl mx-auto space-y-5">
    <h1 className="text-2xl font-bold">Phòng chờ</h1>
    {error && <p role="alert" className="text-red-700">{error}</p>}
    {!exam && !error && <p role="status">Đang tải ca thi…</p>}
    {exam && <div className="bg-white border rounded-xl p-6 space-y-2"><h2 className="text-xl font-semibold">{exam.title}</h2><p>{exam.description}</p><p>{new Date(exam.start_time).toLocaleString("vi-VN")} → {new Date(exam.end_time).toLocaleString("vi-VN")}</p><p>{exam.duration_minutes} phút · Tối đa {exam.max_attempts} lượt</p>
      <p>Bấm bắt đầu khi đến giờ thi. Nếu đã có lượt đang làm, bạn sẽ tiếp tục lượt đó.</p><button disabled={busy} onClick={start} className="bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-50">Bắt đầu / Tiếp tục</button>
    </div>}
    <Link to="/exam/join" className="block text-blue-700">Nhập lại mã phòng / PIN</Link>
  </section>;
}
