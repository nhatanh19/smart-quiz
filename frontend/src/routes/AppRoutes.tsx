import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";

// Layouts
import MainLayout from "@/layouts/MainLayout";
import AuthLayout from "@/layouts/AuthLayout";
import ExamFocusLayout from "@/layouts/ExamFocusLayout";

// Placeholders for the 4 modules
import AuthPage from "@/pages/auth/AuthPage";
import ProtectedRoute from "@/routes/ProtectedRoute";
import ParserPlaceholder from "@/pages/parser/ParserPlaceholder";
import AiGenPlaceholder from "@/pages/ai-generator/AiGenPlaceholder";
import ExamPlaceholder from "@/pages/exam/ExamPlaceholder";
import AnalyticsPlaceholder from "@/pages/tutor-analytics/AnalyticsPlaceholder";
import ReviewExamView from "@/pages/tutor-analytics/ReviewExamView";
import ManageExams from "@/pages/exam/ManageExams";
import JoinExam from "@/pages/exam/JoinExam";
import ExamLobby from "@/pages/exam/ExamLobby";
import ExamRoom from "@/pages/exam/ExamRoom";
import ProfilePage from "@/pages/auth/ProfilePage";
import ForbiddenPage from "@/pages/auth/ForbiddenPage";
import { useAuth } from "@/contexts/AuthContext";
import { homePath, instructorRoles } from "@/lib/permissions";

function HomeRedirect() {
  const { user } = useAuth();
  return <Navigate to={user ? homePath(user.role) : "/login"} replace />;
}

/**
 * AppRoutes:
 * Global router configuration mapping all 4 modules and authentication views to layout shells.
 */
export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* 1. Authentication Routes (Wrapped in AuthLayout) */}
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<AuthPage key="login" />} />
        <Route path="/register" element={<AuthPage key="register" register />} />
        <Route path="/auth/login" element={<Navigate to="/login" replace />} />
        <Route path="/auth/register" element={<Navigate to="/register" replace />} />
      </Route>

      {/* 2. Main Workspace Routes (Wrapped in MainLayout) */}
      <Route element={<ProtectedRoute />}>
        <Route element={<MainLayout />}>
          <Route path="/" element={<HomeRedirect />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route element={<ProtectedRoute allowedRoles={instructorRoles} />}>
            <Route path="/instructor/exams" element={<ManageExams />} />
            <Route path="/instructor/exams/new" element={<ManageExams />} />
            <Route path="/instructor/parser" element={<ParserPlaceholder />} />
            <Route path="/instructor/ai-generator" element={<AiGenPlaceholder />} />
            <Route path="/instructor/analytics" element={<AnalyticsPlaceholder />} />
            <Route path="/instructor/*" element={<p>Không tìm thấy trang quản lý.</p>} />
            <Route path="/parser" element={<Navigate to="/instructor/parser" replace />} />
            <Route path="/ai-generator" element={<Navigate to="/instructor/ai-generator" replace />} />
            <Route path="/analytics" element={<Navigate to="/instructor/analytics" replace />} />
          </Route>
          <Route element={<ProtectedRoute allowedRoles={["ADMIN"]} />}>
            <Route path="/admin/*" element={<p>Không tìm thấy trang quản trị.</p>} />
          </Route>
          <Route path="/forbidden" element={<ForbiddenPage />} />
          <Route element={<ProtectedRoute allowedRoles={["STUDENT"]} />}>
            <Route path="/exam/join" element={<JoinExam />} />
            <Route path="/exam/lobby/:examId" element={<ExamLobby />} />
          </Route>
          {/* Post-Exam Review Mode Interface (Issue #15, WBS 5.1.2): all authenticated roles; API enforces ownership */}
          <Route path="/review" element={<ReviewExamView />} />
          <Route path="/review/:attemptId" element={<ReviewExamView />} />
        </Route>

        {/* 3. Focused Exam Room (Wrapped in Isolated ExamFocusLayout for Module 3) */}
        <Route element={<ProtectedRoute allowedRoles={["STUDENT"]} />}>
          <Route element={<ExamFocusLayout />}>
            <Route path="/exam" element={<ExamPlaceholder />} />
            <Route path="/exam/:attemptId" element={<ExamRoom />} />
          </Route>
        </Route>
      </Route>

      {/* 4. Fallback 404 Route */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export default AppRoutes;
