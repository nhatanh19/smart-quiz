import { Link } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { homePath } from "@/lib/permissions";

export default function ForbiddenPage() {
  const { user } = useAuth();
  return <section className="mx-auto max-w-lg rounded-xl border bg-white p-8 text-center">
    <h1 className="text-2xl font-bold">403 — Không có quyền truy cập</h1>
    <p role="alert" className="my-4 text-slate-600">Vai trò của bạn không được phép truy cập trang này.</p>
    <Link className="text-blue-600 underline" to={user ? homePath(user.role) : "/login"}>Về trang chính</Link>
  </section>;
}
