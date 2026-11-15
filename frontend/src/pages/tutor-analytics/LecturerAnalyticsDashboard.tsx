import React, { useEffect, useState } from "react";
import {
  BarChart3,
  Download,
  AlertCircle,
  TrendingUp,
  Award,
  Users,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Clock,
  Search,
  Filter,
  RefreshCw,
} from "lucide-react";
import {
  AccessibleExam,
  ExamAnalyticsData,
  tutorService,
} from "@/services/tutorService";

interface LecturerAnalyticsDashboardProps {
  initialExamId?: string;
}

export const LecturerAnalyticsDashboard: React.FC<LecturerAnalyticsDashboardProps> = ({
  initialExamId,
}) => {
  const [exams, setExams] = useState<AccessibleExam[]>([]);
  const [selectedExamId, setSelectedExamId] = useState<string>(initialExamId || "");
  const [analytics, setAnalytics] = useState<ExamAnalyticsData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [loadingExams, setLoadingExams] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [exportingCsv, setExportingCsv] = useState<boolean>(false);
  const [studentSearch, setStudentSearch] = useState<string>("");

  // Load list of exams managed by instructor
  useEffect(() => {
    let mounted = true;
    async function loadExams() {
      setLoadingExams(true);
      try {
        const list = await tutorService.getInstructorExams();
        if (mounted) {
          setExams(list);
          if (list.length > 0 && !selectedExamId) {
            setSelectedExamId(list[0].id);
          }
        }
      } catch (err: any) {
        if (mounted) {
          setError(err.message || "Không thể tải danh sách đề thi.");
        }
      } finally {
        if (mounted) setLoadingExams(false);
      }
    }
    loadExams();
    return () => {
      mounted = false;
    };
  }, []);

  // Fetch analytics whenever selectedExamId changes
  useEffect(() => {
    if (!selectedExamId) return;

    let mounted = true;
    async function loadAnalytics() {
      setLoading(true);
      setError(null);
      try {
        const data = await tutorService.getExamAnalytics(selectedExamId);
        if (mounted) {
          setAnalytics(data);
        }
      } catch (err: any) {
        if (mounted) {
          setError(err.message || "Không thể tải dữ liệu phân tích đề thi.");
          setAnalytics(null);
        }
      } finally {
        if (mounted) setLoading(false);
      }
    }
    loadAnalytics();
    return () => {
      mounted = false;
    };
  }, [selectedExamId]);

  // Handler for CSV Export
  const handleExportCsv = async () => {
    if (!selectedExamId || !analytics) return;
    setExportingCsv(true);
    try {
      await tutorService.downloadExamCsv(selectedExamId, analytics.exam_code);
    } catch (err: any) {
      alert(err.message || "Xuất CSV thất bại.");
    } finally {
      setExportingCsv(false);
    }
  };

  // Filter students
  const filteredStudents = (analytics?.student_scores || []).filter((s) => {
    const query = studentSearch.toLowerCase();
    return (
      s.student_name.toLowerCase().includes(query) ||
      s.student_email.toLowerCase().includes(query) ||
      s.score.toString().includes(query)
    );
  });

  const maxHistogramCount = Math.max(
    ...(analytics?.score_distribution.map((b) => b.count) || [1]),
    1
  );

  return (
    <div className="space-y-6">
      {/* Header & Exam Selector */}
      <div className="bg-white p-5 rounded-2xl shadow-xs border border-slate-200 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-slate-800">
              Phân tích Phổ điểm & Kết quả Đề thi
            </h2>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800">
              Dành cho Giảng viên (Issue #36)
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Theo dõi phổ điểm phân bố chuẩn, các câu hỏi khó hay sai và xuất bảng điểm chi tiết.
          </p>
        </div>

        {/* Exam Dropdown Selector & Refresh */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <label className="text-xs font-medium text-slate-600 whitespace-nowrap">
              Chọn đề thi:
            </label>
            <select
              value={selectedExamId}
              onChange={(e) => setSelectedExamId(e.target.value)}
              disabled={loadingExams || exams.length === 0}
              className="px-3 py-2 text-sm border border-slate-300 rounded-xl bg-slate-50 focus:outline-hidden focus:ring-2 focus:ring-blue-500 font-medium text-slate-700 min-w-[220px]"
            >
              {exams.length === 0 ? (
                <option value="">{loadingExams ? "Đang tải đề thi..." : "Chưa có đề thi"}</option>
              ) : (
                exams.map((ex) => (
                  <option key={ex.id} value={ex.id}>
                    [{ex.exam_code}] {ex.title}
                  </option>
                ))
              )}
            </select>
          </div>

          <button
            onClick={() => {
              if (selectedExamId) {
                setLoading(true);
                tutorService.getExamAnalytics(selectedExamId).then(setAnalytics).finally(() => setLoading(false));
              }
            }}
            title="Làm mới dữ liệu"
            className="p-2 border border-slate-200 text-slate-600 hover:text-slate-900 rounded-xl hover:bg-slate-100 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-blue-600" : ""}`} />
          </button>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 rounded-xl border border-red-200 bg-red-50 flex items-center gap-3 text-red-700 text-sm">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Loading state */}
      {loading && !analytics && (
        <div className="bg-white p-12 rounded-2xl border border-slate-200 text-center">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-3" />
          <p className="text-sm font-medium text-slate-600">Đang tổng hợp dữ liệu phổ điểm...</p>
        </div>
      )}

      {/* Main Analytics Content */}
      {analytics && (
        <>
          {/* Key Metric Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
              <div className="flex items-center justify-between text-slate-500 text-xs mb-1">
                <span>Tổng bài thi</span>
                <Users className="w-4 h-4 text-blue-500" />
              </div>
              <div className="text-2xl font-bold text-slate-800">
                {analytics.summary.total_attempts}
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5">
                {analytics.summary.total_students} thí sinh
              </div>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
              <div className="flex items-center justify-between text-slate-500 text-xs mb-1">
                <span>Điểm trung bình</span>
                <TrendingUp className="w-4 h-4 text-emerald-500" />
              </div>
              <div className="text-2xl font-bold text-emerald-600">
                {analytics.summary.avg_score.toFixed(1)}
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5">
                Trung vị: {analytics.summary.median_score.toFixed(1)}
              </div>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
              <div className="flex items-center justify-between text-slate-500 text-xs mb-1">
                <span>Điểm cao nhất</span>
                <Award className="w-4 h-4 text-amber-500" />
              </div>
              <div className="text-2xl font-bold text-amber-600">
                {analytics.summary.max_score.toFixed(1)}
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5">Thang điểm 10</div>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
              <div className="flex items-center justify-between text-slate-500 text-xs mb-1">
                <span>Điểm thấp nhất</span>
                <XCircle className="w-4 h-4 text-rose-500" />
              </div>
              <div className="text-2xl font-bold text-rose-600">
                {analytics.summary.min_score.toFixed(1)}
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5">Thang điểm 10</div>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
              <div className="flex items-center justify-between text-slate-500 text-xs mb-1">
                <span>Tỷ lệ đạt (&ge;5)</span>
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              </div>
              <div className="text-2xl font-bold text-slate-800">
                {analytics.summary.pass_rate}%
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5">
                {analytics.summary.pass_count} đạt / {analytics.summary.fail_count} hỏng
              </div>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
              <div className="flex items-center justify-between text-slate-500 text-xs mb-1">
                <span>Độ lệch chuẩn</span>
                <BarChart3 className="w-4 h-4 text-indigo-500" />
              </div>
              <div className="text-2xl font-bold text-indigo-600">
                &plusmn;{analytics.summary.standard_deviation.toFixed(2)}
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5">Phân hóa điểm</div>
            </div>
          </div>

          {/* Visual Charts Grid: Score Distribution Histogram + Grade Tiers */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Score Distribution Histogram (2 cols) */}
            <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-blue-600" />
                  <h3 className="font-bold text-slate-800 text-base">
                    Phổ điểm lớp học (Score Distribution Histogram)
                  </h3>
                </div>
                <span className="text-xs text-slate-500 font-medium">
                  {analytics.summary.total_attempts} bài nộp
                </span>
              </div>

              {/* Histogram Bars */}
              <div className="h-56 flex items-end gap-2 pt-6 pb-2 border-b border-slate-200 px-2">
                {analytics.score_distribution.map((bin, index) => {
                  const heightPercent =
                    maxHistogramCount > 0 ? (bin.count / maxHistogramCount) * 100 : 0;
                  const isPassing = bin.min_score >= 5.0;

                  return (
                    <div
                      key={index}
                      className="flex-1 flex flex-col items-center justify-end h-full group relative"
                    >
                      {/* Tooltip on Hover */}
                      <div className="absolute -top-10 opacity-0 group-hover:opacity-100 transition-opacity bg-slate-800 text-white text-[11px] py-1 px-2 rounded-md whitespace-nowrap pointer-events-none shadow-md z-10">
                        {bin.bin_label}: {bin.count} bài ({bin.percentage}%)
                      </div>

                      {/* Bar Count label */}
                      {bin.count > 0 && (
                        <span className="text-[10px] font-bold text-slate-600 mb-1">
                          {bin.count}
                        </span>
                      )}

                      {/* Bar element */}
                      <div
                        style={{ height: `${Math.max(heightPercent, 4)}%` }}
                        className={`w-full rounded-t-md transition-all duration-300 ${
                          bin.count === 0
                            ? "bg-slate-100"
                            : isPassing
                            ? "bg-blue-500 group-hover:bg-blue-600"
                            : "bg-rose-400 group-hover:bg-rose-500"
                        }`}
                      />
                    </div>
                  );
                })}
              </div>

              {/* X-axis labels */}
              <div className="flex gap-2 pt-2 px-2 text-center">
                {analytics.score_distribution.map((bin, index) => (
                  <div key={index} className="flex-1 text-[10px] text-slate-500 truncate" title={bin.bin_label}>
                    {bin.bin_label}
                  </div>
                ))}
              </div>

              <div className="mt-4 flex items-center justify-center gap-6 text-xs text-slate-600">
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-xs bg-rose-400" />
                  <span>Dưới trung bình (&lt; 5.0)</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-xs bg-blue-500" />
                  <span>Đạt yêu cầu (&ge; 5.0)</span>
                </div>
              </div>
            </div>

            {/* Academic Grade Breakdown (1 col) */}
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs flex flex-col justify-between">
              <div>
                <h3 className="font-bold text-slate-800 text-base mb-1">
                  Xếp loại Học lực
                </h3>
                <p className="text-xs text-slate-500 mb-4">
                  Phân tầng kết quả theo quy chế đánh giá
                </p>

                <div className="space-y-3.5">
                  {analytics.grade_distribution.map((grade, idx) => {
                    const colors = [
                      "bg-emerald-500",
                      "bg-blue-500",
                      "bg-amber-500",
                      "bg-orange-400",
                      "bg-rose-500",
                    ];
                    const color = colors[idx % colors.length];

                    return (
                      <div key={idx} className="space-y-1">
                        <div className="flex justify-between text-xs font-medium text-slate-700">
                          <span>{grade.bin_label}</span>
                          <span className="font-bold">
                            {grade.count} ({grade.percentage}%)
                          </span>
                        </div>
                        <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                          <div
                            className={`h-full ${color} rounded-full transition-all duration-300`}
                            style={{ width: `${grade.percentage}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="mt-6 p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-600">
                <strong>Ghi chú:</strong> Tỷ lệ bài đạt điểm khá - giỏi (từ 6.5 trở lên) chiếm{" "}
                <strong>
                  {(
                    (analytics.grade_distribution[0]?.percentage || 0) +
                    (analytics.grade_distribution[1]?.percentage || 0) +
                    (analytics.grade_distribution[2]?.percentage || 0)
                  ).toFixed(1)}
                  %
                </strong>
                .
              </div>
            </div>
          </div>

          {/* Top Difficult Questions Card */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-4">
            <div className="flex items-center gap-2">
              <HelpCircle className="w-5 h-5 text-amber-600" />
              <h3 className="font-bold text-slate-800 text-base">
                Top câu hỏi sinh viên hay làm sai nhất
              </h3>
            </div>
            <p className="text-xs text-slate-500 -mt-2">
              Phát hiện các điểm nghẽn kiến thức để giảng viên giải đáp hoặc điều chỉnh độ khó đề thi.
            </p>

            {analytics.difficult_questions.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-400 bg-slate-50 rounded-xl">
                Chưa có dữ liệu câu trả lời sai cho đề thi này.
              </div>
            ) : (
              <div className="space-y-3">
                {analytics.difficult_questions.map((q, index) => (
                  <div
                    key={q.question_id}
                    className="p-4 rounded-xl border border-slate-200 bg-slate-50/60 flex flex-col md:flex-row md:items-center justify-between gap-3"
                  >
                    <div className="space-y-1.5 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded-md text-[11px] font-bold bg-amber-100 text-amber-800">
                          Top {index + 1}
                        </span>
                        <span className="px-2 py-0.5 rounded-md text-[11px] font-medium bg-slate-200 text-slate-700">
                          {q.category_name || "Chung"}
                        </span>
                        <span className="text-xs text-slate-400">
                          Loại: {q.question_type}
                        </span>
                      </div>
                      <p className="text-sm font-medium text-slate-800">
                        {q.content}
                      </p>
                    </div>

                    <div className="flex items-center gap-4 self-end md:self-auto shrink-0">
                      <div className="text-right">
                        <div className="text-sm font-bold text-rose-600">
                          {q.incorrect_rate}% trả lời sai
                        </div>
                        <div className="text-xs text-slate-500">
                          {q.wrong_count} sai / {q.total_responses} lượt trả lời
                        </div>
                      </div>
                      <div className="w-12 h-12 rounded-xl bg-rose-50 border border-rose-200 flex items-center justify-center font-bold text-rose-700 text-sm">
                        {q.wrong_count}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Student Score Sheet Table & CSV Export Button */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h3 className="font-bold text-slate-800 text-base">
                  Bảng điểm chi tiết bài thi
                </h3>
                <p className="text-xs text-slate-500">
                  Danh sách sinh viên đã hoàn thành và nộp bài
                </p>
              </div>

              {/* Search & Export Buttons */}
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                  <input
                    type="text"
                    placeholder="Tìm tên hoặc email..."
                    value={studentSearch}
                    onChange={(e) => setStudentSearch(e.target.value)}
                    className="pl-9 pr-3 py-1.5 text-xs border border-slate-300 rounded-xl bg-slate-50 focus:outline-hidden focus:ring-2 focus:ring-blue-500 text-slate-700 w-48 sm:w-60"
                  />
                </div>

                <button
                  onClick={handleExportCsv}
                  disabled={exportingCsv || analytics.student_scores.length === 0}
                  className="px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold flex items-center gap-2 shadow-2xs transition-colors disabled:opacity-50"
                >
                  <Download className={`w-4 h-4 ${exportingCsv ? "animate-bounce" : ""}`} />
                  <span>{exportingCsv ? "Đang xuất..." : "Xuất bảng điểm CSV"}</span>
                </button>
              </div>
            </div>

            {/* Score Table */}
            <div className="overflow-x-auto rounded-xl border border-slate-200">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                  <tr>
                    <th className="py-3 px-4 w-12 text-center">STT</th>
                    <th className="py-3 px-4">Họ và tên thí sinh</th>
                    <th className="py-3 px-4">Email</th>
                    <th className="py-3 px-4 text-center">Lần thi</th>
                    <th className="py-3 px-4 text-center">Điểm số</th>
                    <th className="py-3 px-4 text-center">Thời gian làm</th>
                    <th className="py-3 px-4 text-center">Vi phạm</th>
                    <th className="py-3 px-4">Thời điểm nộp</th>
                    <th className="py-3 px-4 text-center">Trạng thái</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {filteredStudents.length === 0 ? (
                    <tr>
                      <td colSpan={9} className="py-8 text-center text-slate-400">
                        Không tìm thấy bài làm phù hợp.
                      </td>
                    </tr>
                  ) : (
                    filteredStudents.map((st, idx) => (
                      <tr key={st.attempt_id} className="hover:bg-slate-50/70 transition-colors">
                        <td className="py-3 px-4 text-center text-slate-400">{idx + 1}</td>
                        <td className="py-3 px-4 font-semibold text-slate-900">{st.student_name}</td>
                        <td className="py-3 px-4 text-slate-500">{st.student_email}</td>
                        <td className="py-3 px-4 text-center">#{st.attempt_number}</td>
                        <td className="py-3 px-4 text-center">
                          <span
                            className={`px-2 py-0.5 rounded-md font-bold text-xs ${
                              st.score >= 8.0
                                ? "bg-emerald-100 text-emerald-800"
                                : st.score >= 5.0
                                ? "bg-blue-100 text-blue-800"
                                : "bg-rose-100 text-rose-800"
                            }`}
                          >
                            {st.score.toFixed(1)}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-center text-slate-500">
                          {Math.floor(st.time_spent_seconds / 60)}p {st.time_spent_seconds % 60}s
                        </td>
                        <td className="py-3 px-4 text-center">
                          {st.violation_count > 0 ? (
                            <span className="px-1.5 py-0.5 rounded-xs text-[11px] font-semibold bg-amber-100 text-amber-800">
                              {st.violation_count} lần
                            </span>
                          ) : (
                            <span className="text-slate-400">0</span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-slate-500">
                          {st.submitted_at
                            ? new Date(st.submitted_at).toLocaleString("vi-VN")
                            : "—"}
                        </td>
                        <td className="py-3 px-4 text-center">
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-800">
                            {st.status}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default LecturerAnalyticsDashboard;
