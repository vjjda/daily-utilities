# Hướng dẫn sử dụng: tree

`tree` là một công cụ tạo cây thư mục thông minh, tương tự như lệnh `tree` trên Linux nhưng được tăng cường khả năng lọc. Nó cung cấp các tùy chọn lọc nâng cao thông qua các đối số dòng lệnh và file cấu hình, đồng thời tự động bỏ qua các file/thư mục không cần thiết (như `.venv`, `__pycache__`, và `.git`).

## Khởi Động Nhanh

Cách dễ nhất để bắt đầu là khởi tạo một file cấu hình trong dự án của bạn:

```sh
# 1. Khởi tạo file cấu hình cục bộ (.tree.toml)
# Tạo/cập nhật file .tree.toml và mở nó.
tree --config-local

# 2. Hoặc, cập nhật file cấu hình toàn dự án (.project.toml)
# Cập nhật phần [tree] trong file .project.toml.
tree --config-project
```

## Cách Sử Dụng

```sh
tree [start_path] [options]
```

- `start_path`: Thư mục hoặc file để bắt đầu tạo cây. Mặc định là thư mục hiện tại (`.`).

## Tùy Chọn Dòng Lệnh (CLI Options)

- **`-h, --help`**: Hiển thị trợ giúp.
- **`-L, --level <num>`**: Giới hạn độ sâu hiển thị của cây.
- **`-e, --extensions <exts>`**: **(BỊ THIẾU TRONG DOC CŨ)** Chỉ hiển thị các file có đuôi mở rộng được liệt kê (phân cách bởi dấu phẩy).
  - Hỗ trợ các toán tử:
    - `py,md` (không có toán tử đầu): Ghi đè hoàn toàn danh sách mặc định/config (vốn là `None` - hiển thị tất cả).
    - `+ts,js`: Thêm `ts` và `js` vào danh sách hiện có.
    - `~yaml,yml`: Loại bỏ `yaml` và `yml` khỏi danh sách hiện có.
- **`-I, --ignore <patterns>`**: Thêm các pattern (giống `.gitignore`, phân cách bởi dấu phẩy) vào danh sách **ẩn hoàn toàn**. Các pattern này được **nối** vào danh sách từ config/default .
- **`-P, --prune <patterns>`**: Thêm các pattern thư mục (giống `.gitignore`, phân cách bởi dấu phẩy) để **cắt tỉa**. Thư mục sẽ hiển thị nhưng nội dung bên trong bị ẩn (`[...]`). Các pattern này được **nối** vào danh sách từ config/default .
- **`-d, --all-dirs`**: Chỉ hiển thị thư mục cho toàn bộ cây.
- **`-D, --dirs-patterns <patterns>`**: Chỉ hiển thị thư mục con _bên trong_ các thư mục khớp với pattern (phân cách bởi dấu phẩy).
- **`-s, --show-submodules`**: Hiển thị nội dung của Git submodules (mặc định là ẩn).
- **`-N, --no-gitignore`**: Không tôn trọng các quy tắc từ file `.gitignore` (mặc định là có nếu là kho Git).
- **`-f, --full-view`**: Bỏ qua tất cả các bộ lọc (`.gitignore`, `ignore`, `prune`, `level`, `extensions`) và hiển thị tất cả file.
- **`-c, --config-project`**: Khởi tạo hoặc cập nhật section `[tree]` trong `.project.toml`.
- **`-C, --config-local`**: Khởi tạo hoặc cập nhật file `.tree.toml` cục bộ.

---

## File Cấu Hình

`tree` tự động tải cấu hình từ các file `.toml` sau:

- `.tree.toml`: File cấu hình cục bộ.
- `.project.toml`: File cấu hình dự phòng toàn dự án (sử dụng section `[tree]`).

### Độ Ưu Tiên Cấu Hình

1. **Đối Số Dòng Lệnh (CLI Arguments)** (Ưu tiên cao nhất)
2. **File `.tree.toml`**
3. **File `.project.toml` (Section `[tree]`)**
4. **Cài Đặt Mặc Định Của Script** (Ưu tiên thấp nhất)

### Các tùy chọn cấu hình trong file `.toml`

```toml
# Ví dụ: .tree.toml hoặc section [tree] trong .project.toml

[tree]

# level (Optional[int]): Giới hạn độ sâu hiển thị.
# Mặc định: không giới hạn (None)
# level = 3

# show-submodules (bool): Hiển thị nội dung của Git submodules.
# Mặc định: false (ẩn submodules)
show-submodules = false

# use-gitignore (bool): Có tôn trọng file .gitignore hay không.
# Mặc định: true (luôn tôn trọng nếu là kho Git)
use-gitignore = true

# ignore (List[str]): Danh sách các pattern (giống .gitignore) để ẩn hoàn toàn.
# Các pattern này sẽ được NỐI VÀO danh sách mặc định của script.
# Mặc định (script): [".venv", "__pycache__", ".git", ...]
ignore = ["*.tmp", ".env"]

# prune (List[str]): Danh sách các pattern thư mục để "cắt tỉa" ([...]).
# Các pattern này sẽ được NỐI VÀO danh sách mặc định của script.
# Mặc định (script): ["dist", "build"]
prune = ["node_modules/", "vendor/"]

# dirs-only (Union[str, List[str], None]): Chế độ chỉ hiển thị thư mục.
# - "_ALL_": Chỉ hiển thị thư mục cho toàn bộ cây (tương đương cờ -d).
# - ["pattern1", "pattern2/"]: Chỉ hiển thị thư mục con BÊN TRONG các thư mục khớp pattern.
# Mặc định: [] (hiển thị cả file và thư mục)
# dirs-only = "_ALL_"

# extensions (Optional[List[str]]): Chỉ hiển thị các file có đuôi trong danh sách này.
# Ghi đè hoàn toàn danh sách mặc định (là None - hiển thị tất cả).
# Bị ảnh hưởng bởi cờ -e (với logic +/~/overwrite).
# extensions = ["py", "md"]
```
