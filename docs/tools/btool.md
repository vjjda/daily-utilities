# Hướng dẫn sử dụng: btool

`btool` (Bootstrap Tool) là một "meta-utility" (công cụ tạo công cụ) dùng để tự động khởi tạo toàn bộ cấu trúc file cần thiết cho một tool utility mới.

Nó có hai chế độ hoạt động chính:

1.  **Chế độ Khởi tạo (Initialization Mode):** Dùng để tạo file đặc tả `*.spec.toml` hoặc cập nhật cấu hình `[bootstrap]` trong file `pyproject.toml`.
2.  **Chế độ Chạy (Run Mode):** Dùng để đọc một file `*.spec.toml` và tự động tạo ra toàn bộ cấu trúc của một tool mới.

## Cách Sử Dụng

`btool` được thiết kế để chạy từ gốc của dự án.

**1. Chế độ Khởi tạo**

```sh
# Tạo một file spec mẫu
btool -s [đường_dẫn/tên_file.spec.toml]

# Khởi tạo/cập nhật cấu hình trong .project.toml
btool -c
```

**2. Chế độ Chạy**

```sh
# Tạo tool mới từ một file spec
btool <đường_dẫn/tên_file.spec.toml> [options]
```

## Tùy Chọn Dòng Lệnh (CLI Options)

Các tùy chọn được chia thành hai nhóm tương ứng với hai chế độ hoạt động.

### Tùy chọn Khởi tạo (Chạy riêng lẻ)

- **`-s, --init-spec [path]`**: Khởi tạo một file `.spec.toml` mới từ template.
  - Nếu không cung cấp `path`, sẽ tạo file `new_tool.spec.toml` ở thư mục hiện tại.
  - Nếu cung cấp `path` (ví dụ: `-s 'path/to/my_spec.toml'`), file sẽ được tạo ở đó.
- **`-c, --config-project`**: Khởi tạo hoặc cập nhật section `[bootstrap]` trong file `pyproject.toml` với các giá trị mặc định.

### Tùy chọn Chế độ Chạy (Mặc định)

- **`spec_file_path_str`**: (Đối số vị trí) Đường dẫn đến file `*.spec.toml` để định nghĩa tool mới. Bắt buộc cho chế độ này.
- **`-f, --force`**: Ghi đè (overwrite) các file và thư mục đã tồn tại nếu có. Nếu không có cờ này, `btool` sẽ dừng lại nếu phát hiện file/thư mục đích đã tồn tại.
- **`-i, --interface <typer|argparse>`**: Ghi đè lựa chọn thư viện CLI (`typer` hoặc `argparse`) được định nghĩa trong file `.spec.toml`.

## File Đặc Tả (`.spec.toml`)

Đây là file đầu vào quan trọng nhất cho **Chế độ Chạy**. `btool` đọc file này để biết _cách_ tạo ra tool mới.

```toml
# Ví dụ: my_tool.spec.toml

# Thông tin meta bắt buộc
[meta]
tool_name = "mytool"           # Tên sẽ dùng cho file wrapper (ví dụ: bin/mytool)
script_file = "my_tool.py"     # Tên file entrypoint (ví dụ: tools/my_tool.py)
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

## File Cấu Hình (`pyproject.toml`)

`btool` đọc section `[bootstrap]` trong file `pyproject.toml` của dự án để biết _nơi_ đặt các file được tạo ra. Bạn có thể dùng cờ `-c` để tự động tạo section này.

```toml
# Ví dụ: .project.toml

[bootstrap]
# Tên thư mục chứa các wrapper Zsh
bin_dir = "bin"
# Tên thư mục chứa các script entrypoint Python
scripts_dir = "tools"
# Tên thư mục chứa các module code logic
modules_dir = "modules"
# Tên thư mục chứa tài liệu
docs_dir = "docs/tools"
```

## Ví dụ

```sh
# 1. Tạo một file spec mẫu tên là 'newtool.spec.toml'
btool -s newtool.spec.toml

# 2. Tự động thêm cấu hình bootstrap vào file .project.toml
btool -c

# 3. Tạo một tool mới tên là 'newtool' từ file spec
btool newtool.spec.toml

# 4. Tạo tool mới, nhưng ghi đè các file cũ nếu chúng tồn tại
btool newtool.spec.toml -f

# 5. Tạo tool mới, ép buộc sử dụng 'argparse' bất kể file spec nói gì
btool newtool.spec.toml -i argparse
```