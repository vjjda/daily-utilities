#!/usr/bin/env python
# Path: utils/constants.py

# --- CẤU HÌNH TƯƠNG ĐỐI VÀ HÀNH VI MẶC ĐỊNH ---

# Tên thư mục chứa tất cả các file log (Tương đối so với PROJECT_ROOT)
LOG_DIR_NAME = "logs"

# Thư mục mặc định cho các file đã xử lý/dọn dẹp 
# (Sử dụng đường dẫn Shell mở rộng để Python có thể giải quyết với Path().expanduser())
DEFAULT_ARCHIVE_FOLDER = "~/Desktop/"

# Cấp độ log cho Console (người dùng chỉ thấy INFO trở lên)
CONSOLE_LOG_LEVEL = "INFO"

# Cấp độ log cho File (ghi tất cả chi tiết vào file)
FILE_LOG_LEVEL = "DEBUG"