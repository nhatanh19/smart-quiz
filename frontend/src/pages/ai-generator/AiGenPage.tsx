import React, { useState, useCallback } from "react";
import {
  Sparkles,
  Settings2,
  Eye,
  Zap,
  Save,
  CheckSquare,
  Square,
  ChevronDown,
  ChevronUp,
  Loader2,
  AlertCircle,
  CheckCircle2,
  RefreshCw,
} from "lucide-react";
import {
  previewMatrixAllocation,
  generateByMatrix,
  type MatrixRequest,
  type MatrixPreviewData,
  type GeneratedQuestionItem,
} from "@/services/aiGeneratorApi";
import {
  listSubjects,
  listCategories,
  createQuestion,
} from "@/services/questionBankApi";
import type { Subject, Category, QuestionOption } from "@/types";

// ==============================================================================
// HELPERS
// ==============================================================================

function clamp(val: number, min: number, max: number) {
  return Math.min(max, Math.max(min, val));
}

const BLOOM_COLORS: Record<string, string> = {
  REMEMBER: "bg-blue-100 text-blue-800",
  UNDERSTAND: "bg-green-100 text-green-800",
  APPLY: "bg-orange-100 text-orange-800",
};

const BLOOM_LABELS: Record<string, string> = {
  REMEMBER: "Nhận biết",
  UNDERSTAND: "Thông hiểu",
  APPLY: "Vận dụng",
};

const TYPE_LABELS: Record<string, string> = {
  SINGLE_CHOICE: "Một đáp án",
  MULTIPLE_CHOICE: "Nhiều đáp án",
  TRUE_FALSE: "Đúng/Sai",
};

const LEVEL_LABELS: Record<string, string> = {
  EASY: "Dễ",
  MEDIUM: "Trung bình",
  HARD: "Khó",
};

function extractError(error: unknown): string {
  if (error instanceof Error) return error.message;
  return "Đã xảy ra lỗi không xác định.";
}

// ==============================================================================
// SUB-COMPONENTS
// ==============================================================================

/** Thanh phần trăm tỷ lệ Bloom / Type */
function RatioInput({
  label,
  value,
  onChange,
  colorClass,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  colorClass?: string;
}) {
  return (
    <div className="flex items-center gap-3">
      <span
        className={`text-xs font-semibold px-2 py-0.5 rounded-full whitespace-nowrap ${colorClass ?? "bg-slate-100 text-slate-700"}`}
      >
        {label}
      </span>
      <input
        type="range"
        min={0}
        max={100}
        step={5}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="flex-1 accent-purple-600"
      />
      <input
        type="number"
        min={0}
        max={100}
        step={5}
        value={value}
        onChange={(e) => onChange(clamp(Number(e.target.value), 0, 100))}
        className="w-16 border border-slate-200 rounded-md px-2 py-1 text-sm text-right"
      />
      <span className="text-xs text-slate-400 w-4">%</span>
    </div>
  );
}

/** Badge tổng tỷ lệ — đỏ nếu ≠ 100 */
function SumBadge({ sum, label }: { sum: number; label: string }) {
  const ok = sum === 100;
  return (
    <div
      className={`flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full ${ok ? "bg-green-50 text-green-700" : "bg-red-50 text-red-600"}`}
    >
      {ok ? (
        <CheckCircle2 className="w-3 h-3" />
      ) : (
        <AlertCircle className="w-3 h-3" />
      )}
      {label}: {sum}%{!ok && " (phải = 100%)"}
    </div>
  );
}

/** Card câu hỏi có thể edit nhẹ */
function QuestionCard({
  index,
  question,
  selected,
  onToggleSelect,
  onEdit,
}: {
  index: number;
  question: GeneratedQuestionItem & { _localId: number };
  selected: boolean;
  onToggleSelect: () => void;
  onEdit: (field: string, value: unknown) => void;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className={`border rounded-lg transition-all ${selected ? "border-purple-400 bg-purple-50/30" : "border-slate-200 bg-white"}`}
    >
      {/* Header */}
      <div className="flex items-start gap-3 p-4">
        <button
          onClick={onToggleSelect}
          className="mt-0.5 flex-shrink-0 text-purple-600"
        >
          {selected ? (
            <CheckSquare className="w-5 h-5" />
          ) : (
            <Square className="w-5 h-5 text-slate-400" />
          )}
        </button>

        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap gap-1.5 mb-2">
            <span
              className={`text-xs px-2 py-0.5 rounded-full font-medium ${BLOOM_COLORS[question.cognitive_level] ?? "bg-slate-100 text-slate-600"}`}
            >
              {BLOOM_LABELS[question.cognitive_level] ?? question.cognitive_level}
            </span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-medium">
              {TYPE_LABELS[question.question_type] ?? question.question_type}
            </span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
              {LEVEL_LABELS[question.level] ?? question.level}
            </span>
          </div>

          {/* Content editable */}
          <textarea
            value={question.content}
            onChange={(e) => onEdit("content", e.target.value)}
            rows={2}
            className="w-full text-sm text-slate-800 font-medium border-0 bg-transparent resize-none focus:ring-1 focus:ring-purple-300 rounded p-1 -ml-1"
          />
        </div>

        <button
          onClick={() => setExpanded((p) => !p)}
          className="flex-shrink-0 text-slate-400 hover:text-slate-600"
        >
          {expanded ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </button>
      </div>

      {/* Options & Explanation */}
      {expanded && (
        <div className="px-4 pb-4 border-t border-slate-100 pt-3 space-y-2">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
            Đáp án
          </p>
          {question.options.map((opt: QuestionOption, oi: number) => (
            <div key={opt.id} className="flex items-center gap-2">
              <span
                className={`text-xs font-bold w-5 h-5 flex items-center justify-center rounded-full flex-shrink-0 ${opt.is_correct ? "bg-green-500 text-white" : "bg-slate-200 text-slate-600"}`}
              >
                {opt.id}
              </span>
              <input
                type="text"
                value={opt.text}
                onChange={(e) => {
                  const updated = question.options.map((o: QuestionOption, i: number) =>
                    i === oi ? { ...o, text: e.target.value } : o,
                  );
                  onEdit("options", updated);
                }}
                className="flex-1 text-sm border border-slate-200 rounded px-2 py-1 focus:ring-1 focus:ring-purple-300"
              />
            </div>
          ))}

          {question.explanation && (
            <div className="mt-2">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">
                Giải thích
              </p>
              <textarea
                value={question.explanation ?? ""}
                onChange={(e) => onEdit("explanation", e.target.value)}
                rows={2}
                className="w-full text-sm text-slate-600 border border-slate-200 rounded px-2 py-1 focus:ring-1 focus:ring-purple-300 resize-none"
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ==============================================================================
// MAIN PAGE
// ==============================================================================

type Step = "config" | "review";

interface LocalQuestion extends GeneratedQuestionItem {
  _localId: number;
}

export const AiGenPage: React.FC = () => {
  // ── Config state ────────────────────────────────────────────────────────────
  const [topic, setTopic] = useState("");
  const [totalQuestions, setTotalQuestions] = useState(10);

  const [bloomRatios, setBloomRatios] = useState({
    REMEMBER: 40,
    UNDERSTAND: 40,
    APPLY: 20,
  });
  const [typeRatios, setTypeRatios] = useState({
    SINGLE_CHOICE: 60,
    MULTIPLE_CHOICE: 20,
    TRUE_FALSE: 20,
  });

  const bloomSum =
    bloomRatios.REMEMBER + bloomRatios.UNDERSTAND + bloomRatios.APPLY;
  const typeSum =
    typeRatios.SINGLE_CHOICE + typeRatios.MULTIPLE_CHOICE + typeRatios.TRUE_FALSE;

  // ── Preview state ────────────────────────────────────────────────────────────
  const [preview, setPreview] = useState<MatrixPreviewData | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);

  // ── Generate state ───────────────────────────────────────────────────────────
  const [step, setStep] = useState<Step>("config");
  const [questions, setQuestions] = useState<LocalQuestion[]>([]);
  const [genLoading, setGenLoading] = useState(false);
  const [genError, setGenError] = useState<string | null>(null);

  // ── Save state ───────────────────────────────────────────────────────────────
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState("");
  const [selectedCategoryId, setSelectedCategoryId] = useState("");
  const [saveLoading, setSaveLoading] = useState(false);
  const [saveResult, setSaveResult] = useState<{
    saved: number;
    failed: number;
  } | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);

  // ── Helpers ──────────────────────────────────────────────────────────────────
  const buildRequest = useCallback((): MatrixRequest => ({
    topic: topic.trim(),
    total_questions: totalQuestions,
    cognitive_ratios: bloomRatios,
    type_ratios: typeRatios,
  }), [topic, totalQuestions, bloomRatios, typeRatios]);

  const canSubmit =
    topic.trim().length > 0 &&
    totalQuestions >= 1 &&
    bloomSum === 100 &&
    typeSum === 100;

  // ── Handlers ─────────────────────────────────────────────────────────────────
  const handlePreview = async () => {
    if (!canSubmit) return;
    setPreviewLoading(true);
    setPreviewError(null);
    try {
      const data = await previewMatrixAllocation(buildRequest());
      setPreview(data);
    } catch (err) {
      setPreviewError(extractError(err));
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleGenerate = async () => {
    if (!canSubmit) return;
    setGenLoading(true);
    setGenError(null);
    try {
      const data = await generateByMatrix(buildRequest());
      const local: LocalQuestion[] = data.generated_questions.map((q, i) => ({
        ...q,
        _localId: i,
      }));
      setQuestions(local);
      setSelectedIds(new Set(local.map((q) => q._localId)));
      setStep("review");

      // Fetch subjects for save dropdown
      const subs = await listSubjects();
      setSubjects(subs);
      if (subs.length > 0) {
        setSelectedSubjectId(subs[0].id);
        const cats = await listCategories();
        const filtered = cats.filter((c) => c.subject_id === subs[0].id);
        setCategories(filtered);
        if (filtered.length > 0) setSelectedCategoryId(filtered[0].id);
      }
    } catch (err) {
      setGenError(extractError(err));
    } finally {
      setGenLoading(false);
    }
  };

  const handleSubjectChange = async (subjectId: string) => {
    setSelectedSubjectId(subjectId);
    setSelectedCategoryId("");
    const cats = await listCategories();
    const filtered = cats.filter((c) => c.subject_id === subjectId);
    setCategories(filtered);
    if (filtered.length > 0) setSelectedCategoryId(filtered[0].id);
  };

  const handleEditQuestion = (localId: number, field: string, value: unknown) => {
    setQuestions((prev) =>
      prev.map((q) => (q._localId === localId ? { ...q, [field]: value } : q)),
    );
  };

  const handleToggleSelect = (localId: number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(localId)) next.delete(localId);
      else next.add(localId);
      return next;
    });
  };

  const handleSelectAll = () => {
    if (selectedIds.size === questions.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(questions.map((q) => q._localId)));
    }
  };

  const handleSave = async () => {
    if (!selectedCategoryId) {
      setSaveError("Vui lòng chọn Danh mục trước khi lưu.");
      return;
    }
    setSaveLoading(true);
    setSaveError(null);
    setSaveResult(null);

    const toSave = questions.filter((q) => selectedIds.has(q._localId));
    let saved = 0;
    let failed = 0;

    for (const q of toSave) {
      try {
        await createQuestion({
          category_id: selectedCategoryId,
          content: q.content,
          question_type: q.question_type,
          cognitive_level: q.cognitive_level,
          level: q.level,
          options: q.options,
          tags: q.tags,
          explanation: q.explanation,
          source_type: "AI_GENERATED",
        });
        saved++;
      } catch {
        failed++;
      }
    }

    setSaveResult({ saved, failed });
    setSaveLoading(false);
  };

  // ==============================================================================
  // RENDER — STEP CONFIG
  // ==============================================================================
  if (step === "config") {
    return (
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Page header */}
        <div className="flex items-center gap-3">
          <div className="p-3 bg-purple-50 text-purple-600 rounded-lg">
            <Sparkles className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-800">
              AI Exam Matrix Builder
            </h1>
            <p className="text-sm text-slate-500">
              Cấu hình ma trận đề thi theo thang nhận thức Bloom và sinh câu hỏi bằng AI
            </p>
          </div>
        </div>

        {/* Config card */}
        <div className="bg-white border border-slate-200 rounded-xl shadow-sm p-6 space-y-6">
          <div className="flex items-center gap-2 text-slate-700 font-semibold">
            <Settings2 className="w-4 h-4 text-purple-500" />
            Thông số cấu hình
          </div>

          {/* Topic */}
          <div className="space-y-1.5">
            <label className="block text-sm font-medium text-slate-700">
              Chủ đề <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="VD: Lập trình hướng đối tượng trong Python"
              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-400"
            />
          </div>

          {/* Total questions */}
          <div className="space-y-1.5">
            <label className="block text-sm font-medium text-slate-700">
              Tổng số câu hỏi <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              min={1}
              max={50}
              value={totalQuestions}
              onChange={(e) =>
                setTotalQuestions(clamp(Number(e.target.value), 1, 50))
              }
              className="w-28 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-400"
            />
          </div>

          {/* Bloom ratios */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-slate-700">
                Tỷ lệ nhận thức Bloom
              </label>
              <SumBadge sum={bloomSum} label="Tổng" />
            </div>
            <RatioInput
              label="Nhận biết"
              value={bloomRatios.REMEMBER}
              onChange={(v) => setBloomRatios((p) => ({ ...p, REMEMBER: v }))}
              colorClass={BLOOM_COLORS.REMEMBER}
            />
            <RatioInput
              label="Thông hiểu"
              value={bloomRatios.UNDERSTAND}
              onChange={(v) => setBloomRatios((p) => ({ ...p, UNDERSTAND: v }))}
              colorClass={BLOOM_COLORS.UNDERSTAND}
            />
            <RatioInput
              label="Vận dụng"
              value={bloomRatios.APPLY}
              onChange={(v) => setBloomRatios((p) => ({ ...p, APPLY: v }))}
              colorClass={BLOOM_COLORS.APPLY}
            />
          </div>

          {/* Type ratios */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-slate-700">
                Tỷ lệ loại câu hỏi
              </label>
              <SumBadge sum={typeSum} label="Tổng" />
            </div>
            <RatioInput
              label="1 đáp án"
              value={typeRatios.SINGLE_CHOICE}
              onChange={(v) =>
                setTypeRatios((p) => ({ ...p, SINGLE_CHOICE: v }))
              }
            />
            <RatioInput
              label="Nhiều đáp án"
              value={typeRatios.MULTIPLE_CHOICE}
              onChange={(v) =>
                setTypeRatios((p) => ({ ...p, MULTIPLE_CHOICE: v }))
              }
            />
            <RatioInput
              label="Đúng/Sai"
              value={typeRatios.TRUE_FALSE}
              onChange={(v) =>
                setTypeRatios((p) => ({ ...p, TRUE_FALSE: v }))
              }
            />
          </div>
        </div>

        {/* Preview + Generate buttons */}
        <div className="flex gap-3">
          <button
            onClick={handlePreview}
            disabled={!canSubmit || previewLoading}
            className="flex items-center gap-2 px-4 py-2 rounded-lg border border-purple-300 text-purple-700 text-sm font-medium hover:bg-purple-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
          >
            {previewLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Eye className="w-4 h-4" />
            )}
            Xem trước phân bổ
          </button>

          <button
            onClick={handleGenerate}
            disabled={!canSubmit || genLoading}
            className="flex items-center gap-2 px-5 py-2 rounded-lg bg-purple-600 text-white text-sm font-semibold hover:bg-purple-700 disabled:opacity-40 disabled:cursor-not-allowed transition shadow"
          >
            {genLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Zap className="w-4 h-4" />
            )}
            {genLoading ? "Đang sinh câu hỏi…" : "Sinh câu hỏi bằng AI"}
          </button>
        </div>

        {/* Error */}
        {genError && (
          <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            {genError}
          </div>
        )}

        {/* Preview table */}
        {preview && (
          <div className="bg-white border border-slate-200 rounded-xl shadow-sm p-5 space-y-3">
            <p className="font-semibold text-slate-700 text-sm flex items-center gap-2">
              <Eye className="w-4 h-4 text-purple-500" />
              Phân bổ ma trận — {preview.topic} ({preview.total_questions} câu)
            </p>
            {previewError && (
              <p className="text-xs text-red-500">{previewError}</p>
            )}
            <div className="overflow-x-auto">
              <table className="w-full text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-50">
                    <th className="border border-slate-200 px-3 py-2 text-left text-slate-600">
                      Nhận thức ↓ / Loại →
                    </th>
                    <th className="border border-slate-200 px-3 py-2 text-center text-slate-600">
                      1 đáp án
                    </th>
                    <th className="border border-slate-200 px-3 py-2 text-center text-slate-600">
                      Nhiều đáp án
                    </th>
                    <th className="border border-slate-200 px-3 py-2 text-center text-slate-600">
                      Đúng/Sai
                    </th>
                    <th className="border border-slate-200 px-3 py-2 text-center font-semibold text-slate-700">
                      Tổng
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {(["REMEMBER", "UNDERSTAND", "APPLY"] as const).map((level) => {
                    const rowAllocations = preview.allocations.filter(
                      (a) => a.cognitive_level === level,
                    );
                    const getCount = (type: string) =>
                      rowAllocations.find((a) => a.question_type === type)?.count ?? 0;
                    const rowTotal = rowAllocations.reduce(
                      (s, a) => s + a.count,
                      0,
                    );
                    return (
                      <tr key={level}>
                        <td className="border border-slate-200 px-3 py-2">
                          <span
                            className={`px-2 py-0.5 rounded-full text-xs font-medium ${BLOOM_COLORS[level]}`}
                          >
                            {BLOOM_LABELS[level]}
                          </span>
                        </td>
                        {["SINGLE_CHOICE", "MULTIPLE_CHOICE", "TRUE_FALSE"].map(
                          (type) => (
                            <td
                              key={type}
                              className="border border-slate-200 px-3 py-2 text-center text-slate-700"
                            >
                              {getCount(type)}
                            </td>
                          ),
                        )}
                        <td className="border border-slate-200 px-3 py-2 text-center font-semibold text-slate-800">
                          {rowTotal}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    );
  }

  // ==============================================================================
  // RENDER — STEP REVIEW
  // ==============================================================================
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-purple-50 text-purple-600 rounded-lg">
            <Sparkles className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-800">
              Duyệt câu hỏi AI
            </h1>
            <p className="text-sm text-slate-500">
              Chủ đề: <strong>{topic}</strong> — {questions.length} câu được sinh
            </p>
          </div>
        </div>
        <button
          onClick={() => {
            setStep("config");
            setSaveResult(null);
          }}
          className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700"
        >
          <RefreshCw className="w-4 h-4" />
          Cấu hình lại
        </button>
      </div>

      {/* Save banner */}
      {saveResult && (
        <div
          className={`flex items-center gap-2 px-4 py-3 rounded-lg text-sm border ${saveResult.failed === 0 ? "bg-green-50 border-green-200 text-green-700" : "bg-yellow-50 border-yellow-200 text-yellow-700"}`}
        >
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          Đã lưu {saveResult.saved} câu hỏi vào Ngân hàng.
          {saveResult.failed > 0 && ` ${saveResult.failed} câu thất bại.`}
        </div>
      )}

      {/* Save toolbar */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-sm p-4 flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2 flex-1">
          <label className="text-sm font-medium text-slate-700 whitespace-nowrap">
            Môn học:
          </label>
          <select
            value={selectedSubjectId}
            onChange={(e) => handleSubjectChange(e.target.value)}
            className="border border-slate-200 rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-purple-400 focus:outline-none"
          >
            {subjects.length === 0 && (
              <option value="">-- Không có môn học --</option>
            )}
            {subjects.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2 flex-1">
          <label className="text-sm font-medium text-slate-700 whitespace-nowrap">
            Danh mục:
          </label>
          <select
            value={selectedCategoryId}
            onChange={(e) => setSelectedCategoryId(e.target.value)}
            className="border border-slate-200 rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-purple-400 focus:outline-none"
          >
            {categories.length === 0 && (
              <option value="">-- Chọn môn học trước --</option>
            )}
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2 ml-auto">
          <button
            onClick={handleSelectAll}
            className="text-sm text-slate-500 hover:text-slate-700 underline"
          >
            {selectedIds.size === questions.length
              ? "Bỏ chọn tất cả"
              : "Chọn tất cả"}
          </button>
          <button
            onClick={handleSave}
            disabled={saveLoading || selectedIds.size === 0 || !selectedCategoryId}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white text-sm font-semibold rounded-lg hover:bg-purple-700 disabled:opacity-40 disabled:cursor-not-allowed transition shadow"
          >
            {saveLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Save className="w-4 h-4" />
            )}
            {saveLoading
              ? "Đang lưu…"
              : `Lưu ${selectedIds.size} câu vào Ngân hàng`}
          </button>
        </div>

        {saveError && (
          <p className="w-full text-xs text-red-500">{saveError}</p>
        )}
      </div>

      {/* Question list */}
      <div className="space-y-3">
        {questions.map((q) => (
          <QuestionCard
            key={q._localId}
            index={q._localId}
            question={q}
            selected={selectedIds.has(q._localId)}
            onToggleSelect={() => handleToggleSelect(q._localId)}
            onEdit={(field, value) =>
              handleEditQuestion(q._localId, field, value)
            }
          />
        ))}
      </div>
    </div>
  );
};

export default AiGenPage;
