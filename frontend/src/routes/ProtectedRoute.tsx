import React, { useEffect } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { UserRole } from "@/types";
import { useAuth } from "@/contexts/AuthContext";

interface ProtectedRouteProps {
  allowedRoles?: UserRole[];
  redirectPath?: string;
  children?: React.ReactNode;
}

export default function ProtectedRoute({ allowedRoles, redirectPath = "/login", children }: ProtectedRouteProps) {
  const location = useLocation();
  const { user, loading, error, ensureSession } = useAuth();
  useEffect(() => {
    void ensureSession();
  }, [ensureSession]);
  if (loading) return <p role="status" className="p-8">Đang kiểm tra phiên đăng nhập…</p>;
  if (error) return <p role="alert" className="p-8">{error} <button onClick={() => window.location.reload()}>Thử lại</button></p>;
  if (!user) return <Navigate to={redirectPath} state={{ from: location }} replace />;
  if (allowedRoles && !allowedRoles.includes(user.role)) return <p role="alert">Bạn không có quyền truy cập trang này.</p>;
  return children ? <>{children}</> : <Outlet />;
}
