# Hướng dẫn sử dụng: sgen

`sgen` (Stubgen) là công cụ dùng để phân tích các file `__init__.py` và tự động tạo ra các file stub (`.pyi`) tương ứng. 

Mục đích chính là để cung cấp thông tin type hinting chính xác cho các công cụ kiểm tra kiểu (như Mypy, Pyright) và hỗ trợ tự động hoàn thành (autocomplete) trong IDE. Nó đặc biệt hữu ích cho các `__init__.py` đóng vai trò là "cổng giao tiếp" (gateway/facade), nơi tập trung các import để định nghĩa API công khai của một module.

Công cụ này sẽ đọc các câu lệnh `import` và biến `__all__` trong file `__init__.py` để tạo ra một file `.pyi` chỉ chứa các định nghĩa cần thiết.

## Cách Sử Dụng

```sh
sgen [target_paths...] [options]
```

- `target_paths`: Một hoặc nhiều đường dẫn đến file `__init__.py` hoặc thư mục chứa chúng. Mặc định là thư mục hiện tại (`.`).

## Tùy Chọn Dòng Lệnh (CLI Options)

### Tùy chọn Tạo Stub

- **`-f, --force`**: Ghi đè file `.pyi` nếu đã tồn tại mà không cần hỏi xác nhận.
- **`-g, --git-commit`**: Sau khi tạo/cập nhật file stub thành công, tự động tạo một commit Git với các thay đổi đó.
- **`-I, --ignore <patterns>`**: Thêm các pattern (giống `.gitignore`, phân cách bởi dấu phẩy) vào danh sách **bỏ qua**.

### Tùy chọn Khởi tạo Cấu hình

- **`-c, --config-project`**: Khởi tạo hoặc cập nhật section `[sgen]` trong file cấu hình toàn dự án (`pyproject.toml`).
- **`-C, --config-local`**: Khởi tạo hoặc cập nhật file cấu hình cục bộ (`.sgen.toml`) trong thư mục hiện tại.

## File Cấu Hình

`sgen` có thể được cấu hình thông qua các file `.toml` để lưu lại các thiết lập thường dùng.

- `.sgen.toml`: File cấu hình cục bộ.
- ``pyproject.toml`: File cấu hình dự phòng toàn dự án (sử dụng section `[sgen]`).

**Độ ưu tiên:** `Đối số CLI` > `.sgen.toml` > `pyproject.toml` > `Mặc định`.

```toml
# Ví dụ: .sgen.toml hoặc section [sgen] trong .project.toml

# Danh sách các pattern cần bỏ qua khi quét.
# Hỗ trợ cú pháp giống .gitignore.
# Mặc định: [".venv", "__pycache__", ".git", ...]
ignore = ["tests/", "docs/"]
```

## Ví dụ

```sh
# 1. Quét toàn bộ dự án và tạo/cập nhật tất cả các file stub .pyi (sẽ hỏi trước khi ghi đè)
sgen .

# 2. Quét thư mục 'modules/utils' và tự động ghi đè các file stub đã có
sgen modules/utils -f

# 3. Quét toàn bộ dự án và tự động commit các thay đổi
sgen . -g

# 4. Khởi tạo file cấu hình cục bộ để tùy chỉnh
sgen --config-local
```