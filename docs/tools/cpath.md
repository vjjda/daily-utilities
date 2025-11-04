# Hướng dẫn sử dụng: cpath

`cpath` (Check Path) là công cụ để kiểm tra và tùy chọn sửa các comment đường dẫn (ví dụ: `# Path: ...`) ở đầu các file mã nguồn. Nó đảm bảo các comment này khớp chính xác với vị trí tương đối của file trong dự án.

Công cụ này hỗ trợ nhiều kiểu comment khác nhau (như `#`, `//`, `/* */`) cho các ngôn ngữ lập trình phổ biến.

## Cách Sử Dụng

```sh
cpath [start_paths...] [options]
```

- `start_paths`: Một hoặc nhiều đường dẫn (file hoặc thư mục) để quét. Mặc định là thư mục hiện tại (`.`).

Chế độ hoạt động mặc định là **sửa lỗi (fix mode)**. Công cụ sẽ tìm các file có path comment sai và tự động sửa chúng sau khi có xác nhận của bạn.

## Tùy Chọn Dòng Lệnh (CLI Options)

### Tùy chọn Kiểm tra & Sửa lỗi

- **`-d, --dry-run`**: Chuyển sang chế độ **chỉ kiểm tra (dry-run)**. Công cụ sẽ chỉ báo cáo các file cần sửa mà không thực hiện bất kỳ thay đổi nào trên đĩa.
- **`-f, --force`**: Tự động sửa tất cả các file mà không cần hỏi xác nhận cho từng file. Chỉ có tác dụng ở chế độ sửa lỗi (khi không dùng `-d`).
- **`-g, --git-commit`**: Sau khi sửa lỗi thành công, tự động tạo một commit Git với các thay đổi đó.
- **`-r, --root <path>`**: Chỉ định tường minh đường dẫn gốc của dự án (Project Root) để tính toán path tương đối. Mặc định, công cụ sẽ tự động tìm thư mục gốc chứa `.git`.
- **`-e, --extensions <exts>`**: Ghi đè hoặc chỉnh sửa danh sách các đuôi file cần quét (phân cách bởi dấu phẩy).
  - `py,js`: Ghi đè danh sách mặc định.
  - `+ts,md`: Thêm `ts` và `md` vào danh sách hiện tại.
  - `~py`: Loại bỏ `py` khỏi danh sách hiện tại.
- **`-I, --ignore <patterns>`**: Thêm các pattern (giống `.gitignore`, phân cách bởi dấu phẩy) vào danh sách **bỏ qua**. Các pattern này được **nối** vào danh sách có sẵn từ file cấu hình.

### Tùy chọn Khởi tạo Cấu hình

- **`-c, --config-project`**: Khởi tạo hoặc cập nhật section `[cpath]` trong file cấu hình toàn dự án (`pyproject.toml`).
- **`-C, --config-local`**: Khởi tạo hoặc cập nhật file cấu hình cục bộ (`.cpath.toml`) trong thư mục hiện tại.

## File Cấu Hình

`cpath` có thể được cấu hình thông qua các file `.toml` để bạn không phải gõ lại các tùy chọn thường dùng.

- `.cpath.toml`: File cấu hình cục bộ.
- ``pyproject.toml`: File cấu hình dự phòng toàn dự án (sử dụng section `[cpath]`).

**Độ ưu tiên:** `Đối số CLI` > `.cpath.toml` > `pyproject.toml` > `Mặc định`.

```toml
# Ví dụ: .cpath.toml hoặc section [cpath] trong .project.toml

# Danh sách các đuôi file mặc định cần quét.
# Mặc định: ["py", "pyi", "js", "ts", ...]
extensions = ["py", "js", "zsh", "sh"]

# Danh sách các pattern cần bỏ qua.
# Hỗ trợ cú pháp giống .gitignore.
# Mặc định: [".venv", "__pycache__", ".git", ...]
ignore = ["*.log", "**/temp/*"]
```

## Ví dụ

```sh
# 1. Chỉ kiểm tra tất cả các file trong thư mục hiện tại
cpath --dry-run

# 2. Sửa tất cả các file .py và .js, sau đó tự động commit
cpath -e py,js --git-commit

# 3. Sửa tất cả các file trong thư mục 'src', bỏ qua thư mục 'src/legacy'
cpath src -I 'src/legacy/*'

# 4. Khởi tạo file cấu hình cục bộ để tùy chỉnh lâu dài
cpath --config-local
```