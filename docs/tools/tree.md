# Tool Guide: tree

`tree` là một công cụ tạo cây thư mục thông minh. Nó cung cấp các tùy chọn lọc nâng cao thông qua các đối số dòng lệnh và file cấu hình, đồng thời tự động bỏ qua các file/thư mục không cần thiết như `.venv` và `__pycache__`.

## Khởi Động Nhanh

Cách dễ nhất để bắt đầu là khởi tạo một file cấu hình trong dự án của bạn:

```sh
# 1. Khởi tạo file cấu hình cục bộ
# Tạo/cập nhật file .tree.toml (cục bộ cho thư mục hiện tại) và mở nó.
tree --config-local

# 2. Hoặc, cập nhật file cấu hình toàn dự án
# Cập nhật phần [tree] trong file .project.toml tại thư mục hiện tại.
tree --config-project
```

## Cách Sử Dụng

```sh
tree [start_path] [options]
```

* `start_path`: Thư mục hoặc file để bắt đầu tạo cây. Mặc định là thư mục hiện tại (`.`).

## Tùy Chọn Dòng Lệnh (CLI Options)

Các tùy chọn này cung cấp khả năng ghi đè một lần đối với cấu hình.

* **`-c, --config-project`**: Khởi tạo/cập nhật file .project.toml (scope 'project').
* **`-C, --config-local`**: Khởi tạo/cập nhật file .tree.toml (scope 'local').
* `-L, --level <num>`: Giới hạn độ sâu hiển thị của cây.
* **`-I, --ignore <patterns>`**: Danh sách các pattern (ví dụ: `*.log,*.tmp`) được phân tách bằng dấu komma để ẩn hoàn toàn khỏi đầu ra. Các pattern này sẽ được **THÊM** vào danh sách ignore từ file cấu hình hoặc giá trị mặc định.
* **`-P, --prune <patterns>`**: Danh sách các pattern thư mục (ví dụ: `dist,build`) được phân tách bằng dấu komma. Thư mục sẽ được hiển thị nhưng `tree` sẽ không duyệt vào bên trong (được đánh dấu bằng `[...]`). Các pattern này sẽ được **THÊM** vào danh sách prune từ file cấu hình hoặc giá trị mặc định.
* `-d, --all-dirs` / `-D, --dirs-patterns <patterns>`:
  * `-d`: Chỉ hiển thị thư mục cho toàn bộ cây.
  * `-D`: Chỉ hiển thị thư mục con *bên trong* các thư mục khớp với các pattern được cung cấp (phân tách bằng dấu komma, ví dụ: `-D 'assets,static'`). Các thư mục bị ảnh hưởng sẽ được đánh dấu bằng `[dirs only]`.
* `-s, --show-submodules`: Theo mặc định, `tree` phát hiện các submodule của Git (thông qua `.gitmodules`) và ẩn nội dung của chúng. Sử dụng cờ này để hiển thị chúng.
* **`-N, --no-gitignore`**: Không tôn trọng các file `.gitignore`.
* **`-f, --full-view`**: Bỏ qua tất cả các bộ lọc (`.gitignore`, các quy tắc, cấp độ) và hiển thị tất cả các file.

## File Cấu Hình

Đối với các cài đặt lâu dài, `tree` tự động tải cấu hình từ các file `.toml` trong thư mục mục tiêu.

* `.tree.toml`: File cấu hình chính cho `tree`.
* `.project.toml`: File cấu hình dự phòng toàn dự án. `tree` sẽ đọc file này nếu nó tồn tại, nhưng bất kỳ cài đặt nào trong `.tree.toml` sẽ ghi đè nó.

### Độ Ưu Tiên Cấu Hình

`tree` sử dụng một hệ thống ưu tiên rõ ràng để quyết định cài đặt nào được áp dụng:

1. **Đối Số Dòng Lệnh (CLI Arguments)** (Ưu tiên cao nhất)
2. **File `.tree.toml`**
3. **File `.project.toml`** (Dự phòng)
4. **Cài Đặt Mặc Định Của Script** (Ưu tiên thấp nhất)

**Ví dụ:** Nếu `.tree.toml` của bạn ghi `level = 5`, nhưng bạn chạy `tree -L 3`, cây sẽ chỉ đi đến **cấp độ 3** vì đối số CLI thắng. Nếu bạn chạy `tree` mà không có đối số, nó sẽ sử dụng **cấp độ 5** từ file.

### Pattern Lọc (`ignore`, `prune`, `dirs-only`)

Tất cả các pattern lọc trong file `.toml` đều hỗ trợ **cú pháp giống `.gitignore`** (thông qua thư viện `pathspec`). Điều này bao gồm:

* **Tên đơn giản:** `node_modules`
* **Ký tự đại diện (Wildcards):** `*.log`, `temp_?`
* **Glob hai dấu sao:** `**/__pycache__` (khớp ở mọi cấp độ)
* **Phủ định:** `!important.log` (không bỏ qua file này)
* **Neo vào gốc:** `/README.md` (chỉ khớp file ở thư mục gốc)
* **Chỉ thư mục:** `build/` (khớp thư mục `build` ở mọi cấp, nhưng không khớp file tên `build`)

