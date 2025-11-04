# Hướng dẫn sử dụng: pcode

`pcode` (Pack Code) là công cụ dùng để thu thập nội dung của nhiều file mã nguồn hoặc văn bản, sau đó đóng gói chúng thành một file văn bản duy nhất. Mục đích chính là tạo ra một ngữ cảnh (context) đầy đủ, dễ dàng sao chép để cung cấp cho các mô hình ngôn ngữ lớn (LLM) hoặc để lưu trữ.

Công cụ này hỗ trợ lọc file theo đuôi mở rộng, bỏ qua các file/thư mục không cần thiết (tự động tôn trọng `.gitignore`), và tùy chọn hiển thị cấu trúc cây thư mục ở đầu file output.

## Cách Sử Dụng

```sh
pcode [start_paths...] [options]
```

- `start_paths`: Một hoặc nhiều đường dẫn (file hoặc thư mục) để bắt đầu quét. Mặc định là thư mục hiện tại (`.`).

## Tùy Chọn Dòng Lệnh (CLI Options)

- **`-o, --output <path>`**: Chỉ định file output để ghi kết quả. Nếu không cung cấp, một file sẽ được tự động tạo trong thư mục `output_dir` được cấu hình.
- **`--stdout`**: In kết quả ra màn hình (stdout) thay vì ghi vào file.
- **`--copy`**: Tự động sao chép **toàn bộ nội dung** của file output vào clipboard sau khi ghi thành công.
- **`-d, --dry-run`**: Chế độ chạy thử. Chỉ hiển thị cây thư mục và danh sách file, không đọc hay ghi nội dung.

### Tùy chọn Lọc File

- **`-e, --extensions <exts>`**: Chỉ **bao gồm** các file có đuôi mở rộng được liệt kê (phân cách bởi dấu phẩy). Hỗ trợ các toán tử `+` (thêm) và `~` (bớt).
- **`-I, --ignore <patterns>`**: Thêm các pattern (giống `.gitignore`, phân cách bởi dấu phẩy) vào danh sách **bỏ qua**.
- **`-i, --include <patterns>`**: Bộ lọc dương. **CHỈ** các file khớp với pattern này mới được xử lý. Các pattern khác sẽ bị bỏ qua.
- **`-N, --no-gitignore`**: Không tự động đọc và áp dụng các quy tắc từ file `.gitignore`.

### Tùy chọn Xử lý Nội dung

- **`-a, --all-clean`**: Làm sạch nội dung (xóa docstring/comment) của các file có đuôi được cấu hình trong `clean_extensions` trước khi đóng gói.
- **`-x, --clean-extensions <exts>`**: Chỉ định/sửa đổi danh sách đuôi file cần **làm sạch** khi cờ `-a` được bật. Hoạt động giống `-e`.
- **`-b, --beautify`**: Định dạng (format) code (ví dụ: chạy Black cho `.py`) trước khi đóng gói. Áp dụng cho các đuôi file trong `format_extensions`.
- **`--no-header`**: Không in các marker `[[START_FILE_CONTENT: ...]]` và `[[END_FILE_CONTENT]]` quanh nội dung mỗi file.
- **`--no-tree`**: Không hiển thị cây thư mục ở đầu file output.

### Tùy chọn Cấu hình

- **`-c, --config-project`**: Khởi tạo/cập nhật section `[pcode]` trong `.project.toml`.
- **`-C, --config-local`**: Khởi tạo/cập nhật file `.pcode.toml` cục bộ.

## File Cấu Hình

`pcode` tự động tải cấu hình từ các file `.toml` (ưu tiên `CLI` > `.pcode.toml` > `.project.toml` > `Mặc định`).

```toml
# Ví dụ: .pcode.toml hoặc section [pcode] trong .project.toml

# Thư mục mặc định để lưu file output.
output_dir = "~/Desktop/code_contexts"

# Danh sách các đuôi file mặc định cần bao gồm.
extensions = ["py", "md", "yaml"]

# Danh sách các pattern mặc định cần bỏ qua.
ignore = ["*.log", "**/temp/*", ".env"]

# Chỉ xử lý các file khớp với những pattern này (nếu được định nghĩa).
# include = ["src/**/*.py", "docs/**/*.md"]

# Các đuôi file sẽ được làm sạch khi dùng -a/--all-clean.
clean_extensions = ["py", "sh"]

# Các đuôi file sẽ được định dạng khi dùng -b/--beautify.
format_extensions = ["py"]
```

## Ví dụ

```sh
# 1. Đóng gói tất cả file .py và .md, in ra màn hình
pcode . -e py,md --stdout

# 2. Đóng gói thư mục 'src', bỏ qua file log, lưu vào 'project_src.txt' và sao chép nội dung
pcode src -I '*.log' -o project_src.txt --copy

# 3. Đóng gói CHỈ các file Python trong 'scripts' và file .md trong 'docs'
pcode . -i "scripts/*.py,docs/**/*.md"

# 4. Đóng gói thư mục 'app', làm sạch và định dạng các file Python
pcode app -a -b -o app_cleaned_formatted.txt
```