import React, { useState } from "react";
import {
  Sparkles,
  Bot,
  AlertTriangle,
  CheckCircle2,
  BookOpen,
  ArrowRight,
  TrendingDown,
  Target,
  ChevronDown,
  ChevronUp,
  Award,
  Layers,
} from "lucide-react";
import { KnowledgeGapData } from "@/services/tutorService";

interface KnowledgeGapCardProps {
  data: KnowledgeGapData;
  loading?: boolean;
}

export const KnowledgeGapCard: React.FC<KnowledgeGapCardProps> = ({
  data,
  loading = false,
}) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(true);

  if (loading) {
    return (
      <div className="rounded-2xl border border-amber-200 bg-amber-50/40 p-6 animate-pulse text-amber-900">
        <div className="h-6 w-1/3 bg-amber-200/60 rounded-md mb-3" />
        <div className="h-4 w-2/3 bg-amber-200/40 rounded-md mb-2" />
        <div className="h-20 bg-amber-200/30 rounded-xl" />
      </div>
    );
  }

  const {
    summary_headline,
    primary_weak_topic,
    has_gaps,
    total_wrong,
    total_questions,
    weak_topics,
    advice,
  } = data;

  return (
    <div
      className={`rounded-2xl border transition-all duration-300 shadow-sm overflow-hidden ${
        has_gaps
          ? "border-amber-300/80 bg-gradient-to-br from-amber-50/80 via-white to-orange-50/40"
          : "border-emerald-300/80 bg-gradient-to-br from-emerald-50/80 via-white to-teal-50/40"
      }`}
    >
      {/* 1. Header Banner */}
      <div className="p-5 sm:p-6 pb-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div
              className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl shadow-xs ${
                has_gaps ? "bg-amber-600 text-white" : "bg-emerald-600 text-white"
              }`}
            >
              {has_gaps ? <Target className="h-5 w-5" /> : <Award className="h-5 w-5" />}
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <span
                  className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                    has_gaps
                      ? "bg-amber-100 text-amber-900 border border-amber-200"
                      : "bg-emerald-100 text-emerald-900 border border-emerald-200"
                  }`}
                >
                  <Bot className="inline-block h-3.5 w-3.5 mr-1" />
                  Chẩn đoán bởi AI Tutor
                </span>
                <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-slate-100 text-slate-700">
                  WBS 5.2.2 • Issue #17
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Tổng hợp câu hỏi làm sai theo chủ đề & định hướng lộ trình ôn tập cá nhân hóa
              </p>
            </div>
          </div>

          {/* Toggle Expand / Collapse */}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="self-end sm:self-auto p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
            title={isExpanded ? "Thu gọn thẻ" : "Mở rộng thẻ"}
          >
            {isExpanded ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
          </button>
        </div>

        {/* Primary Headline Callout Box (Fulfills Acceptance Criteria 1) */}
        <div
          className={`mt-4 p-4 rounded-xl border flex items-start gap-3.5 ${
            has_gaps
              ? "bg-amber-100/70 border-amber-300 text-amber-950"
              : "bg-emerald-100/70 border-emerald-300 text-emerald-950"
          }`}
        >
          {has_gaps ? (
            <AlertTriangle className="h-5 w-5 shrink-0 text-amber-600 mt-0.5" />
          ) : (
            <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-600 mt-0.5" />
          )}
          <div className="flex-1">
            <h2 className="text-base sm:text-lg font-bold leading-snug">
              {summary_headline}
            </h2>
            {has_gaps ? (
              <p className="text-xs text-amber-900/90 mt-1">
                Hệ thống phát hiện bạn làm sai <strong>{total_wrong} / {total_questions}</strong> câu hỏi. 
                {primary_weak_topic && (
                  <span>
                    {" "}Tập trung củng cố chuyên đề <strong>"{primary_weak_topic}"</strong> sẽ giúp bạn cải thiện điểm số nhanh nhất trong các kỳ thi tới.
                  </span>
                )}
              </p>
            ) : (
              <p className="text-xs text-emerald-900/90 mt-1">
                Bạn đã làm chủ toàn bộ các chủ đề trong bài thi với độ chính xác tuyệt đối. Tiếp tục phát huy!
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Expanded Details: Weak Topics Breakdown & Actionable Study Advice */}
      {isExpanded && (
        <div className="p-5 sm:p-6 pt-0 space-y-5">
          {/* 2. Weak Topics Breakdown Table / Badges */}
          {has_gaps && weak_topics && weak_topics.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-slate-500 mb-2.5">
                <Layers className="h-3.5 w-3.5" />
                <span>Chi tiết chủ đề & tỷ lệ nhầm lẫn:</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {weak_topics.map((item, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-xl border border-slate-200 bg-white shadow-2xs flex flex-col justify-between"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="flex h-5 w-5 items-center justify-center rounded-md bg-rose-100 text-rose-800 font-bold text-[11px]">
                          {idx + 1}
                        </span>
                        <h4 className="text-xs sm:text-sm font-semibold text-slate-800">
                          {item.topic}
                        </h4>
                      </div>
                      <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200 shrink-0">
                        Sai {item.wrong_count}/{item.total_questions} câu
                      </span>
                    </div>

                    {/* Accuracy Progress Bar */}
                    <div className="mt-3">
                      <div className="flex items-center justify-between text-[11px] text-slate-500 mb-1">
                        <span>Độ chính xác:</span>
                        <span className="font-semibold text-slate-700">
                          {item.accuracy_percentage.toFixed(1)}%
                        </span>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                        <div
                          className={`h-1.5 rounded-full transition-all duration-500 ${
                            item.accuracy_percentage >= 50
                              ? "bg-amber-500"
                              : "bg-rose-500"
                          }`}
                          style={{ width: `${Math.max(5, item.accuracy_percentage)}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 3. Actionable Study Advice (Fulfills Acceptance Criteria 2: Min 2 suggestions) */}
          {advice && advice.length > 0 && (
            <div className="pt-2 border-t border-slate-200/80">
              <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-slate-600 mb-3">
                <Sparkles className="h-3.5 w-3.5 text-amber-500 fill-amber-400" />
                <span>Gợi ý ôn tập đề xuất (Actionable Study Advice):</span>
              </div>

              <div className="grid grid-cols-1 gap-3">
                {advice.map((adv, index) => {
                  let badgeBg = "bg-emerald-50 text-emerald-800 border-emerald-200";
                  let actionLabel = "Luyện tập";
                  if (adv.action_type === "REVIEW_THEORY") {
                    badgeBg = "bg-blue-50 text-blue-800 border-blue-200";
                    actionLabel = "Lý thuyết";
                  } else if (adv.action_type === "AI_TUTOR_REVIEW") {
                    badgeBg = "bg-purple-50 text-purple-800 border-purple-200";
                    actionLabel = "AI Tutor";
                  } else if (adv.action_type === "ADVANCED_STUDY") {
                    badgeBg = "bg-emerald-50 text-emerald-800 border-emerald-200";
                    actionLabel = "Nâng cao";
                  }

                  return (
                    <div
                      key={index}
                      className="p-4 rounded-xl border border-slate-200/90 bg-white hover:border-slate-300 transition-colors shadow-2xs flex flex-col sm:flex-row sm:items-start justify-between gap-3.5"
                    >
                      <div className="flex items-start gap-3">
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-700 font-bold text-xs mt-0.5">
                          #{index + 1}
                        </div>
                        <div>
                          <div className="flex flex-wrap items-center gap-2">
                            <h4 className="text-sm font-bold text-slate-900">
                              {adv.title}
                            </h4>
                            <span
                              className={`px-2 py-0.5 rounded-md text-[11px] font-semibold border ${badgeBg}`}
                            >
                              {actionLabel}
                            </span>
                            {adv.priority === "HIGH" && (
                              <span className="px-2 py-0.5 rounded-md text-[11px] font-medium bg-rose-50 text-rose-700 border border-rose-200">
                                Ưu tiên cao
                              </span>
                            )}
                          </div>
                          <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">
                            {adv.description}
                          </p>
                          {adv.resource_hint && (
                            <div className="mt-2 flex items-center gap-1.5 text-[11px] text-slate-500">
                              <BookOpen className="h-3 w-3 text-slate-400" />
                              <span>Gợi ý tài liệu: <strong>{adv.resource_hint}</strong></span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default KnowledgeGapCard;
