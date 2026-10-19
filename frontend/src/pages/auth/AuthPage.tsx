import React, { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { apiClient, authError } from "@/lib/apiClient";

export default function AuthPage({ register = false }: { register?: boolean }) {
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending) return;
    setError("");
    const form = new FormData(event.currentTarget);
    const password = String(form.get("password"));
    if (register && password !== form.get("confirm_password")) {
      setError("Mật khẩu xác nhận không khớp."); return;
    }
    if (new TextEncoder().encode(password).length > 72) {
      setError("Mật khẩu không được vượt quá 72 byte UTF-8."); return;
    }
    setPending(true);
    try {
      await apiClient.post(`/auth/${register ? "register" : "login"}`, {
        email: String(form.get("email")).trim(), password,
        ...(register ? { full_name: String(form.get("full_name")).trim() } : {}),
      });
      if (register) navigate("/login", { replace: true, state: { registered: true } });
      else {
        const from = location.state?.from;
        navigate(from?.pathname?.startsWith("/") && !from.pathname.startsWith("//") ? from.pathname + (from.search || "") : "/", { replace: true });
      }
    } catch (err) { setError(authError(err)); }
    finally { setPending(false); }
  }
  const inputClass = "w-full mt-1 rounded-lg border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500";
  return <section className="bg-white p-8 rounded-xl shadow-sm border border-slate-200">
    <Link to="/" className="font-bold text-blue-600">Smart Quiz</Link>
    <h1 className="text-2xl font-bold mt-5 mb-2">{register ? "Tạo tài khoản" : "Đăng nhập"}</h1>
    <p className="text-sm text-slate-500 mb-6">{register ? "Đăng ký tài khoản sinh viên để bắt đầu học tập." : "Chào mừng bạn quay lại."}</p>
    {!register && location.state?.registered && <p role="status" className="mb-4 text-green-700">Đăng ký thành công. Vui lòng đăng nhập.</p>}
    {error && <p role="alert" className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}
    <form onSubmit={submit} className="space-y-4" aria-busy={pending}>
      <fieldset disabled={pending} className="space-y-4">
        {register && <label className="block text-sm font-medium">Họ tên<input className={inputClass} name="full_name" autoComplete="name" required maxLength={255} /></label>}
        <label className="block text-sm font-medium">Email<input className={inputClass} type="email" name="email" autoComplete="email" required maxLength={255} /></label>
        <label className="block text-sm font-medium">Mật khẩu<input className={inputClass} type="password" name="password" autoComplete={register ? "new-password" : "current-password"} required minLength={register ? 8 : 1} />{register && <span className="text-xs text-slate-500">Ít nhất 8 ký tự, tối đa 72 byte UTF-8.</span>}</label>
        {register && <label className="block text-sm font-medium">Xác nhận mật khẩu<input className={inputClass} type="password" name="confirm_password" autoComplete="new-password" required minLength={8} /></label>}
        <button className="w-full rounded-lg bg-blue-600 py-2.5 text-white font-medium disabled:opacity-60" type="submit">{pending ? "Đang xử lý…" : register ? "Đăng ký" : "Đăng nhập"}</button>
      </fieldset>
    </form>
    <p className="mt-6 text-sm text-center text-slate-600">{register ? "Đã có tài khoản? " : "Chưa có tài khoản? "}<Link className="text-blue-600 font-medium" to={register ? "/login" : "/register"}>{register ? "Đăng nhập" : "Đăng ký"}</Link></p>
  </section>;
}
