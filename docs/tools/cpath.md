# Tool Guide: cpath

`cpath` là công cụ để kiểm tra và tùy chọn sửa các comment `# Path:` ở đầu các file mã nguồn, đảm bảo chúng khớp với vị trí thực tế của file trong dự án. Nó hỗ trợ nhiều loại comment khác nhau (ví dụ: `#`, `//`, `/* */`).

## Khởi Động Nhanh

Cách dễ nhất để bắt đầu là khởi tạo một file cấu hình trong dự án của bạn:

```sh
# 1. Khởi tạo file cấu hình cục bộ
# Tạo/cập nhật file .cpath.toml (cục bộ cho thư mục hiện tại) và mở nó.
cpath --config-local

# 2. Hoặc, cập nhật file cấu hình toàn dự án
# Cập nhật phần [cpath] trong file .project.toml tại thư mục hiện tại.
cpath --config-project
```

## Cách Sử Dụng

```sh
cpath [target_directory] [options]
```

* `target_directory`: Thư mục để bắt đầu quét. Mặc định là thư mục hiện tại (`.`).

## Tùy Chọn Dòng Lệnh (CLI Options)

* **`-c, --config-project`**: Khởi tạo hoặc cập nhật section `[cpath]` trong file `.project.toml`.
* **`-C, --config-local`**: Khởi tạo hoặc cập nhật file `.cpath.toml` cục bộ.
* **`-e, --extensions <exts>`**: Danh sách các đuôi file cần quét (phân cách bởi dấu phẩy). Hỗ trợ các toán tử `+` (thêm vào config/default), `~` (bớt khỏi config/default) hoặc không có toán tử (ghi đè hoàn toàn config/default). Ví dụ: `py,js` (ghi đè), `+ts,md` (thêm), `~py` (bớt).
* **`-I, --ignore <patterns>`**: Danh sách các pattern (phân cách bởi dấu phẩy) để bỏ qua khi quét. Sử dụng cú pháp giống `.gitignore` (pathspec/gitwildmatch). Các pattern này sẽ được **THÊM** vào danh sách ignore từ file cấu hình hoặc giá trị mặc định.
* **`-d, --dry-run`**: Chỉ chạy ở chế độ kiểm tra (dry-run) và báo cáo các file cần sửa, không thực hiện ghi file. Nếu không có cờ này, `cpath` sẽ chạy ở chế độ sửa lỗi và yêu cầu xác nhận trước khi ghi.

## File Cấu Hình

Đối với các cài đặt lâu dài, `cpath` tự động tải cấu hình từ các file `.toml`.

* `.cpath.toml`: File cấu hình cục bộ.
* `.project.toml`: File cấu hình dự phòng toàn dự án (section `[cpath]`).

### Độ Ưu Tiên Cấu Hình

1. **Đối Số Dòng Lệnh (CLI Arguments)** (Ưu tiên cao nhất)
2. **File `.cpath.toml`**
3. **File `.project.toml` (Section `[cpath]`)**
4. **Cài Đặt Mặc Định Của Script** (Ưu tiên thấp nhất)

### Pattern Lọc (`ignore`)

Pattern `ignore` trong file `.toml` hỗ trợ cú pháp giống `.gitignore` (thông qua thư viện `pathspec`).

### Danh sách Đuôi file (`extensions`)

Danh sách `extensions` trong file `.toml` là một mảng các chuỗi, ví dụ: `extensions = ["py", "js", "ts"]`.
