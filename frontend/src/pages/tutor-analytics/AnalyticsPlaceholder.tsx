import React, { useState } from "react";
import { BarChart3, Bot, Sparkles, CheckCircle2 } from "lucide-react";
import ReviewExamView from "./ReviewExamView";

/**
 * Module 4: Auto-Grading, AI Tutor & Analytics
 * Assigned to: Dev 4 (Data & Tutor Engineer)
 * Implements Issue #16 (WBS 5.2.1): Contextual Explanation Generator API & Review Mode AI Tutor
 */
export const AnalyticsPlaceholder: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"TUTOR_REVIEW" | "ROADMAP">("TUTOR_REVIEW");

  return (
    <div className="space-y-6">
      {/* Top Header & Tab Navigation */}
      <div className="bg-white p-5 rounded-2xl shadow-xs border border-slate-200 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-xl shadow-2xs">
            <Bot className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-slate-800">
                Module 4: Auto-Grading, AI Tutor & Analytics
              </h1>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
                Sprint 1 Core
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Phụ trách: <strong>Dev 4 (Data & Tutor Engineer)</strong> • WBS: <strong>5.1, 5.2, 5.3</strong>
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center gap-1.5 bg-slate-100 p-1.5 rounded-xl border border-slate-200 text-xs font-medium self-start md:self-auto">
          <button
            onClick={() => setActiveTab("TUTOR_REVIEW")}
            className={`px-3.5 py-2 rounded-lg transition-all flex items-center gap-2 ${
              activeTab === "TUTOR_REVIEW"
                ? "bg-white text-emerald-700 font-semibold shadow-xs"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Sparkles className="h-4 w-4 text-emerald-600" />
            <span>Gia sư ảo AI (Issue #16)</span>
          </button>
          <button
            onClick={() => setActiveTab("ROADMAP")}
            className={`px-3.5 py-2 rounded-lg transition-all flex items-center gap-2 ${
              activeTab === "ROADMAP"
                ? "bg-white text-slate-900 font-semibold shadow-xs"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <BarChart3 className="h-4 w-4 text-slate-500" />
            <span>Phân công WBS Module 4</span>
          </button>
        </div>
      </div>

      {/* Tab 1: Interactive AI Tutor & Review Mode (Issue #16 Core Implementation) */}
      {activeTab === "TUTOR_REVIEW" && <ReviewExamView />}

      {/* Tab 2: Module 4 Roadmap & Sprint Checklist */}
      {activeTab === "ROADMAP" && (
        <div className="bg-white p-6 rounded-2xl shadow-xs border border-slate-200 space-y-4">
          <h2 className="text-lg font-bold text-slate-800">
            Tiến độ triển khai Mô-đun 4 (Dev 4 - Data & Tutor Engineer)
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl border border-emerald-200 bg-emerald-50/50">
              <div className="flex items-center gap-2 text-emerald-800 font-semibold text-sm mb-1">
                <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                Issue #16: [AI-Tutor] Contextual Explanation Generator API
              </div>
              <p className="text-xs text-slate-600">
                - Xây dựng prompt phân tích ngữ cảnh, giải thích vì sao đáp án chuẩn đúng và vì sao phương án chọn bị sai.
                <br />
                - Tiêu chí DoD: Nút "Giải thích bằng AI" phản hồi &lt; 3 giây với giọng văn sư phạm dễ hiểu.
                <br />
                - <strong>Trạng thái:</strong> Đã hoàn thành (Done).
              </p>
            </div>

            <div className="p-4 rounded-xl border border-slate-200 bg-slate-50">
              <div className="flex items-center gap-2 text-slate-800 font-semibold text-sm mb-1">
                <span className="h-2 w-2 rounded-full bg-amber-500" />
                Issue #14: [Grading] Instant Multi-Question Type Auto-Grading Engine
              </div>
              <p className="text-xs text-slate-600">
                - Chấm điểm tự động tức thì các dạng câu hỏi trắc nghiệm (Chọn 1, chọn nhiều, đúng/sai).
                <br />
                - <strong>Trạng thái:</strong> Sprint 1 (3 Story Points).
              </p>
            </div>

            <div className="p-4 rounded-xl border border-slate-200 bg-slate-50">
              <div className="flex items-center gap-2 text-slate-800 font-semibold text-sm mb-1">
                <span className="h-2 w-2 rounded-full bg-amber-500" />
                Issue #15: [Grading] Post-Exam Detailed Review Mode Interface
              </div>
              <p className="text-xs text-slate-600">
                - Giao diện đối chiếu chi tiết kết quả làm bài của thí sinh với đáp án chuẩn.
                <br />
                - <strong>Trạng thái:</strong> Sprint 1 (3 Story Points).
              </p>
            </div>

            <div className="p-4 rounded-xl border border-slate-200 bg-slate-50">
              <div className="flex items-center gap-2 text-slate-800 font-semibold text-sm mb-1">
                <span className="h-2 w-2 rounded-full bg-slate-400" />
                Issue #17: [AI-Tutor] Knowledge Gap Diagnostic Card in Review UI
              </div>
              <p className="text-xs text-slate-600">
                - Hiển thị thẻ chẩn đoán lỗ hổng kiến thức và đề xuất chủ đề ôn tập ngay trên màn hình xem lại.
                <br />
                - <strong>Trạng thái:</strong> Sprint 1 (3 Story Points).
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalyticsPlaceholder;
