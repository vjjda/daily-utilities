# Hướng dẫn sử dụng: forc

`forc` (Format Code) là một công cụ để quét và định dạng (format) các file mã nguồn trong dự án của bạn. Nó giúp đảm bảo code tuân thủ các tiêu chuẩn về định dạng một cách nhất quán.

## Cách Sử Dụng

```sh
forc [start_paths...] [options]
```

- `start_paths`: Một hoặc nhiều đường dẫn (file hoặc thư mục) để quét. Mặc định là thư mục hiện tại (`.`).

Chế độ hoạt động mặc định là **sửa lỗi (fix mode)**. Công cụ sẽ tìm các file cần định dạng và tự động sửa chúng sau khi có xác nhận của bạn.

## Tùy Chọn Dòng Lệnh (CLI Options)

### Tùy chọn Định dạng & Sửa lỗi

- **`-d, --dry-run`**: Chuyển sang chế độ **chỉ kiểm tra (dry-run)**. Công cụ sẽ chỉ báo cáo các file cần định dạng mà không thực hiện bất kỳ thay đổi nào.
- **`-f, --force`**: Tự động sửa tất cả các file mà không cần hỏi xác nhận. Chỉ có tác dụng ở chế độ sửa lỗi (khi không dùng `-d`).
- **`-g, --git-commit`**: Sau khi định dạng thành công, tự động tạo một commit Git với các thay đổi đó.
- **`-w, --stepwise`**: Bật **chế độ gia tăng (stepwise mode)**. Ở chế độ này, `forc` chỉ quét các file đã thay đổi kể từ lần chạy cuối cùng có cùng cài đặt (cùng `extensions` và `ignore`). Điều này giúp tăng tốc độ đáng kể cho các lần chạy sau.
- **`-e, --extensions <exts>`**: Ghi đè hoặc chỉnh sửa danh sách các đuôi file cần quét (phân cách bởi dấu phẩy).
  - `py,js`: Ghi đè danh sách mặc định.
  - `+ts,md`: Thêm `ts` và `md` vào danh sách hiện tại.
  - `~py`: Loại bỏ `py` khỏi danh sách hiện tại.
- **`-I, --ignore <patterns>`**: Thêm các pattern (giống `.gitignore`, phân cách bởi dấu phẩy) vào danh sách **bỏ qua**.

### Tùy chọn Khởi tạo Cấu hình

- **`-c, --config-project`**: Khởi tạo hoặc cập nhật section `[format_code]` trong file cấu hình toàn dự án (`.project.toml`).
- **`-C, --config-local`**: Khởi tạo hoặc cập nhật file cấu hình cục bộ (`.forc.toml`) trong thư mục hiện tại.

## File Cấu Hình

`forc` có thể được cấu hình thông qua các file `.toml` để lưu lại các thiết lập thường dùng.

- `.forc.toml`: File cấu hình cục bộ.
- `.project.toml`: File cấu hình dự phòng toàn dự án (sử dụng section `[format_code]`).

**Độ ưu tiên:** `Đối số CLI` > `.forc.toml` > `.project.toml` > `Mặc định`.

```toml
# Ví dụ: .forc.toml hoặc section [format_code] trong .project.toml

# Danh sách các đuôi file mặc định cần quét.
extensions = ["py", "js", "ts"]

# Danh sách các pattern cần bỏ qua.
ignore = ["node_modules/", "dist/"]
```

## Ví dụ

```sh
# 1. Chỉ kiểm tra (dry-run) tất cả các file trong thư mục hiện tại
forc --dry-run

# 2. Định dạng tất cả các file đã thay đổi kể từ lần chạy trước và commit kết quả
forc -w -g

# 3. Định dạng tất cả file Python, bỏ qua thư mục 'tests'
forc -e py -I 'tests/*'

# 4. Khởi tạo file cấu hình cục bộ để tùy chỉnh
forc --config-local
```