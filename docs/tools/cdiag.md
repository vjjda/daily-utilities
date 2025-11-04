# Hướng dẫn sử dụng: cdiag

`cdiag` (Clipboard Diagram) là công cụ để xử lý nhanh code vẽ đồ thị (Graphviz hoặc Mermaid) được sao chép vào clipboard. Nó sẽ tự động phát hiện loại code, làm sạch (xóa comment, emoji), lưu thành file nguồn và tùy chọn render ra file ảnh.

## Luồng làm việc cơ bản

1.  **Sao chép (Copy)** toàn bộ đoạn code Graphviz (`.dot`) hoặc Mermaid (`.mmd`) vào clipboard.
2.  Chạy lệnh `cdiag` trong terminal.
3.  Công cụ sẽ tự động xử lý và mở file kết quả cho bạn.

## Cách Sử Dụng

```sh
cdiag [options]
```

Công cụ không nhận đường dẫn đầu vào mà hoạt động trực tiếp trên nội dung của clipboard.

## Tùy Chọn Dòng Lệnh (CLI Options)

- **`-t, --to <svg|png>`**: Chuyển đổi code thành file ảnh và mở file ảnh đó.
  - Nếu không có cờ này, `cdiag` chỉ tạo và mở file mã nguồn (`.dot` hoặc `.mmd`).
  - `svg`: Tạo file ảnh định dạng SVG.
  - `png`: Tạo file ảnh định dạng PNG.

- **`-f, --filter`**: Bật bộ lọc emoji. Công cụ sẽ chủ động xóa các ký tự emoji khỏi code trong clipboard trước khi xử lý.

- **`-g, --is-graph`**: Chế độ kiểm tra. `cdiag` sẽ chỉ kiểm tra clipboard và in ra `Graphviz`, `Mermaid`, hoặc `False` rồi thoát. Hữu ích cho việc scripting.

## Cấu hình

`cdiag` **không** sử dụng hệ thống cấu hình `.toml` như các công cụ khác. Các thiết lập được quản lý bằng hằng số trực tiếp trong file Python.

Để thay đổi, bạn cần chỉnh sửa file: `modules/clip_diag/clip_diag_config.py`

- **`DEFAULT_OUTPUT_DIR`**: Thư mục lưu trữ tất cả các file được tạo ra. Mặc định: `~/Documents/graphviz`.
- **`DOT_PATH`**: Đường dẫn đến trình biên dịch `dot` của Graphviz. Mặc định: `/opt/homebrew/bin/dot`.
- **`MMC_PATH`**: Đường dẫn đến trình biên dịch `mmc` của Mermaid. Mặc định: `/opt/homebrew/bin/mmc`.
- **`APP_CONFIG`**: Cấu hình ứng dụng mặc định để mở các loại file (`.dot`, `.svg`, `.png`...). 

## Ví dụ

```sh
# 1. Copy một đoạn code Graphviz vào clipboard
# Chạy lệnh sau để tạo file .dot và mở nó bằng trình soạn thảo mặc định
cdiag

# 2. Copy một đoạn code Mermaid vào clipboard
# Chạy lệnh sau để tạo file .mmd, render nó ra ảnh SVG, và mở file SVG
cdiag -t svg

# 3. Copy một đoạn code có lẫn emoji
# Chạy lệnh với cờ -f để tự động xóa emoji trước khi xử lý
cdiag -f

# 4. Kiểm tra nhanh xem clipboard có chứa code đồ thị hợp lệ không
cdiag -g
# Output có thể là: Graphviz, Mermaid, hoặc False
```
