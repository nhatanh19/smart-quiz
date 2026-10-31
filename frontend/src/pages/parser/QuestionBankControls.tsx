import React from "react";
import { BookOpen, Check, ChevronLeft, ChevronRight, Filter, Plus, Search, Tags } from "lucide-react";
import type {
  Category,
  CognitiveLevel,
  Question,
  QuestionLevel,
  Subject,
} from "@/types";

const LEVELS: { value: QuestionLevel; label: string }[] = [
  { value: "EASY", label: "Dễ" },
  { value: "MEDIUM", label: "Trung bình" },
  { value: "HARD", label: "Khó" },
];

const COGNITIVE_LEVELS: { value: CognitiveLevel; label: string }[] = [
  { value: "REMEMBER", label: "Nhận biết" },
  { value: "UNDERSTAND", label: "Thông hiểu" },
  { value: "APPLY", label: "Vận dụng" },
];

export interface QuestionBankFilterValues {
  keyword: string;
  subjectId: string;
  categoryId: string;
  level: string;
  cognitiveLevel: string;
  tag: string;
}

interface FilterToolbarProps {
  filters: QuestionBankFilterValues;
  subjects: Subject[];
  categories: Category[];
  onKeywordChange: (value: string) => void;
  onSubjectChange: (value: string) => void;
  onCategoryChange: (value: string) => void;
  onLevelChange: (value: QuestionLevel | "") => void;
  onCognitiveLevelChange: (value: CognitiveLevel | "") => void;
  onTagChange: (value: string) => void;
  onClear: () => void;
}

export const FilterToolbar: React.FC<FilterToolbarProps> = ({
  filters,
  subjects,
  categories,
  onKeywordChange,
  onSubjectChange,
  onCategoryChange,
  onLevelChange,
  onCognitiveLevelChange,
  onTagChange,
  onClear,
}) => {
  const visibleCategories = filters.subjectId
    ? categories.filter((category) => category.subject_id === filters.subjectId)
    : categories;

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:p-5">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <h2 className="font-semibold text-slate-900">Tìm câu hỏi</h2>
          <p className="mt-0.5 text-xs text-slate-500">
            Kết hợp từ khóa, môn học, chuyên đề, độ khó và mức độ Bloom.
          </p>
        </div>
        <button
          type="button"
          onClick={onClear}
          className="text-xs font-medium text-slate-500 hover:text-indigo-700"
        >
          Xóa bộ lọc
        </button>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-6">
        <label className="relative sm:col-span-2 xl:col-span-2">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            value={filters.keyword}
            onChange={(event) => onKeywordChange(event.target.value)}
            maxLength={200}
            placeholder="Tìm trong nội dung câu hỏi..."
            aria-label="Từ khóa trong nội dung câu hỏi"
            className="w-full rounded-lg border border-slate-200 bg-slate-50 py-2.5 pl-9 pr-3 text-sm outline-none focus:border-indigo-400 focus:bg-white focus:ring-2 focus:ring-indigo-100"
          />
        </label>
        <select
          aria-label="Lọc môn học"
          value={filters.subjectId}
          onChange={(event) => onSubjectChange(event.target.value)}
          className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
        >
          <option value="">Tất cả môn học</option>
          {subjects.map((subject) => (
            <option key={subject.id} value={subject.id}>{subject.name}</option>
          ))}
        </select>
        <select
          aria-label="Lọc chuyên đề"
          value={filters.categoryId}
          onChange={(event) => onCategoryChange(event.target.value)}
          className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
        >
          <option value="">Tất cả chuyên đề</option>
          {visibleCategories.map((category) => (
            <option key={category.id} value={category.id}>{category.name}</option>
          ))}
        </select>
        <select
          aria-label="Lọc độ khó"
          value={filters.level}
          onChange={(event) => onLevelChange(event.target.value as QuestionLevel | "")}
          className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
        >
          <option value="">Mọi độ khó</option>
          {LEVELS.map((item) => (
            <option key={item.value} value={item.value}>{item.label}</option>
          ))}
        </select>
        <select
          aria-label="Lọc mức độ Bloom"
          value={filters.cognitiveLevel}
          onChange={(event) => onCognitiveLevelChange(event.target.value as CognitiveLevel | "")}
          className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
        >
          <option value="">Mọi mức Bloom</option>
          {COGNITIVE_LEVELS.map((item) => (
            <option key={item.value} value={item.value}>{item.label}</option>
          ))}
        </select>
        <label className="relative sm:col-span-2 xl:col-span-1">
          <Tags className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            value={filters.tag}
            onChange={(event) => onTagChange(event.target.value)}
            placeholder="Lọc theo tag"
            aria-label="Lọc theo tag"
            className="w-full rounded-lg border border-slate-200 bg-slate-50 py-2.5 pl-9 pr-3 text-sm outline-none focus:border-indigo-400 focus:bg-white focus:ring-2 focus:ring-indigo-100"
          />
        </label>
      </div>
      <div className="mt-3 flex items-center gap-1.5 text-xs text-slate-400">
        <Filter className="h-3.5 w-3.5" />
        Độ khó độc lập với điểm số của câu hỏi trong đề thi.
      </div>
    </section>
  );
};

interface QuestionTableProps {
  questions: Question[];
  categories: Category[];
  subjects: Subject[];
  loading: boolean;
  page: number;
  hasMore: boolean;
  onPageChange: (page: number) => void;
  onCreate: () => void;
  onEdit: (question: Question) => void;
  onDelete: (question: Question) => void;
}

export const QuestionTable: React.FC<QuestionTableProps> = ({
  questions,
  categories,
  subjects,
  loading,
  page,
  hasMore,
  onPageChange,
  onCreate,
  onEdit,
  onDelete,
}) => {
  const categoryById = new Map(categories.map((category) => [category.id, category]));
  const subjectById = new Map(subjects.map((subject) => [subject.id, subject]));

  return (
    <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      {loading && questions.length === 0 ? (
        <div className="flex min-h-48 items-center justify-center text-sm text-slate-500">
          Đang tải ngân hàng câu hỏi...
        </div>
      ) : questions.length === 0 ? (
        <div className="px-6 py-14 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600">
            <BookOpen className="h-6 w-6" />
          </div>
          <h3 className="mt-4 font-semibold text-slate-900">Chưa tìm thấy câu hỏi</h3>
          <p className="mt-1 text-sm text-slate-500">
            Thử đổi bộ lọc hoặc tạo câu hỏi đầu tiên vào ngân hàng.
          </p>
          <button
            type="button"
            onClick={onCreate}
            className="mt-4 inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700"
          >
            <Plus className="h-4 w-4" /> Tạo câu hỏi
          </button>
        </div>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] border-collapse text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th scope="col" className="px-4 py-3 font-semibold">Câu hỏi</th>
                  <th scope="col" className="px-4 py-3 font-semibold">Môn / chuyên đề</th>
                  <th scope="col" className="px-4 py-3 font-semibold">Phân loại</th>
                  <th scope="col" className="px-4 py-3 text-right font-semibold">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {questions.map((question) => {
                  const category = categoryById.get(question.category_id);
                  const subject = category?.subject_id
                    ? subjectById.get(category.subject_id)
                    : undefined;
                  return (
                    <tr key={question.id} className="align-top hover:bg-slate-50/70">
                      <td className="max-w-xl px-4 py-4">
                        <p className="whitespace-pre-wrap break-words font-medium leading-6 text-slate-900">
                          {question.content}
                        </p>
                        <ul className="mt-2 grid gap-1 text-xs text-slate-600 sm:grid-cols-2">
                          {question.options.map((option) => (
                            <li
                              key={option.id}
                              className={`flex items-center gap-1.5 break-words ${
                                option.is_correct ? "font-medium text-emerald-700" : ""
                              }`}
                            >
                              <span>{option.id}.</span>
                              <span>{option.text}</span>
                              {option.is_correct && <Check className="h-3.5 w-3.5 shrink-0" />}
                            </li>
                          ))}
                        </ul>
                      </td>
                      <td className="px-4 py-4">
                        {subject && <p className="font-medium text-slate-700">{subject.name}</p>}
                        <p className="mt-1 text-slate-500">{category?.name ?? "Chưa phân loại"}</p>
                        {question.tags.length > 0 && (
                          <p className="mt-2 text-xs text-violet-700">{question.tags.join(", ")}</p>
                        )}
                      </td>
                      <td className="whitespace-nowrap px-4 py-4">
                        <p className="font-medium text-slate-700">{question.level}</p>
                        <p className="mt-1 text-xs text-slate-500">{question.cognitive_level}</p>
                        <p className="mt-1 text-xs text-slate-500">{question.question_type}</p>
                      </td>
                      <td className="whitespace-nowrap px-4 py-4 text-right">
                        <div className="flex justify-end gap-2">
                          <button
                            type="button"
                            onClick={() => onEdit(question)}
                            className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:border-indigo-200 hover:bg-indigo-50 hover:text-indigo-700"
                          >
                            Sửa
                          </button>
                          <button
                            type="button"
                            onClick={() => onDelete(question)}
                            className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-rose-600 hover:border-rose-200 hover:bg-rose-50"
                          >
                            Xóa
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="flex items-center justify-between border-t border-slate-100 px-4 py-3">
            <span className="text-xs text-slate-500">
              Trang {page + 1} · {questions.length} câu hỏi
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                disabled={page === 0 || loading}
                onClick={() => onPageChange(page - 1)}
                className="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-40"
              >
                <ChevronLeft className="h-4 w-4" /> Trước
              </button>
              <button
                type="button"
                disabled={!hasMore || loading}
                onClick={() => onPageChange(page + 1)}
                className="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-40"
              >
                Sau <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </>
      )}
    </section>
  );
};
