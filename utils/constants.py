# Path: utils/constants.py

# --- NEW: Thêm Path để xác định root ---
from pathlib import Path
# --- END NEW ---

# --- NEW: Xác định Project Root ---
# Lấy đường dẫn file hiện tại (utils/constants.py)
# .parent -> thư mục utils
# .parent -> thư mục gốc của dự án (daily-utilities)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
# --- END NEW ---


# --- CẤU HÌNH TƯƠNG ĐỐI VÀ HÀNH VI MẶC ĐỊNH ---

# Tên thư mục chứa tất cả các file log (Tương đối so với PROJECT_ROOT)
LOG_DIR_NAME = "logs"

# --- NEW: Đường dẫn tuyệt đối đến thư mục log ---
LOG_DIR_PATH = PROJECT_ROOT / LOG_DIR_NAME
# --- END NEW ---

# Thư mục mặc định cho các file đã xử lý/dọn dẹp 
DEFAULT_ARCHIVE_FOLDER = "~/Desktop/"

# Cấp độ log cho Console
CONSOLE_LOG_LEVEL = "INFO"

# Cấp độ log cho File
FILE_LOG_LEVEL = "DEBUG"