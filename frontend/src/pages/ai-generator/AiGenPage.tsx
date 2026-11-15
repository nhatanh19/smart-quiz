import React, { useState, useCallback, useRef } from "react";
import axios from "axios";
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
  FileText,
  SlidersHorizontal,
  UploadCloud,
  FileUp,
  FileCheck,
} from "lucide-react";
import {
  previewMatrixAllocation,
  generateByMatrix,
  generateFromContext,
  type MatrixRequest,
  type MatrixPreviewData,
  type GeneratedQuestionItem,
} from "@/services/aiGeneratorApi";
import {
  uploadAndExtractDocument,
  extractUploadErrorMessage,
} from "@/services/parserApi";
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
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string" && detail.trim()) return detail;
    if (Array.isArray(detail)) {
      const messages = detail
        .map((item) => (typeof item === "object" && item && "msg" in item ? String(item.msg) : ""))
        .filter(Boolean);
      if (messages.length > 0) return messages.join(", ");
    }
    if (!error.response) {
      return "Không thể kết nối tới máy chủ. Vui lòng thử lại.";
    }
    return error.message || "Không thể xử lý yêu cầu. Vui lòng thử lại.";
  }
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
type TabType = "matrix" | "document";

interface LocalQuestion extends GeneratedQuestionItem {
  _localId: number;
}

export const AiGenPage: React.FC = () => {
  // ── Tab state ───────────────────────────────────────────────────────────────
  const [activeTab, setActiveTab] = useState<TabType>("matrix");

  // ── Shared Config state ─────────────────────────────────────────────────────
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

  // ── Document Tab state (Issue #33) ──────────────────────────────────────────
  const [rawText, setRawText] = useState("");
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [chunkSize, setChunkSize] = useState(1500);
  const [overlap, setOverlap] = useState(200);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [chunksInfo, setChunksInfo] = useState<{ used: number; total: number } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // ── Preview state (Matrix Tab) ──────────────────────────────────────────────
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
  const buildMatrixRequest = useCallback((): MatrixRequest => ({
    topic: topic.trim(),
    total_questions: totalQuestions,
    cognitive_ratios: bloomRatios,
    type_ratios: typeRatios,
  }), [topic, totalQuestions, bloomRatios, typeRatios]);

  const canSubmitMatrix =
    topic.trim().length >= 2 &&
    totalQuestions >= 1 &&
    bloomSum === 100 &&
    typeSum === 100;

  const canSubmitDocument =
    rawText.trim().length >= 20 &&
    totalQuestions >= 1 &&
    bloomSum === 100 &&
    typeSum === 100 &&
    overlap < chunkSize;

  // ── Handlers (Matrix) ───────────────────────────────────────────────────────
  const handlePreview = async () => {
    if (!canSubmitMatrix) return;
    setPreviewLoading(true);
    setPreviewError(null);
    try {
      const data = await previewMatrixAllocation(buildMatrixRequest());
      setPreview(data);
    } catch (err) {
      setPreviewError(extractError(err));
    } finally {
      setPreviewLoading(false);
    }
  };

  const initSubjectCategories = async () => {
    const subs = await listSubjects();
    setSubjects(subs);
    if (subs.length > 0) {
      setSelectedSubjectId(subs[0].id);
      const cats = await listCategories();
      const filtered = cats.filter((c) => c.subject_id === subs[0].id);
      setCategories(filtered);
      if (filtered.length > 0) setSelectedCategoryId(filtered[0].id);
    }
  };

  const handleGenerate = async () => {
    if (!canSubmitMatrix) return;
    setGenLoading(true);
    setGenError(null);
    setChunksInfo(null);
    try {
      const data = await generateByMatrix(buildMatrixRequest());
      const local: LocalQuestion[] = data.generated_questions.map((q, i) => ({
        ...q,
        _localId: i,
      }));
      setQuestions(local);
      setSelectedIds(new Set(local.map((q) => q._localId)));
      setSaveError(null);
      setStep("review");
      try {
        await initSubjectCategories();
      } catch (catErr) {
        setSaveError(extractError(catErr));
      }
    } catch (err) {
      setGenError(extractError(err));
    } finally {
      setGenLoading(false);
    }
  };

  // ── Handlers (Document Upload & Chunked Generate) ───────────────────────────
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadLoading(true);
    setUploadError(null);
    try {
      const result = await uploadAndExtractDocument(file);
      setRawText(result.raw_text);
      setUploadedFileName(result.filename);
      if (!topic.trim()) {
        const inferredTopic = result.filename.replace(/\.[^/.]+$/, "");
        setTopic(inferredTopic);
      }
    } catch (err) {
      setUploadError(extractUploadErrorMessage(err));
    } finally {
      setUploadLoading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleGenerateFromDoc = async () => {
    if (!canSubmitDocument) return;
    setGenLoading(true);
    setGenError(null);
    try {
      const data = await generateFromContext({
        raw_text: rawText.trim(),
        topic: topic.trim() || undefined,
        total_questions: totalQuestions,
        cognitive_ratios: bloomRatios,
        type_ratios: typeRatios,
        chunk_size: chunkSize,
        overlap: overlap,
      });

      setChunksInfo({
        used: data.chunks_used,
        total: data.total_chunks,
      });

      const local: LocalQuestion[] = data.generated_questions.map((q, i) => ({
        ...q,
        _localId: i,
      }));
      setQuestions(local);
      setSelectedIds(new Set(local.map((q) => q._localId)));
      setSaveError(null);
      setStep("review");
      try {
        await initSubjectCategories();
      } catch (catErr) {
        setSaveError(extractError(catErr));
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
    setSaveError(null);
    try {
      const cats = await listCategories();
      const filtered = cats.filter((c) => c.subject_id === subjectId);
      setCategories(filtered);
      if (filtered.length > 0) setSelectedCategoryId(filtered[0].id);
    } catch (err) {
      setSaveError(extractError(err));
    }
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
              AI Exam Generator & Matrix Builder
            </h1>
            <p className="text-sm text-slate-500">
              Sinh câu hỏi trắc nghiệm thông minh theo Ma trận Bloom hoặc bóc tách ngữ cảnh tài liệu
            </p>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-slate-200">
          <button
            onClick={() => setActiveTab("matrix")}
            className={`flex items-center gap-2 py-3 px-4 font-semibold text-sm border-b-2 transition ${
              activeTab === "matrix"
                ? "border-purple-600 text-purple-600"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            <SlidersHorizontal className="w-4 h-4" />
            Cấu hình Ma trận Bloom
          </button>
          <button
            onClick={() => setActiveTab("document")}
            className={`flex items-center gap-2 py-3 px-4 font-semibold text-sm border-b-2 transition ${
              activeTab === "document"
                ? "border-purple-600 text-purple-600"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            <FileText className="w-4 h-4" />
            Sinh từ Tài liệu & Giáo trình
          </button>
        </div>

        {/* ================= TAB 1: MA TRẬN BLOOM ================= */}
        {activeTab === "matrix" && (
          <div className="space-y-6">
            <div className="bg-white border border-slate-200 rounded-xl shadow-sm p-6 space-y-6">
              <div className="flex items-center gap-2 text-slate-700 font-semibold">
                <Settings2 className="w-4 h-4 text-purple-500" />
                Thông số ma trận đề thi
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
                {topic.trim().length === 1 && (
                  <p className="text-xs text-amber-600">Chủ đề cần tối thiểu 2 ký tự.</p>
                )}
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
                disabled={!canSubmitMatrix || previewLoading}
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
                disabled={!canSubmitMatrix || genLoading}
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
        )}

        {/* ================= TAB 2: SINH TỪ TÀI LIỆU (Issue #33) ================= */}
        {activeTab === "document" && (
          <div className="space-y-6">
            <div className="bg-white border border-slate-200 rounded-xl shadow-sm p-6 space-y-6">
              <div className="flex items-center gap-2 text-slate-700 font-semibold">
                <FileText className="w-4 h-4 text-purple-500" />
                Tài liệu & Ngữ cảnh bài giảng
              </div>

              {/* Upload Dropzone */}
              <div className="border-2 border-dashed border-slate-200 rounded-xl p-5 text-center bg-slate-50/50 hover:bg-slate-50 transition">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx,.txt"
                  onChange={handleFileChange}
                  className="hidden"
                  id="doc-upload-input"
                />
                <label
                  htmlFor="doc-upload-input"
                  className="cursor-pointer flex flex-col items-center gap-2"
                >
                  <div className="p-2.5 bg-purple-100 text-purple-600 rounded-full">
                    {uploadLoading ? (
                      <Loader2 className="w-6 h-6 animate-spin" />
                    ) : (
                      <UploadCloud className="w-6 h-6" />
                    )}
                  </div>
                  <div>
                    <span className="text-sm font-semibold text-purple-700 hover:underline">
                      Tải lên tệp tài liệu
                    </span>{" "}
                    <span className="text-sm text-slate-500">
                      hoặc dán trực tiếp nội dung bên dưới
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">
                    Hỗ trợ định dạng .PDF, .DOCX, .TXT (Tối đa 10MB)
                  </p>
                </label>

                {uploadedFileName && (
                  <div className="mt-3 inline-flex items-center gap-1.5 px-3 py-1 bg-green-50 border border-green-200 text-green-700 text-xs rounded-full">
                    <FileCheck className="w-3.5 h-3.5" />
                    Đã nạp: <strong>{uploadedFileName}</strong>
                  </div>
                )}
              </div>

              {uploadError && (
                <div className="flex items-center gap-2 text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg p-3">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  {uploadError}
                </div>
              )}

              {/* Raw Text Area */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="block text-sm font-medium text-slate-700">
                    Nội dung văn bản / Giáo trình <span className="text-red-500">*</span>
                  </label>
                  <span className="text-xs text-slate-400">
                    {rawText.length} ký tự — {rawText.trim() ? rawText.trim().split(/\s+/).length : 0} từ
                  </span>
                </div>
                <textarea
                  value={rawText}
                  onChange={(e) => setRawText(e.target.value)}
                  rows={6}
                  placeholder="Dán nội dung bài giảng, tóm tắt chương học, hoặc trích đoạn tài liệu cần sinh câu hỏi trắc nghiệm tại đây..."
                  className="w-full border border-slate-200 rounded-lg p-3 text-sm focus:outline-none focus:ring-2 focus:ring-purple-400 font-mono text-slate-800"
                />
              </div>

              {/* Topic override */}
              <div className="space-y-1.5">
                <label className="block text-sm font-medium text-slate-700">
                  Tên chủ đề / Chuyên đề (Tuỳ chọn)
                </label>
                <input
                  type="text"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="VD: Chương 4 - Tầng Giao vận và Giao thức TCP/UDP (mặc định lấy theo tài liệu)"
                  className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-400"
                />
              </div>

              {/* Total questions */}
              <div className="space-y-1.5">
                <label className="block text-sm font-medium text-slate-700">
                  Tổng số câu hỏi cần sinh <span className="text-red-500">*</span>
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

              {/* Advanced chunking toggle */}
              <div className="border-t border-slate-100 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAdvanced((p) => !p)}
                  className="flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900"
                >
                  <Settings2 className="w-3.5 h-3.5" />
                  {showAdvanced ? "Ẩn cấu hình phân đoạn (Chunking)" : "Tùy chỉnh thuật toán phân đoạn (Sliding Window)"}
                </button>

                {showAdvanced && (
                  <div className="mt-3 p-4 bg-slate-50 border border-slate-200 rounded-lg space-y-3 text-xs">
                    <p className="text-slate-600">
                      Hệ thống tự động chia văn bản thành các cửa sổ trượt (Sliding Window Chunking) để giữ mạch ngữ cảnh tự nhiên.
                    </p>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="font-medium text-slate-700 block mb-1">
                          Kích thước đoạn (Chunk size - ký tự):
                        </label>
                        <input
                          type="number"
                          min={300}
                          max={8000}
                          step={100}
                          value={chunkSize}
                          onChange={(e) => setChunkSize(Number(e.target.value))}
                          className="w-full border border-slate-200 rounded px-2.5 py-1.5 bg-white text-sm"
                        />
                      </div>
                      <div>
                        <label className="font-medium text-slate-700 block mb-1">
                          Độ gối đầu (Overlap - ký tự):
                        </label>
                        <input
                          type="number"
                          min={0}
                          max={chunkSize - 50}
                          step={50}
                          value={overlap}
                          onChange={(e) => setOverlap(Number(e.target.value))}
                          className="w-full border border-slate-200 rounded px-2.5 py-1.5 bg-white text-sm"
                        />
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Generate from document button */}
            <div className="flex gap-3">
              <button
                onClick={handleGenerateFromDoc}
                disabled={!canSubmitDocument || genLoading}
                className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-purple-600 text-white text-sm font-semibold hover:bg-purple-700 disabled:opacity-40 disabled:cursor-not-allowed transition shadow"
              >
                {genLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Zap className="w-4 h-4" />
                )}
                {genLoading ? "Đang phân đoạn và sinh câu hỏi…" : "Sinh câu hỏi từ tài liệu"}
              </button>
            </div>

            {/* Error */}
            {genError && (
              <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                {genError}
              </div>
            )}
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
            <div className="flex items-center gap-2 text-sm text-slate-500">
              <span>Chủ đề: <strong>{topic || "Tài liệu học tập"}</strong></span>
              <span>•</span>
              <span>{questions.length} câu đã sinh</span>
              {chunksInfo && (
                <>
                  <span>•</span>
                  <span className="text-purple-600 font-medium bg-purple-50 px-2 py-0.5 rounded-full text-xs">
                    {chunksInfo.used}/{chunksInfo.total} đoạn ngữ cảnh (Sliding Window)
                  </span>
                </>
              )}
            </div>
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
