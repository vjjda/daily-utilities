# Hướng dẫn sử dụng: zrap

`zrap` là một công cụ tiện ích ("meta-utility") dùng để "gói" (wrap) một script Python thành một file thực thi Zsh. File wrapper này sẽ tự động xử lý việc kích hoạt môi trường ảo (`.venv`) và thiết lập `PYTHONPATH`, cho phép bạn chạy script như một lệnh shell thông thường.

## Các Chế độ (Modes)

`zrap` cung cấp hai chế độ gói chính:

### 1. Mode `relative` (Mặc định)

- **Mục đích:** Tạo các file thực thi để sử dụng _bên trong_ dự án (ví dụ: `bin/ctree`).
- **Hành vi:** Wrapper sử dụng đường dẫn _tương đối_ (`../`) để tìm gốc dự án. Toàn bộ dự án có thể di chuyển được, nhưng file wrapper thì không.

### 2. Mode `absolute`

- **Mục đích:** Tạo các file thực thi "di động" để cài đặt ra bên ngoài dự án (ví dụ: vào `~/bin/`).
- **Hành vi:** Wrapper "đóng băng" (hard-code) **đường dẫn tuyệt đối** đến dự án. File wrapper có thể di chuyển được, nhưng dự án thì không.

## Cách Dùng (Usage)

```sh
zrap [script_path_arg] [options]
# hoặc
zrap -n <tool_name> [options]
```

### Tùy chọn Chính

- **`script_path_arg`**: Đường dẫn đến file Python cần wrap. Tùy chọn nếu bạn dùng `-n`.
- **`-n, --name <name>`**: Tên của tool (ví dụ: `ndoc`). `zrap` sẽ tự động tìm script tương ứng (ví dụ: `tools/no_doc.py`). **Ưu tiên hơn `script_path_arg`**.
- **`-M, --multi-mode`**: Tạo cả hai wrapper `relative` (trong `bin/`) và `absolute` (trong `~/bin`). Cờ `-o` sẽ bị bỏ qua.
- **`-o, --output <path>`**: Đường dẫn file wrapper Zsh sẽ được tạo. Nếu bỏ qua, `zrap` sẽ tự động đề xuất đường dẫn mặc định.
- **`-m, --mode <mode>`**: Chọn chế độ (`relative` hoặc `absolute`). Mặc định là `relative`.
- **`-f, --force`**: Ghi đè file output nếu đã tồn tại.

### Tùy chọn Nâng cao

- **`-r, --root <path>`**: Chỉ định tường minh `PROJECT_ROOT`. Mặc định, `zrap` sẽ tự động tìm thư mục `.git` gần nhất.
- **`-v, --venv <name>`**: Tên thư mục môi trường ảo (mặc định: `.venv`).

### Tùy chọn Cấu hình

- **`-c, --config-project`**: Khởi tạo/cập nhật section `[zrap]` trong `pyproject.toml`.
- **`-C, --config-local`**: Khởi tạo/cập nhật file `.zrap.toml` cục bộ.

## File Cấu Hình

`zrap` có thể được cấu hình qua `.zrap.toml` hoặc `pyproject.toml` (section `[zrap]`).

```toml
# Ví dụ: .zrap.toml

# Chế độ mặc định khi không có cờ -m
mode = "relative"

# Tên thư mục venv mặc định
venv = ".venv"

# Thư mục output mặc định cho mode 'relative'
relative_dir = "bin"

# Thư mục output mặc định cho mode 'absolute' (hỗ trợ ~)
absolute_dir = "~/bin"
```

## Ví dụ

```sh
# 1. Tạo wrapper cho 'ctree' bằng cách chỉ định tên
# Tự động tìm 'tools/tree.py' và tạo 'bin/ctree'
zrap -n ctree

# 2. Tạo cả 2 wrapper (relative và absolute) cho tool 'ndoc'
zrap -n ndoc -M

# 3. Tạo wrapper với đường dẫn script cụ thể, chế độ absolute
zrap tools/my_tool.py -m absolute -o "~/bin/my-tool"

# 4. Khởi tạo cấu hình trong .project.toml
zrap -c
```
