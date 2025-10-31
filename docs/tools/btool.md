# Hướng dẫn sử dụng: btool

`btool` (Bootstrap Tool) là một "meta-utility" (công cụ tạo công cụ) dùng để tự động khởi tạo toàn bộ cấu trúc file cần thiết cho một tool utility mới dựa trên một file đặc tả (`.spec.toml`).

Nó sẽ tự động tạo ra:

- File script entrypoint (trong `scripts/`)
- File wrapper Zsh (trong `bin/`)
- Cấu trúc module đầy đủ (trong `modules/ten_module/`)
- File tài liệu Markdown (trong `docs/tools/`)

## Cách Sử Dụng

`btool` được thiết kế để chạy từ gốc của dự án.

```sh
btool <spec_file_path> [options]
```

- `spec_file_path`: (Bắt buộc) Đường dẫn đến file `.spec.toml` định nghĩa tool mới của bạn (ví dụ: `docs/drafts/my_tool.spec.toml`).

## Tùy Chọn Dòng Lệnh (CLI Options)

- **`-h, --help`**: Hiển thị trợ giúp.
- **`-f, --force`**: Ghi đè (overwrite) các file và thư mục đã tồn tại nếu có. Nếu không có cờ này, `btool` sẽ dừng lại nếu phát hiện file/thư mục đích đã tồn tại .
- **`-i, --interface <typer|argparse>`**: Ghi đè (overwrite) lựa chọn thư viện CLI (ví dụ: `typer` hoặc `argparse`) được định nghĩa trong file `.spec.toml`.

## File Đặc Tả (`.spec.toml`)

Đây là file đầu vào quan trọng nhất. `btool` đọc file này để biết _cách_ tạo ra tool mới.

```toml
# Ví dụ: my_tool.spec.toml

# Thông tin meta bắt buộc
[meta]
tool_name = "mytool"           # Tên sẽ dùng cho file wrapper (ví dụ: bin/mytool)
script_file = "my_tool.py"     # Tên file entrypoint (ví dụ: scripts/my_tool.py)
module_name = "my_tool"        # Tên thư mục module (ví dụ: modules/my_tool)
logger_name = "MyTool"         # Tên dùng cho logger

# (Tùy chọn) Cấu hình tài liệu
[docs]
enabled = true
short_description = "Mô tả ngắn gọn về MyTool."

# (Tùy chọn) Cấu hình CLI (Typer hoặc Argparse)
[cli]
interface = "typer" # "typer" hoặc "argparse"

[cli.help]
description = "Mô tả đầy đủ cho phần --help của tool."
epilog = "Văn bản hiển thị ở cuối phần --help."

# (Tùy chọn) Định nghĩa các tham số dòng lệnh
[[cli.args]]
name = "level"
short = "-L"
type = "int"
default = 3
help = "Giới hạn độ sâu hiển thị."

[[cli.args]]
name = "all_dirs"
short = "-d"
type = "bool"
default = false
help = "Chỉ hiển thị thư mục."

[[cli.args]]
name = "start_path"
type = "Path"
is_argument = true # Đánh dấu đây là đối số vị trí (positional argument)
default = "."
help = "Đường dẫn bắt đầu quét."
```

## File Cấu Hình (`.project.toml`)

`btool` **không** có file cấu hình riêng (`.btool.toml`) và **không** hỗ trợ cờ `--config-local` hay `--config-project` như các tool khác.

Thay vào đó, nó đọc section `[bootstrap]` trong file `.project.toml` của dự án để biết _nơi_ đặt các file được tạo ra.

```toml
# Ví dụ: .project.toml

[bootstrap]
# Tên thư mục chứa các wrapper Zsh
bin_dir = "bin"
# Tên thư mục chứa các script entrypoint Python
scripts_dir = "scripts"
# Tên thư mục chứa các module code logic
modules_dir = "modules"
# Tên thư mục chứa tài liệu
docs_dir = "docs"
```

## Ví dụ

```sh
# 1. Tạo một tool mới tên là 'newtool' từ file spec
btool docs/drafts/newtool.spec.toml

# 2. Tạo tool mới, nhưng ghi đè các file cũ nếu chúng tồn tại
btool docs/drafts/newtool.spec.toml -f

# 3. Tạo tool mới, ép buộc sử dụng 'argparse' bất kể file spec nói gì
btool docs/drafts/newtool.spec.toml -i argparse
```
