# 🗄️ HƯỚNG DẪN IMPORT CƠ SỞ DỮ LIỆU BẰNG FILE .SQL

Thư mục này chứa toàn bộ các script SQL thuần (Pure SQL DDL & DML) để bạn có thể import trực tiếp vào bất kỳ PostgreSQL Server nào (PostgreSQL Local, Docker, pgAdmin, DBeaver, Supabase, Neon, AWS RDS, GCP Cloud SQL, Render, Railway, v.v.) mà không bắt buộc phải chạy qua Python/Alembic.

---

## 📂 Danh mục File SQL

| Tên File | Chức năng | Chi tiết nội dung |
| :--- | :--- | :--- |
| **`schema.sql`** | **Khởi tạo toàn bộ CSDL** | Tạo extension `pgcrypto`, 6 kiểu Enum PostgreSQL native, 9 bảng thực thể, toàn bộ khóa chính UUID, khóa ngoại, ràng buộc `CHECK`, `DEFERRABLE`, chỉ mục tối ưu, và ghi chú `COMMENT ON TABLE/COLUMN`. |
| **`seed.sql`** | **Nạp dữ liệu mẫu ban đầu** | Nạp 3 tài khoản mẫu (Admin, Instructor, Student với password `SmartQuiz@123`), 1 chuyên đề Quản trị dự án, 3 câu hỏi mẫu (Bloom: Nhận biết, Thông hiểu, Vận dụng) và 1 đề thi mẫu `DEMO0001` gồm 3 câu hỏi. |

---

## 🚀 Cách 1: Import bằng dòng lệnh `psql` (Terminal / CMD / PowerShell)

Nếu bạn có PostgreSQL client trên máy:

```bash
# 1. Chạy file khởi tạo cấu trúc 9 bảng và 6 enum
psql -h <HOST> -p <PORT> -U <USER> -d <DATABASE_NAME> -f database/schema.sql

# 2. Nạp dữ liệu mẫu (demo data)
psql -h <HOST> -p <PORT> -U <USER> -d <DATABASE_NAME> -f database/seed.sql
```

**Ví dụ chạy trên máy cục bộ (localhost):**
```powershell
psql -h localhost -p 5432 -U postgres -d smart_quiz -f database/schema.sql
psql -h localhost -p 5432 -U postgres -d smart_quiz -f database/seed.sql
```

---

## 🖥️ Cách 2: Import bằng pgAdmin / DBeaver / Navicat

1. Mở phần mềm quản trị CSDL (pgAdmin 4, DBeaver hoặc DataGrip).
2. Kết nối tới PostgreSQL Server và chọn database của dự án (`smart_quiz`).
3. Mở công cụ **SQL Query Tool** (hoặc `Ctrl + E` / `F3`).
4. Mở file `database/schema.sql`, bấm **Execute / Run (F5)** để tạo toàn bộ bảng và enum.
5. Mở tiếp file `database/seed.sql`, bấm **Execute / Run (F5)** để nạp dữ liệu mẫu.

---

## ☁️ Cách 3: Import lên Supabase / Neon / Cloud Postgres

1. Đăng nhập vào Dashboard của Supabase / Neon.
2. Vào mục **SQL Editor**.
3. Copy toàn bộ nội dung trong file [`database/schema.sql`](./schema.sql), dán vào và bấm **RUN**.
4. Copy toàn bộ nội dung trong file [`database/seed.sql`](./seed.sql), dán vào và bấm **RUN**.

---

## 🔑 Thông tin tài khoản mẫu sau khi Seed

Mật khẩu đăng nhập mặc định cho tất cả tài khoản mẫu là: `SmartQuiz@123`

| Vai trò | Email | Quyền hạn |
| :--- | :--- | :--- |
| **Quản trị viên (ADMIN)** | `admin@smartquiz.edu.vn` | Quản trị toàn hệ thống |
| **Giảng viên (INSTRUCTOR)** | `instructor@smartquiz.edu.vn` | Tạo ngân hàng câu hỏi, tạo đề thi |
| **Sinh viên (STUDENT)** | `student@smartquiz.edu.vn` | Vào phòng thi thử nghiệm đề `DEMO0001` |
