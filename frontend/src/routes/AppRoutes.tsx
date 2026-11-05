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
          <Route path="/" element={<Navigate to="/parser" replace />} />
          <Route path="/parser" element={<ParserPlaceholder />} />
          <Route path="/ai-generator" element={<AiGenPlaceholder />} />
          <Route path="/analytics" element={<AnalyticsPlaceholder />} />
          {/* Post-Exam Review Mode Interface (Issue #15, WBS 5.1.2) */}
          <Route path="/review" element={<ReviewExamView />} />
          <Route path="/review/:attemptId" element={<ReviewExamView />} />
        </Route>

        {/* 3. Focused Exam Room (Wrapped in Isolated ExamFocusLayout for Module 3) */}
        <Route element={<ExamFocusLayout />}>
          <Route path="/exam" element={<ExamPlaceholder />} />
          <Route path="/exam/:attemptId" element={<ExamPlaceholder />} />
        </Route>
      </Route>

      {/* 4. Fallback 404 Route */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export default AppRoutes;
