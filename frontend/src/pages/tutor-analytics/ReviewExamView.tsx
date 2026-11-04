import React, { useState } from "react";
import {
  Bot,
  CheckCircle2,
  XCircle,
  Sparkles,
  Loader2,
  RefreshCw,
  Filter,
  Award,
  Clock,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import AITutorExplanationCard from "@/components/tutor/AITutorExplanationCard";
import { tutorService, AITutorFeedback } from "@/services/tutorService";

interface QuestionOption {
  id: string;
  text: string;
  is_correct: boolean;
}

interface ReviewQuestionItem {
  id: string;
  content: string;
  cognitive_level: string;
  options: QuestionOption[];
  selected_options: string[];
  correct_options: string[];
  is_correct: boolean;
  explanation_note?: string;
  ai_feedback?: AITutorFeedback;
  response_time_ms?: number;
}

// Sample realistic exam attempt data matching seed.py (Quản trị dự án phần mềm)
const SAMPLE_REVIEW_QUESTIONS: ReviewQuestionItem[] = [
  {
    id: "q-1",
    content: "Trong chuẩn quản lý dự án PMBOK, WBS (Work Breakdown Structure) được định nghĩa là gì?",
    cognitive_level: "REMEMBER",
    options: [
      { id: "A", text: "Cấu trúc phân rã công việc định hướng theo sản phẩm bàn giao (Deliverable-oriented hierarchical decomposition)", is_correct: true },
      { id: "B", text: "Bảng phân bổ ngân sách chi tiết và lịch biểu thanh toán hàng tuần của dự án", is_correct: false },
      { id: "C", text: "Báo cáo tổng kết khối lượng công việc hàng tuần của nhóm Scrum", is_correct: false },
      { id: "D", text: "Hệ thống quản lý quy trình luồng công việc tự động trên Jira", is_correct: false },
    ],
    selected_options: ["B"], // Student answered WRONG
    correct_options: ["A"],
    is_correct: false,
    explanation_note: "WBS là cấu trúc phân rã công việc mang tính định hướng bàn giao (Deliverable-oriented), tuân thủ quy tắc 100% Rule.",
  },
  {
    id: "q-2",
    content: "Theo mô hình Agile/Scrum, nguyên tắc 'WIP Limit' (Work In Progress Limit) trên Kanban Board có mục đích cốt lõi là gì?",
    cognitive_level: "UNDERSTAND",
    options: [
      { id: "A", text: "Ngăn chặn nghẽn cổ chai (bottlenecks), tối ưu hóa lưu lượng luân chuyển công việc và nâng cao chất lượng", is_correct: true },
      { id: "B", text: "Bắt buộc mọi lập trình viên phải hoàn thành tất cả task trước giờ Daily Standup", is_correct: false },
      { id: "C", text: "Giới hạn số giờ làm việc thêm (overtime) của thành viên trong tuần", is_correct: false },
      { id: "D", text: "Tự động phân công công việc từ Backlog sang cột In Progress", is_correct: false },
    ],
    selected_options: ["A"], // Student answered CORRECT
    correct_options: ["A"],
    is_correct: true,
    explanation_note: "WIP Limit hạn chế số lượng công việc được triển khai đồng thời trong một giai đoạn để tránh tắc nghẽn.",
  },
  {
    id: "q-3",
    content: "Trong một dự án phần mềm gồm 4 thành viên, Scrum Master phát hiện hai lập trình viên cùng nhận hai Issue phụ thuộc chéo vào CSDL của nhau dẫn đến tắc nghẽn. Giải pháp kiến trúc nào là phù hợp nhất theo tài liệu dự án?",
    cognitive_level: "APPLY",
    options: [
      { id: "A", text: "Yêu cầu cả 2 dev tạm dừng, đợi Tech Leader thiết kế xong toàn bộ DB mới bắt đầu viết code", is_correct: false },
      { id: "B", text: "Áp dụng nguyên tắc Decoupled Rule: thống nhất Interface/Contract sớm, lập trình viên sử dụng Mock Data độc lập", is_correct: true },
      { id: "C", text: "Gộp 2 Issue lại thành 1 Issue lớn và chỉ giao cho 1 người làm từ đầu đến cuối", is_correct: false },
      { id: "D", text: "Chuyển dự án từ Agile/Scrum sang mô hình Thác nước (Waterfall)", is_correct: false },
    ],
    selected_options: ["A"], // Student answered WRONG
    correct_options: ["B"],
    is_correct: false,
    explanation_note: "Nguyên tắc Decoupled Rule khóa hợp đồng giao tiếp sớm (Interfaces/Schemas) cho phép các thành viên làm việc song song với Mock data.",
  },
];

export const ReviewExamView: React.FC = () => {
  const [questions, setQuestions] = useState<ReviewQuestionItem[]>(SAMPLE_REVIEW_QUESTIONS);
  const [filterMode, setFilterMode] = useState<"ALL" | "INCORRECT" | "CORRECT">("ALL");
  const [loadingQuestions, setLoadingQuestions] = useState<Record<string, boolean>>({});
  const [errorQuestions, setErrorQuestions] = useState<Record<string, string>>({});
  const [elapsedTimers, setElapsedTimers] = useState<Record<string, number>>({});
  const [expandedCards, setExpandedCards] = useState<Record<string, boolean>>({
    "q-1": true,
    "q-3": true,
  });

  const correctCount = questions.filter((q) => q.is_correct).length;
  const totalCount = questions.length;
  const scoreThang10 = ((correctCount / totalCount) * 10).toFixed(1);

  const filteredQuestions = questions.filter((q) => {
    if (filterMode === "INCORRECT") return !q.is_correct;
    if (filterMode === "CORRECT") return q.is_correct;
    return true;
  });

  const handleRequestAIExplanation = async (question: ReviewQuestionItem) => {
    const qId = question.id;
    setLoadingQuestions((prev) => ({ ...prev, [qId]: true }));
    setErrorQuestions((prev) => ({ ...prev, [qId]: "" }));
    setExpandedCards((prev) => ({ ...prev, [qId]: true }));

    // Start a timer ticker to show live sub-3-second progress
    const startTime = Date.now();
    const interval = setInterval(() => {
      setElapsedTimers((prev) => ({
        ...prev,
        [qId]: (Date.now() - startTime) / 1000,
      }));
    }, 100);

    try {
      const result = await tutorService.getExplanation({
        question_id: qId,
        question_content: question.content,
        question_type: "SINGLE_CHOICE",
        options: question.options,
        selected_options: question.selected_options,
        correct_options: question.correct_options,
        question_explanation: question.explanation_note,
      });

      setQuestions((prevList) =>
        prevList.map((item) =>
          item.id === qId
            ? {
                ...item,
                ai_feedback: result.feedback,
                response_time_ms: result.response_time_ms,
              }
            : item
        )
      );
    } catch (error: any) {
      console.error("Error fetching AI explanation:", error);
      const message =
        error?.response?.data?.detail ||
        error?.message ||
        "Không gọi được AI Tutor. Kiểm tra backend đang chạy và cấu hình LLM_API_KEY trong backend/.env.";
      setErrorQuestions((prev) => ({ ...prev, [qId]: String(message) }));
    } finally {
      clearInterval(interval);
      setLoadingQuestions((prev) => ({ ...prev, [qId]: false }));
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* 1. Exam Overview Summary Banner */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
                Chế độ xem lại (Review Mode)
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700">
                WBS 5.2.1 • Issue #16
              </span>
            </div>
            <h1 className="text-2xl font-bold text-slate-900">
              Kiểm tra Quản trị Dự án Phần mềm — Sprint 1
            </h1>
            <p className="text-sm text-slate-500 mt-0.5">
              Thí sinh: <strong>Sinh viên Mẫu (student@smartquiz.edu.vn)</strong> • Trạng thái:{" "}
              <span className="text-emerald-600 font-medium">Đã nộp bài</span>
            </p>
          </div>

          {/* Score Badge */}
          <div className="flex items-center gap-4 bg-slate-50 border border-slate-200 rounded-xl p-3.5 px-5">
            <div className="text-center">
              <div className="text-xs uppercase font-medium text-slate-400">Điểm số</div>
              <div className="text-2xl font-extrabold text-slate-800">
                {scoreThang10} <span className="text-sm font-normal text-slate-400">/ 10</span>
              </div>
            </div>
            <div className="h-8 w-px bg-slate-200" />
            <div className="text-center">
              <div className="text-xs uppercase font-medium text-slate-400">Kết quả</div>
              <div className="text-sm font-semibold text-slate-700">
                <span className="text-emerald-600 font-bold">{correctCount}</span> đúng /{" "}
                <span className="text-rose-500 font-bold">{totalCount - correctCount}</span> sai
              </div>
            </div>
          </div>
        </div>

        {/* DoD Banner */}
        <div className="mt-5 rounded-xl bg-gradient-to-r from-emerald-500/10 via-teal-500/10 to-transparent p-3.5 border border-emerald-200/60 flex items-center justify-between gap-4 text-xs text-emerald-950">
          <div className="flex items-center gap-2">
            <Bot className="h-4 w-4 text-emerald-600 shrink-0" />
            <span>
              <strong>Acceptance Criteria (DoD):</strong> Bấm nút{" "}
              <span className="font-semibold text-emerald-700">"Giải thích bằng AI"</span> trên câu
              sai hiển thị lời giải thích chi tiết trong vòng <strong>&lt; 3 giây</strong> với giọng
              văn sư phạm chuẩn mực.
            </span>
          </div>
          <span className="inline-flex items-center gap-1 font-semibold text-emerald-700 whitespace-nowrap">
            <Sparkles className="h-3.5 w-3.5" /> Chuẩn Issue #16
          </span>
        </div>
      </div>

      {/* 2. Filter & Navigation Bar */}
      <div className="flex items-center justify-between gap-3 bg-white p-3 rounded-xl border border-slate-200 shadow-2xs">
        <div className="flex items-center gap-1.5 text-xs font-medium">
          <Filter className="h-4 w-4 text-slate-400 ml-2 mr-1" />
          <button
            onClick={() => setFilterMode("ALL")}
            className={`px-3 py-1.5 rounded-lg transition-colors ${
              filterMode === "ALL"
                ? "bg-slate-900 text-white font-semibold"
                : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            Tất cả ({totalCount})
          </button>
          <button
            onClick={() => setFilterMode("INCORRECT")}
            className={`px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 ${
              filterMode === "INCORRECT"
                ? "bg-rose-600 text-white font-semibold"
                : "text-rose-700 hover:bg-rose-50"
            }`}
          >
            <XCircle className="h-3.5 w-3.5" />
            Chỉ câu sai ({totalCount - correctCount})
          </button>
          <button
            onClick={() => setFilterMode("CORRECT")}
            className={`px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 ${
              filterMode === "CORRECT"
                ? "bg-emerald-600 text-white font-semibold"
                : "text-emerald-700 hover:bg-emerald-50"
            }`}
          >
            <CheckCircle2 className="h-3.5 w-3.5" />
            Chỉ câu đúng ({correctCount})
          </button>
        </div>

        <div className="text-xs text-slate-500 pr-2">
          Hiển thị <strong>{filteredQuestions.length}</strong> câu hỏi
        </div>
      </div>

      {/* 3. Questions List */}
      <div className="space-y-5">
        {filteredQuestions.map((q, index) => {
          const isLoading = loadingQuestions[q.id];
          const hasFeedback = !!q.ai_feedback;
          const isExpanded = expandedCards[q.id];

          return (
            <div
              key={q.id}
              className={`rounded-2xl border transition-all duration-200 bg-white p-6 shadow-xs ${
                q.is_correct ? "border-slate-200" : "border-rose-200/90 ring-1 ring-rose-100/50"
              }`}
            >
              {/* Question Header */}
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-center gap-2.5">
                  <span
                    className={`flex h-7 w-7 items-center justify-center rounded-lg text-xs font-bold ${
                      q.is_correct
                        ? "bg-emerald-100 text-emerald-800"
                        : "bg-rose-100 text-rose-800"
                    }`}
                  >
                    {index + 1}
                  </span>
                  <span
                    className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md text-xs font-semibold ${
                      q.is_correct
                        ? "bg-emerald-50 text-emerald-700 border border-emerald-200/60"
                        : "bg-rose-50 text-rose-700 border border-rose-200/60"
                    }`}
                  >
                    {q.is_correct ? (
                      <>
                        <CheckCircle2 className="h-3.5 w-3.5" /> Đúng (+1.0 đ)
                      </>
                    ) : (
                      <>
                        <XCircle className="h-3.5 w-3.5" /> Sai (0.0 đ)
                      </>
                    )}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-slate-100 text-slate-600">
                    Bloom: {q.cognitive_level}
                  </span>
                </div>

                {/* AI Tutor Explanation Action Button */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleRequestAIExplanation(q)}
                    disabled={isLoading}
                    className={`inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all shadow-xs ${
                      hasFeedback
                        ? "bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200"
                        : q.is_correct
                        ? "bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-200"
                        : "bg-gradient-to-r from-emerald-600 to-teal-600 text-white hover:from-emerald-700 hover:to-teal-700 active:scale-95"
                    }`}
                    title="Bấm để nhận giải thích chi tiết từ Gia sư ảo AI trong vòng < 3 giây"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        <span>Đang phân tích... ({(elapsedTimers[q.id] || 0).toFixed(1)}s)</span>
                      </>
                    ) : hasFeedback ? (
                      <>
                        <RefreshCw className="h-3.5 w-3.5" />
                        <span>Phân tích lại bằng AI</span>
                      </>
                    ) : (
                      <>
                        <Bot className="h-4 w-4" />
                        <span>Giải thích bằng AI</span>
                        <Sparkles className="h-3 w-3 text-amber-300" />
                      </>
                    )}
                  </button>

                  {hasFeedback && (
                    <button
                      onClick={() =>
                        setExpandedCards((prev) => ({ ...prev, [q.id]: !prev[q.id] }))
                      }
                      className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
                      title={isExpanded ? "Thu gọn" : "Mở rộng"}
                    >
                      {isExpanded ? (
                        <ChevronUp className="h-4 w-4" />
                      ) : (
                        <ChevronDown className="h-4 w-4" />
                      )}
                    </button>
                  )}
                </div>
              </div>

              {/* Question Content */}
              <div className="mt-3.5 text-base font-semibold text-slate-900 leading-snug">
                {q.content}
              </div>

              {/* Options List */}
              <div className="mt-4 grid grid-cols-1 gap-2">
                {q.options.map((opt) => {
                  const isSelected = q.selected_options.includes(opt.id);
                  const isCorrect = opt.is_correct;

                  let borderStyle = "border-slate-200 bg-white hover:bg-slate-50";
                  let badgeStyle = "bg-slate-100 text-slate-700";

                  if (isCorrect) {
                    borderStyle = "border-emerald-300 bg-emerald-50/70 text-emerald-950 font-medium";
                    badgeStyle = "bg-emerald-600 text-white";
                  } else if (isSelected && !isCorrect) {
                    borderStyle = "border-rose-300 bg-rose-50/70 text-rose-950 font-medium line-through";
                    badgeStyle = "bg-rose-600 text-white";
                  }

                  return (
                    <div
                      key={opt.id}
                      className={`flex items-center justify-between p-3 rounded-xl border text-sm transition-colors ${borderStyle}`}
                    >
                      <div className="flex items-center gap-3">
                        <span
                          className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-lg text-xs font-bold ${badgeStyle}`}
                        >
                          {opt.id}
                        </span>
                        <span>{opt.text}</span>
                      </div>

                      <div className="flex items-center gap-2 text-xs">
                        {isSelected && (
                          <span
                            className={`px-2 py-0.5 rounded-md font-semibold ${
                              isCorrect
                                ? "bg-emerald-100 text-emerald-800"
                                : "bg-rose-100 text-rose-800"
                            }`}
                          >
                            Bạn đã chọn
                          </span>
                        )}
                        {isCorrect && (
                          <span className="px-2 py-0.5 rounded-md font-semibold bg-emerald-200 text-emerald-900 flex items-center gap-1">
                            <CheckCircle2 className="h-3 w-3" /> Đáp án chuẩn
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* AI Tutor Feedback Card */}
              {hasFeedback && isExpanded && (
                <AITutorExplanationCard
                  feedback={q.ai_feedback!}
                  responseTimeMs={q.response_time_ms}
                />
              )}

              {/* AI Tutor Error State (no mock data — surface the real failure) */}
              {errorQuestions[q.id] && !isLoading && (
                <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50/70 p-4 text-sm text-rose-800 flex items-start gap-2.5">
                  <XCircle className="h-5 w-5 shrink-0 mt-0.5 text-rose-600" />
                  <div>
                    <p className="font-semibold">Không nhận được lời giải từ AI Tutor</p>
                    <p className="text-rose-700/90 mt-0.5">{errorQuestions[q.id]}</p>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ReviewExamView;
