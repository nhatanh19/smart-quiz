import React, { useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  AlertTriangle,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Database,
  LoaderCircle,
  Plus,
  RotateCcw,
  Search,
  Trash2,
  X,
} from "lucide-react";
import {
  createQuestion,
  listCategories,
  listSubjects,
} from "@/services/questionBankApi";
import { extractUploadErrorMessage } from "@/services/parserApi";
import type {
  Category,
  CognitiveLevel,
  QuestionLevel,
  QuestionType,
  Subject,
} from "@/types";
import {
  addOptionToQuestion,
  changeQuestionType,
  COGNITIVE_LEVEL_LABELS,
  EditableParsedQuestion,
  parseTagsInput,
  QUESTION_LEVEL_LABELS,
  QUESTION_TYPE_LABELS,
  removeOptionFromQuestion,
  revalidateParsedQuestion,
  toggleOptionCorrect,
  toQuestionPayload,
} from "./parsedQuestionUtils";

type ValidityFilter = "all" | "valid" | "needs_review";

interface ParsedQuestionPreviewPanelProps {
  questions: EditableParsedQuestion[];
  documentWarnings: string[];
  unmatchedAnswerKeys: Record<number, string[]>;
  deletedCount: number;
  onUpdateQuestion: (
    localId: string,
    updater: (prev: EditableParsedQuestion) => EditableParsedQuestion,
  ) => void;
  onDeleteQuestion: (localId: string) => void;
  onUndoDelete: () => void;
  onAddQuestion: () => void;
  onToggleSelectAll: (checked: boolean) => void;
  onMarkQuestionsSaved: (
    savedIds: Set<string>,
    failedMap: Map<string, string>,
  ) => void;
  onQuestionsSaved?: () => void;
}

interface QuestionEditCardProps {
  question: EditableParsedQuestion;
  displayNumber: number;
  onUpdate: (
    updater: (prev: EditableParsedQuestion) => EditableParsedQuestion,
  ) => void;
  onDelete: () => void;
}

const QuestionEditCard: React.FC<QuestionEditCardProps> = ({
  question,
  displayNumber,
  onUpdate,
  onDelete,
}) => {
  const [showMetaDetails, setShowMetaDetails] = useState<boolean>(
    Boolean(question.explanation?.trim()) || (question.tags?.length ?? 0) > 0,
  );
  const [tagsDraft, setTagsDraft] = useState<string>(
    (question.tags ?? []).join(", "),
  );

  useEffect(() => {
    setTagsDraft((question.tags ?? []).join(", "));
  }, [question.localId]);

  const cardBorderClass =
    question.saveStatus === "saved"
      ? "border-emerald-300 bg-emerald-50/30"
      : question.is_valid
        ? "border-slate-200 bg-white"
        : "border-amber-300 bg-amber-50/30";

  return (
    <article
      data-testid={`parsed-question-card-${displayNumber}`}
      className={`rounded-2xl border p-4 sm:p-5 shadow-sm transition ${cardBorderClass}`}
    >
      {/* Card Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-3">
        <div className="flex flex-wrap items-center gap-2.5">
          <input
            type="checkbox"
            checked={question.selected}
            disabled={question.saveStatus === "saved"}
            onChange={(event) =>
              onUpdate((prev) => ({
                ...prev,
                selected: event.target.checked,
              }))
            }
            aria-label={`Chọn câu ${displayNumber}`}
            className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
          />

          <span className="inline-flex items-center rounded-lg bg-slate-900 px-2.5 py-1 font-mono text-xs font-semibold text-white">
            Câu {displayNumber}
          </span>

          {question.saveStatus === "saved" ? (
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-800">
              <CheckCircle2 className="h-3.5 w-3.5" />
              Đã lưu vào Ngân hàng
            </span>
          ) : question.is_valid ? (
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-800">
              <Check className="h-3.5 w-3.5" />
              Hợp lệ
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-semibold text-amber-900">
              <AlertTriangle className="h-3.5 w-3.5" />
              Cần kiểm tra
            </span>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <select
            aria-label={`Loại câu hỏi ${displayNumber}`}
            value={question.question_type}
            onChange={(event) =>
              onUpdate((prev) =>
                changeQuestionType(prev, event.target.value as QuestionType),
              )
            }
            className="rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs font-medium text-slate-700 outline-none focus:border-indigo-400 focus:bg-white"
          >
            {QUESTION_TYPE_LABELS.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>

          <select
            aria-label={`Mức độ Bloom câu ${displayNumber}`}
            value={question.cognitive_level}
            onChange={(event) =>
              onUpdate((prev) => ({
                ...prev,
                cognitive_level: event.target.value as CognitiveLevel,
              }))
            }
            className="rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs font-medium text-slate-700 outline-none focus:border-indigo-400 focus:bg-white"
          >
            {COGNITIVE_LEVEL_LABELS.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>

          <select
            aria-label={`Độ khó câu ${displayNumber}`}
            value={question.level}
            onChange={(event) =>
              onUpdate((prev) => ({
                ...prev,
                level: event.target.value as QuestionLevel,
              }))
            }
            className="rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs font-medium text-slate-700 outline-none focus:border-indigo-400 focus:bg-white"
          >
            {QUESTION_LEVEL_LABELS.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>

          <button
            type="button"
            onClick={onDelete}
            aria-label={`Xóa câu ${displayNumber}`}
            className="inline-flex items-center gap-1 rounded-lg border border-red-200 bg-white px-2.5 py-1.5 text-xs font-medium text-red-600 transition hover:bg-red-50"
          >
            <Trash2 className="h-3.5 w-3.5" />
            Xóa
          </button>
        </div>
      </div>

      {/* Inline Warnings / Save Error */}
      {!question.is_valid && question.warnings.length > 0 && (
        <div
          role="note"
          className="mt-3 flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900"
        >
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
          <span>{question.warnings.join(" • ")}</span>
        </div>
      )}

      {question.saveStatus === "error" && question.saveError && (
        <div
          role="alert"
          className="mt-3 flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-800"
        >
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-600" />
          <span>Lỗi khi lưu: {question.saveError}</span>
        </div>
      )}

      {/* Question Content */}
      <div className="mt-3">
        <label className="block space-y-1">
          <span className="text-xs font-medium text-slate-500">
            Nội dung câu hỏi
          </span>
          <textarea
            rows={2}
            value={question.content}
            onChange={(event) =>
              onUpdate((prev) =>
                revalidateParsedQuestion({
                  ...prev,
                  content: event.target.value,
                  saveStatus: undefined,
                  saveError: undefined,
                }),
              )
            }
            aria-label={`Nội dung câu ${displayNumber}`}
            placeholder="Nhập nội dung câu hỏi..."
            className="w-full resize-y rounded-xl border border-slate-200 bg-slate-50/60 px-3 py-2 text-sm text-slate-900 outline-none focus:border-indigo-400 focus:bg-white focus:ring-2 focus:ring-indigo-100"
          />
        </label>
      </div>

      {/* Options */}
      <div className="mt-3 space-y-2">
        <div className="flex items-center justify-between gap-2">
          <span className="text-xs font-medium text-slate-500">
            Phương án trả lời ({question.question_type === "MULTIPLE_CHOICE" ? "tick nhiều đáp án đúng" : "chọn 1 đáp án đúng"})
          </span>
          {question.question_type !== "TRUE_FALSE" && (
            <button
              type="button"
              disabled={question.options.length >= 10}
              onClick={() => onUpdate((prev) => addOptionToQuestion(prev))}
              className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
            >
              <Plus className="h-3.5 w-3.5" />
              Thêm phương án
            </button>
          )}
        </div>

        <div className="grid gap-2 sm:grid-cols-2">
          {question.options.map((option, optionIdx) => (
            <div
              key={`${question.localId}-${option.id}`}
              className={`flex items-center gap-2 rounded-xl border px-2.5 py-1.5 transition ${
                option.is_correct
                  ? "border-emerald-300 bg-emerald-50/70"
                  : "border-slate-200 bg-white"
              }`}
            >
              <input
                type={
                  question.question_type === "MULTIPLE_CHOICE"
                    ? "checkbox"
                    : "radio"
                }
                name={`correct-${question.localId}`}
                checked={option.is_correct}
                onChange={() =>
                  onUpdate((prev) => ({
                    ...toggleOptionCorrect(prev, optionIdx),
                    saveStatus: undefined,
                    saveError: undefined,
                  }))
                }
                aria-label={`Đánh dấu phương án ${option.id} là đáp án đúng cho câu ${displayNumber}`}
                className="h-4 w-4 shrink-0 accent-emerald-600 cursor-pointer"
              />

              <span
                className={`w-5 shrink-0 text-center font-mono text-xs font-bold ${
                  option.is_correct ? "text-emerald-800" : "text-slate-500"
                }`}
              >
                {option.id}
              </span>

              <input
                type="text"
                value={option.text}
                onChange={(event) => {
                  const nextText = event.target.value;
                  onUpdate((prev) =>
                    revalidateParsedQuestion({
                      ...prev,
                      options: prev.options.map((item, idx) =>
                        idx === optionIdx ? { ...item, text: nextText } : item,
                      ),
                      saveStatus: undefined,
                      saveError: undefined,
                    }),
                  );
                }}
                aria-label={`Phương án ${option.id} câu ${displayNumber}`}
                placeholder={`Nội dung phương án ${option.id}`}
                className="min-w-0 flex-1 bg-transparent py-1 text-sm text-slate-900 outline-none placeholder:text-slate-400"
              />

              {question.question_type !== "TRUE_FALSE" &&
                question.options.length > 2 && (
                  <button
                    type="button"
                    onClick={() =>
                      onUpdate((prev) =>
                        removeOptionFromQuestion(prev, optionIdx),
                      )
                    }
                    aria-label={`Xóa phương án ${option.id} câu ${displayNumber}`}
                    className="rounded-md p-1 text-slate-400 hover:bg-red-50 hover:text-red-600"
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                )}
            </div>
          ))}
        </div>
      </div>

      {/* Expandable Explanation & Tags */}
      <div className="mt-3 border-t border-slate-100 pt-2.5">
        <button
          type="button"
          onClick={() => setShowMetaDetails((prev) => !prev)}
          className="inline-flex items-center gap-1.5 text-xs font-medium text-indigo-600 hover:text-indigo-800"
        >
          {showMetaDetails ? (
            <ChevronUp className="h-3.5 w-3.5" />
          ) : (
            <ChevronDown className="h-3.5 w-3.5" />
          )}
          Giải thích & Tags
        </button>

        {showMetaDetails && (
          <div className="mt-2.5 grid gap-3 sm:grid-cols-2">
            <label className="block space-y-1">
              <span className="text-xs font-medium text-slate-500">
                Giải thích đáp án
              </span>
              <textarea
                rows={2}
                value={question.explanation ?? ""}
                onChange={(event) =>
                  onUpdate((prev) => ({
                    ...prev,
                    explanation: event.target.value,
                    saveStatus: undefined,
                    saveError: undefined,
                  }))
                }
                aria-label={`Giải thích câu ${displayNumber}`}
                placeholder="Nhập lời giải thích (không bắt buộc)..."
                className="w-full resize-y rounded-lg border border-slate-200 bg-slate-50/60 px-3 py-1.5 text-xs text-slate-800 outline-none focus:border-indigo-400 focus:bg-white"
              />
            </label>

            <label className="block space-y-1">
              <span className="text-xs font-medium text-slate-500">
                Tags (phân cách bằng dấu phẩy)
              </span>
              <input
                type="text"
                value={tagsDraft}
                onChange={(event) => {
                  const nextRaw = event.target.value;
                  setTagsDraft(nextRaw);
                  onUpdate((prev) =>
                    revalidateParsedQuestion({
                      ...prev,
                      tags: parseTagsInput(nextRaw),
                      saveStatus: undefined,
                      saveError: undefined,
                    }),
                  );
                }}
                aria-label={`Tags câu ${displayNumber}`}
                placeholder="chuong-1, on-tap"
                className="w-full rounded-lg border border-slate-200 bg-slate-50/60 px-3 py-2 text-xs text-slate-800 outline-none focus:border-indigo-400 focus:bg-white"
              />
            </label>
          </div>
        )}
      </div>
    </article>
  );
};

export const ParsedQuestionPreviewPanel: React.FC<
  ParsedQuestionPreviewPanelProps
> = ({
  questions,
  documentWarnings,
  unmatchedAnswerKeys,
  deletedCount,
  onUpdateQuestion,
  onDeleteQuestion,
  onUndoDelete,
  onAddQuestion,
  onToggleSelectAll,
  onMarkQuestionsSaved,
  onQuestionsSaved,
}) => {
  const [validityFilter, setValidityFilter] = useState<ValidityFilter>("all");
  const [keyword, setKeyword] = useState<string>("");

  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState<string>("");
  const [selectedCategoryId, setSelectedCategoryId] = useState<string>("");
  const [taxonomyError, setTaxonomyError] = useState<string | null>(null);
  const [loadingTaxonomy, setLoadingTaxonomy] = useState<boolean>(true);

  const [savingToBank, setSavingToBank] = useState<boolean>(false);
  const [saveProgress, setSaveProgress] = useState<{
    current: number;
    total: number;
  } | null>(null);
  const [saveFeedback, setSaveFeedback] = useState<{
    savedCount: number;
    failedCount: number;
  } | null>(null);

  useEffect(() => {
    let active = true;
    setLoadingTaxonomy(true);
    setTaxonomyError(null);

    Promise.all([listSubjects(), listCategories()])
      .then(([loadedSubjects, loadedCategories]) => {
        if (!active) return;
        setSubjects(loadedSubjects);
        setCategories(loadedCategories);

        const defaultSubjectId = loadedSubjects[0]?.id ?? "";
        setSelectedSubjectId(defaultSubjectId);
        const defaultCategory =
          loadedCategories.find((cat) => cat.subject_id === defaultSubjectId) ??
          loadedCategories[0];
        setSelectedCategoryId(defaultCategory?.id ?? "");
      })
      .catch((err: unknown) => {
        if (!active) return;
        setTaxonomyError(extractUploadErrorMessage(err));
      })
      .finally(() => {
        if (active) setLoadingTaxonomy(false);
      });

    return () => {
      active = false;
    };
  }, []);

  const visibleCategories = useMemo(() => {
    if (!selectedSubjectId) return categories;
    return categories.filter((cat) => cat.subject_id === selectedSubjectId);
  }, [categories, selectedSubjectId]);

  const stats = useMemo(() => {
    const valid = questions.filter((q) => q.is_valid).length;
    const needsReview = questions.length - valid;
    const withExplanation = questions.filter((q) =>
      Boolean(q.explanation?.trim()),
    ).length;
    const selectedValid = questions.filter(
      (q) => q.selected && q.is_valid && q.saveStatus !== "saved",
    ).length;
    const saved = questions.filter((q) => q.saveStatus === "saved").length;
    return {
      total: questions.length,
      valid,
      needsReview,
      withExplanation,
      selectedValid,
      saved,
    };
  }, [questions]);

  const filteredQuestions = useMemo(() => {
    const qLower = keyword.trim().toLowerCase();
    return questions
      .map((item, idx) => ({ item, displayNumber: idx + 1 }))
      .filter(({ item }) => {
        if (validityFilter === "valid" && !item.is_valid) return false;
        if (validityFilter === "needs_review" && item.is_valid) return false;
        if (!qLower) return true;
        return (
          item.content.toLowerCase().includes(qLower) ||
          (item.explanation ?? "").toLowerCase().includes(qLower) ||
          item.options.some((opt) => opt.text.toLowerCase().includes(qLower))
        );
      });
  }, [keyword, questions, validityFilter]);

  const allValidChecked =
    stats.valid > 0 &&
    questions
      .filter((q) => q.is_valid && q.saveStatus !== "saved")
      .every((q) => q.selected);

  const handleSubjectChange = (nextSubjectId: string) => {
    setSelectedSubjectId(nextSubjectId);
    const matching = nextSubjectId
      ? categories.filter((cat) => cat.subject_id === nextSubjectId)
      : categories;
    setSelectedCategoryId(matching[0]?.id ?? "");
  };

  const handleSaveSelectedToBank = async () => {
    if (!selectedCategoryId) return;
    const targets = questions.filter(
      (q) => q.selected && q.is_valid && q.saveStatus !== "saved",
    );
    if (targets.length === 0) return;

    setSavingToBank(true);
    setSaveFeedback(null);
    setSaveProgress({ current: 0, total: targets.length });

    const savedIds = new Set<string>();
    const failedMap = new Map<string, string>();

    for (let i = 0; i < targets.length; i += 1) {
      const target = targets[i];
      setSaveProgress({ current: i + 1, total: targets.length });
      try {
        await createQuestion(toQuestionPayload(target, selectedCategoryId));
        savedIds.add(target.localId);
      } catch (err: unknown) {
        failedMap.set(target.localId, extractUploadErrorMessage(err));
      }
    }

    onMarkQuestionsSaved(savedIds, failedMap);
    setSaveProgress(null);
    setSavingToBank(false);
    setSaveFeedback({
      savedCount: savedIds.size,
      failedCount: failedMap.size,
    });

    if (savedIds.size > 0) {
      onQuestionsSaved?.();
    }
  };

  const unmatchedEntries = Object.entries(unmatchedAnswerKeys ?? {});

  return (
    <div className="space-y-4">
      {/* Live Question KPIs */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-5 text-xs">
        <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
          <span className="text-slate-500">Tổng câu nhận diện</span>
          <p className="mt-1 text-lg font-bold text-slate-900 font-mono">
            {stats.total}
          </p>
        </div>
        <div className="rounded-xl border border-emerald-200 bg-emerald-50/60 p-3 shadow-sm">
          <span className="text-emerald-700">Hợp lệ</span>
          <p className="mt-1 text-lg font-bold text-emerald-900 font-mono">
            {stats.valid}
          </p>
        </div>
        <div className="rounded-xl border border-amber-200 bg-amber-50/70 p-3 shadow-sm">
          <span className="text-amber-800">Cần kiểm tra</span>
          <p className="mt-1 text-lg font-bold text-amber-950 font-mono">
            {stats.needsReview}
          </p>
        </div>
        <div className="rounded-xl border border-indigo-200 bg-indigo-50/50 p-3 shadow-sm">
          <span className="text-indigo-700">Có giải thích</span>
          <p className="mt-1 text-lg font-bold text-indigo-950 font-mono">
            {stats.withExplanation}
          </p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-sm col-span-2 sm:col-span-1">
          <span className="text-slate-500">Đã lưu ngân hàng</span>
          <p className="mt-1 text-lg font-bold text-emerald-700 font-mono">
            {stats.saved}
          </p>
        </div>
      </div>

      {/* Document Warnings / Unmatched Keys */}
      {(documentWarnings.length > 0 || unmatchedEntries.length > 0) && (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-xs text-amber-900 shadow-sm space-y-1">
          <div className="flex items-center gap-2 font-semibold text-amber-950">
            <AlertTriangle className="h-4 w-4 text-amber-600" />
            Lưu ý từ bộ bóc tách Regex
          </div>
          {documentWarnings.map((warn, idx) => (
            <p key={idx}>• {warn}</p>
          ))}
          {unmatchedEntries.length > 0 && (
            <p>
              • Có bảng đáp án cuối đề chưa ghép được tự động:{" "}
              {unmatchedEntries
                .map(([num, keys]) => `Câu ${num}: ${keys.join(", ")}`)
                .join("; ")}
              .
            </p>
          )}
        </div>
      )}

      {/* Save to Question Bank Bar */}
      <section className="rounded-2xl border border-indigo-200 bg-indigo-50/50 p-4 shadow-sm">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div className="grid flex-1 gap-3 sm:grid-cols-2">
            <label className="block space-y-1">
              <span className="text-xs font-semibold text-slate-700">
                Môn học đích
              </span>
              <select
                aria-label="Chọn môn học đích"
                value={selectedSubjectId}
                disabled={loadingTaxonomy || savingToBank}
                onChange={(event) => handleSubjectChange(event.target.value)}
                className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 disabled:opacity-60"
              >
                <option value="">Tất cả môn học</option>
                {subjects.map((sub) => (
                  <option key={sub.id} value={sub.id}>
                    {sub.name}
                  </option>
                ))}
              </select>
            </label>

            <label className="block space-y-1">
              <span className="text-xs font-semibold text-slate-700">
                Chuyên đề đích <span className="text-rose-500">*</span>
              </span>
              <select
                aria-label="Chọn chuyên đề đích"
                value={selectedCategoryId}
                disabled={loadingTaxonomy || savingToBank}
                onChange={(event) => setSelectedCategoryId(event.target.value)}
                className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 disabled:opacity-60"
              >
                <option value="">
                  {loadingTaxonomy
                    ? "Đang tải chuyên đề..."
                    : visibleCategories.length === 0
                      ? "Chưa có chuyên đề"
                      : "Chọn chuyên đề để lưu"}
                </option>
                {visibleCategories.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <button
            type="button"
            disabled={
              savingToBank || !selectedCategoryId || stats.selectedValid === 0
            }
            onClick={() => void handleSaveSelectedToBank()}
            className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {savingToBank ? (
              <>
                <LoaderCircle className="h-4 w-4 animate-spin" />
                <span>
                  Đang lưu{" "}
                  {saveProgress
                    ? `${saveProgress.current}/${saveProgress.total}`
                    : "..."}
                </span>
              </>
            ) : (
              <>
                <Database className="h-4 w-4" />
                <span>
                  Lưu {stats.selectedValid} câu vào Ngân hàng
                </span>
              </>
            )}
          </button>
        </div>

        {taxonomyError && (
          <p className="mt-2 text-xs text-red-700">
            Không thể tải danh sách Môn học / Chuyên đề: {taxonomyError}
          </p>
        )}

        {!loadingTaxonomy && !taxonomyError && categories.length === 0 && (
          <p className="mt-2 text-xs text-amber-800">
            Chưa có Chuyên đề nào trong Ngân hàng câu hỏi. Hãy chuyển sang tab{" "}
            <strong>Ngân hàng câu hỏi → Phân loại</strong> để tạo trước khi lưu.
          </p>
        )}

        {saveFeedback && (
          <div
            role="status"
            className={`mt-3 flex items-center gap-2 rounded-xl border px-3 py-2 text-xs font-medium ${
              saveFeedback.failedCount > 0
                ? "border-amber-200 bg-amber-50 text-amber-900"
                : "border-emerald-200 bg-emerald-50 text-emerald-900"
            }`}
          >
            <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
            <span>
              Đã lưu thành công {saveFeedback.savedCount} câu hỏi (nguồn{" "}
              <code className="font-mono">FILE_PARSER</code>) vào Ngân hàng.
              {saveFeedback.failedCount > 0 &&
                ` Có ${saveFeedback.failedCount} câu gặp lỗi cần kiểm tra lại.`}
            </span>
          </div>
        )}
      </section>

      {/* Filter & Bulk Controls */}
      <div className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          <label className="inline-flex cursor-pointer items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-700">
            <input
              type="checkbox"
              checked={allValidChecked}
              onChange={(event) => onToggleSelectAll(event.target.checked)}
              aria-label="Chọn tất cả câu hợp lệ"
              className="h-3.5 w-3.5 rounded accent-indigo-600"
            />
            Chọn tất cả hợp lệ
          </label>

          <button
            type="button"
            onClick={() => setValidityFilter("all")}
            className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
              validityFilter === "all"
                ? "bg-slate-900 text-white"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
          >
            Tất cả ({stats.total})
          </button>

          <button
            type="button"
            onClick={() => setValidityFilter("valid")}
            className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
              validityFilter === "valid"
                ? "bg-emerald-600 text-white"
                : "bg-emerald-50 text-emerald-800 hover:bg-emerald-100"
            }`}
          >
            Hợp lệ ({stats.valid})
          </button>

          <button
            type="button"
            onClick={() => setValidityFilter("needs_review")}
            className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
              validityFilter === "needs_review"
                ? "bg-amber-600 text-white"
                : "bg-amber-50 text-amber-800 hover:bg-amber-100"
            }`}
          >
            Cần kiểm tra ({stats.needsReview})
          </button>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="relative flex-1 sm:w-56 sm:flex-none">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
              aria-label="Tìm câu hỏi đã bóc tách"
              placeholder="Tìm trong danh sách..."
              className="w-full rounded-lg border border-slate-200 bg-slate-50 py-1.5 pl-8 pr-3 text-xs text-slate-800 outline-none focus:border-indigo-400 focus:bg-white"
            />
          </div>

          {deletedCount > 0 && (
            <button
              type="button"
              onClick={onUndoDelete}
              className="inline-flex items-center gap-1 rounded-lg border border-amber-300 bg-amber-50 px-3 py-1.5 text-xs font-semibold text-amber-900 hover:bg-amber-100"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              Hoàn tác xóa ({deletedCount})
            </button>
          )}

          <button
            type="button"
            onClick={onAddQuestion}
            className="inline-flex items-center gap-1 rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-1.5 text-xs font-semibold text-indigo-700 hover:bg-indigo-100"
          >
            <Plus className="h-3.5 w-3.5" />
            Thêm câu hỏi
          </button>
        </div>
      </div>

      {/* Question Cards List */}
      {filteredQuestions.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center">
          <p className="text-sm font-medium text-slate-700">
            {questions.length === 0
              ? "Không nhận diện được câu hỏi nào từ tài liệu này."
              : "Không có câu hỏi nào khớp với bộ lọc hiện tại."}
          </p>
          <p className="mt-1 text-xs text-slate-500">
            {questions.length === 0
              ? "Bạn có thể chuyển sang tab Văn bản thô để xem/sửa nội dung hoặc bấm Thêm câu hỏi thủ công."
              : "Thử đổi bộ lọc hoặc xóa từ khóa tìm kiếm."}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredQuestions.map(({ item, displayNumber }) => (
            <QuestionEditCard
              key={item.localId}
              question={item}
              displayNumber={displayNumber}
              onUpdate={(updater) => onUpdateQuestion(item.localId, updater)}
              onDelete={() => onDeleteQuestion(item.localId)}
            />
          ))}
        </div>
      )}
    </div>
  );
};
