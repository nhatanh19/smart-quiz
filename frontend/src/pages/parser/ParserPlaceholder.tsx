import React, { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import axios from "axios";
import {
  AlertCircle,
  BookOpen,
  Check,
  LoaderCircle,
  Plus,
  Settings2,
  Trash2,
  X,
} from "lucide-react";
import type {
  Category,
  CognitiveLevel,
  Question,
  QuestionLevel,
  QuestionOption,
  QuestionType,
  Subject,
} from "@/types";
import {
  assignCategorySubject,
  createCategory as createCategoryRequest,
  createQuestion,
  createSubject as createSubjectRequest,
  deleteQuestion as deleteQuestionRequest,
  isRequestCancelled,
  listCategories,
  listQuestions,
  listSubjects,
  updateQuestion,
} from "@/services/questionBankApi";
import {
  FilterToolbar,
  QuestionTable,
} from "@/pages/parser/QuestionBankControls";

const QUESTION_TYPES: { value: QuestionType; label: string }[] = [
  { value: "SINGLE_CHOICE", label: "Một đáp án đúng" },
  { value: "MULTIPLE_CHOICE", label: "Nhiều đáp án đúng" },
  { value: "TRUE_FALSE", label: "Đúng / Sai" },
];

const COGNITIVE_LEVELS: { value: CognitiveLevel; label: string }[] = [
  { value: "REMEMBER", label: "Nhận biết" },
  { value: "UNDERSTAND", label: "Thông hiểu" },
  { value: "APPLY", label: "Vận dụng" },
];

const QUESTION_LEVELS: { value: QuestionLevel; label: string }[] = [
  { value: "EASY", label: "Dễ" },
  { value: "MEDIUM", label: "Trung bình" },
  { value: "HARD", label: "Khó" },
];

interface QuestionForm {
  category_id: string;
  content: string;
  question_type: QuestionType;
  cognitive_level: CognitiveLevel;
  level: QuestionLevel;
  options: QuestionOption[];
  tags: string;
  explanation: string;
}

const EMPTY_FORM: QuestionForm = {
  category_id: "",
  content: "",
  question_type: "SINGLE_CHOICE",
  cognitive_level: "REMEMBER",
  level: "MEDIUM",
  options: [
    { id: "A", text: "", is_correct: true },
    { id: "B", text: "", is_correct: false },
  ],
  tags: "",
  explanation: "",
};

function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((item) => item.msg)
        .filter(Boolean)
        .join(", ");
    }
    if (error.response?.status === 401) {
      return "Phiên đăng nhập không hợp lệ hoặc đã hết hạn. Hãy nhập JWT giảng viên/quản trị viên.";
    }
    if (error.response?.status === 403) {
      return "Tài khoản hiện tại không có quyền quản lý ngân hàng câu hỏi.";
    }
    return error.message || "Không thể kết nối tới API.";
  }
  return error instanceof Error ? error.message : "Đã xảy ra lỗi không xác định.";
}

function initialForm(question?: Question | null): QuestionForm {
  if (!question) return { ...EMPTY_FORM, options: EMPTY_FORM.options.map((option) => ({ ...option })) };
  return {
    category_id: question.category_id,
    content: question.content,
    question_type: question.question_type,
    cognitive_level: question.cognitive_level,
    level: question.level,
    options: question.options.map((option) => ({ ...option })),
    tags: (question.tags ?? []).join(", "),
    explanation: question.explanation ?? "",
  };
}

export const ParserPlaceholder: React.FC = () => {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [questionRevision, setQuestionRevision] = useState(0);
  const [subjectFilter, setSubjectFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [levelFilter, setLevelFilter] = useState<QuestionLevel | "">("");
  const [cognitiveLevelFilter, setCognitiveLevelFilter] = useState<CognitiveLevel | "">("");
  const [tagFilter, setTagFilter] = useState("");
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loadingQuestions, setLoadingQuestions] = useState(true);
  const [loadingTaxonomy, setLoadingTaxonomy] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [editor, setEditor] = useState<Question | null | undefined>(undefined);
  const [form, setForm] = useState<QuestionForm>(() => initialForm());
  const [taxonomyOpen, setTaxonomyOpen] = useState(false);
  const [subjectName, setSubjectName] = useState("");
  const [subjectDescription, setSubjectDescription] = useState("");
  const [topicName, setTopicName] = useState("");
  const [topicDescription, setTopicDescription] = useState("");
  const [topicSubjectId, setTopicSubjectId] = useState("");
  const [legacySubjectIds, setLegacySubjectIds] = useState<Record<string, string>>({});
  const [tokenDraft, setTokenDraft] = useState("");
  const [hasToken, setHasToken] = useState(false);

  const categoryById = useMemo(
    () => new Map(categories.map((category) => [category.id, category])),
    [categories],
  );
  const formCategories = useMemo(
    () => categories.filter((category) => (category.subject_id ?? "") === subjectFilter),
    [categories, subjectFilter],
  );
  const legacyCategories = useMemo(
    () => categories.filter((category) => !category.subject_id),
    [categories],
  );

  const loadClassifications = useCallback(async () => {
    const [subjectResponse, categoryResponse] = await Promise.all([
      listSubjects(),
      listCategories(),
    ]);
    const nextSubjects = subjectResponse;
    const nextCategories = categoryResponse;
    setSubjects(nextSubjects);
    setCategories(nextCategories);
    setTopicSubjectId((current) => current || nextSubjects[0]?.id || "");
    setLegacySubjectIds((current) => {
      const next = { ...current };
      nextCategories.forEach((category) => {
        if (!category.subject_id && !next[category.id]) {
          next[category.id] = nextSubjects[0]?.id ?? "";
        }
      });
      return next;
    });
  }, []);

  useEffect(() => {
    const token = localStorage.getItem("access_token") || localStorage.getItem("token");
    setHasToken(Boolean(token));
    if (!token) {
      setLoadingTaxonomy(false);
      return;
    }
    void loadClassifications()
      .catch((loadError: unknown) => setError(getErrorMessage(loadError)))
      .finally(() => setLoadingTaxonomy(false));
  }, [loadClassifications]);

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedSearch(search.trim()), 250);
    return () => window.clearTimeout(timer);
  }, [search]);

  useEffect(() => {
    const controller = new AbortController();
    if (!hasToken) {
      setQuestions([]);
      setHasMore(false);
      setLoadingQuestions(false);
      return () => controller.abort();
    }
    setLoadingQuestions(true);
    setError("");

    const params: {
      skip: number;
      limit: number;
      keyword?: string;
      subject_id?: string;
      category_id?: string;
      level?: QuestionLevel;
      cognitive_level?: CognitiveLevel;
      tag?: string;
    } = {
      skip: page * 50,
      limit: 50,
    };
    if (subjectFilter) params.subject_id = subjectFilter;
    if (categoryFilter) params.category_id = categoryFilter;
    if (levelFilter) params.level = levelFilter;
    if (cognitiveLevelFilter) params.cognitive_level = cognitiveLevelFilter;
    if (tagFilter.trim()) params.tag = tagFilter.trim();
    if (debouncedSearch) params.keyword = debouncedSearch;

    listQuestions(params, controller.signal)
      .then((response) => {
        const result = response.data ?? [];
        setQuestions(result);
        setHasMore(result.length === 50);
      })
      .catch((requestError: unknown) => {
        if (!isRequestCancelled(requestError)) setError(getErrorMessage(requestError));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoadingQuestions(false);
      });

    return () => controller.abort();
  }, [categoryFilter, cognitiveLevelFilter, debouncedSearch, hasToken, levelFilter, page, questionRevision, subjectFilter, tagFilter]);

  const resetPage = () => setPage(0);

  const openCreate = () => {
    setForm({
      ...initialForm(),
      category_id: formCategories[0]?.id ?? "",
    });
    setEditor(null);
    setError("");
  };

  const openEdit = (question: Question) => {
    const category = categoryById.get(question.category_id);
    setSubjectFilter(category?.subject_id ?? "");
    setForm(initialForm(question));
    setEditor(question);
    setError("");
  };

  const closeEditor = () => setEditor(undefined);

  const updateForm = <K extends keyof QuestionForm>(key: K, value: QuestionForm[K]) => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  const updateOption = (index: number, patch: Partial<QuestionOption>) => {
    setForm((current) => ({
      ...current,
      options: current.options.map((option, optionIndex) =>
        optionIndex === index ? { ...option, ...patch } : option,
      ),
    }));
  };

  const addOption = () => {
    setForm((current) => {
      if (current.options.length >= 10) return current;
      const id = String.fromCharCode(65 + current.options.length);
      return { ...current, options: [...current.options, { id, text: "", is_correct: false }] };
    });
  };

  const removeOption = (index: number) => {
    setForm((current) => ({
      ...current,
      options: current.options
        .filter((_, optionIndex) => optionIndex !== index)
        .map((option, optionIndex) => ({ ...option, id: String.fromCharCode(65 + optionIndex) })),
    }));
  };

  const saveQuestion = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!form.category_id) {
      setError("Hãy chọn chuyên đề. Nếu chưa có, thêm môn học và chuyên đề ở mục Phân loại.");
      return;
    }
    if (form.options.length < 2 || form.options.length > 10) {
      setError("Câu hỏi cần có từ 2 đến 10 phương án.");
      return;
    }
    const correctCount = form.options.filter((option) => option.is_correct).length;
    if (
      (form.question_type !== "MULTIPLE_CHOICE" && correctCount !== 1) ||
      (form.question_type === "MULTIPLE_CHOICE" && correctCount < 1)
    ) {
      setError(
        form.question_type === "MULTIPLE_CHOICE"
          ? "Hãy chọn ít nhất một đáp án đúng."
          : "Hãy chọn đúng một đáp án đúng.",
      );
      return;
    }
    if (form.question_type === "TRUE_FALSE" && form.options.length !== 2) {
      setError("Câu hỏi đúng/sai phải có chính xác hai phương án.");
      return;
    }
    const tags = form.tags
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean);
    if (tags.length > 20 || tags.some((tag) => tag.length > 40)) {
      setError("Tối đa 20 tag, mỗi tag không quá 40 ký tự.");
      return;
    }
    const payload = {
      category_id: form.category_id,
      content: form.content.trim(),
      question_type: form.question_type,
      cognitive_level: form.cognitive_level,
      level: form.level,
      options: form.options.map((option) => ({
        ...option,
        text: option.text.trim(),
      })),
      tags,
      explanation: form.explanation.trim() || null,
    };
    setSaving(true);
    setError("");
    try {
      if (editor) {
        await updateQuestion(editor.id, payload);
        setNotice("Đã cập nhật câu hỏi.");
      } else {
        await createQuestion(payload);
        setNotice("Đã thêm câu hỏi vào ngân hàng.");
      }
      closeEditor();
      setQuestionRevision((revision) => revision + 1);
      resetPage();
    } catch (saveError) {
      setError(getErrorMessage(saveError));
    } finally {
      setSaving(false);
    }
  };

  const deleteQuestion = async (question: Question) => {
    if (!window.confirm("Bạn có chắc muốn xóa câu hỏi này?")) return;
    setError("");
    try {
      await deleteQuestionRequest(question.id);
      setNotice("Đã xóa câu hỏi.");
      setQuestions((current) => current.filter((item) => item.id !== question.id));
      setQuestionRevision((revision) => revision + 1);
    } catch (deleteError) {
      setError(getErrorMessage(deleteError));
    }
  };

  const createSubject = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      const response = await createSubjectRequest({
        name: subjectName,
        description: subjectDescription.trim() || null,
      });
      await loadClassifications();
      setSubjectFilter(response.data?.id ?? "");
      setTopicSubjectId(response.data?.id ?? "");
      setSubjectName("");
      setSubjectDescription("");
      setNotice("Đã thêm môn học.");
      resetPage();
    } catch (createError) {
      setError(getErrorMessage(createError));
    } finally {
      setSaving(false);
    }
  };

  const createTopic = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!topicSubjectId) {
      setError("Hãy tạo hoặc chọn môn học trước.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      const response = await createCategoryRequest({
        name: topicName,
        description: topicDescription.trim() || null,
        subject_id: topicSubjectId,
      });
      await loadClassifications();
      setSubjectFilter(topicSubjectId);
      setCategoryFilter(response.data?.id ?? "");
      setTopicName("");
      setTopicDescription("");
      setNotice("Đã thêm chuyên đề.");
      resetPage();
    } catch (createError) {
      setError(getErrorMessage(createError));
    } finally {
      setSaving(false);
    }
  };

  const attachLegacyTopic = async (category: Category) => {
    const subjectId = legacySubjectIds[category.id];
    if (!subjectId) {
      setError("Hãy chọn môn học để gán chuyên đề cũ.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      await assignCategorySubject(category.id, subjectId);
      await loadClassifications();
      setNotice(`Đã gán chuyên đề "${category.name}" vào môn học.`);
      resetPage();
    } catch (attachError) {
      setError(getErrorMessage(attachError));
    } finally {
      setSaving(false);
    }
  };

  const saveToken = () => {
    const token = tokenDraft.trim().replace(/^Bearer\s+/i, "");
    if (!token) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("token");
      setHasToken(false);
      setTokenDraft("");
      setError("Đã xóa JWT đang lưu trong trình duyệt.");
      return;
    }
    localStorage.setItem("access_token", token);
    setHasToken(true);
    setTokenDraft("");
    setError("");
    setNotice("Đã lưu JWT trong localStorage của trình duyệt.");
    setLoadingTaxonomy(true);
    void loadClassifications()
      .catch((loadError: unknown) => setError(getErrorMessage(loadError)))
      .finally(() => setLoadingTaxonomy(false));
    resetPage();
  };

  const clearFilters = () => {
    setSearch("");
    setSubjectFilter("");
    setCategoryFilter("");
    setLevelFilter("");
    setCognitiveLevelFilter("");
    setTagFilter("");
    resetPage();
  };

  return (
    <div className="space-y-6">
      <section className="overflow-hidden rounded-2xl bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 p-6 text-white shadow-lg sm:p-8">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
          <div className="max-w-2xl">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-1 text-xs font-medium text-indigo-100">
              <BookOpen className="h-3.5 w-3.5" />
              THƯ VIỆN HỌC TẬP
            </div>
            <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
              Ngân hàng câu hỏi
            </h1>
            <p className="mt-2 max-w-xl text-sm leading-6 text-slate-300">
              Quản lý câu hỏi theo môn học, chuyên đề, tag và độ khó — tất cả trong một nơi.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => setTaxonomyOpen((open) => !open)}
              className="inline-flex items-center gap-2 rounded-lg border border-white/20 bg-white/10 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-white/15"
            >
              <Settings2 className="h-4 w-4" />
              Phân loại
            </button>
            <button
              type="button"
              onClick={openCreate}
              className="inline-flex items-center gap-2 rounded-lg bg-indigo-400 px-4 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-indigo-300"
            >
              <Plus className="h-4 w-4" />
              Thêm câu hỏi
            </button>
          </div>
        </div>
        <div className="mt-7 flex flex-wrap gap-3 text-xs text-slate-300">
          <span className="rounded-full bg-white/10 px-3 py-1.5">
            {questions.length}{hasMore ? "+" : ""} câu hỏi đang hiển thị
          </span>
          <span className="rounded-full bg-white/10 px-3 py-1.5">
            {subjects.length} môn học
          </span>
          <span className="rounded-full bg-white/10 px-3 py-1.5">
            {categories.filter((category) => category.subject_id).length} chuyên đề
          </span>
        </div>
      </section>

      {!hasToken && (
        <section className="rounded-xl border border-amber-200 bg-amber-50 p-4 sm:p-5">
          <div className="flex items-start gap-3">
            <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-amber-700" />
            <div className="min-w-0 flex-1">
              <h2 className="font-semibold text-amber-950">Cần JWT giảng viên hoặc quản trị viên</h2>
              <p className="mt-1 text-sm leading-6 text-amber-900">
                Backend bảo vệ các API ngân hàng câu hỏi. Dán access token để kết nối. Token được lưu
                trong localStorage của trình duyệt này.
              </p>
              <div className="mt-3 flex flex-col gap-2 sm:flex-row">
                <input
                  type="password"
                  value={tokenDraft}
                  onChange={(event) => setTokenDraft(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") saveToken();
                  }}
                  placeholder="JWT access token"
                  aria-label="JWT access token"
                  className="min-w-0 flex-1 rounded-lg border border-amber-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-200"
                />
                <button
                  type="button"
                  onClick={saveToken}
                  className="rounded-lg bg-amber-800 px-4 py-2 text-sm font-semibold text-white hover:bg-amber-900"
                >
                  Kết nối API
                </button>
              </div>
            </div>
          </div>
        </section>
      )}

      {hasToken && (
        <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
          <span className="inline-flex items-center gap-2">
            <Check className="h-4 w-4 text-emerald-600" />
            Đang gửi JWT khi gọi API
          </span>
          <button type="button" onClick={saveToken} className="text-xs font-medium text-slate-500 hover:text-red-700">
            Xóa JWT khỏi trình duyệt
          </button>
        </div>
      )}

      {error && (
        <div role="alert" className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          <span className="flex-1">{error}</span>
          <button type="button" onClick={() => setError("")} aria-label="Đóng thông báo lỗi">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}
      {notice && !error && (
        <div role="status" className="flex items-center justify-between gap-3 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          <span className="inline-flex items-center gap-2"><Check className="h-4 w-4" />{notice}</span>
          <button type="button" onClick={() => setNotice("")} aria-label="Đóng thông báo">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {taxonomyOpen && (
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
          <div className="mb-5 flex items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-indigo-600">Danh mục</p>
              <h2 className="mt-1 text-xl font-semibold text-slate-900">Môn học & chuyên đề</h2>
              <p className="mt-1 text-sm text-slate-500">Tạo môn học, tạo chuyên đề và gán dữ liệu cũ vào môn học.</p>
            </div>
            <button type="button" onClick={() => setTaxonomyOpen(false)} aria-label="Đóng phân loại" className="rounded-lg p-2 text-slate-500 hover:bg-slate-100">
              <X className="h-5 w-5" />
            </button>
          </div>
          <div className="grid gap-5 lg:grid-cols-2">
            <form onSubmit={createSubject} className="space-y-3 rounded-xl border border-slate-200 bg-slate-50 p-4">
              <h3 className="font-semibold text-slate-900">Thêm môn học</h3>
              <input required maxLength={255} value={subjectName} onChange={(event) => setSubjectName(event.target.value)} placeholder="Tên môn học" className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100" />
              <input maxLength={2000} value={subjectDescription} onChange={(event) => setSubjectDescription(event.target.value)} placeholder="Mô tả (không bắt buộc)" className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100" />
              <button disabled={saving} className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50">
                <Plus className="h-4 w-4" /> Tạo môn học
              </button>
            </form>

            <form onSubmit={createTopic} className="space-y-3 rounded-xl border border-slate-200 bg-slate-50 p-4">
              <h3 className="font-semibold text-slate-900">Thêm chuyên đề</h3>
              <select required value={topicSubjectId} onChange={(event) => setTopicSubjectId(event.target.value)} className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100">
                <option value="">Chọn môn học</option>
                {subjects.map((subject) => <option key={subject.id} value={subject.id}>{subject.name}</option>)}
              </select>
              <input required maxLength={255} value={topicName} onChange={(event) => setTopicName(event.target.value)} placeholder="Tên chuyên đề" className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100" />
              <input maxLength={2000} value={topicDescription} onChange={(event) => setTopicDescription(event.target.value)} placeholder="Mô tả (không bắt buộc)" className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100" />
              <button disabled={saving || !subjects.length} className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50">
                <Plus className="h-4 w-4" /> Tạo chuyên đề
              </button>
            </form>
          </div>
          {legacyCategories.length > 0 && (
            <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-4">
              <h3 className="font-semibold text-amber-950">Chuyên đề chưa gán môn học</h3>
              <p className="mt-1 text-sm text-amber-900">Các chuyên đề đã tồn tại được giữ nguyên; gán môn học để phân loại và lọc chúng.</p>
              <div className="mt-3 space-y-2">
                {legacyCategories.map((category) => (
                  <div key={category.id} className="flex flex-col gap-2 rounded-lg border border-amber-200 bg-white p-3 sm:flex-row sm:items-center">
                    <span className="min-w-0 flex-1 text-sm font-medium text-slate-800">{category.name}</span>
                    <select value={legacySubjectIds[category.id] ?? ""} onChange={(event) => setLegacySubjectIds((current) => ({ ...current, [category.id]: event.target.value }))} className="rounded-lg border border-slate-300 px-3 py-2 text-sm">
                      <option value="">Chọn môn học</option>
                      {subjects.map((subject) => <option key={subject.id} value={subject.id}>{subject.name}</option>)}
                    </select>
                    <button type="button" disabled={saving || !subjects.length} onClick={() => void attachLegacyTopic(category)} className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium hover:bg-slate-50 disabled:opacity-50">Gán</button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      )}

      <FilterToolbar
        filters={{
          keyword: search,
          subjectId: subjectFilter,
          categoryId: categoryFilter,
          level: levelFilter,
          cognitiveLevel: cognitiveLevelFilter,
          tag: tagFilter,
        }}
        subjects={subjects}
        categories={categories}
        onKeywordChange={(value) => {
          setSearch(value);
          resetPage();
        }}
        onSubjectChange={(value) => {
          setSubjectFilter(value);
          setCategoryFilter("");
          resetPage();
        }}
        onCategoryChange={(value) => {
          setCategoryFilter(value);
          resetPage();
        }}
        onLevelChange={(value) => {
          setLevelFilter(value);
          resetPage();
        }}
        onCognitiveLevelChange={(value) => {
          setCognitiveLevelFilter(value);
          resetPage();
        }}
        onTagChange={(value) => {
          setTagFilter(value);
          resetPage();
        }}
        onClear={clearFilters}
      />

      <QuestionTable
        questions={questions}
        categories={categories}
        subjects={subjects}
        loading={loadingQuestions}
        page={page}
        hasMore={hasMore}
        onPageChange={setPage}
        onCreate={openCreate}
        onEdit={openEdit}
        onDelete={(question) => void deleteQuestion(question)}
      />

      {editor !== undefined && (
        <div className="fixed inset-0 z-[60] flex items-start justify-center overflow-y-auto bg-slate-950/60 p-3 backdrop-blur-sm sm:p-6" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) closeEditor(); }}>
          <section role="dialog" aria-modal="true" aria-labelledby="question-editor-title" className="my-auto w-full max-w-3xl rounded-2xl bg-white shadow-2xl">
            <form onSubmit={saveQuestion}>
              <div className="flex items-start justify-between gap-4 border-b border-slate-100 p-5 sm:p-6">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-indigo-600">Ngân hàng câu hỏi</p>
                  <h2 id="question-editor-title" className="mt-1 text-xl font-semibold text-slate-900">{editor ? "Chỉnh sửa câu hỏi" : "Tạo câu hỏi mới"}</h2>
                </div>
                <button type="button" onClick={closeEditor} aria-label="Đóng form" className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"><X className="h-5 w-5" /></button>
              </div>

              <div className="max-h-[70vh] space-y-5 overflow-y-auto p-5 sm:p-6">
                <label className="block space-y-1.5">
                  <span className="text-sm font-medium text-slate-700">Nội dung câu hỏi <span className="text-rose-500">*</span></span>
                  <textarea required minLength={1} rows={3} maxLength={10000} value={form.content} onChange={(event) => updateForm("content", event.target.value)} placeholder="Nhập nội dung câu hỏi..." className="w-full resize-y rounded-lg border border-slate-300 px-3 py-2.5 text-sm leading-6 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100" />
                </label>

                <div className="grid gap-3 sm:grid-cols-2">
                  <label className="space-y-1.5">
                    <span className="text-sm font-medium text-slate-700">Môn học <span className="text-rose-500">*</span></span>
                    <select required value={subjectFilter} onChange={(event) => { const next = event.target.value; setSubjectFilter(next); setForm((current) => ({ ...current, category_id: categories.find((category) => category.subject_id === next)?.id ?? "" })); }} className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100">
                      <option value="">Chọn môn học</option>
                      {subjects.map((subject) => <option key={subject.id} value={subject.id}>{subject.name}</option>)}
                    </select>
                  </label>
                  <label className="space-y-1.5">
                    <span className="text-sm font-medium text-slate-700">Chuyên đề <span className="text-rose-500">*</span></span>
                    <select required value={form.category_id} onChange={(event) => updateForm("category_id", event.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100">
                      <option value="">Chọn chuyên đề</option>
                      {formCategories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}
                    </select>
                  </label>
                </div>
                {!subjects.length || !formCategories.length ? (
                  <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
                    Cần có môn học và chuyên đề trước khi lưu câu hỏi.{" "}
                    <button type="button" onClick={() => { closeEditor(); setTaxonomyOpen(true); }} className="font-semibold underline">Mở phần Phân loại</button>
                  </div>
                ) : null}

                <div className="grid gap-3 sm:grid-cols-3">
                  <label className="space-y-1.5">
                    <span className="text-sm font-medium text-slate-700">Dạng câu hỏi</span>
                    <select value={form.question_type} onChange={(event) => {
                      const nextType = event.target.value as QuestionType;
                      setForm((current) => ({
                        ...current,
                        question_type: nextType,
                        options: nextType === "TRUE_FALSE"
                          ? [
                              { id: "A", text: "Đúng", is_correct: current.options[0]?.is_correct ?? true },
                              { id: "B", text: "Sai", is_correct: !(current.options[0]?.is_correct ?? true) },
                            ]
                          : current.options.length < 2
                            ? EMPTY_FORM.options.map((option) => ({ ...option }))
                            : current.options,
                      }));
                    }} className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100">
                      {QUESTION_TYPES.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                    </select>
                  </label>
                  <label className="space-y-1.5">
                    <span className="text-sm font-medium text-slate-700">Mức độ Bloom</span>
                    <select value={form.cognitive_level} onChange={(event) => updateForm("cognitive_level", event.target.value as CognitiveLevel)} className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100">
                      {COGNITIVE_LEVELS.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                    </select>
                  </label>
                  <label className="space-y-1.5">
                    <span className="text-sm font-medium text-slate-700">Độ khó</span>
                    <select value={form.level} onChange={(event) => updateForm("level", event.target.value as QuestionLevel)} className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100">
                      {QUESTION_LEVELS.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                    </select>
                  </label>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <h3 className="text-sm font-medium text-slate-700">Phương án trả lời <span className="text-rose-500">*</span></h3>
                      <p className="mt-0.5 text-xs text-slate-500">{form.question_type === "MULTIPLE_CHOICE" ? "Đánh dấu tất cả đáp án đúng." : "Chọn duy nhất một đáp án đúng."}</p>
                    </div>
                    {form.question_type !== "TRUE_FALSE" && (
                      <button type="button" disabled={form.options.length >= 10} onClick={addOption} className="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-50"><Plus className="h-3.5 w-3.5" /> Thêm phương án</button>
                    )}
                  </div>
                  <div className="space-y-2">
                    {form.options.map((option, index) => (
                      <div key={option.id} className={`flex items-center gap-2 rounded-xl border p-2 ${option.is_correct ? "border-emerald-200 bg-emerald-50/50" : "border-slate-200"}`}>
                        <span className="w-7 shrink-0 text-center text-sm font-semibold text-slate-500">{option.id}</span>
                        <input required minLength={1} value={option.text} onChange={(event) => updateOption(index, { text: event.target.value })} placeholder={`Nội dung phương án ${option.id}`} className="min-w-0 flex-1 bg-transparent px-1 py-2 text-sm outline-none placeholder:text-slate-400" />
                        <label className="inline-flex shrink-0 cursor-pointer items-center gap-1.5 rounded-lg px-2 py-1.5 text-xs font-medium text-slate-600 hover:bg-white">
                          <input type={form.question_type === "MULTIPLE_CHOICE" ? "checkbox" : "radio"} name="correct-option" checked={option.is_correct} onChange={(event) => {
                            if (form.question_type === "MULTIPLE_CHOICE") {
                              updateOption(index, { is_correct: event.target.checked });
                            } else {
                              setForm((current) => ({ ...current, options: current.options.map((item, itemIndex) => ({ ...item, is_correct: itemIndex === index })) }));
                            }
                          }} className="accent-emerald-600" />
                          Đúng
                        </label>
                        {form.question_type !== "TRUE_FALSE" && form.options.length > 2 && (
                          <button type="button" onClick={() => removeOption(index)} aria-label={`Xóa phương án ${option.id}`} className="rounded-md p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600"><Trash2 className="h-4 w-4" /></button>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  <label className="space-y-1.5">
                    <span className="text-sm font-medium text-slate-700">Tag</span>
                    <input maxLength={500} value={form.tags} onChange={(event) => updateForm("tags", event.target.value)} placeholder="Ví dụ: chương-1, ôn-tập, trọng-tâm" className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100" />
                    <span className="block text-xs text-slate-400">Phân cách các tag bằng dấu phẩy.</span>
                  </label>
                  <label className="space-y-1.5">
                    <span className="text-sm font-medium text-slate-700">Giải thích</span>
                    <textarea rows={3} maxLength={5000} value={form.explanation} onChange={(event) => updateForm("explanation", event.target.value)} placeholder="Giải thích đáp án (không bắt buộc)" className="w-full resize-y rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100" />
                  </label>
                </div>
                {error && <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
              </div>

              <div className="flex flex-col-reverse justify-end gap-2 border-t border-slate-100 p-4 sm:flex-row sm:p-5">
                <button type="button" onClick={closeEditor} className="rounded-lg border border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-50">Hủy</button>
                <button type="submit" disabled={saving || loadingTaxonomy || !hasToken} className="inline-flex items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50">
                  {saving && <LoaderCircle className="h-4 w-4 animate-spin" />}
                  {editor ? "Lưu thay đổi" : "Tạo câu hỏi"}
                </button>
              </div>
            </form>
          </section>
        </div>
      )}
    </div>
  );
};

export default ParserPlaceholder;
