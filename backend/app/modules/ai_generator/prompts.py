"""Bloom Taxonomy Prompt Templates and Matrix Allocation Planners (Issue #11 / WBS 3.2.1).

Provides structured prompt engineering templates for the 3 Bloom cognitive levels
(Remember/Knowledge, Understand/Comprehension, Apply/Application) and the 3 supported
question types (Single Choice, Multiple Choice, True/False), with strict anti-duplication
and high-discrimination distractor design rules.
"""

from dataclasses import dataclass
import math
from typing import Dict, List, Literal, Optional, Sequence, Tuple, TypeVar

from app.models.entities import CognitiveLevel, QuestionLevel, QuestionType

K = TypeVar("K")

COGNITIVE_ORDER: Tuple[CognitiveLevel, ...] = (
    CognitiveLevel.REMEMBER,
    CognitiveLevel.UNDERSTAND,
    CognitiveLevel.APPLY,
)

QUESTION_TYPE_ORDER: Tuple[QuestionType, ...] = (
    QuestionType.SINGLE_CHOICE,
    QuestionType.MULTIPLE_CHOICE,
    QuestionType.TRUE_FALSE,
)

COGNITIVE_TO_DEFAULT_LEVEL: Dict[CognitiveLevel, QuestionLevel] = {
    CognitiveLevel.REMEMBER: QuestionLevel.EASY,
    CognitiveLevel.UNDERSTAND: QuestionLevel.MEDIUM,
    CognitiveLevel.APPLY: QuestionLevel.HARD,
}


@dataclass(frozen=True)
class BloomTemplateSpec:
    """Prompt specification for a single Bloom cognitive level."""

    cognitive_level: CognitiveLevel
    label_vi: str
    label_en: str
    default_difficulty: QuestionLevel
    objective: str
    bloom_verbs: Tuple[str, ...]
    question_design_rules: str
    distractor_strategy: str
    example_snippet: str


@dataclass(frozen=True)
class QuestionTypeTemplateSpec:
    """Prompt specification for a single question format."""

    question_type: QuestionType
    label_vi: str
    label_en: str
    option_count_rule: str
    correct_answer_rule: str
    format_guidelines: str


BLOOM_PROMPT_TEMPLATES: Dict[CognitiveLevel, BloomTemplateSpec] = {
    CognitiveLevel.REMEMBER: BloomTemplateSpec(
        cognitive_level=CognitiveLevel.REMEMBER,
        label_vi="Nhận biết",
        label_en="Knowledge (Remember)",
        default_difficulty=QuestionLevel.EASY,
        objective=(
            "Kiểm tra khả năng ghi nhớ, nhận diện lại chính xác thuật ngữ, định nghĩa, "
            "thành phần cấu tạo, quy ước chuẩn hoặc sự kiện cốt lõi trong chủ đề."
        ),
        bloom_verbs=(
            "Nêu",
            "Xác định",
            "Liệt kê",
            "Nhận diện",
            "Định nghĩa",
            "Gọi tên",
            "Identify",
            "Define",
            "Recall",
        ),
        question_design_rules=(
            "- Đặt câu hỏi trực diện, ngắn gọn, rõ nghĩa, tập trung vào một khái niệm hoặc thuộc tính xác định.\n"
            "- Không hỏi mẹo câu chữ hay phủ định kép gây hiểu nhầm.\n"
            "- Thân câu hỏi phải chứa đủ ngữ cảnh để chuyên gia xác định được duy nhất đáp án đúng mà không cần đoán."
        ),
        distractor_strategy=(
            "- Các phương án nhiễu phải là thuật ngữ, tên gọi hoặc khái niệm có thật trong cùng học phần/chương "
            "nhưng sai về đối tượng hoặc phạm vi định nghĩa.\n"
            "- Tránh phương án nhiễu phi thực tế, ngây ngô hoặc lệch hẳn chủ đề."
        ),
        example_snippet=(
            'Ví dụ Nhận biết: "Trong quản lý dự án phần mềm theo PMBOK, cấu trúc phân rã công việc định hướng '
            'theo sản phẩm bàn giao được gọi là gì?" -> Đúng: "Work Breakdown Structure (WBS)"; '
            'Nhiễu: "Work Budget Schedule (WBS)", "Project Network Diagram", "Scope Baseline Matrix".'
        ),
    ),
    CognitiveLevel.UNDERSTAND: BloomTemplateSpec(
        cognitive_level=CognitiveLevel.UNDERSTAND,
        label_vi="Thông hiểu",
        label_en="Comprehension (Understand)",
        default_difficulty=QuestionLevel.MEDIUM,
        objective=(
            "Kiểm tra khả năng diễn giải bản chất, phân biệt các khái niệm dễ nhầm lẫn, "
            "hiểu quan hệ nguyên nhân–hệ quả, ý nghĩa hoặc mục đích sử dụng của một cơ chế."
        ),
        bloom_verbs=(
            "Giải thích",
            "Phân biệt",
            "So sánh",
            "Diễn giải",
            "Phân loại",
            "Suy ra ý nghĩa",
            "Explain",
            "Distinguish",
            "Compare",
        ),
        question_design_rules=(
            "- KHÔNG hỏi chép lại định nghĩa nguyên văn; hãy diễn đạt lại khái niệm theo ngữ cảnh mới hoặc yêu cầu so sánh/giải thích 'vì sao'.\n"
            "- Nhấn mạnh mối liên hệ bản chất, điều kiện đúng hoặc sự khác biệt cốt lõi giữa hai đối tượng gần nghĩa.\n"
            "- Độ khó mức trung bình: người học thuộc vẹt định nghĩa nhưng không hiểu bản chất sẽ dễ chọn nhầm."
        ),
        distractor_strategy=(
            "- Xây dựng phương án nhiễu từ các hiểu lầm phổ biến (common misconceptions): đảo ngược nguyên nhân–kết quả, "
            "đánh đồng hai khái niệm hay nhầm lẫn, đúng một phần nhưng sai ở điều kiện ràng buộc.\n"
            "- Các phương án phải tương đồng về độ dài, giọng văn học thuật và cấu trúc ngữ pháp."
        ),
        example_snippet=(
            'Ví dụ Thông hiểu: "Điểm khác biệt cốt lõi giữa kiểm thử hộp đen (Black-box) và kiểm thử hộp trắng (White-box) là gì?" '
            "-> Đúng: tập trung hành vi đầu vào/ra so với kiểm tra cấu trúc mã nguồn bên trong; "
            "Nhiễu: nhầm lẫn giữa kiểm thử tự động/thủ công, mức độ ưu tiên hoặc vai trò người thực hiện."
        ),
    ),
    CognitiveLevel.APPLY: BloomTemplateSpec(
        cognitive_level=CognitiveLevel.APPLY,
        label_vi="Vận dụng",
        label_en="Application (Apply)",
        default_difficulty=QuestionLevel.HARD,
        objective=(
            "Kiểm tra khả năng vận dụng kiến thức, nguyên lý, quy tắc hoặc công thức vào một "
            "tình huống thực tế mới, bài toán ngắn, kịch bản nghiệp vụ hoặc đoạn mã/dữ liệu cụ thể."
        ),
        bloom_verbs=(
            "Áp dụng",
            "Xử lý tình huống",
            "Lựa chọn giải pháp",
            "Dự đoán kết quả",
            "Tính toán",
            "Khắc phục sự cố",
            "Apply",
            "Solve",
            "Predict",
        ),
        question_design_rules=(
            "- BẮT BUỘC đặt câu hỏi trong một bối cảnh/tình huống cụ thể (mini-case, kịch bản kỹ thuật, dữ kiện số hoặc đoạn code ngắn).\n"
            "- Đòi hỏi thí sinh phải phân tích dữ kiện của tình huống rồi áp dụng đúng quy tắc/nguyên lý mới chọn được đáp án.\n"
            "- Không hỏi lý thuyết thuần túy không gắn tình huống."
        ),
        distractor_strategy=(
            "- Mỗi phương án nhiễu phải tương ứng với một lỗi sai thường gặp khi áp dụng thực tế: dùng sai công thức, "
            "bỏ qua ràng buộc của đề bài, chọn giải pháp phù hợp cho tình huống khác hoặc thiếu bước xử lý quan trọng.\n"
            "- Đảm bảo mọi phương án đều nghe có vẻ khả thi nếu thí sinh bỏ sót chi tiết quan trọng trong tình huống."
        ),
        example_snippet=(
            'Ví dụ Vận dụng: "Một API thanh toán thường xuyên nhận lỗi HTTP 429 khi lưu lượng tăng đột biến trong 5 giây. '
            'Giải pháp client-side nào phù hợp nhất để giảm nghẽn mà không làm sập máy chủ?" '
            "-> Đúng: Exponential Backoff kết hợp Jitter và giới hạn số lần retry; "
            "Nhiễu: Retry liên tục không nghỉ, tăng timeout lên 10 phút, hoặc cache lỗi 429 vĩnh viễn."
        ),
    ),
}

QUESTION_TYPE_TEMPLATES: Dict[QuestionType, QuestionTypeTemplateSpec] = {
    QuestionType.SINGLE_CHOICE: QuestionTypeTemplateSpec(
        question_type=QuestionType.SINGLE_CHOICE,
        label_vi="Chọn 1 đáp án",
        label_en="Single Choice",
        option_count_rule="Chính xác 4 phương án lựa chọn có id lần lượt là 'A', 'B', 'C', 'D'.",
        correct_answer_rule="DUY NHẤT 1 phương án có is_correct=true và 3 phương án nhiễu có is_correct=false.",
        format_guidelines=(
            "- Bốn phương án phải độc lập, loại trừ lẫn nhau và cùng cấp độ chi tiết.\n"
            "- Không viết nhãn 'A.', 'B.' lặp lại bên trong trường 'text' (chỉ đưa nội dung phương án vào 'text').\n"
            "- Độ dài của đáp án đúng và các đáp án nhiễu phải tương đương nhau (không làm đáp án đúng dài vượt trội)."
        ),
    ),
    QuestionType.MULTIPLE_CHOICE: QuestionTypeTemplateSpec(
        question_type=QuestionType.MULTIPLE_CHOICE,
        label_vi="Chọn nhiều đáp án",
        label_en="Multiple Choice",
        option_count_rule="Từ 4 đến 5 phương án lựa chọn (khuyến nghị 4 phương án 'A', 'B', 'C', 'D' hoặc thêm 'E').",
        correct_answer_rule=(
            "BẮT BUỘC có TỐI THIỂU 2 phương án có is_correct=true và TỐI THIỂU 1 phương án có is_correct=false "
            "(tức từ 2 đến N-1 đáp án đúng; KHÔNG được chỉ có 1 đáp án đúng và KHÔNG được đúng tất cả)."
        ),
        format_guidelines=(
            "- Trong thân câu hỏi nên gợi ý rõ ràng đây là câu nhiều lựa chọn (ví dụ: '(Chọn nhiều đáp án đúng)' "
            "hoặc 'Những phát biểu nào sau đây đúng?').\n"
            "- Mỗi phương án phải là một mệnh đề độc lập để thí sinh phải đánh giá từng ý.\n"
            "- Các phương án sai phải tinh tế (ví dụ: đúng một nửa, sai điều kiện biên), không đặt phương án vô nghĩa."
        ),
    ),
    QuestionType.TRUE_FALSE: QuestionTypeTemplateSpec(
        question_type=QuestionType.TRUE_FALSE,
        label_vi="Đúng / Sai",
        label_en="True / False",
        option_count_rule="CHÍNH XÁC 2 phương án lựa chọn với id 'A' và 'B'.",
        correct_answer_rule="DUY NHẤT 1 phương án có is_correct=true và 1 phương án có is_correct=false.",
        format_guidelines=(
            "- Thân câu hỏi phải là MỘT mệnh đề/nhận định rõ ràng có giá trị chân lý dứt khoát (hoàn toàn đúng hoặc sai).\n"
            "- Không ghép hai vế mà một vế đúng, một vế sai gây nhập nhằng.\n"
            "- Với tiếng Việt: option A có text='Đúng', option B có text='Sai'. Với tiếng Anh: option A='True', option B='False'.\n"
            "- Nếu sinh từ 2 câu Đúng/Sai trở lên, hãy cân bằng cả câu có đáp án Đúng và câu có đáp án Sai."
        ),
    ),
}

DISTRACTOR_QUALITY_RULES = """QUY TẮC CHẤT LƯỢNG PHƯƠNG ÁN NHIỄU & CHỐNG TRÙNG LẶP (BẮT BUỘC):
1. KHÔNG TRÙNG LẶP NỘI DUNG: Các phương án trong cùng một câu hỏi phải hoàn toàn khác nhau cả về câu chữ lẫn ý nghĩa; không lặp lại cùng một ý dưới cách diễn đạt khác.
2. KHÔNG TRÙNG LẶP CÂU HỎI: Mọi câu hỏi trong danh sách phải kiểm tra các khía cạnh/tình huống riêng biệt, không trùng lặp câu hỏi trước đó.
3. CẤM PHƯƠNG ÁN SÁO RỖNG: Tuyệt đối KHÔNG tạo phương án kiểu "Tất cả các đáp án trên", "Tất cả đều đúng", "Tất cả đều sai", "Không có đáp án nào đúng", "Cả A và B", "Chỉ A và C".
4. TÍNH PHÂN LOẠI CAO: Mọi phương án nhiễu phải hợp lý về mặt ngữ cảnh đối với người chưa nắm vững kiến thức, dựa trên nhầm lẫn thực tế; không tạo nhiễu ngớ ngẩn, hài hước hay sai hiển nhiên về chính tả/ngữ pháp.
5. KHÔNG LỘ MANH MỐI: Không lặp từ khóa của đề bài chỉ vào riêng đáp án đúng; tránh dùng từ tuyệt đối ("luôn luôn", "không bao giờ", "tất cả") chỉ xuất hiện trong phương án sai.
6. GIẢI THÍCH SƯ PHẠM: Trường 'explanation' phải giải thích ngắn gọn vì sao đáp án đúng chính xác và chỉ ra lỗi sai của phương án nhiễu dễ nhầm nhất."""


def allocate_counts_by_weights(
    total: int,
    weights: Dict[K, float],
    ordered_keys: Sequence[K],
) -> Dict[K, int]:
    """Convert non-negative weights or percentages into exact integers summing to `total`.

    Uses the Largest Remainder (Hamilton) method so totals are always exact and
    zero-weight entries always receive zero questions.
    """
    if total < 1:
        raise ValueError("Tổng số câu hỏi (total) phải lớn hơn hoặc bằng 1")

    sanitized: Dict[K, float] = {}
    for key in ordered_keys:
        value = float(weights.get(key, 0.0) or 0.0)
        if value < 0:
            raise ValueError(f"Trọng số cho {key} không được là số âm")
        sanitized[key] = value

    weight_sum = sum(sanitized.values())
    if weight_sum <= 0:
        raise ValueError("Phải có ít nhất một trọng số lớn hơn 0")

    raw_shares = {key: (sanitized[key] / weight_sum) * total for key in ordered_keys}
    allocated = {key: math.floor(raw_shares[key]) for key in ordered_keys}
    remainder = total - sum(allocated.values())

    ranked_keys = sorted(
        [key for key in ordered_keys if sanitized[key] > 0],
        key=lambda key: (
            raw_shares[key] - allocated[key],
            sanitized[key],
            -ordered_keys.index(key),
        ),
        reverse=True,
    )

    idx = 0
    while remainder > 0 and ranked_keys:
        allocated[ranked_keys[idx % len(ranked_keys)]] += 1
        remainder -= 1
        idx += 1

    return allocated


def plan_matrix_cells(
    cognitive_counts: Dict[CognitiveLevel, int],
    type_counts: Dict[QuestionType, int],
) -> List[Tuple[CognitiveLevel, QuestionType, int]]:
    """Allocate a 2D (cognitive_level x question_type) matrix matching exact marginals.

    Guarantees that for every row `c`: sum of cell counts == `cognitive_counts[c]`,
    and for every column `t`: sum of cell counts == `type_counts[t]`.
    """
    row_targets = {c: int(cognitive_counts.get(c, 0)) for c in COGNITIVE_ORDER}
    col_targets = {t: int(type_counts.get(t, 0)) for t in QUESTION_TYPE_ORDER}

    if any(v < 0 for v in row_targets.values()) or any(v < 0 for v in col_targets.values()):
        raise ValueError("Số lượng câu hỏi trong phân bổ không được âm")

    total_rows = sum(row_targets.values())
    total_cols = sum(col_targets.values())
    if total_rows <= 0:
        raise ValueError("Tổng số câu hỏi phải lớn hơn 0")
    if total_rows != total_cols:
        raise ValueError(
            f"Tổng mức Bloom ({total_rows}) phải bằng tổng thể loại câu hỏi ({total_cols})"
        )

    ideal: Dict[Tuple[CognitiveLevel, QuestionType], float] = {}
    matrix: Dict[Tuple[CognitiveLevel, QuestionType], int] = {}
    for c in COGNITIVE_ORDER:
        for t in QUESTION_TYPE_ORDER:
            exact = (row_targets[c] * col_targets[t]) / total_rows
            ideal[(c, t)] = exact
            matrix[(c, t)] = math.floor(exact)

    rem_rows = {
        c: row_targets[c] - sum(matrix[(c, t)] for t in QUESTION_TYPE_ORDER)
        for c in COGNITIVE_ORDER
    }
    rem_cols = {
        t: col_targets[t] - sum(matrix[(c, t)] for c in COGNITIVE_ORDER)
        for t in QUESTION_TYPE_ORDER
    }

    # First pass: distribute remainders by highest fractional excess where both row & col have capacity
    candidates = sorted(
        [(c, t) for c in COGNITIVE_ORDER for t in QUESTION_TYPE_ORDER],
        key=lambda pair: (
            ideal[pair] - matrix[pair],
            row_targets[pair[0]] * col_targets[pair[1]],
        ),
        reverse=True,
    )
    for c, t in candidates:
        if rem_rows[c] > 0 and rem_cols[t] > 0:
            matrix[(c, t)] += 1
            rem_rows[c] -= 1
            rem_cols[t] -= 1

    # Second pass: assign any remaining capacity deterministically
    for c in COGNITIVE_ORDER:
        for t in QUESTION_TYPE_ORDER:
            while rem_rows[c] > 0 and rem_cols[t] > 0:
                matrix[(c, t)] += 1
                rem_rows[c] -= 1
                rem_cols[t] -= 1

    return [
        (c, t, matrix[(c, t)])
        for c in COGNITIVE_ORDER
        for t in QUESTION_TYPE_ORDER
        if matrix[(c, t)] > 0
    ]


def build_cell_prompts(
    topic: str,
    cognitive_level: CognitiveLevel,
    question_type: QuestionType,
    count: int,
    *,
    subject_name: Optional[str] = None,
    language: Literal["vi", "en"] = "vi",
    additional_instructions: Optional[str] = None,
    existing_question_contents: Optional[Sequence[str]] = None,
    repair_feedback: Optional[str] = None,
) -> Tuple[str, str]:
    """Build tailored (system_prompt, user_prompt) for one Bloom level + question type cell."""
    if count < 1:
        raise ValueError("Số lượng câu hỏi (count) phải lớn hơn hoặc bằng 1")

    bloom = BLOOM_PROMPT_TEMPLATES[cognitive_level]
    qtype = QUESTION_TYPE_TEMPLATES[question_type]

    language_label = (
        "Tiếng Việt chuẩn xác, tự nhiên, đúng thuật ngữ chuyên ngành"
        if language == "vi"
        else "Clear, natural academic English"
    )
    true_false_labels = (
        'A: "Đúng", B: "Sai"' if language == "vi" else 'A: "True", B: "False"'
    )

    system_prompt = f"""Bạn là Chuyên gia Khảo thí & Thiết kế Ngân hàng Câu hỏi Trắc nghiệm cho nền tảng Smart Quiz.
Nhiệm vụ của bạn là soạn thảo bộ câu hỏi trắc nghiệm chuẩn sư phạm tuân thủ tuyệt đối cấp độ nhận thức Bloom và thể loại câu hỏi được chỉ định.

======================================================================
1. ĐẶC TẢ MỨC ĐỘ NHẬN THỨC BLOOM: {bloom.label_vi.upper()} ({bloom.cognitive_level.value} / {bloom.label_en})
- Mục tiêu đánh giá: {bloom.objective}
- Động từ Bloom gợi ý: {", ".join(bloom.bloom_verbs)}
- Mức độ khó ánh xạ: {bloom.default_difficulty.value}
- Hướng dẫn viết thân câu hỏi:
{bloom.question_design_rules}
- Chiến lược tạo phương án nhiễu cho mức {bloom.label_vi}:
{bloom.distractor_strategy}
- Tham khảo chất lượng:
  {bloom.example_snippet}

======================================================================
2. ĐẶC TẢ THỂ LOẠI CÂU HỎI: {qtype.label_vi.upper()} ({qtype.question_type.value} / {qtype.label_en})
- Quy tắc số phương án: {qtype.option_count_rule}
- Quy tắc đáp án đúng: {qtype.correct_answer_rule}
- Hướng dẫn trình bày:
{qtype.format_guidelines}
{"- Nhãn phương án Đúng/Sai cho ngôn ngữ hiện tại: " + true_false_labels if question_type == QuestionType.TRUE_FALSE else ""}

======================================================================
3. {DISTRACTOR_QUALITY_RULES}
"""

    subject_line = f"- Môn học / Học phần: {subject_name.strip()}\n" if subject_name else ""
    extra_block = (
        f"\n[YÊU CẦU BỔ SUNG TỪ GIẢNG VIÊN]:\n{additional_instructions.strip()}\n"
        if additional_instructions and additional_instructions.strip()
        else ""
    )

    dedup_block = ""
    if existing_question_contents:
        preview_items = "\n".join(
            f"  {idx + 1}. {item.strip()[:160]}"
            for idx, item in enumerate(existing_question_contents)
            if item and item.strip()
        )
        if preview_items:
            dedup_block = (
                "\n[CÁC CÂU HỎI ĐÃ SINH TRƯỚC ĐÓ — TUYỆT ĐỐI KHÔNG TRÙNG Ý HOẶC LẶP LẠI]:\n"
                f"{preview_items}\n"
            )

    repair_block = (
        f"\n[LƯU Ý SỬA LỖI TỪ LẦN KIỂM TRA TRƯỚC]:\n{repair_feedback.strip()}\n"
        if repair_feedback and repair_feedback.strip()
        else ""
    )

    user_prompt = f"""Hãy sinh CHÍNH XÁC {count} câu hỏi trắc nghiệm mới theo thông số sau:
{subject_line}- Chủ đề / Chuyên đề: {topic.strip()}
- Số lượng câu hỏi BẮT BUỘC trong mảng "questions": ĐÚNG {count} câu (không thiếu, không thừa).
- Mức độ Bloom BẮT BUỘC cho TẤT CẢ {count} câu: "{bloom.cognitive_level.value}" ({bloom.label_vi}).
- Thể loại BẮT BUỘC cho TẤT CẢ {count} câu: "{qtype.question_type.value}" ({qtype.label_vi}).
- Mức độ khó đề xuất ("level"): "{bloom.default_difficulty.value}".
- Ngôn ngữ câu hỏi & giải thích: {language_label}.
{extra_block}{dedup_block}{repair_block}
Đảm bảo mỗi câu hỏi trong mảng JSON "questions":
1. Có đúng "cognitive_level": "{bloom.cognitive_level.value}" và "question_type": "{qtype.question_type.value}".
2. Có danh sách "options" đáp ứng đúng quy tắc của {qtype.question_type.value}, các phương án hoàn toàn không trùng lặp nội dung, không chứa "Tất cả các đáp án trên" hay "Không có đáp án nào đúng".
3. Các phương án nhiễu phải có tính phân loại cao, bám sát lỗi sai/nhầm lẫn phổ biến trong chủ đề "{topic.strip()}".
4. Có trường "explanation" giải thích rõ vì sao đáp án đúng chính xác và phương án nhiễu sai ở điểm nào, cùng 1–3 "tags" ngắn gọn (tối đa 40 ký tự mỗi tag)."""

    return system_prompt, user_prompt

