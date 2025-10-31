# Hướng dẫn sử dụng: cpath

`cpath` (Check Path) là công cụ để kiểm tra và tùy chọn sửa các comment đường dẫn (ví dụ: `# Path: ...`) ở đầu các file mã nguồn. Nó đảm bảo các comment này khớp chính xác với vị trí tương đối của file trong dự án.

Công cụ này hỗ trợ nhiều kiểu comment khác nhau (như `#`, `//`, `/* */`) cho các ngôn ngữ lập trình phổ biến.

## Khởi Động Nhanh

Cách dễ nhất để bắt đầu là khởi tạo một file cấu hình trong dự án của bạn:

```sh
# 1. Khởi tạo file cấu hình cục bộ (.cpath.toml)
# Tạo/cập nhật file .cpath.toml và mở nó.
cpath --config-local

# 2. Hoặc, cập nhật file cấu hình toàn dự án (.project.toml)
# Cập nhật phần [cpath] trong file .project.toml.
cpath --config-project
```

## Cách Sử Dụng

```sh
cpath [target_paths...] [options]
```

- `target_paths`: Một hoặc nhiều đường dẫn (file hoặc thư mục) để quét. Mặc định là thư mục hiện tại (`.`).

## Tùy Chọn Dòng Lệnh (CLI Options)

- **`-h, --help`**: Hiển thị trợ giúp.
- **`-r, --root <path>`**: Chỉ định tường minh đường dẫn gốc (Project Root) để tính toán path tương đối. Mặc định: tự động tìm gốc Git từ các đường dẫn đầu vào.
- **`-e, --extensions <exts>`**: Danh sách các đuôi file cần quét (phân cách bởi dấu phẩy).
  - Hỗ trợ các toán tử:
    - `py,js` (không có toán tử đầu): Ghi đè hoàn toàn danh sách mặc định/config.
    - `+ts,md`: Thêm `ts` và `md` vào danh sách hiện có.
    - `~py`: Loại bỏ `py` khỏi danh sách hiện có.
- **`-I, --ignore <patterns>`**: Thêm các pattern (giống `.gitignore`, phân cách bởi dấu phẩy) vào danh sách **bỏ qua**. Các pattern này được **nối** vào danh sách từ config/default.
- **`-d, --dry-run`**: Chỉ chạy ở chế độ kiểm tra (dry-run) và báo cáo các file cần sửa, không thực hiện ghi file.
- **`-f, --force`**: Tự động sửa file mà không hỏi xác nhận (chỉ áp dụng ở chế độ "fix", tức là khi không có `-d`).
- **`-c, --config-project`**: Khởi tạo hoặc cập nhật section `[cpath]` trong `.project.toml`.
- **`-C, --config-local`**: Khởi tạo hoặc cập nhật file `.cpath.toml` cục bộ.

---

## File Cấu Hình

Đối với các cài đặt lâu dài, `cpath` tự động tải cấu hình từ các file `.toml` sau:

- `.cpath.toml`: File cấu hình cục bộ.
- `.project.toml`: File cấu hình dự phòng toàn dự án (sử dụng section `[cpath]`).

### Độ Ưu Tiên Cấu Hình

1. **Đối Số Dòng Lệnh (CLI Arguments)** (Ưu tiên cao nhất)
2. **File `.cpath.toml`** (Cấu hình cục bộ)
3. **File `.project.toml` (Section `[cpath]`)** (Cấu hình toàn dự án)
4. **Cài Đặt Mặc Định Của Script** (Ưu tiên thấp nhất)

### Các tùy chọn cấu hình trong file `.toml`

```toml
# Ví dụ: .cpath.toml hoặc section [cpath] trong .project.toml

# extensions (List[str]): Danh sách các đuôi file mặc định cần BAO GỒM.
# Mặc định: ["py", "pyi", "js", "ts", ...]
extensions = ["py", "js", "zsh", "sh"]

# ignore (List[str]): Danh sách các pattern mặc định cần BỎ QUA.
# Hỗ trợ cú pháp giống .gitignore.
# Mặc định: [".venv", "__pycache__", ".git", ...]
ignore = ["*.log", "**/temp/*"]
```
