# Tool Guide: sgen

Công cụ tạo file stub `.pyi` cho các module gateway động của Python.

## Khởi Động Nhanh

Cách dễ nhất để bắt đầu là khởi tạo một file cấu hình trong dự án của bạn:

```sh
# 1. Khởi tạo file cấu hình cục bộ
# Tạo/cập nhật file .sgen.toml (cục bộ cho thư mục hiện tại) và mở nó.
sgen --config-local

# 2. Hoặc, cập nhật file cấu hình toàn dự án
# Cập nhật phần [sgen] trong file .project.toml tại thư mục hiện tại.
sgen --config-project
```

## Cách Sử Dụng

```sh
sgen [target_dir] [options]
```

* `target_dir`: Thư mục để bắt đầu quét (base directory). Mặc định là thư mục hiện tại (`.`).

## Tùy Chọn Dòng Lệnh (CLI Options)

* **`-c, --config-project`**: Khởi tạo hoặc cập nhật section `[sgen]` trong file `.project.toml`.
* **`-C, --config-local`**: Khởi tạo hoặc cập nhật file `.sgen.toml` cục bộ.
* **`-f, --force`**: Ghi đè file `.pyi` nếu đã tồn tại mà không cần hỏi xác nhận.
* **`-I, --ignore <patterns>`**: Danh sách các pattern (phân cách bởi dấu phẩy) để bỏ qua. Sử dụng cú pháp giống `.gitignore` (pathspec/gitwildmatch). Các pattern này sẽ được **THÊM** vào danh sách ignore từ file cấu hình hoặc giá trị mặc định.
* **`-R, --restrict <dirs>`**: Danh sách các thư mục con (so với `target_dir`, phân cách bởi dấu phẩy) để giới hạn quét. Sẽ **GHI ĐÈ** danh sách từ file cấu hình hoặc giá trị mặc định.

## File Cấu Hình

Đối với các cài đặt lâu dài, `sgen` tự động tải cấu hình từ các file `.toml`.

* `.sgen.toml`: File cấu hình cục bộ.
* `.project.toml`: File cấu hình dự phòng toàn dự án (section `[sgen]`).

### Độ Ưu Tiên Cấu Hình

1. **Đối Số Dòng Lệnh (CLI Arguments)** (Ưu tiên cao nhất)
2. **File `.sgen.toml`**
3. **File `.project.toml` (Section `[sgen]`)**
4. **Cài Đặt Mặc Định Của Script** (Ưu tiên thấp nhất)

### Pattern Lọc (`ignore`)

Pattern `ignore` trong file `.toml` hỗ trợ cú pháp giống `.gitignore` (thông qua thư viện `pathspec`).

