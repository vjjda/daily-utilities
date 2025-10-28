# Tool Guide: pcode

Một công cụ để đóng gói (flatten) cây thư mục thành một file context.txt duy nhất.

## Khởi Động Nhanh

Cách dễ nhất để bắt đầu là khởi tạo một file cấu hình trong dự án của bạn:

```sh
# 1. Khởi tạo file cấu hình cục bộ
# Tạo/cập nhật file .pcode.toml (cục bộ cho thư mục hiện tại) và mở nó.
pcode --config-local

# 2. Hoặc, cập nhật file cấu hình toàn dự án
# Cập nhật phần [pcode] trong file .project.toml tại thư mục hiện tại.
pcode --config-project
```

## Cách Sử Dụng

```sh
pcode [start_path] [options]
```

- `start_path`: Đường dẫn (file hoặc thư mục) để bắt đầu quét. Mặc định là thư mục hiện tại (`.`) hoặc giá trị trong file cấu hình.

## Tùy Chọn Dòng Lệnh (CLI Options)

- **`-c, --config-project`**: Khởi tạo hoặc cập nhật section `[pcode]` trong file `.project.toml`.
- **`-C, --config-local`**: Khởi tạo hoặc cập nhật file `.pcode.toml` cục bộ.
- **`-o, --output <path>`**: File output để ghi. Ghi đè mọi cấu hình.
- **`-S, --stdout`**: In kết quả ra stdout (console) thay vì ghi file.
- **`-e, --extensions <exts>`**: Danh sách các đuôi file (phân cách bởi dấu phẩy).
  - Hỗ trợ các toán tử `+` (thêm vào config/default), `~` (bớt khỏi config/default) hoặc không có toán tử (ghi đè hoàn toàn config/default).
  - Ví dụ: `py,js` (ghi đè), `+ts,md` (thêm), `~py` (bớt).
- **`-I, --ignore <patterns>`**: Danh sách các pattern (phân cách bởi dấu phẩy) để bỏ qua. Các pattern này sẽ được **THÊM** vào danh sách ignore từ file cấu hình hoặc giá trị mặc định.
- **`-N, --no-gitignore`**: Không tôn trọng các file `.gitignore`.
- **`-d, --dry-run`**: Chỉ in danh sách file và cây thư mục, không đọc hay ghi nội dung.
- **`--no-header`**: Không in header phân tách (`===== Path: ...`).
- **`--no-tree`**: Không in cây thư mục ở đầu output.

## File Cấu Hình

Đối với các cài đặt lâu dài, `pcode` tự động tải cấu hình từ các file `.toml`.

- `.pcode.toml`: File cấu hình cục bộ.
- `.project.toml`: File cấu hình dự phòng toàn dự án (section `[pcode]`).

### Độ Ưu Tiên Cấu Hình

1. **Đối Số Dòng Lệnh (CLI Arguments)** (Ưu tiên cao nhất)
2. **File `.pcode.toml`**
3. **File `.project.toml` (Section `[pcode]`)**
4. **Cài Đặt Mặc Định Của Script** (Ưu tiên thấp nhất)

### Các Cài Đặt (Trong file `.toml`)

- **`start_path`** (String): Đường dẫn quét mặc định.
- **`output_dir`** (String): Thư mục mặc định để lưu file `_context.txt` (hỗ trợ `~`).
- **`extensions`** (Array of Strings): Danh sách đuôi file GHI ĐÈ mặc định. (Ví dụ: `extensions = ["py", "md", "toml"]`)
- **`ignore`** (Array of Strings): Danh sách pattern (kiểu `.gitignore`) để THÊM vào mặc định. (Ví dụ: `ignore = ["*.log", "docs/drafts/"]`)
