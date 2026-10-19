import React from "react";
import { LogIn } from "lucide-react";

/**
 * LoginPlaceholder
 * Assigned to: Dev 3 (WBS 1.2 - Authentication & RBAC)
 */
export const LoginPlaceholder: React.FC = () => {
  return (
    <div className="bg-white p-8 rounded-xl shadow-sm border border-slate-200 text-center">
      <div className="inline-flex p-3 bg-blue-50 text-blue-600 rounded-full mb-4">
        <LogIn className="w-6 h-6" />
      </div>
      <h2 className="text-xl font-bold text-slate-800 mb-2">
        Xác thực & Phân quyền (Auth & RBAC)
      </h2>
      <p className="text-sm text-slate-500 mb-6">
        Gói công việc WBS 1.2 — Bàn giao cho <strong>Dev 3</strong>
      </p>

      <div className="bg-slate-50 p-4 rounded-lg text-left text-xs text-slate-600 border border-slate-200">
        <p className="font-semibold text-slate-700 mb-1">// TODO (Dev 3):</p>
        <ul className="list-disc pl-4 space-y-1">
          <li>Thiết kế Form Đăng nhập & Đăng ký (Email, Password, Vai trò).</li>
          <li>Gọi API <code>/api/v1/auth/login</code> qua <code>apiClient</code>.</li>
          <li>Lưu trữ JWT Token & Vai trò (Role) vào <code>localStorage</code>.</li>
          <li>Điều hướng người dùng về trang tương ứng theo Role.</li>
        </ul>
      </div>
    </div>
  );
};

export default LoginPlaceholder;
