# Hướng dẫn sử dụng: ctree

`ctree` là một công cụ tạo cây thư mục thông minh, tương tự như lệnh `tree` trên Linux nhưng được tăng cường khả năng lọc. Nó cung cấp các tùy chọn lọc nâng cao thông qua các đối số dòng lệnh và file cấu hình, đồng thời tự động bỏ qua các file/thư mục không cần thiết (như `.venv`, `__pycache__`, và `.git`).

## Cách Sử Dụng

Lệnh để chạy công cụ này là `ctree`.

```sh
ctree [start_path] [options]
```

- `start_path`: Thư mục hoặc file để bắt đầu tạo cây. Mặc định là thư mục hiện tại (`.`).

## Tùy Chọn Dòng Lệnh (CLI Options)

- **`-L, --level <num>`**: Giới hạn độ sâu hiển thị của cây.
- **`-d, --all-dirs`**: Chỉ hiển thị thư mục cho toàn bộ cây.
- **`-D, --dirs-patterns <patterns>`**: Chỉ hiển thị thư mục con _bên trong_ các thư mục khớp với pattern (phân cách bởi dấu phẩy).
- **`-f, --full-view`**: Bỏ qua tất cả các bộ lọc (`.gitignore`, `ignore`, `prune`, `level`, `extensions`) và hiển thị toàn bộ cây.

### Tùy chọn Lọc

- **`-e, --extensions <exts>`**: Chỉ hiển thị các file có đuôi mở rộng được liệt kê (phân cách bởi dấu phẩy). Hỗ trợ các toán tử `+` (thêm) và `~` (bớt).
- **`-I, --ignore <patterns>`**: Thêm các pattern (giống `.gitignore`) để **ẩn hoàn toàn** các file/thư mục khớp. 
- **`-P, --prune <patterns>`**: Thêm các pattern thư mục để **cắt tỉa**. Thư mục sẽ hiển thị nhưng nội dung bên trong bị ẩn (`[...]`).
- **`-s, --show-submodules`**: Hiển thị nội dung của Git submodules (mặc định là ẩn).
- **`-N, --no-gitignore`**: Không tôn trọng các quy tắc từ file `.gitignore`.

### Tùy chọn Cấu hình

- **`-c, --config-project`**: Khởi tạo/cập nhật section `[tree]` trong `.project.toml`.
- **`-C, --config-local`**: Khởi tạo/cập nhật file `.tree.toml` cục bộ.

## File Cấu Hình

`ctree` tự động tải cấu hình từ `.tree.toml` (cục bộ) và `.project.toml` (toàn cục).

**Độ ưu tiên:** `Đối số CLI` > `.tree.toml` > `.project.toml` > `Mặc định`.

```toml
# Ví dụ: .tree.toml hoặc section [tree] trong .project.toml

# Giới hạn độ sâu hiển thị.
# level = 3

# Hiển thị nội dung của Git submodules.
show-submodules = false

# Có tôn trọng file .gitignore hay không (bị ghi đè bởi cờ -N).
use-gitignore = true

# Chỉ hiển thị các file có đuôi trong danh sách này.
# extensions = ["py", "md"]

# Danh sách các pattern để ẩn hoàn toàn.
ignore = ["*.tmp", ".env"]

# Danh sách các pattern thư mục để "cắt tỉa" (hiển thị thư mục, ẩn nội dung).
prune = ["node_modules/", "vendor/"]

# Chế độ chỉ hiển thị thư mục.
# - "_ALL_": Chỉ hiển thị thư mục cho toàn bộ cây (tương đương cờ -d).
# - ["src", "libs"]: Chỉ hiển thị thư mục con bên trong `src` và `libs` (tương đương cờ -D).
# dirs-only = "_ALL_"
```

## Ví dụ

```sh
# 1. Hiển thị cây thư mục hiện tại với độ sâu tối đa là 2
ctree . -L 2

# 2. Hiển thị chỉ các file Python và Markdown, bỏ qua thư mục build
ctree . -e py,md -I build

# 3. Hiển thị toàn bộ cây, không lọc gì cả
ctree . -f

# 4. Khởi tạo file cấu hình cục bộ
ctree --config-local
```