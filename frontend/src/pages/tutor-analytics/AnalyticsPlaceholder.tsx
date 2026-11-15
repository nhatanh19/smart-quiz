import React, { useState } from "react";
import {
  BarChart3,
  TrendingUp,
  Sparkles,
  Layers,
  GraduationCap,
  Users,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import LecturerAnalyticsDashboard from "./LecturerAnalyticsDashboard";
import StudentAnalyticsDashboard from "./StudentAnalyticsDashboard";
import ReviewExamView from "./ReviewExamView";

/**
 * Module 4: Auto-Grading, AI Tutor & Analytics Dashboard
 * Implements Issue #36 (WBS 5.3.1 & 5.3.2):
 * - Lecturer Score Distribution Histogram & Top Difficult Questions & CSV Export
 * - Student Learning Progress Trends & Topic Mastery Breakdown
 */
export const AnalyticsPlaceholder: React.FC = () => {
  const { user } = useAuth();
  const isStudent = user?.role === "STUDENT";

  const [activeTab, setActiveTab] = useState<
    "LECTURER" | "STUDENT" | "TUTOR_REVIEW" | "ROADMAP"
  >(isStudent ? "STUDENT" : "LECTURER");

  React.useEffect(() => {
    if (isStudent && activeTab === "LECTURER") {
      setActiveTab("STUDENT");
    }
  }, [isStudent, activeTab]);

  return (
    <div className="space-y-6">
      {/* Top Header & Tab Navigation */}
      <div className="bg-white p-5 rounded-2xl shadow-xs border border-slate-200 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-blue-50 text-blue-600 rounded-xl shadow-2xs">
            <BarChart3 className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-slate-800">
                Bảng điều khiển Phân tích & Đánh giá Hiệu quả
              </h1>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Theo dõi phổ điểm, tiến độ học tập và chẩn đoán lỗ hổng kiến thức • Vai trò:{" "}
              <strong className="text-slate-700">{user?.role || "GUEST"}</strong>
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex flex-wrap items-center gap-1.5 bg-slate-100 p-1.5 rounded-xl border border-slate-200 text-xs font-medium self-start md:self-auto">
          {/* Lecturer Tab (Ẩn đối với Sinh viên để tránh gọi nhầm API của giảng viên) */}
          {!isStudent && (
            <button
              onClick={() => setActiveTab("LECTURER")}
              className={`px-3 py-2 rounded-lg transition-all flex items-center gap-1.5 ${
                activeTab === "LECTURER"
                  ? "bg-white text-blue-700 font-semibold shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <Users className="h-4 w-4 text-blue-600" />
              <span>Phổ điểm Giảng viên</span>
            </button>
          )}

          {/* Student Tab */}
          <button
            onClick={() => setActiveTab("STUDENT")}
            className={`px-3 py-2 rounded-lg transition-all flex items-center gap-1.5 ${
              activeTab === "STUDENT"
                ? "bg-white text-emerald-700 font-semibold shadow-xs"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <GraduationCap className="h-4 w-4 text-emerald-600" />
            <span>Tiến độ Sinh viên</span>
          </button>

          {/* AI Tutor Tab */}
          <button
            onClick={() => setActiveTab("TUTOR_REVIEW")}
            className={`px-3 py-2 rounded-lg transition-all flex items-center gap-1.5 ${
              activeTab === "TUTOR_REVIEW"
                ? "bg-white text-purple-700 font-semibold shadow-xs"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Sparkles className="h-4 w-4 text-purple-600" />
            <span>Gia sư ảo AI</span>
          </button>

          {/* Roadmap Info Tab */}
          <button
            onClick={() => setActiveTab("ROADMAP")}
            className={`px-3 py-2 rounded-lg transition-all flex items-center gap-1.5 ${
              activeTab === "ROADMAP"
                ? "bg-white text-slate-900 font-semibold shadow-xs"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Layers className="h-4 w-4 text-slate-500" />
            <span>Tiêu chí DoD</span>
          </button>
        </div>
      </div>

      {/* Tab 1: Lecturer Exam Distribution Dashboard (Issue #36 / WBS 5.3.2) */}
      {!isStudent && activeTab === "LECTURER" && <LecturerAnalyticsDashboard />}

      {/* Tab 2: Student Progress & Topic Mastery Dashboard (Issue #36 / WBS 5.3.1) */}
      {activeTab === "STUDENT" && <StudentAnalyticsDashboard />}

      {/* Tab 3: Interactive AI Tutor & Review Exam Mode (Issue #15 & #16) */}
      {activeTab === "TUTOR_REVIEW" && <ReviewExamView />}

      {/* Tab 4: Issue #36 Roadmap & Definition of Done */}
      {activeTab === "ROADMAP" && (
        <div className="bg-white p-6 rounded-2xl shadow-xs border border-slate-200 space-y-4">
          <h2 className="text-lg font-bold text-slate-800">
            Kế hoạch & Tiêu chí nghiệm thu Issue #36 (WBS 5.3.1 & 5.3.2)
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl border border-blue-200 bg-blue-50/50 space-y-2">
              <div className="flex items-center gap-2 text-blue-900 font-bold text-sm">
                <BarChart3 className="h-4 w-4 text-blue-600" />
                WBS 5.3.2: Bảng điều khiển Giảng viên
              </div>
              <ul className="text-xs text-slate-700 space-y-1 list-disc list-inside">
                <li>Chọn ca thi theo mã đề và tiêu đề.</li>
                <li>Biểu đồ phổ điểm 10-bin histogram và phân tầng học lực.</li>
                <li>Thống kê Min, Max, Avg, Median, Std Dev, Tỷ lệ đạt.</li>
                <li>Top 5 câu hỏi hay làm sai nhất kèm tỷ lệ sai.</li>
                <li>Bảng điểm chi tiết và nút xuất tệp CSV bảng điểm.</li>
              </ul>
            </div>

            <div className="p-4 rounded-xl border border-emerald-200 bg-emerald-50/50 space-y-2">
              <div className="flex items-center gap-2 text-emerald-900 font-bold text-sm">
                <TrendingUp className="h-4 w-4 text-emerald-600" />
                WBS 5.3.1: Bảng điều khiển Sinh viên
              </div>
              <ul className="text-xs text-slate-700 space-y-1 list-disc list-inside">
                <li>Theo dõi tiến độ và biểu đồ xu hướng điểm số qua các lần thi.</li>
                <li>Đo lường tỷ lệ đúng/sai theo chuyên đề (Topic Mastery).</li>
                <li>Chẩn đoán lỗ hổng kiến thức và đề xuất bài học cải thiện.</li>
                <li>Xếp hạng mức độ thành thạo theo từng phân môn.</li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalyticsPlaceholder;
