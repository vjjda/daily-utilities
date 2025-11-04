# Hướng dẫn sử dụng: ndoc

`ndoc` (No Docstring) là công cụ dùng để quét và tự động loại bỏ docstrings (và tùy chọn cả comments) khỏi các file mã nguồn. Nó rất hữu ích khi bạn muốn tạo ra một phiên bản "sạch" của code, ví dụ như để giảm kích thước file hoặc chuẩn bị code cho một số công cụ phân tích nhất định.

## Cách Sử Dụng

```sh
ndoc [start_paths...] [options]
```

- `start_paths`: Một hoặc nhiều đường dẫn (file hoặc thư mục) để quét. Mặc định là thư mục hiện tại (`.`).

Chế độ hoạt động mặc định là **sửa lỗi (fix mode)**, chỉ xóa docstrings. Công cụ sẽ tìm và sửa các file sau khi có xác nhận của bạn.

## Tùy Chọn Dòng Lệnh (CLI Options)

### Tùy chọn Xóa Docstring & Comment

- **`-a, --all-clean`**: Bật chế độ **làm sạch toàn bộ**. Ngoài docstrings, chế độ này sẽ loại bỏ cả tất cả các comment (`#`) khỏi file (ngoại trừ shebang `#!` ở đầu file).
- **`-b, --beautify`**: Tự động **định dạng (format)** lại code (ví dụ: dùng Black cho Python) *sau khi* đã xóa docstring/comment. Giúp code trông gọn gàng hơn sau khi chỉnh sửa.
- **`-d, --dry-run`**: Chuyển sang chế độ **chỉ kiểm tra (dry-run)**. Công cụ sẽ chỉ báo cáo các file cần sửa mà không thực hiện bất kỳ thay đổi nào.
- **`-f, --force`**: Tự động sửa tất cả các file mà không cần hỏi xác nhận. Chỉ có tác dụng ở chế độ sửa lỗi (khi không dùng `-d`).
- **`-g, --git-commit`**: Sau khi sửa lỗi thành công, tự động tạo một commit Git với các thay đổi đó.
- **`-w, --stepwise`**: Bật **chế độ gia tăng (stepwise mode)**. `ndoc` chỉ quét các file đã thay đổi kể từ lần chạy cuối cùng có cùng cài đặt. Giúp tăng tốc độ đáng kể cho các lần chạy sau.
- **`-e, --extensions <exts>`**: Ghi đè hoặc chỉnh sửa danh sách các đuôi file cần quét.
- **`-I, --ignore <patterns>`**: Thêm các pattern (giống `.gitignore`) vào danh sách **bỏ qua**.

### Tùy chọn Khởi tạo Cấu hình

- **`-c, --config-project`**: Khởi tạo hoặc cập nhật section `[no_doc]` trong file `pyproject.toml`.
- **`-C, --config-local`**: Khởi tạo hoặc cập nhật file cấu hình cục bộ (`.ndoc.toml`).

## File Cấu Hình

`ndoc` có thể được cấu hình thông qua các file `.toml`.

- `.ndoc.toml`: File cấu hình cục bộ.
- ``pyproject.toml`: File cấu hình dự phòng toàn dự án (section `[no_doc]`).

**Độ ưu tiên:** `Đối số CLI` > `.ndoc.toml` > `pyproject.toml` > `Mặc định`.

```toml
# Ví dụ: .ndoc.toml hoặc section [no_doc] trong .project.toml

# Danh sách các đuôi file mặc định cần quét.
extensions = ["py"]

# Danh sách các pattern cần bỏ qua.
ignore = ["__pycache__/", "*.tmp"]

# Danh sách các đuôi file sẽ được định dạng khi dùng cờ -b/--beautify
format_extensions = ["py"]
```

## Ví dụ

```sh
# 1. Chỉ kiểm tra (dry-run) xem có file Python nào chứa docstring không
ndoc -e py --dry-run

# 2. Xóa tất cả docstring VÀ comment khỏi các file đã thay đổi, sau đó commit
ndoc -a -w -g

# 3. Xóa docstring và định dạng lại code trong thư mục 'src'
ndoc src -b

# 4. Khởi tạo file cấu hình cục bộ để tùy chỉnh
ndoc --config-local
```