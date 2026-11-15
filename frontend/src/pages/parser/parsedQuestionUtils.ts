import type { QuestionPayload } from "@/services/questionBankApi";
import type { ParsedQuestionItem } from "@/services/parserApi";
import type {
  CognitiveLevel,
  QuestionLevel,
  QuestionOption,
  QuestionType,
} from "@/types";

export interface EditableParsedQuestion extends ParsedQuestionItem {
  localId: string;
  selected: boolean;
  saveStatus?: "saved" | "error";
  saveError?: string;
}

let localSequence = 0;

export function nextLocalQuestionId(): string {
  localSequence += 1;
  return `parsed-q-${Date.now()}-${localSequence}`;
}

export const QUESTION_TYPE_LABELS: { value: QuestionType; label: string }[] = [
  { value: "SINGLE_CHOICE", label: "Một đáp án đúng" },
  { value: "MULTIPLE_CHOICE", label: "Nhiều đáp án đúng" },
  { value: "TRUE_FALSE", label: "Đúng / Sai" },
];

export const COGNITIVE_LEVEL_LABELS: { value: CognitiveLevel; label: string }[] = [
  { value: "REMEMBER", label: "Nhận biết" },
  { value: "UNDERSTAND", label: "Thông hiểu" },
  { value: "APPLY", label: "Vận dụng" },
];

export const QUESTION_LEVEL_LABELS: { value: QuestionLevel; label: string }[] = [
  { value: "EASY", label: "Dễ" },
  { value: "MEDIUM", label: "Trung bình" },
  { value: "HARD", label: "Khó" },
];

export function revalidateParsedQuestion(
  question: EditableParsedQuestion,
): EditableParsedQuestion {
  const normalizedOptions: QuestionOption[] = question.options.map((opt, idx) => ({
    ...opt,
    id: String.fromCharCode(65 + idx),
  }));

  const correctIds = normalizedOptions
    .filter((opt) => opt.is_correct)
    .map((opt) => opt.id);

  const warnings: string[] = [];

  if (!question.content.trim()) {
    warnings.push("Nội dung câu hỏi đang trống.");
  }

  if (normalizedOptions.length < 2) {
    warnings.push("Câu hỏi phải có ít nhất 2 phương án trả lời.");
  } else if (normalizedOptions.length > 10) {
    warnings.push("Câu hỏi tối đa 10 phương án trả lời.");
  }

  if (normalizedOptions.some((opt) => !opt.text.trim())) {
    warnings.push("Có phương án trả lời bị trống nội dung.");
  }

  if (question.question_type === "TRUE_FALSE" && normalizedOptions.length !== 2) {
    warnings.push("Câu hỏi Đúng/Sai phải có chính xác 2 phương án.");
  }

  if (question.question_type === "MULTIPLE_CHOICE") {
    if (correctIds.length < 1) {
      warnings.push("Chưa chọn đáp án đúng cho câu nhiều lựa chọn.");
    }
  } else {
    if (correctIds.length === 0) {
      warnings.push("Chưa xác định được đáp án đúng.");
    } else if (correctIds.length > 1) {
      warnings.push("Câu hỏi một đáp án chỉ được chọn duy nhất 1 đáp án đúng.");
    }
  }

  if (question.tags.length > 20 || question.tags.some((tag) => tag.length > 40)) {
    warnings.push("Tối đa 20 tag và mỗi tag không vượt quá 40 ký tự.");
  }

  return {
    ...question,
    options: normalizedOptions,
    correct_option_ids: correctIds,
    warnings,
    is_valid: warnings.length === 0,
  };
}

export function toEditableQuestions(
  items: ParsedQuestionItem[],
): EditableParsedQuestion[] {
  return items.map((item, idx) =>
    revalidateParsedQuestion({
      ...item,
      question_number: item.question_number ?? idx + 1,
      options: item.options.map((opt) => ({ ...opt })),
      correct_option_ids: [...item.correct_option_ids],
      tags: [...(item.tags ?? [])],
      warnings: [...(item.warnings ?? [])],
      localId: nextLocalQuestionId(),
      selected: item.is_valid,
    }),
  );
}

export function createEmptyParsedQuestion(
  questionNumber: number,
): EditableParsedQuestion {
  return revalidateParsedQuestion({
    question_number: questionNumber,
    content: "",
    question_type: "SINGLE_CHOICE",
    cognitive_level: "REMEMBER",
    level: "MEDIUM",
    options: [
      { id: "A", text: "", is_correct: true },
      { id: "B", text: "", is_correct: false },
      { id: "C", text: "", is_correct: false },
      { id: "D", text: "", is_correct: false },
    ],
    correct_option_ids: ["A"],
    explanation: null,
    tags: [],
    source_type: "FILE_PARSER",
    is_valid: false,
    warnings: [],
    localId: nextLocalQuestionId(),
    selected: true,
  });
}

export function toggleOptionCorrect(
  question: EditableParsedQuestion,
  optionIndex: number,
): EditableParsedQuestion {
  const nextOptions =
    question.question_type === "MULTIPLE_CHOICE"
      ? question.options.map((opt, idx) =>
          idx === optionIndex ? { ...opt, is_correct: !opt.is_correct } : opt,
        )
      : question.options.map((opt, idx) => ({
          ...opt,
          is_correct: idx === optionIndex,
        }));

  return revalidateParsedQuestion({
    ...question,
    options: nextOptions,
  });
}

export function changeQuestionType(
  question: EditableParsedQuestion,
  nextType: QuestionType,
): EditableParsedQuestion {
  let nextOptions: QuestionOption[] = question.options.map((opt) => ({ ...opt }));

  if (nextType === "TRUE_FALSE") {
    if (nextOptions.length === 2) {
      const firstCorrectIndex = nextOptions.findIndex((opt) => opt.is_correct);
      const chosenIndex = firstCorrectIndex >= 0 ? firstCorrectIndex : 0;
      nextOptions = nextOptions.map((opt, idx) => ({
        ...opt,
        id: String.fromCharCode(65 + idx),
        is_correct: idx === chosenIndex,
      }));
    } else {
      const firstIsCorrect = nextOptions[0]?.is_correct ?? true;
      nextOptions = [
        { id: "A", text: "Đúng", is_correct: firstIsCorrect },
        { id: "B", text: "Sai", is_correct: !firstIsCorrect },
      ];
    }
  } else if (nextType === "SINGLE_CHOICE") {
    const firstCorrectIndex = nextOptions.findIndex((opt) => opt.is_correct);
    if (firstCorrectIndex >= 0) {
      nextOptions = nextOptions.map((opt, idx) => ({
        ...opt,
        is_correct: idx === firstCorrectIndex,
      }));
    }
  }

  return revalidateParsedQuestion({
    ...question,
    question_type: nextType,
    options: nextOptions,
  });
}

export function addOptionToQuestion(
  question: EditableParsedQuestion,
): EditableParsedQuestion {
  if (question.options.length >= 10 || question.question_type === "TRUE_FALSE") {
    return question;
  }
  const nextId = String.fromCharCode(65 + question.options.length);
  return revalidateParsedQuestion({
    ...question,
    options: [...question.options, { id: nextId, text: "", is_correct: false }],
  });
}

export function removeOptionFromQuestion(
  question: EditableParsedQuestion,
  optionIndex: number,
): EditableParsedQuestion {
  if (question.options.length <= 2 || question.question_type === "TRUE_FALSE") {
    return question;
  }
  const nextOptions = question.options.filter((_, idx) => idx !== optionIndex);
  return revalidateParsedQuestion({
    ...question,
    options: nextOptions,
  });
}

export function parseTagsInput(raw: string): string[] {
  const seen = new Set<string>();
  const tags: string[] = [];
  for (const part of raw.split(",")) {
    const trimmed = part.trim();
    if (!trimmed) continue;
    const key = trimmed.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    tags.push(trimmed);
  }
  return tags;
}

export function toQuestionPayload(
  question: EditableParsedQuestion,
  categoryId: string,
): QuestionPayload {
  return {
    category_id: categoryId,
    content: question.content.trim(),
    question_type: question.question_type,
    cognitive_level: question.cognitive_level,
    level: question.level,
    options: question.options.map((opt, idx) => ({
      id: String.fromCharCode(65 + idx),
      text: opt.text.trim(),
      is_correct: opt.is_correct,
    })),
    tags: parseTagsInput((question.tags ?? []).join(", ")),
    explanation: question.explanation?.trim() || null,
    source_type: "FILE_PARSER",
  };
}
