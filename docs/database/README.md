# 🗄️ DATABASE ARTIFACTS & SƠ ĐỒ ERD

Thư mục này chứa tài liệu thiết kế CSDL phục vụ cho **Issue #2: [Database] Design Relational Schema (ERD) & Database Migrations**.

---

## 📌 Danh mục tài liệu

1. **[ERD.md](./ERD.md)**: Sơ đồ thực thể liên kết (Mermaid ERD), ma trận khóa ngoại, 5 kiểu enum và các ràng buộc đặc biệt.
2. **[Tài liệu hướng dẫn tổng quan (`docs/DATABASE_GUIDE.md`)](../DATABASE_GUIDE.md)**: Bàn giao chi tiết cho 4 Dev, giải thích 8 bảng, 6 cấu trúc JSONB và cheatsheet SQLAlchemy 2.0.
3. **[Script SQL DDL (`database/schema.sql`)](../../database/schema.sql)**: File SQL thuần tạo toàn bộ 8 bảng và 5 enum trên PostgreSQL/Supabase.
4. **[Script Seed Data (`database/seed.sql`)](../../database/seed.sql)**: File SQL thuần nạp tài khoản test và 10 câu hỏi mẫu.
