import React from "react";
import { GraduationCap, ShieldAlert } from "lucide-react";

/**
 * ExamPlaceholder
 * Assigned to: Dev 3 (Module 3 - Online Exam Engine & Anti-cheat - WBS 4.1, 4.2, 4.3)
 */
export const ExamPlaceholder: React.FC = () => {
  return (
    <div className="bg-white p-8 rounded-xl shadow-sm border border-slate-200">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-3 bg-amber-50 text-amber-600 rounded-lg">
          <GraduationCap className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-800">
            Module 3: Online Exam Engine & Anti-Cheat
          </h1>
          <p className="text-sm text-slate-500">
            Phòng thi trực tuyến, Xáo trộn đề & Giám sát chống gian lận — Phụ trách: <strong>Dev 3 (Core Engine)</strong>
          </p>
        </div>
      </div>

      <div className="bg-slate-50 border border-slate-200 rounded-lg p-5 text-sm text-slate-700">
        <p className="font-semibold text-slate-900 mb-2">// TODO (Dev 3):</p>
        <ul className="list-disc pl-5 space-y-1.5 text-slate-600">
          <li>Xây dựng giao diện phòng thi tập trung (Đồng hồ đếm ngược, bảng điều hướng câu hỏi).</li>
          <li>Cơ chế lưu tạm câu trả lời vào <code>localStorage</code> để chống mất dữ liệu khi mất kết nối mạng.</li>
          <li>
            <div className="inline-flex items-center gap-1 text-amber-700 font-medium">
              <ShieldAlert className="w-4 h-4" /> Client Anti-Cheat Monitor:
            </div>{" "}
            Bắt sự kiện <code>visibilitychange</code> (chuyển tab), <code>window.blur</code>, và chặn Copy/Paste.
          </li>
          <li>Gửi cảnh báo và gọi API <code>/api/v1/exam-engine/attempts/:id/log-violation</code> khi phát hiện gian lận.</li>
          <li>Tự động thu bài khi hết thời gian thi hoặc vượt ngưỡng vi phạm cho phép.</li>
        </ul>
      </div>
    </div>
  );
};

export default ExamPlaceholder;
