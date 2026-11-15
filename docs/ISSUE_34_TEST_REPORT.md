# Báo cáo kết quả kiểm thử — Issue #34

- Ngày thực hiện: 14/11/2026 (Asia/Saigon).
- Nhánh: `feature/issue-34-focused-exam-room`.
- Phạm vi: phòng thi tập trung, countdown, lưu/khôi phục đáp án và tự nộp khi hết giờ.
- Trạng thái tại thời điểm báo cáo: thay đổi ở working tree, chưa commit/push/mở PR. Báo cáo ghi nhận các lần chạy trong phiên triển khai, không phải kết quả CI.
- Tài liệu bàn giao: [ISSUE_34_HANDOFF.md](ISSUE_34_HANDOFF.md).

## 1. Kết quả tổng hợp

| Hạng mục | Kết quả | Ghi chú |
| --- | --- | --- |
| Frontend: ExamPages + ExamRoom | **10 passed** | Vitest, môi trường jsdom; API được mock |
| Backend: exam engine + shuffle | **44 passed, 1 skipped** | SQLite; test concurrency PostgreSQL bị bỏ qua |
| Backend: grading + review | **33 passed** | Kiểm tra hồi quy chấm điểm và xem lại bài |
| Frontend production build | **PASS** | `tsc` và Vite build thành công |
| Backend khởi động | **PASS** | Uvicorn báo application startup complete, cổng 8000 |
| HTTP Swagger `/docs` | **200 OK** | Kiểm tra trực tiếp qua HTTP |
| Kết nối database khi chạy server | **PASS** | `SELECT 1` trả về `1`; tách biệt với DB SQLite dùng trong test |
| Frontend dev server | **Chưa khởi động thành công** | Vite bị sandbox chặn tạo tiến trình esbuild (`spawn EPERM`); yêu cầu chạy ngoài sandbox bị từ chối |
| Kiểm tra giao diện bằng trình duyệt / E2E | **Chưa thực hiện** | Build và test component chưa xác nhận bố cục, thao tác thực tế trên trình duyệt |

Tổng cộng **87 test passed, 1 skipped** trong các nhóm đã chạy. Đây không phải toàn bộ test suite của repository.

## 2. Các hành vi đã được kiểm tra

### Frontend — 10 test

Nguồn: `frontend/src/pages/exam/ExamPages.test.tsx` và `frontend/src/pages/exam/ExamRoom.test.tsx`.

1. Tạo ca thi công khai với câu hỏi được chọn, chuyển thời gian địa phương sang UTC.
2. Chỉ chuyển vào lobby sau khi kiểm tra mã phòng/PIN thành công.
3. Hiển thị lỗi khi vào phòng thất bại và giữ nguyên trang.
4. Bắt đầu/tiếp tục lượt thi rồi chuyển sang phòng thi riêng.
5. Hiển thị lỗi khi backend từ chối bắt đầu bài thi.
6. Khôi phục đáp án sau khi component được tải lại, nộp bằng option ID gốc và xóa cache của lượt thi sau khi thành công.
7. Tự nộp lượt thi đã hết hạn đúng một lần.
8. Giữ đáp án khi nộp thất bại và cho phép thử lại.
9. Không làm hỏng màn hình khi localStorage chứa JSON lỗi.
10. Kiểm tra trạng thái server để xử lý trường hợp server đã lưu bài nhưng phản hồi nộp bài bị mất.

### Backend — exam engine, shuffle và kiểm tra hồi quy

Nguồn: `backend/tests/test_exam_engine.py`, `test_exam_shuffle.py`, `test_grading.py`, `test_review.py`.

Các nhóm test đã chạy bao gồm kiểm tra tạo/vào phòng, PIN, bắt đầu/tiếp tục bài, xác thực/phân quyền, xáo trộn và kiểm tra option ID, nộp bài/chấm điểm, rollback khi grading lỗi và quyền truy cập review.

Test bổ sung cho #34 kiểm tra:

- Lưu đáp án và lấy lại qua API recovery.
- API recovery không trả trường `is_correct`.
- Sinh viên khác không được đọc/lưu đáp án của lượt thi.
- Từ chối lưu đáp án sau deadline.
- Khi nộp sau deadline, bỏ qua đáp án mới trong payload và chấm bằng đáp án đã lưu trước hạn.
- Bài hết hạn được chấm với trạng thái `EXPIRED`.

**Test bị bỏ qua:** `test_concurrent_start_postgres`, vì cần PostgreSQL để kiểm tra khóa dòng bằng các kết nối độc lập. Kết quả SQLite không chứng minh hành vi concurrency trên PostgreSQL.

## 3. Lệnh tái hiện

Chạy từ thư mục gốc repository, dùng hai terminal riêng nếu cần.

### Frontend

```powershell
cd frontend
npm test -- --run src/pages/exam/ExamPages.test.tsx src/pages/exam/ExamRoom.test.tsx
npm run build
```

### Backend

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_exam_engine.py tests/test_exam_shuffle.py -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest tests/test_grading.py tests/test_review.py -q -p no:cacheprovider
```

Trong phiên này, test/build frontend chạy thành công sau khi được phép chạy ngoài sandbox. Không cần thay đổi mã nguồn để xử lý lỗi esbuild EPERM.

## 4. Cảnh báo và giới hạn cần lead lưu ý

- Có warning về React Router v7 future flags và deprecation của Starlette/httpx/cookie trong test; các warning này không làm test thất bại.
- localStorage giữ đáp án khi mất mạng trên cùng tài khoản/lượt thi ở trình duyệt đó. Đáp án cần đến server trước `expires_at` mới được tính khi chấm sau hạn; đáp án chỉ còn ở localStorage và chưa đồng bộ sẽ không được nhận sau hạn.
- Chưa có scheduler tự chấm nếu thí sinh đóng hẳn trình duyệt; việc thu/chấm hết giờ chạy khi client gửi submit hoặc kết nối lại.
- Chưa kiểm tra trực tiếp countdown đang chạy, nhiều lựa chọn, điều hướng bằng bàn phím, bố cục mobile, debounce/sự kiện reconnect thực tế và nhiều tab cùng sửa đáp án trên trình duyệt.
- Cần chạy kiểm thử concurrency trên PostgreSQL trước khi kết luận về khóa dòng trong môi trường triển khai.
- Lần test backend đầu tiên bị chặn bởi chuỗi `phan tich issue` chèn trước câu import ở `tutor_analytics/router.py`. Đã bỏ chuỗi này; file sau sửa không còn diff so với Git. Các kết quả PASS nêu trên là các lần chạy sau khi sửa.

## 5. Phạm vi tiếp theo

**Issue #35 chưa được triển khai/kiểm thử trong báo cáo này.** Theo chỉ đạo lead: review và merge #34 vào `main` trước, sau đó tạo nhánh #35 để tích hợp monitor chống gian lận, ghi log, ngưỡng khóa động và tự khóa/chấm bài.
