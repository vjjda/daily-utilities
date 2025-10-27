# Tiếng Việt: Hướng Dẫn Công Cụ: tree

`tree` là một công cụ tạo cây thư mục thông minh. Nó cung cấp các tùy chọn lọc nâng cao thông qua các đối số dòng lệnh và file cấu hình, đồng thời tự động bỏ qua các file/thư mục không cần thiết như `.venv` và `__pycache__`.

## Khởi Động Nhanh

Cách dễ nhất để bắt đầu là khởi tạo một file cấu hình trong dự án của bạn:

```sh
# 1. Khởi tạo file cấu hình cục bộ
# Tạo/cập nhật file .tree.toml (cục bộ cho thư mục hiện tại) và mở nó.
tree --config local

# 2. Hoặc, cập nhật file cấu hình toàn dự án
# Cập nhật phần [tree] trong file .project.toml tại thư mục hiện tại.
tree --config project
```

## Cách Sử Dụng

```sh
tree [start_path] [options]
```

  * `start_path`: Thư mục hoặc file để bắt đầu tạo cây. Mặc định là thư mục hiện tại (`.`).

## Tùy Chọn Dòng Lệnh (CLI Options)

Các tùy chọn này cung cấp khả năng ghi đè một lần đối với cấu hình.

  * **`-c, --config <scope>`**: Khởi tạo hoặc cập nhật các file cấu hình.
      * `local`: Tạo/ghi đè file `.tree.toml` cục bộ và mở nó.
      * `project`: Ghi đè hoặc thêm phần `[tree]` vào file `.project.toml` toàn dự án và mở nó.
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

1.  **Đối Số Dòng Lệnh (CLI Arguments)** (Ưu tiên cao nhất)
2.  **File `.tree.toml`**
3.  **File `.project.toml`** (Dự phòng)
4.  **Cài Đặt Mặc Định Của Script** (Ưu tiên thấp nhất)

**Ví dụ:** Nếu `.tree.toml` của bạn ghi `level = 5`, nhưng bạn chạy `tree -L 3`, cây sẽ chỉ đi đến **cấp độ 3** vì đối số CLI thắng. Nếu bạn chạy `tree` mà không có đối số, nó sẽ sử dụng **cấp độ 5** từ file.

### Pattern Lọc (`ignore`, `prune`, `dirs-only`)

Tất cả các pattern lọc trong file `.toml` đều hỗ trợ **cú pháp giống `.gitignore`** (thông qua thư viện `pathspec`). Điều này bao gồm:

  * **Tên đơn giản:** `node_modules`
  * **Ký tự đại diện (Wildcards):** `*.log`, `temp_?`
  * **Glob hai dấu sao:** `**/__pycache__` (khớp ở mọi cấp độ)
  * **Phủ định:** `!important.log` (không bỏ qua file này)
  * **Neo vào gốc:** `/README.md` (chỉ khớp file ở thư mục gốc)
  * **Chỉ thư mục:** `build/` (khớp thư mục `build` ở mọi cấp, nhưng không khớp file tên `build`)

-----

# English: Tool Guide: tree

`tree` is a smart directory tree generator. It provides advanced filtering options via command-line arguments and configuration files, automatically ignoring clutter like `.venv` and `__pycache__`.

## Quick Start

The easiest way to start is by initializing a configuration file in your project:

```sh
# 1. Initialize a local config file
# Creates/updates .tree.toml (local to the current directory) and opens it.
tree --config local

# 2. Or, update the project-wide config file
# Updates the [tree] section in .project.toml in the current directory.
tree --config project
```

## Usage

```sh
tree [start_path] [options]
```

  * `start_path`: The directory or file to start the tree from. Defaults to the current directory (`.`).

## CLI Options

These options provide one-time overrides for the configuration.

  * **`-c, --config <scope>`**: Initialize or update config files.
      * `local`: Creates/overwrites a local `.tree.toml` file and opens it.
      * `project`: Overwrites or appends the `[tree]` section in the project-wide `.project.toml` file and opens it.
  * `-L, --level <num>`: Limit the display depth of the tree.
  * **`-I, --ignore <patterns>`**: A comma-separated list of patterns (e.g., `*.log,*.tmp`) to completely hide from the output. These patterns are **ADDED** to the ignore list from config files or defaults.
  * **`-P, --prune <patterns>`**: A comma-separated list of directory patterns (e.g., `dist,build`). The directory will be shown, but `tree` will not traverse into it (marked with `[...]`). These patterns are **ADDED** to the prune list from config files or defaults.
  * `-d, --all-dirs` / `-D, --dirs-patterns <patterns>`:
      * `-d`: Shows directories only for the entire tree.
      * `-D`: Only shows sub-directories *within* directories that match the provided comma-separated patterns (e.g., `-D 'assets,static'`). Affected directories are marked with `[dirs only]`.
  * `-s, --show-submodules`: By default, `tree` detects Git submodules (via `.gitmodules`) and hides their contents. Use this flag to show them.
  * **`-N, --no-gitignore`**: Do not respect `.gitignore` files.
  * **`-f, --full-view`**: Bypass all filters (`.gitignore`, rules, level) and show all files.

## Configuration Files

For persistent settings, `tree` automatically loads configurations from `.toml` files in the target directory.

  * `.tree.toml`: The primary configuration file for `tree`.
  * `.project.toml`: A fallback project-wide config file. `tree` will read this if it exists, but any settings in `.tree.toml` will override it.

### Configuration Priority

`tree` uses a clear priority system to decide which setting to apply:

1.  **CLI Arguments** (Highest priority)
2.  **`.tree.toml` file**
3.  **`.project.toml` file** (Fallback)
4.  **Script Defaults** (Lowest priority)

**Example:** If your `.tree.toml` says `level = 5`, but you run `tree -L 3`, the tree will only go to **level 3** because the CLI argument wins. If you run `tree` with no arguments, it will use **level 5** from the file.

### Filter Patterns (`ignore`, `prune`, `dirs-only`)

All filter patterns in the `.toml` file support **`.gitignore`-style syntax** (via the `pathspec` library). This includes:

  * **Simple names:** `node_modules`
  * **Wildcards:** `*.log`, `temp_?`
  * **Double Star Glob:** `**/__pycache__` (matches at any level)
  * **Negation:** `!important.log` (don't ignore this file)
  * **Anchoring to root:** `/README.md` (only matches the root file)
  * **Directory-only:** `build/` (matches `build` directories anywhere, but not a file named `build`)
