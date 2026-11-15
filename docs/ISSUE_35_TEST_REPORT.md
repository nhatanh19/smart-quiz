# Issue #35 — Anti-cheat: triển khai và kết quả kiểm thử

- Ngày: 14/11/2026 (Asia/Saigon).
- Nhánh: `feature/issue-35-browser-focus-monitor`.
- Nhánh được tạo trực tiếp từ `main` tại `689ba2b` (merge PR #38, Issue #34).
- Phạm vi: WBS 4.3.1 và 4.3.2; theo các quyết định lead đã chốt trong issue.
- Kết quả dưới đây là test chạy local, không phải CI hoặc kiểm thử trình duyệt thực tế.

## Hành vi đã triển khai

| Acceptance criteria | Thực hiện |
| --- | --- |
| Monitor trình duyệt và chặn thao tác | Hook `useAntiCheatMonitor` lắng nghe `visibilitychange`, `window.blur`, F12, phím mở DevTools phổ biến, copy/paste/cut và chuột phải. Chặn thao tác bằng `preventDefault`. |
| Tránh đếm trùng một lần rời màn hình | Gộp `blur`/`visibilitychange` trong 750ms, theo cả hai thứ tự sự kiện. Chỉ tính `visibilitychange` khi trạng thái là `hidden`. |
| Cảnh báo toàn màn hình | Modal cho hành vi có tính vi phạm, hiển thị số lần và ngưỡng do server xác nhận; cảnh báo nhẹ cho clipboard/chuột phải. |
| API ghi log thật | Thay HTTP 501 bằng transaction lưu `anti_cheat_logs` và cập nhật attempt. |
| Ngưỡng động | Đọc `exam.max_tab_violations`, khóa khi `violation_count >= max_tab_violations`. Mặc định 3: khóa ngay lần thứ 3. |
| Lưu đáp án và chấm khi khóa | Validate/upsert đáp án gửi kèm, set `LOCKED_VIOLATION` và `submitted_at`, flush, gọi `grade_attempt`, commit một lần. Lỗi validate/grading rollback toàn bộ. |
| Chuyển review | Khi server xác nhận trạng thái kết thúc, FE xóa cache đáp án của lượt thi và chuyển `/review/:attemptId`. Recovery API cũng dọn cache khi tải lại một lượt đã kết thúc. |

## Chính sách đếm

- `TAB_SWITCH`, `WINDOW_BLUR`, `DEVTOOLS_SHORTCUT`: ghi log và tăng `violation_count` một đơn vị.
- `COPY_PASTE_ATTEMPT`: ghi log, không tăng số lần. Bao gồm clipboard, Ctrl/Cmd+C/V/X và chuột phải.
- `metadata_info` luôn được lưu thành JSON object. `event_id` và `counted` được server gán, không tin giá trị tương ứng do client chèn trong metadata.
- Khóa dòng attempt để phối hợp các request vi phạm, autosave và submit.
- Các lần gửi lại cùng `event_id` của một attempt không tạo thêm log hoặc tăng số lần. Bài đã kết thúc trả trạng thái hiện tại, không chấm hoặc đếm thêm.
- Sự kiện đến sau deadline không nhận đáp án muộn; chấm đáp án đã lưu theo luồng hết hạn của #34 và trả `EXPIRED`.

## API contract

`POST /api/v1/exam-engine/attempts/{attempt_id}/log-violation`

Chỉ sinh viên sở hữu attempt được gọi; áp dụng kiểm tra Origin như submit. Response có `Cache-Control: no-store`.

```json
{
  "event_id": "d5f34367-2a09-452b-9c64-4cfc27e9ac7f",
  "event_type": "TAB_SWITCH",
  "metadata_info": {
    "client_ts": "2026-11-14T16:00:00.000Z",
    "visibility_state": "hidden",
    "source": "visibilitychange"
  },
  "answers": []
}
```

- `event_id`: UUID bắt buộc; giữ nguyên khi gửi lại cùng sự kiện.
- `event_type`: một trong bốn loại ở trên.
- `metadata_info`: object hoặc null, optional.
- `answers`: danh sách `AnswerInput` dùng option ID gốc theo K-01; optional, null hoặc danh sách tối đa 500 phần tử. Khi bỏ qua, dùng đáp án đã có trong DB khi chấm.
- Dữ liệu trong response envelope chung:

```json
{
  "status": "IN_PROGRESS",
  "violation_count": 1,
  "max_tab_violations": 3
}
```

`GET /attempts/{attempt_id}` bổ sung `violation_count` và `max_tab_violations` để khôi phục bộ đếm theo server khi reload.

## Kết quả kiểm thử

| Lệnh / nhóm | Kết quả |
| --- | --- |
| Toàn bộ frontend: `npm test` | **52 passed**, 5 file |
| Monitor: `useAntiCheatMonitor.test.tsx` (nằm trong 52 test) | **15 passed** |
| Phòng thi: `ExamRoom.test.tsx` (nằm trong 52 test) | **7 passed**, gồm 2 test tích hợp #35 |
| Backend: anti-cheat + exam engine + shuffle + grading + review | **92 passed, 1 skipped** |
| Backend: `test_anti_cheat.py` (nằm trong 92 test) | **15 passed** |
| `npm run build` | **PASS**, TypeScript và Vite |
| `git diff --check` trước khi viết báo cáo | **PASS**, chỉ có cảnh báo chuyển LF/CRLF |

Không cộng các nhóm con thêm lần nữa. Tổng hai nhóm chính: **144 passed, 1 skipped**.

### Test #35 bao phủ

- Frontend: gộp focus events theo hai thứ tự; sự kiện sau 750ms là lượt riêng; không tính tab trở về visible; chặn clipboard/chuột phải/phím tắt; không đếm key repeat; cảnh báo nhẹ so với modal; retry cùng event ID; dừng sau trạng thái kết thúc; tháo listeners khi unmount; không bật ngoài lượt đang làm.
- Tích hợp FE: modal hiển thị số lần/ngưỡng từ server; lockout gửi option ID hiện có, xóa cache và mở review.
- Backend: phân loại bốn loại sự kiện; metadata do server quản lý; ngưỡng cấu hình và mặc định; gửi lặp; upsert đáp án cũ và tạo đáp án mới; chấm điểm; submitted_at; commit một lần; rollback log/count/answers/status khi validate hoặc grading lỗi; payload không hợp lệ; xác thực, quyền sở hữu và Origin; xử lý sự kiện muộn.
- Test bị bỏ qua: `test_concurrent_start_postgres`, yêu cầu PostgreSQL; lần chạy này dùng SQLite. Chưa xác minh concurrency thực tế của #35 trên PostgreSQL.

## Lệnh tái hiện

Từ thư mục `frontend`:

```powershell
npm test
npm run build
```

Từ thư mục `backend`:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_anti_cheat.py tests/test_exam_engine.py tests/test_exam_shuffle.py tests/test_grading.py tests/test_review.py -q -p no:cacheprovider
```

Frontend test/build cần chạy ngoài sandbox trong phiên này vì esbuild bị chặn tạo tiến trình. Có warning React Router future flags và Starlette/httpx/cookie deprecation, không làm các test thất bại.

## Giới hạn kiểm chứng

- Chưa chạy kiểm thử thủ công trên trình duyệt, E2E hoặc kiểm thử khóa dòng trên PostgreSQL. FE test sử dụng jsdom và mock API; backend test dùng SQLite.
- Retry sự kiện lỗi mạng/5xx sau 3 giây và khi có sự kiện online, giữ nguyên event ID và thứ tự gửi. Hàng đợi chỉ nằm trong bộ nhớ; reload/đóng trang trước khi gửi thành công có thể mất sự kiện chưa gửi. FE hiển thị thông báo yêu cầu giữ trang mở khi đồng bộ thất bại.
- Chỉ số trong modal là số lần server đã xác nhận, không phải số lần FE tự dự đoán khi mất mạng.
- Kiểm soát phía trình duyệt chỉ chặn các sự kiện/phím tắt mà trang nhận được; không bảo đảm chặn DevTools mở từ menu trình duyệt hoặc các cách vượt qua JavaScript của client.
- Theo yêu cầu tiếp theo, đã bổ sung đánh dấu và snapshot recovery cho checklist #34 trên cùng nhánh. Kết quả mới: frontend 57 passed, backend 92 passed/1 skipped, build PASS. Chi tiết và giới hạn khởi động hoàn toàn offline: [ISSUE_34_CHECKLIST_VERIFICATION.md](ISSUE_34_CHECKLIST_VERIFICATION.md). Các con số ở bảng phía trên ghi nhận lần kiểm thử #35 ban đầu.
