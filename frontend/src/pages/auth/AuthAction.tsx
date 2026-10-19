import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiClient, authError } from "@/lib/apiClient";

export default function AuthAction() {
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const navigate = useNavigate();
  useEffect(() => {
    let active = true;
    apiClient.get("/auth/me").then(({ data }) => { if (active) setName(data.data.full_name); }).catch(() => {});
    return () => { active = false; };
  }, []);
  async function logout() {
    setPending(true);
    try { await apiClient.post("/auth/logout"); navigate("/login", { replace: true }); }
    catch (err) { setError(authError(err)); }
    finally { setPending(false); }
  }
  return <div className="text-sm">
    {name ? <><span className="mr-3">{name}</span><button disabled={pending} onClick={logout} className="border rounded-md px-3 py-1.5 disabled:opacity-60">{pending ? "Đang xử lý…" : "Đăng xuất"}</button></> : <Link to="/login">Đăng nhập</Link>}
    {error && <p role="alert" className="text-red-700">{error}</p>}
  </div>;
}
