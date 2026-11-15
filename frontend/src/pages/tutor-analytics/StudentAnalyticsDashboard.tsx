import React, { useEffect, useState } from "react";
import {
  TrendingUp,
  Award,
  BookOpen,
  CheckCircle2,
  AlertTriangle,
  Lightbulb,
  Clock,
  Calendar,
  Sparkles,
  RefreshCw,
  AlertCircle,
  ShieldAlert,
} from "lucide-react";
import {
  StudentAnalyticsData,
  tutorService,
} from "@/services/tutorService";

interface StudentAnalyticsDashboardProps {
  studentId?: string; // defaults to "me"
}

export const StudentAnalyticsDashboard: React.FC<StudentAnalyticsDashboardProps> = ({
  studentId = "me",
}) => {
  const [analytics, setAnalytics] = useState<StudentAnalyticsData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await tutorService.getStudentAnalytics(studentId);
      setAnalytics(data);
    } catch (err: any) {
      setError(err.message || "Không thể tải dữ liệu tiến độ học tập.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [studentId]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-5 rounded-2xl shadow-xs border border-slate-200 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-slate-800">
              Tiến độ Học tập & Mức độ Nắm vững Chuyên đề
            </h2>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
              Dành cho Sinh viên (Issue #36)
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Theo dõi xu hướng cải thiện điểm số qua các ca thi và phát hiện các chủ đề cần củng cố lại.
          </p>
        </div>

        <button
          onClick={fetchAnalytics}
          className="p-2 border border-slate-200 text-slate-600 hover:text-slate-900 rounded-xl hover:bg-slate-100 transition-colors self-start md:self-auto flex items-center gap-1.5 text-xs font-medium"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-emerald-600" : ""}`} />
          <span>Làm mới</span>
        </button>
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
          <RefreshCw className="w-8 h-8 animate-spin text-emerald-600 mx-auto mb-3" />
          <p className="text-sm font-medium text-slate-600">Đang tổng hợp tiến độ học tập...</p>
        </div>
      )}

      {analytics && (
        <>
          {/* Summary Metric Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
              <div className="flex items-center justify-between text-slate-500 text-xs mb-1">
                <span>Tổng bài kiểm tra</span>
                <BookOpen className="w-4 h-4 text-emerald-500" />
              </div>
              <div className="text-2xl font-bold text-slate-800">
                {analytics.summary.total_attempts}
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5">
                Trên {analytics.summary.total_exams} bộ đề khác nhau
              </div>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
              <div className="flex items-center justify-between text-slate-500 text-xs mb-1">
                <span>Điểm trung bình</span>
                <TrendingUp className="w-4 h-4 text-blue-500" />
              </div>
              <div className="text-2xl font-bold text-blue-600">
                {analytics.summary.average_score.toFixed(1)}
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5">Thang điểm 10.0</div>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
              <div className="flex items-center justify-between text-slate-500 text-xs mb-1">
                <span>Điểm cao nhất</span>
                <Award className="w-4 h-4 text-amber-500" />
              </div>
              <div className="text-2xl font-bold text-amber-600">
                {analytics.summary.highest_score.toFixed(1)}
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5">
                Thấp nhất: {analytics.summary.lowest_score.toFixed(1)}
              </div>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
              <div className="flex items-center justify-between text-slate-500 text-xs mb-1">
                <span>Tỷ lệ đạt yêu cầu</span>
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              </div>
              <div className="text-2xl font-bold text-emerald-600">
                {analytics.summary.pass_rate}%
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5">Bài đạt điểm &ge; 5.0</div>
            </div>
          </div>

          {/* Score Trends Section */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-blue-600" />
                <h3 className="font-bold text-slate-800 text-base">
                  Xu hướng điểm số qua các lần thi
                </h3>
              </div>
              <span className="text-xs text-slate-500">
                {analytics.trends.length} lần làm bài gần nhất
              </span>
            </div>

            {analytics.trends.length === 0 ? (
              <div className="p-8 text-center bg-slate-50 rounded-xl text-slate-400 text-xs">
                Bạn chưa hoàn thành bài thi nào để hiển thị biểu đồ xu hướng.
              </div>
            ) : (
              <>
                {/* Visual score trend chart */}
                <div className="h-44 flex items-end gap-3 pt-6 pb-2 border-b border-slate-200 px-2 overflow-x-auto">
                  {analytics.trends.map((tr, index) => {
                    const heightPercent = Math.max(10, (tr.score / 10.0) * 100);
                    const isPassing = tr.score >= 5.0;

                    return (
                      <div
                        key={tr.attempt_id}
                        className="flex-1 min-w-[48px] flex flex-col items-center justify-end h-full group relative"
                      >
                        {/* Tooltip */}
                        <div className="absolute -top-12 opacity-0 group-hover:opacity-100 transition-opacity bg-slate-800 text-white text-[11px] py-1 px-2 rounded-md whitespace-nowrap pointer-events-none shadow-md z-10">
                          {tr.exam_title}: {tr.score.toFixed(1)} điểm
                        </div>

                        {/* Value label */}
                        <span className="text-[10px] font-bold text-slate-700 mb-1">
                          {tr.score.toFixed(1)}
                        </span>

                        {/* Bar */}
                        <div
                          style={{ height: `${heightPercent}%` }}
                          className={`w-full max-w-[36px] rounded-t-md transition-all duration-300 ${
                            isPassing
                              ? "bg-emerald-500 group-hover:bg-emerald-600"
                              : "bg-rose-400 group-hover:bg-rose-500"
                          }`}
                        />

                        {/* Attempt label */}
                        <span className="text-[10px] text-slate-500 mt-2 truncate w-full text-center">
                          Lần {index + 1}
                        </span>
                      </div>
                    );
                  })}
                </div>

                {/* Attempt records list */}
                <div className="divide-y divide-slate-100 mt-2">
                  {analytics.trends.slice(-5).reverse().map((tr) => (
                    <div key={tr.attempt_id} className="py-2.5 flex items-center justify-between text-xs">
                      <div className="space-y-0.5">
                        <div className="font-semibold text-slate-800">{tr.exam_title}</div>
                        <div className="text-slate-400 text-[11px] flex items-center gap-3">
                          <span className="flex items-center gap-1">
                            <Calendar className="w-3 h-3" />
                            {tr.submitted_at
                              ? new Date(tr.submitted_at).toLocaleDateString("vi-VN")
                              : "—"}
                          </span>
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {Math.floor(tr.time_spent_seconds / 60)}p {tr.time_spent_seconds % 60}s
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        <span
                          className={`px-2.5 py-1 rounded-lg font-bold text-xs ${
                            tr.score >= 8.0
                              ? "bg-emerald-100 text-emerald-800"
                              : tr.score >= 5.0
                              ? "bg-blue-100 text-blue-800"
                              : "bg-rose-100 text-rose-800"
                          }`}
                        >
                          {tr.score.toFixed(1)} / 10
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>

          {/* Topic Mastery & Knowledge Gaps Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Topic Mastery (Tỷ lệ đúng/sai theo chuyên đề) */}
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-4">
              <div className="flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-emerald-600" />
                <h3 className="font-bold text-slate-800 text-base">
                  Mức độ nắm vững theo Chuyên đề
                </h3>
              </div>
              <p className="text-xs text-slate-500 -mt-2">
                Tỷ lệ trả lời chính xác trên tổng số câu hỏi đã làm theo từng phân môn
              </p>

              {analytics.topics_mastery.length === 0 ? (
                <div className="p-6 text-center text-xs text-slate-400 bg-slate-50 rounded-xl">
                  Chưa có dữ liệu bài làm theo chuyên đề.
                </div>
              ) : (
                <div className="space-y-4">
                  {analytics.topics_mastery.map((topic, idx) => {
                    let badgeClass = "bg-slate-100 text-slate-700";
                    let barColor = "bg-slate-400";
                    let label = "Trung bình";

                    if (topic.mastery_level === "EXCELLENT") {
                      badgeClass = "bg-emerald-100 text-emerald-800";
                      barColor = "bg-emerald-500";
                      label = "Thành thạo";
                    } else if (topic.mastery_level === "GOOD") {
                      badgeClass = "bg-blue-100 text-blue-800";
                      barColor = "bg-blue-500";
                      label = "Khá";
                    } else if (topic.mastery_level === "AVERAGE") {
                      badgeClass = "bg-amber-100 text-amber-800";
                      barColor = "bg-amber-500";
                      label = "Trung bình";
                    } else {
                      badgeClass = "bg-rose-100 text-rose-800";
                      barColor = "bg-rose-500";
                      label = "Cần củng cố";
                    }

                    return (
                      <div key={idx} className="space-y-1.5 p-3 rounded-xl border border-slate-100 bg-slate-50/50">
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-bold text-slate-800">
                            {topic.category_name}
                          </span>
                          <div className="flex items-center gap-2">
                            <span className="text-slate-500">
                              {topic.correct_count}/{topic.total_questions} đúng
                            </span>
                            <span className={`px-2 py-0.5 rounded-md font-semibold text-[11px] ${badgeClass}`}>
                              {label} ({topic.accuracy_percentage}%)
                            </span>
                          </div>
                        </div>

                        {/* Progress Bar */}
                        <div className="w-full h-2 rounded-full bg-slate-200 overflow-hidden">
                          <div
                            className={`h-full ${barColor} rounded-full transition-all duration-300`}
                            style={{ width: `${topic.accuracy_percentage}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Knowledge Gaps & Actionable Advice */}
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-4">
              <div className="flex items-center gap-2">
                <Lightbulb className="w-5 h-5 text-amber-500" />
                <h3 className="font-bold text-slate-800 text-base">
                  Lỗ hổng kiến thức & Lời khuyên Ôn tập
                </h3>
              </div>
              <p className="text-xs text-slate-500 -mt-2">
                Được AI & hệ thống chẩn đoán tự động từ các câu làm sai
              </p>

              {analytics.knowledge_gaps.length === 0 ? (
                <div className="p-8 text-center bg-emerald-50 rounded-xl border border-emerald-100 space-y-2">
                  <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto" />
                  <p className="text-sm font-bold text-emerald-800">
                    Phong độ học tập xuất sắc!
                  </p>
                  <p className="text-xs text-emerald-700">
                    Không phát hiện lỗ hổng kiến thức nghiêm trọng nào (tất cả các chuyên đề đều đạt trên 65%). Hãy duy trì phong độ ôn luyện nhé!
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {analytics.knowledge_gaps.map((gap, idx) => (
                    <div
                      key={idx}
                      className="p-4 rounded-xl border border-amber-200 bg-amber-50/70 space-y-2"
                    >
                      <div className="flex items-center justify-between text-xs font-bold text-amber-900">
                        <div className="flex items-center gap-1.5">
                          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                          <span>Chuyên đề cần cải thiện: {gap.category_name}</span>
                        </div>
                        <span className="text-[11px] px-2 py-0.5 rounded-md bg-amber-200 text-amber-900">
                          Đúng {gap.accuracy_percentage}%
                        </span>
                      </div>
                      <p className="text-xs text-slate-700 leading-relaxed">
                        {gap.advice}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default StudentAnalyticsDashboard;
