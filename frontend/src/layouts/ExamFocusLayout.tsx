import React from "react";
import { Outlet } from "react-router-dom";

/**
 * ExamFocusLayout:
 * Isolated distraction-free layout without navigation bars or global headers.
 * Dedicated to Module 3 (Dev 3) for online exam delivery and client anti-cheat monitoring.
 */
export const ExamFocusLayout: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-100 flex flex-col">
      {/* Isolated Outlet for Focused Exam Experience */}
      <main className="flex-1 w-full">
        <Outlet />
      </main>
    </div>
  );
};

export default ExamFocusLayout;
