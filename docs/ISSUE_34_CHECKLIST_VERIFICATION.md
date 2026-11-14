# Issue #34 — Bổ sung và đối chiếu acceptance criteria

Ngày: 14/11/2026 (Asia/Saigon).

Nhánh hiện tại: `feature/issue-35-browser-focus-monitor`, tạo từ main đã merge #34. Phần bổ sung checklist #34 được thực hiện trên nhánh này theo yêu cầu tiếp theo của người dùng, cùng các thay đổi #35 chưa commit.

## Đối chiếu ảnh yêu cầu

| Acceptance criteria | Kết quả triển khai / kiểm chứng |
| --- | --- |
| Phòng thi tập trung dùng ExamFocusLayout, từ ExamLobby | Đã có trong #34; giữ nguyên layout và route sinh viên. |
| Điều hướng đã làm / chưa làm / đánh dấu | Đã bổ sung đánh dấu và bỏ đánh dấu. Đánh dấu độc lập với đáp án; nav có nhãn trạng thái, biểu tượng và màu riêng, viền câu đang xem. |
| Countdown theo expires_at từ server | Đếm lại theo deadline tuyệt đối. Recovery API bổ sung server_now để bù chênh lệch đồng hồ client; reconnect cập nhật lại độ lệch. |
| Tự POST submit khi hết giờ | Test từ còn 3 giây đến hết giờ xác nhận submit đúng một lần, gửi option ID gốc. |
| Lưu selected_options theo attemptId, debounce | Giữ cache đáp án theo user ID và attempt ID; debounce 300ms, đồng thời ghi ngay ở mỗi thao tác để không mất lựa chọn cuối khi reload tức thì. |
| Khôi phục khi F5/reload hoặc gián đoạn mạng | Lưu thêm snapshot đề, danh sách đánh dấu, câu đang xem và độ lệch đồng hồ. Khi API lỗi mạng, khôi phục từ snapshot cùng cache đáp án. HTTP từ chối quyền sở hữu không được thay bằng bản cache. |
| Xóa cache khi nộp thành công | Xóa cả cache đáp án và snapshot/đánh dấu của lượt hiện tại, giữ cache lượt khác. Cùng cơ chế được dùng khi nhận lockout #35 hoặc recovery trả trạng thái kết thúc. |
| npm run test và npm run build pass | Toàn bộ npm test (cùng script với npm run test): 57 passed; build PASS. |

## Test bổ sung

Trong `frontend/src/pages/exam/ExamRoom.test.tsx`:

1. Giữ đánh dấu, trạng thái đã làm/chưa làm và vị trí câu đang xem qua unmount/remount.
2. Khôi phục đề, nhiều lựa chọn và đánh dấu khi API lỗi mạng.
3. Không dùng cache để vượt qua HTTP 403 từ server.
4. Dọn cache đáp án, snapshot và đánh dấu sau nộp thành công; không xóa cache lượt khác.
5. Dùng server_now để bù đồng hồ máy lệch một giờ; countdown từ 3 giây về 0 và nộp đúng một lần.

Backend test recovery xác nhận `server_now` có timezone.

## Kết quả cuối cùng

- Toàn bộ frontend: **57 passed**, 5 file; trong đó ExamRoom có **12 test**.
- Backend anti-cheat, exam engine, shuffle, grading và review: **92 passed, 1 skipped**.
- Production build TypeScript + Vite: **PASS**.
- Test bị bỏ qua: concurrency cần PostgreSQL; môi trường test hiện dùng SQLite.
- Cảnh báo React Router/Starlette deprecation không làm test thất bại.

Lệnh từ `frontend`:

```powershell
npm test
npm run build
```

Lệnh từ `backend`:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_anti_cheat.py tests/test_exam_engine.py tests/test_exam_shuffle.py tests/test_grading.py tests/test_review.py -q -p no:cacheprovider
```

## Giới hạn cần phân biệt với acceptance tự động

- Các test recovery dùng jsdom và unmount/remount; chưa thao tác F5 thực tế trong trình duyệt hoặc chạy E2E.
- Snapshot cho phép khôi phục dữ liệu nếu ứng dụng đã tải/chạy được. Dự án chưa có service worker/PWA để đảm bảo tải được HTML/JS và xác thực phiên mới khi F5 hoàn toàn offline. Không khẳng định hỗ trợ khởi động ứng dụng hoàn toàn offline.
- Đáp án chưa đồng bộ lên server trước deadline vẫn không được chấm nếu gửi sau hạn; quy tắc deadline backend không thay đổi.
- localStorage bị người dùng xóa, bị trình duyệt chặn hoặc hết dung lượng thì không thể bảo đảm recovery; giao diện hiển thị lỗi lưu khi ghi thất bại.
- Chưa commit/push các thay đổi bổ sung này.
