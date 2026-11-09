import { useAuth } from "@/contexts/AuthContext";
import { roleLabels } from "@/lib/permissions";
import AuthAction from "./AuthAction";

export default function ProfilePage() {
  const { user } = useAuth();
  if (!user) return null;
  const initials = user.full_name.trim().split(/\s+/).slice(-2).map(part => Array.from(part)[0]).join("").toLocaleUpperCase("vi");
  return <section className="mx-auto max-w-xl rounded-xl border border-slate-200 bg-white p-6 sm:p-8">
    <h1 className="text-2xl font-bold mb-6">Thông tin cá nhân</h1>
    <div className="flex items-center gap-4 mb-8">
      <div role="img" aria-label={`Ảnh đại diện của ${user.full_name}`} className="flex h-20 w-20 shrink-0 items-center justify-center rounded-full bg-blue-100 text-2xl font-bold text-blue-700">{initials}</div>
      <div><h2 className="text-xl font-semibold break-words">{user.full_name}</h2><p className="text-slate-500">{roleLabels[user.role]}</p></div>
    </div>
    <dl className="space-y-4 mb-8">
      <div><dt className="text-sm text-slate-500">Họ tên</dt><dd className="break-words font-medium">{user.full_name}</dd></div>
      <div><dt className="text-sm text-slate-500">Email</dt><dd className="break-all font-medium">{user.email}</dd></div>
      <div><dt className="text-sm text-slate-500">Vai trò</dt><dd className="font-medium">{roleLabels[user.role]} ({user.role})</dd></div>
    </dl>
    <AuthAction />
  </section>;
}
