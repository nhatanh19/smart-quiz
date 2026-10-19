import React from "react";
import { Outlet } from "react-router-dom";

/**
 * AuthLayout:
 * Centered container for authentication views (Login / Register).
 */
export const AuthLayout: React.FC = () => {
  return (
    <main className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
      <div className="w-full max-w-md">
        <Outlet />
      </div>
    </main>
  );
};

export default AuthLayout;
