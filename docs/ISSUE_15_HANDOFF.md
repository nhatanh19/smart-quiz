# Issue #15 — Post-Exam Detailed Review Mode Interface Implementation Handoff

Branch: `feature/issue-15-post-exam-review-interface`  
Assignee: Dev 4 (Mai Văn Tỉnh — `@MaiVanTinh17072005`)  
WBS Reference: `5.1.2` (Sprint 1: Core Foundation)  
Classification: `must-have` (3 Story Points)

---

## 1. Overview & Requirements Alignment

Issue #15 implements the **Post-Exam Detailed Review Mode Interface** adhering strictly to:
- `docs/DEV3_DEV4_WORKING_AGREEMENT.md` (§4, §5.3 Endpoint B2, §8, §11)
- `docs/DETAILED_GITHUB_ISSUES.md` (Issue #15 Acceptance Criteria)
- Seamless integration with **Issue #14 (Auto-Grading Engine)** and **Issue #16 (Contextual AI Tutor Feedback)**.

### Acceptance Criteria (Definition of Done Checklist)
- [x] **AC1: Sinh viên xem được chi tiết từng câu làm đúng/sai và tổng điểm:**
  - Header tổng kết: Điểm số thang 10 nổi bật, số lượng câu đúng/sai, thời gian làm bài, tên bài thi và thông tin thí sinh.
  - Chi tiết từng câu: Đánh dấu màu xanh cho câu làm đúng (+điểm), màu đỏ cho câu làm sai (0.0 đ).
  - Đối chiếu trực quan: Phương án thí sinh chọn (gắn nhãn *"Bạn đã chọn"*, gạch ngang nếu sai), phương án chuẩn (gắn nhãn *"Đáp án chuẩn"* kèm icon `CheckCircle`).
  - Hỗ trợ câu hỏi chưa trả lời (gắn nhãn *"Chưa trả lời"*).
  - Tích hợp lời giải thích chuẩn từ ngân hàng đề và nút **"Giải thích bằng AI"** (< 3s) kế thừa từ Issue #16.
- [x] **AC2: Có bộ lọc nhanh:**
  - **"Tất cả"**: Hiển thị toàn bộ câu hỏi.
  - **"Chỉ xem câu sai"**: Lọc tức thì các câu trả lời sai để học viên tập trung ôn tập.
  - **"Chỉ xem câu đúng"**: Lọc danh sách các câu đã làm đúng.
  - Hiển thị số lượng câu hỏi tương ứng trên từng nút và thanh trạng thái đếm.

---

## 2. Architecture & Implementation

### Backend
- **Endpoint**: `GET /api/v1/tutor-analytics/review/{attempt_id}`
  - Role check (RBAC): Thí sinh (`STUDENT`) chỉ được xem bài làm của chính mình; Giảng viên (`INSTRUCTOR`) và Quản trị viên (`ADMIN`) có quyền xem bài của bất kỳ thí sinh nào.
  - Trạng thái bài thi: Chỉ cho phép xem lại bài thi đã nộp/kết thúc (`SUBMITTED`, `EXPIRED`, `LOCKED_VIOLATION`); từ chối nếu bài thi đang làm (`IN_PROGRESS`).
  - Bảo tồn thứ tự xáo trộn: Ưu tiên sắp xếp câu hỏi và phương án theo `question_order_snapshot` (thuật toán Fisher-Yates từ Issue #13).
- **Service**: `backend/app/modules/tutor_analytics/services/review_service.py`
  - Hàm `get_exam_review_data(db, attempt_id, current_user)`
- **Schemas**: `backend/app/modules/tutor_analytics/schemas.py`
  - `QuestionReviewOptionSchema`, `QuestionReviewItemSchema`, `ExamReviewResponseSchema`.

### Frontend
- **Page Component**: `frontend/src/pages/tutor-analytics/ReviewExamView.tsx`
  - Hỗ trợ lấy `attemptId` từ dynamic route `/review/:attemptId` hoặc prop.
  - Có thanh tra cứu nhanh (Quick Attempt Lookup) cho phép nhập Attempt ID bất kỳ để mở bài thi.
  - Tự động chuyển fallback sang dữ liệu thực tế mẫu nếu mở ở `/review` không kèm ID.
  - Bộ lọc 3 chế độ với Tailwind badge trực quan.
- **Service Client**: `frontend/src/services/tutorService.ts`
  - Thêm phương thức `getAttemptReview(attemptId: string): Promise<ExamReviewData>`.
- **Routing**: `frontend/src/routes/AppRoutes.tsx`
  - Khai báo routes `/review` và `/review/:attemptId` trong `ProtectedRoute`.

---

## 3. Test & Quality Verification

### 1. Backend Test Suite (`backend/tests/test_review.py`)
- `test_review_service_and_snapshot_ordering`: Xác minh tính chính xác của dữ liệu review, thứ tự câu hỏi và thứ tự phương án được bảo tồn từ snapshot.
- `test_review_not_found`: Trả về 404 khi không tìm thấy attempt_id.
- `test_review_in_progress_attempt_rejected`: Trả về 400 khi cố gắng review bài thi chưa nộp.
- `test_review_student_forbidden_other_student_attempt`: Trả về 403 khi sinh viên cố tình xem bài của người khác.
- `test_review_instructor_can_access_any_attempt`: Giảng viên được phép xem bài của bất kỳ sinh viên nào.
- `test_review_fallback_order_when_no_snapshot`: Fallback sắp xếp theo `ExamQuestion.order_index` khi snapshot rỗng.

**Kết quả chạy test:**
```text
backend\tests\test_grading.py ..................                         [ 31%]
backend\tests\test_ai_tutor.py ........                                  [ 45%]
backend\tests\test_review.py ......                                      [ 56%]
backend\tests\test_exam_shuffle.py .........................             [100%]
======================= 57 passed, 9 warnings in 13.41s =======================
```

### 2. Frontend Build Verification
```text
> smart-quiz-frontend@0.1.0 build
> tsc && vite build
✓ built in 4.16s (0 errors, 0 warnings)
```
