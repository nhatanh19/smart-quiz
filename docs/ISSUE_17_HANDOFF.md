# Issue #17 — Knowledge Gap Diagnostic Card in Review UI Implementation Handoff

Branch: `feature/issue-17-knowledge-gap-diagnostic-card`  
Assignee: Dev 4 (Mai Văn Tỉnh — `@MaiVanTinh17072005`)  
WBS Reference: `5.2.2` (Sprint 1: Core Foundation)  
Classification: `should-have` (2 Story Points)

---

## 1. Overview & Requirements Alignment

Issue #17 implements the **Knowledge Gap Diagnostic Card in Review UI** adhering strictly to:
- `docs/DEV3_DEV4_WORKING_AGREEMENT.md` (§4, §5.3 Endpoint B4, §9, §11)
- `docs/DETAILED_GITHUB_ISSUES.md` (Issue #17 Acceptance Criteria)
- Seamless integration with **Issue #15 (Review Mode Interface)** and **Issue #16 (Contextual AI Tutor Feedback)**.

### Acceptance Criteria (Definition of Done Checklist)
- [x] **AC1: Thẻ tổng kết hiển thị rõ ràng chủ đề cần củng cố:**
  - Header & Headline hiển thị rõ: *"Chủ đề bạn cần củng cố: Kế thừa & Đa hình trong OOP"* (hoặc tên chủ đề/tag sinh viên làm sai nhiều nhất trong bài thi).
  - Phân tích chi tiết số câu sai / tổng số câu theo từng chuyên đề, tỷ lệ phần trăm chính xác (accuracy percentage) và thanh đo trực quan.
  - Xử lý tình huống đạt điểm tối đa (100%): hiển thị lời khen ngợi và định hướng mở rộng kiến thức chuyên sâu.
- [x] **AC2: Đề xuất ít nhất 2 gợi ý cụ thể để cải thiện kết quả (Actionable Study Advice):**
  - Gợi ý 1: Củng cố lý thuyết & nguyên lý cốt lõi (chỉ rõ tài liệu, slide chuyên đề).
  - Gợi ý 2: Luyện tập bài tập trắc nghiệm chuyên sâu (mức độ Vận dụng - Apply với số lượng bài tập đề xuất).
  - Gợi ý 3: Tích hợp đối chiếu nguyên nhân sai với Gia sư ảo AI Tutor (kế thừa từ Issue #16).
  - Mỗi gợi ý có phân loại hành động (`action_type`), mức độ ưu tiên (`priority`), mô tả sư phạm và chỉ dẫn tài liệu (`resource_hint`).

---

## 2. Architecture & Implementation

### Backend
- **Endpoint**: `GET /api/v1/tutor-analytics/knowledge-gaps/{attempt_id}`
  - Role-based Access Control (RBAC): Sinh viên (`STUDENT`) chỉ xem được chẩn đoán bài của mình; Giảng viên (`INSTRUCTOR`) và Quản trị viên (`ADMIN`) có thể xem bài của bất kỳ ai.
  - State check: Từ chối (`HTTP 400`) nếu bài thi chưa kết thúc/nộp (`IN_PROGRESS`).
  - Phân tích & tổng hợp: Gom nhóm câu hỏi sai theo `tags` hoặc `category.name`, tính toán tỉ lệ chính xác và sắp xếp theo mức độ yếu giảm dần.
- **Service**: `backend/app/modules/tutor_analytics/services/knowledge_gap_service.py`
  - Hàm `diagnose_knowledge_gaps(db, attempt_id, current_user)`
- **Schemas**: `backend/app/modules/tutor_analytics/schemas.py`
  - `WeakTopicItemSchema`, `ActionableStudyAdviceSchema`, `KnowledgeGapDiagnosticResponse`.

### Frontend
- **Card Component**: `frontend/src/components/tutor/KnowledgeGapCard.tsx`
  - Callout banner chẩn đoán nổi bật với biểu tượng Target / CheckCircle2.
  - Danh sách thẻ phân loại chủ đề kèm thanh tiến độ chính xác.
  - Danh sách lời khuyên ôn tập cụ thể với icon, nhãn hành động (`Lý thuyết`, `Luyện tập`, `AI Tutor`) và nhãn `Ưu tiên cao`.
- **Review Page Integration**: `frontend/src/pages/tutor-analytics/ReviewExamView.tsx`
  - Nhúng trực tiếp thẻ `KnowledgeGapCard` ngay trên màn hình xem lại bài thi (Review UI) phía trên thanh lọc và danh sách câu hỏi.
  - Tự động gọi API `tutorService.getKnowledgeGaps(effectiveAttemptId)` khi mở bài thi.
  - Hỗ trợ dữ liệu mẫu chuẩn OOP khi xem ở chế độ preview/demo.
- **Service Client**: `frontend/src/services/tutorService.ts`
  - Thêm phương thức `getKnowledgeGaps(attemptId: string): Promise<KnowledgeGapData>`.

---

## 3. Test & Quality Verification

### 1. Backend Test Suite (`backend/tests/test_knowledge_gaps.py`)
- `test_diagnose_knowledge_gaps_success`: Kiểm tra chính xác headline *"Chủ đề bạn cần củng cố: Kế thừa & Đa hình trong OOP"*, danh sách weak_topics và tối thiểu 2 lời khuyên ôn tập.
- `test_diagnose_perfect_score_no_gaps`: Kiểm tra khi làm đúng 100% không có lỗ hổng (`has_gaps = False`).
- `test_diagnose_not_found`: 404 cho attempt không tồn tại.
- `test_diagnose_in_progress_attempt_rejected`: 400 khi bài thi chưa nộp.
- `test_diagnose_student_forbidden_other_attempt`: 403 khi sinh viên xem bài người khác.
- `test_diagnose_instructor_can_access_any_attempt`: 200 cho Giảng viên.

**Kết quả kiểm thử toàn diện:**
```text
backend\tests\test_grading.py ..................                         [ 28%]
backend\tests\test_ai_tutor.py ........                                  [ 41%]
backend\tests\test_review.py ......                                      [ 50%]
backend\tests\test_knowledge_gaps.py ......                              [ 60%]
backend\tests\test_exam_shuffle.py .........................             [100%]
====================== 63 passed, 15 warnings in 10.19s =======================
```

### 2. Frontend Build Verification
```text
> smart-quiz-frontend@0.1.0 build
> tsc && vite build
✓ built in 2.93s (0 errors, 0 warnings)
```
