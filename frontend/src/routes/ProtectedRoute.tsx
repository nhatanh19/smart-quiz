import React, { useEffect, useState } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { UserRole } from "@/types";
import { apiClient, authError } from "@/lib/apiClient";
import axios from "axios";

interface ProtectedRouteProps {
  allowedRoles?: UserRole[];
  redirectPath?: string;
  children?: React.ReactNode;
}

export default function ProtectedRoute({ allowedRoles, redirectPath = "/login", children }: ProtectedRouteProps) {
  const location = useLocation();
  const [state, setState] = useState<{ role?: UserRole; loading: boolean; unauthenticated?: boolean; error?: string }>({ loading: true });
  useEffect(() => {
    let active = true;
    apiClient.get("/auth/me").then(({ data }) => {
      if (active) setState({ role: data.data.role, loading: false });
    }).catch(err => {
      if (active) setState({ loading: false, unauthenticated: axios.isAxiosError(err) && err.response?.status === 401, error: authError(err) });
    });
    return () => { active = false; };
  }, []);
  if (state.loading) return <p role="status" className="p-8">Đang kiểm tra phiên đăng nhập…</p>;
  if (state.unauthenticated) return <Navigate to={redirectPath} state={{ from: location }} replace />;
  if (state.error) return <p role="alert" className="p-8">{state.error} <button onClick={() => window.location.reload()}>Thử lại</button></p>;
  if (allowedRoles && (!state.role || !allowedRoles.includes(state.role))) return <p role="alert">Bạn không có quyền truy cập trang này.</p>;
  return children ? <>{children}</> : <Outlet />;
}
