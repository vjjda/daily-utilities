# Hướng dẫn sử dụng: sgen

`sgen` (Stubgen) là công cụ dùng để phân tích các file `__init__.py` "gateway" (các file thực hiện import động) và tự động tạo ra các file stub (`.pyi`) tương ứng.

Mục đích là để cung cấp thông tin type hinting chính xác cho các công cụ kiểm tra kiểu (như Mypy, Pyright) và hỗ trợ tự động hoàn thành (autocomplete) trong IDE, vốn không thể hiểu được cấu trúc module được tạo ra một cách tự động lúc runtime.

## Khởi Động Nhanh

Cách dễ nhất để bắt đầu là khởi tạo một file cấu hình trong dự án của bạn:

```sh
# 1. Khởi tạo file cấu hình cục bộ (.sgen.toml)
# Tạo/cập nhật file .sgen.toml và mở nó.
sgen --config-local

# 2. Hoặc, cập nhật file cấu hình toàn dự án (.project.toml)
# Cập nhật phần [sgen] trong file .project.toml.
sgen --config-project
```

## Cách Sử Dụng

```sh
sgen [target_paths...] [options]
```

- `target_paths`: Một hoặc nhiều đường dẫn (file `__init__.py` hoặc thư mục) để quét. Mặc định là thư mục hiện tại (`.`).

## Tùy Chọn Dòng Lệnh (CLI Options)

- **`-h, --help`**: Hiển thị trợ giúp.
- **`-f, --force`**: Ghi đè file `.pyi` nếu đã tồn tại mà không cần hỏi xác nhận.
- **`-I, --ignore <patterns>`**: Thêm các pattern (giống `.gitignore`, phân cách bởi dấu phẩy) vào danh sách **bỏ qua**. Các pattern này được **nối** vào danh sách từ config/default.
- **`-i, --include <patterns>`**: Bộ lọc dương. Thêm các pattern (giống `.gitignore`, phân cách bởi dấu phẩy) vào danh sách **giữ lại**.
  - Nếu được cung cấp, **CHỈ** các file `__init__.py` khớp với pattern này MỚI được xử lý. 
  - Các pattern này được **nối** vào danh sách từ config/default (nếu có).
- **`-c, --config-project`**: Khởi tạo hoặc cập nhật section `[sgen]` trong `.project.toml`.
- **`-C, --config-local`**: Khởi tạo hoặc cập nhật file `.sgen.toml` cục bộ.

---

## File Cấu Hình

`sgen` tự động tải cấu hình từ các file `.toml` sau (theo thứ tự ưu tiên):

1. **Đối Số Dòng Lệnh (CLI Arguments)** (Cao nhất)
2. **File `.sgen.toml`** (Cấu hình cục bộ cho thư mục) 
3. **File `.project.toml`** (Section `[sgen]`) (Cấu hình toàn dự án) 
4. **Giá trị Mặc định của Script** (Thấp nhất)

### Các tùy chọn cấu hình trong file `.toml`

```toml
# Ví dụ: .sgen.toml hoặc section [sgen] trong .project.toml

# ignore (List[str]): Danh sách các pattern mặc định cần BỎ QUA.
# Hỗ trợ cú pháp giống .gitignore. Bị nối thêm bởi cờ -I.
# Mặc định: [".venv", "__pycache__", ...]
ignore = ["*.log", "**/temp/*"]

# include (List[str]): Danh sách các pattern mặc định cần GIỮ LẠI (lọc dương).
# Nếu được định nghĩa, CHỈ các file khớp mới được xử lý. Bị nối thêm bởi cờ -i.
# Mặc định: [] (không lọc)
# include = ["modules/core/**", "utils/cli/**"]

# === Tùy chọn nâng cao cho việc phân tích AST ===

# dynamic_import_indicators (List[str]):
# Các chuỗi văn bản dùng để nhận diện một file __init__.py là "gateway động".
# Mặc định: ["import_module", "globals()[name]", "globals()[name] = obj"]
dynamic_import_indicators = [
    "import_module",
    "globals()[name]",
]

# ast_module_list_name (str):
# Tên biến (list) trong file __init__.py chứa danh sách các module con cần import.
# Mặc định: "modules_to_export"
ast_module_list_name = "modules_to_export"

# ast_all_list_name (str):
# Tên biến (list) trong các file module con (ví dụ: tree_core.py)
# mà 'sgen' sẽ đọc để tìm các symbols cần export.
# Mặc định: "__all__"
ast_all_list_name = "__all__"
```

---

## Ví dụ

```sh
# 1. Quét toàn bộ dự án và tạo/cập nhật tất cả stub .pyi (có hỏi)
sgen .

# 2. Chỉ quét thư mục 'modules/utils' và tự động ghi đè
sgen modules/utils -f

# 3. Quét toàn bộ dự án, nhưng CHỈ xử lý các gateway trong 'modules/core'
sgen . -i "modules/core/**"

# 4. Quét toàn bộ, bỏ qua thư mục 'tests' (ngoài các ignore mặc định)
sgen . -I "tests/"
```
