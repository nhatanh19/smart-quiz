# BIÊN BẢN HƯỚNG DẪN LÀM VIỆC KẾT HỢP DEV 3 + DEV 4

| Thông tin | Nội dung |
| :--- | :--- |
| **Dự án** | Smart Quiz — Nền tảng kiểm tra & ôn luyện trắc nghiệm tích hợp AI |
| **Repo** | `github.com/nhatanh19/smart-quiz` (private) |
| **Ngày lập** | 30/10/2026 |
| **Phiên bản** | v1.0 |
| **Milestone** | `Sprint 1: Core Foundation` — hạn chót **04/11/2026** |
| **Bên A (Dev 3)** | Vương Ngọc Thuận — `@thuan734655` — Module 3: Auth, Exam Engine, Anti-cheat |
| **Bên B (Dev 4)** | Mai Văn Tỉnh — `@MaiVanTinh17072005` — Module 4: Grading, AI Tutor, Analytics |
| **Trọng tài / Escalation** | Dev 1 (Team Leader) — `@nhatanh19` |
| **Phạm vi** | Issue **#13** (Dev 3) → bàn giao cho **#14, #15, #16, #17** (Dev 4) |

> ⚠️ **Lưu ý về đánh số:** Trên GitHub, issue thật chỉ tồn tại từ **#1 → #17**. Các số **#18, #19, #20 đã bị Pull Request chiếm dụng**. Vì vậy biên bản này chỉ tham chiếu issue #13–#17. Khi tạo issue Sprint 2 (theo tài liệu là #18–#32) **phải đổi dãy số**, nếu không sẽ trùng PR.

---

## 1. Mục đích

Biên bản này quy định **cách hai module 3 và 4 phối hợp** để:

1. Chốt và đóng băng **hợp đồng dữ liệu** giữa bộ xáo trộn đề (#13) và bộ chấm điểm (#14) **trong 0,5 ngày đầu**, để Dev 4 lập trình song song mà không phải chờ.
2. Xác định **ranh giới sở hữu mã nguồn**, tránh sửa chéo gây conflict.
3. Định nghĩa **điểm tích hợp duy nhất** giữa 2 module (`submit` → `grade`).
4. Xử lý dứt điểm **PR #19 (#16) đang bị đóng không merge**.
5. Đặt **nhịp làm việc, DoD và escalation** cho 5 ngày còn lại của Sprint 1.

---

## 2. Hiện trạng tại thời điểm lập biên bản (30/10/2026)

### 2.1. Issue

| Issue | Nội dung | SP | Trạng thái GitHub | Ghi chú |
| :--- | :--- | :---: | :--- | :--- |
| **#13** | Seed-based Shuffling Algorithm | 2 | **Open, chưa assign** | Chưa có branch |
| **#14** | Instant Auto-Grading Engine | 3 | **Open**, assign Dev 4 | Branch `feature/issue-14-auto-grading-engine` tồn tại nhưng **0 commit** → chưa bắt đầu |
| **#15** | Post-Exam Review Mode | 3 | Open, **chưa assign** | Phụ thuộc #14 |
| **#16** | Contextual Explanation API | 3 | Open, assign Dev 4 | PR #19 **closed, KHÔNG merge**; branch có 1 commit, 12 file, +1507/−64 |
| **#17** | Knowledge Gap Diagnostic Card | 2 | Open, **chưa assign** | Chưa có branch |

### 2.2. Nền tảng đã có sẵn (không cần chờ ai)

- ✅ **#1, #2, #3 đã đóng** (PR #18, #20 đã merge vào `main` = `91b6c8a`).
- ✅ Toàn bộ 8 bảng + enum + ràng buộc trong `backend/app/models/entities.py`.
- ✅ Auth dùng **JWT trong HttpOnly cookie**, có `/auth/login`, `/register`, `/refresh`, `/logout`, `/me`, `get_current_user`, `require_roles` (`backend/app/core/security.py:70,111`).
- ✅ `backend/app/core/llm_client.py` — adapter LLM + retry exponential + ép JSON schema (dùng được ngay cho #16).
- ✅ `ProtectedRoute` hỗ trợ `allowedRoles` (`frontend/src/routes/ProtectedRoute.tsx`).
- ✅ `frontend/src/lib/apiClient.ts` — axios có `withCredentials` + interceptor refresh 401.
- ✅ Hợp đồng JSONB đã được đặc tả: `docs/DATABASE_GUIDE.md` §5.3, §5.4, §5.5 và `docs/Smart Quiz — Đặc tả Cấu trúc CSDL...md` §5, §8.

### 2.3. Ba phát hiện phải xử lý ngay

| Mã | Phát hiện | Hệ quả | Xử lý |
| :--- | :--- | :--- | :--- |
| **F-01** | Nhánh #16 tạo `frontend/src/lib/api-client.ts` (gạch nối) trong khi `main` có `frontend/src/lib/apiClient.ts` (lạc đà). Bản trong nhánh dùng **Bearer token từ `localStorage`** — trái với auth HttpOnly cookie đã merge. | Nếu merge nguyên trạng: 2 API client song song, toàn bộ request mất cookie → 401 hàng loạt. | **Xóa** `api-client.ts`, sửa import trong `tutorService.ts` sang `@/lib/apiClient`. |
| **F-02** | PR #19 sửa `.gitignore` theo hướng **xóa bớt** rule (`*.db`, `*.sqlite3`, `*.swp`, `uploads/`, `temp/`). | Rủi ro commit nhầm file DB/upload, rác IDE. | **Revert toàn bộ** thay đổi `.gitignore` trong PR (không thuộc phạm vi #16). |
| **F-03** | PR #19 khai báo `Closes #16` nhưng bị đóng không merge; issue #16 vẫn open; Dev 4 đã comment xin gia hạn ngày 29/10. | Code 1.507 dòng nằm ngoài `main`, nếu làm tiếp #15 sẽ phân kỳ. | Reopen PR #19 (Phương án A — mục 10). |

---

## 3. Nguyên tắc phối hợp bắt buộc

| Mã | Nguyên tắc | Diễn giải |
| :--- | :--- | :--- |
| **CO-01** | **Contract-first** | Hợp đồng dữ liệu (mục 5) được chốt **trước khi** viết code. Mọi thay đổi phải comment vào issue tương ứng + báo bên kia trong **2 giờ**. |
| **CO-02** | **Một file – một chủ** | Chỉ chủ sở hữu (mục 4) được commit vào file của mình. Muốn sửa file của người khác: mở PR riêng, tag người đó review. |
| **CO-03** | **Không push trực tiếp `main`** | Mọi thay đổi qua PR từ `feature/issue-<số>-<slug>`, tối thiểu 1 approval. |
| **CO-04** | **PR nhỏ, mạch lạc** | ≤ 400 dòng thay đổi/PR. PR quá lớn phải tách. Không gộp 2 issue vào 1 PR. |
| **CO-05** | **Review SLA 4 giờ** | Trong giờ làm việc, PR được tag phải có review trong 4 giờ (comment hoặc approve). Quá hạn → escalate. |
| **CO-06** | **Blocking > 2 giờ phải báo** | Comment vào issue, tag đối phương; > 4 giờ tag Dev 1. Không im lặng làm lại phần của người khác. |
| **CO-07** | **Không sửa schema DB** | `backend/app/models/entities.py` chỉ Dev 1 được sửa. Cần thêm cột → mở issue mới. |
| **CO-08** | **Test là điều kiện merge** | PR phải có test mới tương ứng (`backend/tests/`) và `pytest` xanh. |

---

## 4. Phân vùng sở hữu mã nguồn

| Vùng | File / thư mục | Chủ sở hữu | Ghi chú |
| :--- | :--- | :--- | :--- |
| **Module 3** | `backend/app/modules/exam_engine/**` | **Dev 3** | Chứa `start`, `submit`, `log-violation`, service xáo trộn |
| | `backend/tests/test_exam_*.py` | **Dev 3** | |
| | `frontend/src/pages/exam/**`, `frontend/src/layouts/ExamFocusLayout.tsx` | **Dev 3** | |
| | `backend/app/modules/auth/**`, `backend/app/core/security.py` | **Dev 3** | Sửa `security.py` cần Dev 1 review |
| **Module 4** | `backend/app/modules/tutor_analytics/**` | **Dev 4** | Chứa `grading`, `explain`, `review`, `knowledge-gaps`, `analytics` |
| | `backend/tests/test_grading*.py`, `test_ai_tutor.py`, `test_review*.py` | **Dev 4** | |
| | `frontend/src/pages/tutor-analytics/**`, `frontend/src/components/tutor/**` | **Dev 4** | |
| | `frontend/src/services/tutorService.ts` | **Dev 4** | |
| **Dùng chung – cần review** | `frontend/src/routes/AppRoutes.tsx` | **Dev 3** (chủ) | Dev 4 gửi snippet 5 dòng cho Dev 3 để thêm route `/review/:attemptId`, **không tự sửa** |
| | `frontend/src/lib/apiClient.ts` | **Dev 3** | Chỉ mở rộng, không tạo client thứ 2 |
| **Chỉ Dev 1** | `backend/app/models/entities.py`, `backend/app/schemas/common.py`, `backend/app/main.py`, `backend/requirements.txt`, `.gitignore`, `frontend/src/routes/ProtectedRoute.tsx` | **Dev 1** | Dev 4 cần thêm `pytest` → gửi đề xuất cho Dev 1 |

---

## 5. Hợp đồng dữ liệu (BẮT BUỘC TUÂN THỦ)

Nguồn chuẩn duy nhất: `docs/DATABASE_GUIDE.md` §5.3–5.5 và `docs/Smart Quiz — Đặc tả Cấu trúc CSDL...md` §5, §8.

### 5.1. `exam_attempts.question_order_snapshot` (Dev 3 ghi, Dev 4 đọc)

```json
{
  "version": 1,
  "questions": [
    { "question_id": "d9862108-11ab-4cf8-8435-129165b4bb63", "options_order": ["C", "A", "D", "B"] },
    { "question_id": "1d38526c-e53f-4d5f-9d83-8dc1c32d8286", "options_order": ["B", "D", "A", "C"] }
  ]
}
```

- `questions[].options_order` = **thứ tự hiển thị**, chứa **`id` phương án gốc** (chữ in hoa) đã trộn.
- Không bao giờ ghi lại `text`/`is_correct` vào snapshot.
- Nếu tắt trộn: `options_order` = thứ tự gốc trong `questions.options`.

### 5.2. `attempt_answers.selected_options` (Dev 3 ghi từ client, Dev 4 chấm)

| Trường hợp | Giá trị |
| :--- | :--- |
| Chọn 1 đáp án | `["A"]` |
| Chọn nhiều đáp án | `["A", "C"]` |
| Đúng/Sai | `["TRUE"]` hoặc `["FALSE"]` theo `id` trong `questions.options` |
| Bỏ trống / hết giờ | `[]` |

> 🔒 **Điều khoản then chốt (K-01):** `selected_options` **luôn chứa `id` phương án GỐC**, không phải vị trí hiển thị. Việc xáo trộn chỉ đổi **thứ tự render** ở FE, không đổi `id`. Nhờ vậy Dev 4 chấm điểm độc lập với #13.
>
> 🔒 **Điều khoản then chốt (K-02):** Mọi `question_id` trong payload nộp bài **phải thuộc snapshot** của attempt. Đây là kiểm tra tầng ứng dụng (không phải trigger DB — xem đặc tả CSDL §8). Dev 3 chặn ở `submit`, Dev 4 chặn lại lần nữa ở `grade`.

### 5.3. Hợp đồng API giữa 2 module

| # | Endpoint | Chủ | Quyền | Input | Output chính |
| :--- | :--- | :---: | :--- | :--- | :--- |
| A1 | `POST /api/v1/exam-engine/exams/{exam_id}/start` | Dev 3 | STUDENT | — | `attempt_id`, `expires_at`, `duration_minutes`, `questions[]` |
| A2 | `POST /api/v1/exam-engine/attempts/{attempt_id}/submit` | Dev 3 | STUDENT | `{ "answers": [{ "question_id": "uuid", "selected_options": ["A"] }] }` | `status`, `score`, `correct_count`, `total_questions`, `time_spent_seconds` |
| B1 | `POST /api/v1/tutor-analytics/grade/{attempt_id}?force=false` | Dev 4 | INSTRUCTOR/ADMIN | — | `GradingResult` (như A2) |
| B2 | `GET /api/v1/tutor-analytics/review/{attempt_id}` | Dev 4 | STUDENT (chủ bài) / INSTRUCTOR | — | `attempt_id`, `score`, `correct_count`, `questions_review[]` |
| B3 | `POST /api/v1/tutor-analytics/explain` | Dev 4 | STUDENT | `attempt_id`+`question_id` hoặc context trực tiếp | `feedback{explanation, why_selected_wrong, study_suggestions}`, `cached`, `response_time_ms` |
| B4 | `GET /api/v1/tutor-analytics/knowledge-gaps/{attempt_id}` (#17) | Dev 4 | STUDENT (chủ bài) | — | `weak_topics[]`, `advice[]` |

**Quy ước bắt buộc:**

1. **A1 tuyệt đối không trả `is_correct`** trong `questions[].options[]` — chỉ `{id, text}`. Rò rỉ đáp án là lỗi bảo mật nghiêm trọng.
2. `questions[]` của A1 sắp theo `options_order` (đã trộn) và `order_index` của đề.
3. `A2` gọi **hàm Python** `grade_attempt()` của Dev 4 (mục 8), **không** gọi HTTP nội bộ.
4. Mã lỗi: `400` payload sai/`question_id` ngoài snapshot, `403` sai quyền, `404` không tồn tại, `409` attempt đã nộp và `force=false`.
5. Mọi ID trả về là **UUID dạng string**; `option.id` là **chữ in hoa**.

---

## 6. Đặc tả #13 — Dev 3 bàn giao cho Dev 4

### 6.1. Trách nhiệm

| Hạng mục | Nội dung |
| :--- | :--- |
| Thuật toán | Fisher–Yates với seed = `hash(student_id + exam_id + attempt_number)` (deterministic: reload không đổi thứ tự) |
| Phạm vi | Trộn thứ tự câu hỏi + thứ tự `options_order` cho từng thí sinh |
| Ghi DB | `exam_attempts.question_order_snapshot` (đúng §5.1) + `attempt_answers` với `selected_options` = **id gốc** |
| Không làm | Không tính điểm, không ghi `score`, không đụng `is_correct`/`points_awarded` |

### 6.2. Mốc bàn giao (Gate G1) — **12:00 ngày 31/10/2026**

Dev 4 **chỉ được bắt đầu #14** khi 6 mục sau đã tick:

- [ ] G1.1 — Snapshot mẫu được dán vào comment issue #13 (đúng schema §5.1).
- [ ] G1.2 — Commit interface service (chữ ký hàm + docstring) trước khi có implementation.
- [ ] G1.3 — Test: 2 thí sinh khác nhau → `options_order` khác nhau.
- [ ] G1.4 — Test: reload/khởi động lại → snapshot không đổi (deterministic).
- [ ] G1.5 — Test: `shuffle_options=false` → `options_order` = thứ tự gốc.
- [ ] G1.6 — Xác nhận bằng văn bản: `selected_options` luôn là **id gốc** (K-01).

### 6.3. Định dạng hàm bàn giao

```python
# backend/app/modules/exam_engine/shuffle_service.py  (Dev 3 sở hữu)
def build_attempt_snapshot(
    exam_questions: list[ExamQuestion],
    student_id: uuid.UUID,
    exam_id: uuid.UUID,
    attempt_number: int,
    *,
    shuffle_questions: bool = True,
    shuffle_options: bool = True,
) -> dict:
    """Trả về dict đúng schema DATABASE_GUIDE §5.3."""
```

---

## 7. Đặc tả #14 — Dev 4 triển khai

### 7.1. Chữ ký hàm (bàn giao ngược cho Dev 3)

```python
# backend/app/modules/tutor_analytics/services/grading_service.py  (Dev 4 sở hữu)
@dataclass
class GradingResult:
    attempt_id: uuid.UUID
    score: float
    correct_count: int
    total_questions: int
    answers: list[dict]          # [{question_id, is_correct, points_awarded}]
    time_spent_seconds: int
    already_graded: bool = False

def grade_attempt(
    db: Session,
    attempt_id: uuid.UUID,
    *,
    force: bool = False,
) -> GradingResult:
    """Chấm điểm đồng bộ. KHÔNG commit — caller commit.
    Raise: NotFoundError, InvalidAttemptStateError, SnapshotMismatchError.
    """
```

### 7.2. Công thức chấm

| Loại câu | Công thức | `is_correct` |
| :--- | :--- | :--- |
| `SINGLE_CHOICE` | `ratio = 1.0` nếu `S == C`, ngược lại `0.0` | `S == C` |
| `TRUE_FALSE` | Như single (validate đúng 2 phương án, 1 đáp án đúng) | `S == C` |
| `MULTIPLE_CHOICE` | `ratio = clamp((|S∩C| − |S\C|) / |C|, 0, 1)` | `S == C` |
| Bỏ trống `S = []` | `ratio = 0.0` | `False` |

- `points_awarded = round(exam_questions.points × ratio, 2)`
- `score = clamp(round(Σ points_awarded / Σ exam_questions.points × 10, 2), 0, 10)`
- Nếu `Σ exam_questions.points == 0` → `score = 0.0`, log warning.
- Thời gian làm bài = `submitted_at − started_at` (giây). **Không có cột DB** → chỉ trả trong response, không lưu.

**Ví dụ MULTIPLE_CHOICE:** `C = {A, C}`, `points = 2`.

| Sinh viên chọn | ratio | điểm |
| :--- | :---: | :---: |
| `["A","C"]` | 1.0 | 2.00 |
| `["A"]` | 0.5 | 1.00 |
| `["A","B"]` | 0.0 | 0.00 |
| `["A","B","C"]` | 0.5 | 1.00 |

### 7.3. Bảng tình huống biên (bắt buộc có test)

| # | Tình huống | Hành vi mong đợi |
| :---: | :--- | :--- |
| E1 | `attempt_id` không tồn tại | `404` |
| E2 | Attempt đã `SUBMITTED`, `force=false` | Trả kết quả cũ, `already_graded=true`, không ghi đè |
| E3 | Attempt `LOCKED_VIOLATION` / `EXPIRED` | Vẫn chấm; giữ nguyên status, set `submitted_at` nếu trống |
| E4 | `question_id` không thuộc snapshot (K-02) | `400`, không chấm phần nào |
| E5 | `selected_options` chứa id lạ ngoài câu hỏi | Coi như chọn sai (`ratio=0`), log warning, không crash |
| E6 | `selected_options` trùng id `["A","A"]` | Dedupe trước khi chấm |
| E7 | Câu hỏi không có bản ghi `attempt_answers` | Tính 0 điểm, vẫn đếm vào `total_questions` |
| E8 | Đề 0 câu / tổng points = 0 | `score = 0.0`, không chia cho 0 |
| E9 | `score` vượt biên do làm tròn | Clamp `[0, 10]` (ràng buộc DB `score_range`) |
| E10 | Gọi `grade` 2 lần liên tiếp | Lần 2 idempotent, không nhân đôi điểm |

### 7.4. Hiệu năng (DoD < 300ms)

- **1 query** lấy `exam_questions` + `questions` (dùng `selectinload`/JOIN), **1 query** lấy `attempt_answers`.
- **Cấm N+1**: không gọi `db.query` trong vòng lặp.
- Chấm thuần Python trên dữ liệu đã nạp; không gọi LLM trong luồng `submit`.

---

## 8. Điểm tích hợp duy nhất: `submit` → `grade`

```
POST /exam-engine/attempts/{id}/submit          (Dev 3)
  ├─ 1. Xác thực: attempt thuộc user, status = IN_PROGRESS, chưa quá expires_at
  ├─ 2. Validate: mọi question_id ∈ snapshot (K-02)
  ├─ 3. Upsert attempt_answers (selected_options = id gốc)
  ├─ 4. Gọi grade_attempt(db, attempt_id)        ← Dev 4
  │      ├─ ghi attempt_answers.is_correct / points_awarded
  │      └─ ghi exam_attempts.score / status=SUBMITTED / submitted_at
  ├─ 5. db.commit()                              ← CHỈ Dev 3 commit
  └─ 6. Trả GradingResult → FE chuyển /review/{attempt_id}
```

**Quy tắc giao kèo:**

| Mã | Quy tắc |
| :--- | :--- |
| **I-01** | `grade_attempt()` **không commit**, chỉ `flush()`. Caller (Dev 3) commit — đảm bảo 1 transaction cho toàn bộ submit. |
| **I-02** | Dev 3 **không** import router của Dev 4; chỉ import `services/grading_service.grade_attempt`. |
| **I-03** | Nếu #14 chưa xong: Dev 3 bọc `try/except NotImplementedError` → vẫn `SUBMITTED` với `score = NULL`, ghi TODO. Endpoint `B1` cho phép chấm bù sau. |
| **I-04** | Muốn chấm lại (giảng viên sửa đáp án): gọi `B1?force=true`, quyền INSTRUCTOR/ADMIN. |
| **I-05** | Dev 4 **không** sửa `exam_engine/**`; nếu cần đổi payload submit, comment issue #14 và tag Dev 3. |

---

## 9. Kế hoạch 5 ngày (31/10 → 04/11)

| Ngày | Dev 3 (Thuận) | Dev 4 (Tỉnh) | Mốc |
| :--- | :--- | :--- | :--- |
| **31/10** | #13: chốt snapshot + interface (**12:00**), implement + test | #16: rebase PR #19, sửa F-01/F-02, chạy test | **Gate G1** |
| **01/11** | #13: hoàn tất, merge; bắt đầu #12 (exam room + `require_roles`) | #14: `grading_service` + 10 test case | G1 đóng → Dev 4 bắt đầu #14 |
| **02/11** | #12: API tạo đề + start attempt (dùng snapshot #13) | #14: endpoint `B1` + tích hợp A2 với Dev 3 | Demo chấm điểm lần 1 |
| **03/11** | #4: gắn `allowedRoles` + trang Profile | #15: Review UI (dùng `GET B2` sẵn có) | Merge #16 |
| **04/11** | Buffer review, hỗ trợ E2E | #17: `knowledge-gaps` + card UI; buffer | **Milestone due** |

> Nếu trễ: ưu tiên cắt **#17** (should-have) → giữ #14 + #15 (must-have).

---

## 10. Xử lý PR #19 (#16) — Phương án A

**Chọn: Reopen + rebase + sửa 3 lỗi chặn merge.** Lý do: 1.507 dòng giá trị đã viết, `mergeable_state = clean`, không có review comment phản đối.

Quy trình 6 bước:

1. **Reopen PR #19** trên GitHub, đổi base = `main` mới nhất (`91b6c8a`).
2. `git fetch origin && git switch feature/issue-16-contextual-explanation-generator && git rebase origin/main`.
3. **Sửa F-01:** `git rm frontend/src/lib/api-client.ts`; đổi import trong `frontend/src/services/tutorService.ts` thành `import apiClient from "@/lib/apiClient";`; bỏ logic `localStorage.access_token`.
4. **Sửa F-02:** `git checkout origin/main -- .gitignore`.
5. **Sửa F-03:** xác nhận body PR có `Closes #16`; chạy `pytest backend/tests/test_ai_tutor.py` + `npm run build`.
6. Tag `@thuan734655` + `@nhatanh19` review; merge khi CI xanh.

**Điều kiện cấm merge:** còn file `api-client.ts`, còn diff `.gitignore`, hoặc test đỏ.

---

## 11. Definition of Done dùng chung

Một issue chỉ được đóng khi:

- [ ] Code nằm trên `main` qua PR đã merge (không tính "đã push branch").
- [ ] Có test mới chạy xanh; không làm đỏ test cũ.
- [ ] `npm run build` (FE) và `pytest` (BE) pass.
- [ ] Không có `TODO`/`placeholder` còn sót trong phần đã nhận.
- [ ] Hợp đồng dữ liệu (mục 5) không bị vi phạm.
- [ ] Có comment minh chứng: lệnh chạy + kết quả (số test, thời gian xử lý).
- [ ] Đã cập nhật checklist AC trong issue body.

---

## 12. Nhịp làm việc & escalation

| Hoạt động | Thời điểm | Hình thức |
| :--- | :--- | :--- |
| Daily sync 15' | 09:00 hằng ngày | Trực tiếp / call: hôm qua – hôm nay – blocker |
| Cập nhật issue | Cuối mỗi ngày | Comment tiến độ % + commit SHA |
| Review PR | Trong 4 giờ làm việc | GitHub Review |
| Chốt contract | 31/10 12:00 | Comment issue #13, tag Dev 4 + Dev 1 |
| Escalate | Blocker > 4 giờ | Tag `@nhatanh19` trong issue |
| Retro Sprint 1 | Sau 04/11 | Theo issue #31 (đánh số lại nếu trùng) |

**Kênh chính thức:** comment trên GitHub issue. Chat chỉ để nhắc, **không** dùng để chốt contract.

---

## 13. Rủi ro & phương án dự phòng

| Mã | Rủi ro | Xác suất | Tác động | Phương án |
| :--- | :--- | :---: | :---: | :--- |
| **R1** | Dev 3 trễ Gate G1 (snapshot) | Trung bình | Dev 4 mất 1–2 ngày | Dev 4 code với `shuffle=false` + mapping identity; đổi adapter 1 file khi G1 xong |
| **R2** | PR #19 conflict khi rebase | Trung bình | Mất nửa ngày | Rebase từng file; `AnalyticsPlaceholder.tsx` ưu tiên bản nhánh |
| **R3** | Không có `LLM_API_KEY` | Cao | #16 không demo thật | Fallback `_generate_pedagogical_fallback` đã có trong service; test bằng mock |
| **R4** | Dev 4 ôm #14+#15+#16+#17 = 11 SP / 5 ngày | **Cao** | Trượt milestone | Cắt #17; #15 làm UI trước, nối API sau |
| **R5** | `AppRoutes.tsx` bị sửa bởi cả 2 | Trung bình | Conflict nhỏ | Dev 4 gửi snippet, Dev 3 commit (mục 4) |
| **R6** | Issue Sprint 2 trùng số PR #18–#20 | Chắc chắn | Loạn truy vết | Đổi dãy số trước khi tạo issue mới |

---

## 14. Cam kết

Hai bên xác nhận đã đọc, hiểu và thống nhất thực hiện biên bản này. Mọi thay đổi so với biên bản phải được ghi thành **Phụ lục** kèm ngày và chữ ký xác nhận của cả hai bên.

| Bên | Họ tên | GitHub | Chữ ký | Ngày |
| :--- | :--- | :--- | :--- | :--- |
| **Dev 3** | Vương Ngọc Thuận | `@thuan734655` | | |
| **Dev 4** | Mai Văn Tỉnh | `@MaiVanTinh17072005` | | |
| **Trọng tài** | Dev 1 (Team Leader) | `@nhatanh19` | | |

---

## Phụ lục A — Mẫu comment chốt Gate G1 (dán vào issue #13)

```markdown
## ✅ Gate G1 — Contract #13 → #14

- [x] Snapshot schema theo DATABASE_GUIDE §5.3
- [x] `selected_options` = id phương án GỐC (K-01)
- [x] `question_id` phải thuộc snapshot (K-02)
- [x] Deterministic theo `student_id + exam_id + attempt_number`
- [x] Test: 2 sinh viên khác thứ tự / reload không đổi / tắt shuffle = thứ tự gốc

Commit: `<sha>`
@MaiVanTinh17072005 được phép bắt đầu #14 từ thời điểm này.
```

## Phụ lục B — Lệnh git mẫu

```bash
# Dev 3 — bắt đầu #13
git switch main && git pull
git switch -c feature/issue-13-seed-shuffling

# Dev 4 — cứu PR #19 (#16)
git fetch origin
git switch feature/issue-16-contextual-explanation-generator
git rebase origin/main
git rm frontend/src/lib/api-client.ts
git checkout origin/main -- .gitignore
# sửa import trong frontend/src/services/tutorService.ts -> "@/lib/apiClient"
git commit -am "fix(tutor): use shared cookie-based apiClient and restore .gitignore"
git push --force-with-lease

# Dev 4 — bắt đầu #14 sau Gate G1
git switch main && git pull
git switch -c feature/issue-14-auto-grading-engine-v2
```

## Phụ lục C — Checklist review chéo (dán vào PR)

```markdown
### Reviewer checklist (Dev 3 ↔ Dev 4)
- [ ] Không sửa file ngoài vùng sở hữu (mục 4)
- [ ] Snapshot / selected_options đúng §5.1–5.2
- [ ] A1 không trả `is_correct`
- [ ] `grade_attempt()` không commit (I-01)
- [ ] Có test cho E1–E10 (nếu là #14)
- [ ] `pytest` + `npm run build` xanh
```
