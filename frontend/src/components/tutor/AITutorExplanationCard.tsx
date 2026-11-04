import React from "react";
import { Bot, CheckCircle2, AlertTriangle, BookOpen, Sparkles, Clock, Zap } from "lucide-react";
import { AITutorFeedback } from "@/services/tutorService";

interface AITutorExplanationCardProps {
  feedback: AITutorFeedback;
  responseTimeMs?: number;
  cached?: boolean;
}

export const AITutorExplanationCard: React.FC<AITutorExplanationCardProps> = ({
  feedback,
  responseTimeMs,
  cached = false,
}) => {
  const isUnder3Seconds = responseTimeMs !== undefined ? responseTimeMs < 3000 : true;

  return (
    <div className="mt-4 rounded-xl border border-emerald-200 bg-gradient-to-br from-emerald-50/60 via-white to-teal-50/40 p-5 shadow-sm transition-all duration-300 animate-in fade-in slide-in-from-top-2">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-emerald-100 pb-3.5 mb-4">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-600 text-white shadow-sm">
            <Bot className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-slate-800 text-base flex items-center gap-1.5">
                Gia sư ảo AI (Contextual AI Tutor)
                <Sparkles className="h-4 w-4 text-amber-500 fill-amber-400" />
              </h3>
            </div>
            <p className="text-xs text-slate-500">
              Phân tích ngữ cảnh & chẩn đoán tư duy nhầm lẫn
            </p>
          </div>
        </div>

        {/* Latency & Metadata Badges */}
        <div className="flex items-center gap-2 text-xs">
          {responseTimeMs !== undefined && (
            <span
              className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full font-medium ${
                isUnder3Seconds
                  ? "bg-emerald-100 text-emerald-800 border border-emerald-200"
                  : "bg-amber-100 text-amber-800 border border-amber-200"
              }`}
              title="DoD: Phản hồi < 3 giây"
            >
              <Zap className="h-3 w-3" />
              {(responseTimeMs / 1000).toFixed(2)}s {isUnder3Seconds && "(< 3s DoD ✓)"}
            </span>
          )}
          {cached && (
            <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 text-[11px] font-medium border border-slate-200">
              Đã lưu cache
            </span>
          )}
          {feedback.model && (
            <span className="px-2.5 py-1 rounded-md bg-slate-100 text-slate-700 font-mono text-[11px] border border-slate-200">
              {feedback.model}
            </span>
          )}
        </div>
      </div>

      <div className="space-y-4 text-sm">
        {/* 1. Giải thích vì sao đáp án chuẩn đúng */}
        <div className="rounded-lg bg-white/90 p-3.5 border border-emerald-100 shadow-2xs">
          <div className="flex items-start gap-2.5">
            <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0 mt-0.5" />
            <div>
              <h4 className="font-semibold text-emerald-950 mb-1">
                Tại sao đáp án chuẩn là đúng?
              </h4>
              <p className="text-slate-700 leading-relaxed whitespace-pre-line">
                {feedback.explanation}
              </p>
            </div>
          </div>
        </div>

        {/* 2. Phân tích nguyên nhân nhầm lẫn (Vì sao chọn sai) */}
        {feedback.why_selected_wrong && (
          <div className="rounded-lg bg-amber-50/70 p-3.5 border border-amber-200/80 shadow-2xs">
            <div className="flex items-start gap-2.5">
              <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
              <div>
                <h4 className="font-semibold text-amber-950 mb-1">
                  Chẩn đoán nguyên nhân bạn chọn sai:
                </h4>
                <p className="text-slate-700 leading-relaxed whitespace-pre-line">
                  {feedback.why_selected_wrong}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* 3. Gợi ý lỗ hổng kiến thức cần ôn tập */}
        {feedback.study_suggestions && feedback.study_suggestions.length > 0 && (
          <div className="rounded-lg bg-sky-50/70 p-3.5 border border-sky-200/80 shadow-2xs">
            <div className="flex items-start gap-2.5">
              <BookOpen className="h-5 w-5 text-sky-600 shrink-0 mt-0.5" />
              <div className="w-full">
                <h4 className="font-semibold text-sky-950 mb-1.5">
                  Lộ trình khắc phục lỗ hổng kiến thức:
                </h4>
                <ul className="space-y-1.5">
                  {feedback.study_suggestions.map((item, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-slate-700">
                      <span className="text-sky-500 font-bold">•</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer Info */}
      <div className="mt-3.5 pt-2.5 border-t border-emerald-100 flex items-center justify-between text-xs text-slate-400">
        <span className="flex items-center gap-1">
          <Clock className="h-3 w-3" />
          {feedback.generated_at ? new Date(feedback.generated_at).toLocaleTimeString("vi-VN") : "Vừa xong"}
        </span>
        <span className="italic">
          Giọng văn sư phạm chuẩn mực, phân tích bám sát ma trận Bloom
        </span>
      </div>
    </div>
  );
};

export default AITutorExplanationCard;
