import React from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { UserRole } from "@/types";

interface ProtectedRouteProps {
  allowedRoles?: UserRole[];
  redirectPath?: string;
  children?: React.ReactNode;
}

/**
 * ProtectedRoute:
 * Route guard component verifying authentication and RBAC permissions.
 */
export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  allowedRoles,
  redirectPath = "/auth/login",
  children,
}) => {
  const location = useLocation();

  // Retrieve auth credentials from localStorage
  const token =
    localStorage.getItem("access_token") || localStorage.getItem("token");
  const userRole = localStorage.getItem("user_role") as UserRole | null;

  // Unauthenticated -> redirect to login preserving attempted path
  if (!token) {
    return <Navigate to={redirectPath} state={{ from: location }} replace />;
  }

  // Role unauthorized -> redirect to home or unauthorized view
  if (allowedRoles && (!userRole || !allowedRoles.includes(userRole))) {
    return <Navigate to="/" replace />;
  }

  return children ? <>{children}</> : <Outlet />;
};

export default ProtectedRoute;
