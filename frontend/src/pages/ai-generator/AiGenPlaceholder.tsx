import React from "react";
import { Sparkles } from "lucide-react";

/**
 * AiGenPlaceholder
 * Assigned to: Dev 2 (Module 2 - AI Quiz Generator & Exam Matrix - WBS 3.1, 3.2, 3.3)
 */
export const AiGenPlaceholder: React.FC = () => {
  return (
    <div className="bg-white p-8 rounded-xl shadow-sm border border-slate-200">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-3 bg-purple-50 text-purple-600 rounded-lg">
          <Sparkles className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-800">
            Module 2: AI Quiz Generator & Exam Matrix
          </h1>
          <p className="text-sm text-slate-500">
            Sinh đề thi bằng AI & Ma trận nhận thức Bloom — Phụ trách: <strong>Dev 2 (AI Engineer)</strong>
          </p>
        </div>
      </div>

      <div className="bg-slate-50 border border-slate-200 rounded-lg p-5 text-sm text-slate-700">
        <p className="font-semibold text-slate-900 mb-2">// TODO (Dev 2):</p>
        <ul className="list-disc pl-5 space-y-1.5 text-slate-600">
          <li>Xây dựng giao diện cấu hình Ma trận đề thi (Tỷ lệ: Nhận biết, Thông hiểu, Vận dụng).</li>
          <li>Xây dựng form nhập chủ đề hoặc tải tài liệu ngữ cảnh (RAG Context).</li>
          <li>Gọi API sinh câu hỏi thông minh <code>/api/v1/ai-generator/generate-by-matrix</code>.</li>
          <li>Hiển thị danh sách câu hỏi AI sinh ra để Giảng viên duyệt trước khi lưu vào ngân hàng đề.</li>
        </ul>
      </div>
    </div>
  );
};

export default AiGenPlaceholder;
