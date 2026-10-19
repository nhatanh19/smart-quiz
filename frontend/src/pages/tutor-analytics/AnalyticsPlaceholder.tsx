import React from "react";
import { BarChart3, Bot } from "lucide-react";

/**
 * AnalyticsPlaceholder
 * Assigned to: Dev 4 (Module 4 - Auto-Grading, AI Tutor & Analytics - WBS 5.1, 5.2, 5.3)
 */
export const AnalyticsPlaceholder: React.FC = () => {
  return (
    <div className="bg-white p-8 rounded-xl shadow-sm border border-slate-200">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
          <BarChart3 className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-800">
            Module 4: Auto-Grading, AI Tutor & Analytics
          </h1>
          <p className="text-sm text-slate-500">
            Chấm điểm tức thì, Gia sư ảo AI & Bảng phân tích học tập — Phụ trách: <strong>Dev 4 (Data & Tutor)</strong>
          </p>
        </div>
      </div>

      <div className="bg-slate-50 border border-slate-200 rounded-lg p-5 text-sm text-slate-700">
        <p className="font-semibold text-slate-900 mb-2">// TODO (Dev 4):</p>
        <ul className="list-disc pl-5 space-y-1.5 text-slate-600">
          <li>Xây dựng màn hình Xem lại bài thi (Review Mode) đối chiếu đáp án người dùng chọn và đáp án đúng.</li>
          <li>
            <div className="inline-flex items-center gap-1 text-emerald-700 font-medium">
              <Bot className="w-4 h-4" /> Contextual AI Tutor:
            </div>{" "}
            Hiển thị lời giải thích chi tiết vì sao phương án đúng/sai và gợi ý lỗ hổng kiến thức cần ôn tập.
          </li>
          <li>Xây dựng Bảng điều khiển Sinh viên: Biểu đồ tiến độ điểm số và tỷ lệ đúng/sai theo chuyên đề.</li>
          <li>Xây dựng Bảng điều khiển Giảng viên: Biểu đồ phổ điểm lớp học và thống kê các câu hỏi có tỷ lệ sai cao.</li>
        </ul>
      </div>
    </div>
  );
};

export default AnalyticsPlaceholder;
