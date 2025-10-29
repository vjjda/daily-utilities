# Hướng dẫn sử dụng: pcode

`pcode` (Pack Code) 
 là công cụ dùng để thu thập nội dung của nhiều file mã nguồn hoặc văn bản từ một thư mục hoặc file chỉ định, sau đó đóng gói chúng thành một file văn bản duy nhất.
 Mục đích chính là tạo ra một ngữ cảnh (context) đầy đủ, dễ dàng sao chép để cung cấp cho các mô hình ngôn ngữ lớn (LLM) hoặc để lưu trữ.
 Công cụ này hỗ trợ lọc file theo đuôi mở rộng, bỏ qua các file/thư mục không cần thiết (tự động tôn trọng `.gitignore`), và tùy chọn hiển thị cấu trúc cây thư mục ở đầu file output.

## Khởi động Nhanh

Cách dễ nhất để bắt đầu là khởi tạo một file cấu hình trong dự án của bạn:

```sh
# 1. Khởi tạo file cấu hình cục bộ (.pcode.toml)
# Tạo/cập nhật file .pcode.toml và mở nó.
 pcode --config-local

# 2. Hoặc, cập nhật file cấu hình toàn dự án (.project.toml)
# Cập nhật phần [pcode] trong file .project.toml.
 pcode --config-project
```

## Cách Sử Dụng

```sh
pcode [start_path] [options]
```

- `start_path`: Đường dẫn (file hoặc thư mục) để bắt đầu quét.
    Mặc định là thư mục hiện tại (`.`) hoặc giá trị trong file cấu hình.

## Tùy Chọn Dòng Lệnh (CLI Options)

- **`-h, --help`**: Hiển thị trợ giúp.
- **`-o, --output <path>`**: Chỉ định file output để ghi kết quả.
    Nếu không cung cấp, mặc định sẽ tạo file `[output_dir]/<tên_start_path>_context.txt` (thư mục `output_dir` lấy từ config, mặc định là `~/Documents/code.context`).
- **`-S, --stdout`**: In kết quả ra màn hình (stdout) thay vì ghi vào file.
- **`-e, --extensions <exts>`**: Chỉ **bao gồm** các file có đuôi mở rộng được liệt kê (phân cách bởi dấu phẩy).
    Hỗ trợ các toán tử:
  - `py,md` (không có toán tử đầu): Ghi đè hoàn toàn danh sách mặc định/config.
- `+ts,js`: Thêm `ts` và `js` vào danh sách hiện có.
- `~yaml,yml`: Loại bỏ `yaml` và `yml` khỏi danh sách hiện có.
- **`-I, --ignore <patterns>`**: Thêm các pattern (giống `.gitignore`, phân cách bởi dấu phẩy) vào danh sách **bỏ qua**.
    Các pattern này được **nối** vào danh sách từ config/default.
- **`-N, --no-gitignore`**: Không tự động đọc và áp dụng các quy tắc từ file `.gitignore`.
- **`-d, --dry-run`**: Chế độ chạy thử. Chỉ hiển thị cây thư mục (nếu bật) và danh sách file, không đọc/ghi/làm sạch nội dung.
- **`--no-header`**: Không in dòng header `===== Path: ... =====` trước nội dung mỗi file.
- **`--no-tree`**: Không hiển thị cây thư mục ở đầu file output.
- **`--copy`**: Tự động sao chép **đường dẫn file output** vào clipboard sau khi ghi thành công.
- **`-a, --all-clean`**: **(MỚI)** Làm sạch nội dung (xóa docstring/comment) của các file có đuôi được cấu hình trong `clean_extensions` trước khi đóng gói. Yêu cầu `utils.core.code_cleaner` và các "add-on" cleaner tương ứng.
- **`-x, --clean-extensions <exts>`**: **(MỚI)** Chỉ định/sửa đổi danh sách đuôi file cần **làm sạch** *khi* `-a` được bật. Hoạt động giống `-e` với logic `+`/`~`/overwrite so với danh sách `clean_extensions` từ config/default. Ví dụ: `-x py,js` (chỉ clean py, js), `-x +ts` (clean theo config + ts), `-x ~yaml` (clean theo config - yaml).
- **`-c, --config-project`**: Khởi tạo/cập nhật section `[pcode]` trong `.project.toml`.
- **`-C, --config-local`**: Khởi tạo/cập nhật file `.pcode.toml` cục bộ.

## File Cấu Hình

`pcode` tự động tải cấu hình từ các file `.toml` sau (theo thứ tự ưu tiên):

1. **Đối Số Dòng Lệnh (CLI Arguments)** (Cao nhất)
2. **File `.pcode.toml`** (Cấu hình cục bộ cho thư mục)
3. **File `.project.toml`** (Section `[pcode]`) (Cấu hình toàn dự án)
4. **Giá trị Mặc định của Script** (Thấp nhất)

### Các tùy chọn cấu hình trong file `.toml`

```toml
# Ví dụ: .pcode.toml hoặc section [pcode] trong .project.toml

# output_dir (str): Thư mục mặc định để lưu file output.
 # Hỗ trợ ký tự '~' cho thư mục home.
 # Mặc định: "~/Documents/code.context"
output_dir = "~/Desktop/my_contexts"

# extensions (List[str]): Danh sách các đuôi file mặc định cần BAO GỒM.
 # Ghi đè danh sách mặc định của script. Bị ghi đè bởi cờ -e (nếu -e không có +/-/~).
 # Mặc định: ["md", "py", "txt", ...] (xem pack_code_config.py)
extensions = ["py", "md", "yaml"]

# ignore (List[str]): Danh sách các pattern mặc định cần BỎ QUA.
 # Ghi đè danh sách mặc định của script. Bị nối thêm bởi cờ -I.
 # Hỗ trợ cú pháp giống .gitignore.
# Mặc định: [".venv", ...]
ignore = ["*.log", "**/temp/*", ".env"]

# clean_extensions (List[str]): (MỚI) Danh sách các đuôi file cần LÀM SẠCH khi dùng -a/--all-clean.
# Ghi đè hoàn toàn danh sách mặc định của script (thường là ["py"]).
# Bị ghi đè/sửa đổi bởi cờ CLI -x/--clean-extensions.
# Ví dụ: clean_extensions = ["py", "js"] # Làm sạch cả Python và JS nếu có cleaner
clean_extensions = ["py"]
```

## Ví dụ

```sh
# 1. Đóng gói tất cả file Python và Markdown trong thư mục hiện tại, in ra màn hình
pcode . -e py,md -S

# 2. Đóng gói thư mục 'src', loại bỏ file '.log', lưu vào file 'project_src.txt'
pcode src -I '*.log' -o project_src.txt

# 3. Đóng gói file 'main.py' và thư mục 'utils', không hiển thị cây, lưu vào Desktop
pcode main.py utils --no-tree -o "~/Desktop/main_utils_context.txt"

# 4. Chạy thử (dry-run) để xem file nào sẽ được đóng gói từ thư mục 'docs'
pcode docs -d

# 5. (MỚI) Đóng gói thư mục 'app', LÀM SẠCH các file Python (.py) theo mặc định
pcode app -a -o app_cleaned_context.txt

# 6. (MỚI) Đóng gói thư mục 'web', chỉ lấy file JS và CSS, đồng thời LÀM SẠCH CHỈ file JS
# (Ghi đè clean_extensions mặc định/config)
pcode web -e js,css -a -x js -o web_cleaned_js_context.txt

# 7. (MỚI) Đóng gói thư mục 'api', làm sạch file Python (mặc định) VÀ file Typescript
# (Thêm 'ts' vào danh sách clean_extensions mặc định/config)
pcode api -a -x +ts -o api_cleaned_py_ts_context.txt
```

