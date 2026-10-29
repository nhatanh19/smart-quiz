import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { authError } from "@/lib/apiClient";
import { useAuth } from "@/contexts/AuthContext";

export default function AuthAction() {
  const { user, logout: endSession } = useAuth();
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const navigate = useNavigate();
  async function logout() {
    setPending(true);
    try { await endSession(); navigate("/login", { replace: true }); }
    catch (err) { setError(authError(err)); }
    finally { setPending(false); }
  }
  if (!user) return null;
  return <div className="text-sm">
    <span className="mr-3">{user.full_name}</span><button disabled={pending} onClick={logout} className="border rounded-md px-3 py-1.5 disabled:opacity-60">{pending ? "Đang xử lý…" : "Đăng xuất"}</button>
    {error && <p role="alert" className="text-red-700">{error}</p>}
  </div>;
}
