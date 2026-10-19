import React from "react";
import { FileText } from "lucide-react";

/**
 * ParserPlaceholder
 * Assigned to: Dev 1 (Module 1 - File Parser & Question Bank CRUD - WBS 2.1 & 2.2)
 */
export const ParserPlaceholder: React.FC = () => {
  return (
    <div className="bg-white p-8 rounded-xl shadow-sm border border-slate-200">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
          <FileText className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-800">
            Module 1: File Parser & Question Bank
          </h1>
          <p className="text-sm text-slate-500">
            Bóc tách tài liệu (PDF/DOCX/TXT) & Quản lý Ngân hàng câu hỏi — Phụ trách: <strong>Dev 1 (Team Leader)</strong>
          </p>
        </div>
      </div>

      <div className="bg-slate-50 border border-slate-200 rounded-lg p-5 text-sm text-slate-700">
        <p className="font-semibold text-slate-900 mb-2">// TODO (Dev 1):</p>
        <ul className="list-disc pl-5 space-y-1.5 text-slate-600">
          <li>Xây dựng khu vực Kéo thả / Tải lên tài liệu (PDF, DOCX, TXT).</li>
          <li>Xây dựng màn hình Preview câu hỏi đã bóc tách bằng Regex (cho phép chỉnh sửa nội dung, lựa chọn, đáp án đúng).</li>
          <li>Xây dựng bảng danh sách Ngân hàng câu hỏi theo chuyên đề và mức độ nhận thức (Bloom).</li>
          <li>Kết nối các API <code>/api/v1/parser/upload</code> và <code>/api/v1/parser/questions</code>.</li>
        </ul>
      </div>
    </div>
  );
};

export default ParserPlaceholder;
