# Tool Guide: zrap

`zrap` là một công cụ tiện ích ("meta-utility") dùng để "gói" (wrap) một script Python thành một file thực thi Zsh.

File Zsh wrapper này sẽ tự động xử lý các vấn đề phức tạp như:

1. Kích hoạt đúng môi trường ảo (`.venv`) của dự án.
2. Thiết lập `PYTHONPATH` để script Python có thể `import` các module chung (như `utils.core`).

Điều này cho phép bạn chạy script Python phức tạp từ bất kỳ đâu trên hệ thống, y như một lệnh shell thông thường.

---

## Các Chế độ (Modes)

`zrap` cung cấp hai chế độ gói, phục vụ hai mục đích sử dụng khác nhau:

### 1\. Mode `relative` (Mặc định)

Đây là chế độ được dùng để tạo các file thực thi _bên trong_ dự án (ví dụ: `bin/cpath`, `bin/ctree`).

- **Hành vi:** Wrapper sử dụng logic đường dẫn _tương đối_ (ví dụ: `../`) để tự động tìm `PROJECT_ROOT`.
- **Ưu điểm (Project di chuyển được):** Toàn bộ thư mục dự án có thể được đổi tên hoặc di chuyển sang máy khác mà không làm hỏng wrapper.
- **Nhược điểm (Wrapper không di chuyển được):** File wrapper phải luôn nằm cố định ở vị trí nó được tạo ra (ví dụ: `bin/`). Nếu bạn muốn chạy nó từ nơi khác, bạn phải dùng _symlink_.

### 2\. Mode `absolute`

Đây là chế độ được dùng để tạo các file thực thi "di động" (portable) nhằm cài đặt ra bên ngoài project (ví dụ: copy vào `~/bin/` hoặc `/usr/local/bin/`).

- **Hành vi:** Wrapper sẽ "đóng băng" (hard-code) **đường dẫn tuyệt đối** đến `PROJECT_ROOT`, `VENV_PATH`, và file script Python vào bên trong nó.
- **Ưu điểm (Wrapper di chuyển được):** Bạn có thể copy file wrapper này đi bất cứ đâu trên hệ thống và nó vẫn hoạt động.
- **Nhược điểm (Project không di chuyển được):** Nếu bạn di chuyển hoặc đổi tên thư mục project gốc, wrapper sẽ bị hỏng vì đường dẫn hard-code không còn đúng nữa.

---

## Cách dùng (Usage)

Cú pháp cơ bản:

```sh
zrap <script_path> -o <output_path> [options]
```

### Các tham số (Arguments)

- `script_path`

  - (Bắt buộc, Vị trí) Đường dẫn đến file Python bạn muốn wrap.

- `-o, --output <path>`

  - (Bắt buộc) Đường dẫn nơi file wrapper Zsh sẽ được tạo ra.

- `-m, --mode <mode>`

  - Chọn chế độ wrapper: `relative` (mặc định) hoặc `absolute`.

- `-r, --root <path>`

  - (Tùy chọn) Chỉ định tường minh `PROJECT_ROOT`. Nếu bỏ qua, `zrap` sẽ tự động tìm thư mục `.git` gần nhất (tính từ file script) để làm gốc.

- `-v, --venv <name>`

  - (Tùy chọn) Tên thư mục môi trường ảo (mặc định là `.venv`).

- `-f, --force`

  - (Tùy chọn) Ghi đè file output nếu nó đã tồn tại.

---

## Ví dụ (Examples)

### 1\. Tạo wrapper `btool` (Mode `relative`)

Giống như cách chúng ta đã test, lệnh này tạo ra `bin/btool` để sử dụng _bên trong_ project `daily-utilities`.

```sh
# Chạy từ gốc project
zrap scripts/internal/bootstrap_tool.py -o bin/btool
```

- `zrap` sẽ tự động tìm `PROJECT_ROOT` là thư mục `daily-utilities`.
- Nó tính toán đường dẫn tương đối từ `bin/` lên `PROJECT_ROOT` là `../`.
- Wrapper `bin/btool` được tạo ra (và `chmod +x`).

### 2\. Tạo wrapper `my-tool` (Mode `absolute`)

Lệnh này tạo ra một file `my-tool` "di động" trong thư mục `~/bin` của bạn để chạy system-wide.

```sh
# Chạy từ gốc project
zrap scripts/my_tool.py -o "$HOME/bin/my-tool" -m absolute
```

- `zrap` sẽ lấy đường dẫn tuyệt đối, ví dụ `/Users/boss/daily-utilities`.
- Nó hard-code đường dẫn này vào file `~/bin/my-tool`.
- Bây giờ bạn có thể gõ `my-tool` từ bất cứ đâu trong terminal. (Nếu `~/bin` đã có trong `$PATH`).
