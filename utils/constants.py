# Path: utils/constants.py
"""
Các hằng số dùng chung trong toàn bộ dự án.
"""

from pathlib import Path
from typing import Final, Dict

# --- Đường dẫn Gốc Dự án ---
# Xác định đường dẫn tuyệt đối đến thư mục gốc của dự án `daily-utilities`
# Path(__file__) -> utils/constants.py
# .parent        -> utils/
# .parent        -> daily-utilities/
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent

# --- Cấu hình Logging ---

# Tên thư mục chứa file log (tương đối so với PROJECT_ROOT)
LOG_DIR_NAME: Final[str] = "logs"
# Đường dẫn tuyệt đối đến thư mục log
LOG_DIR_PATH: Final[Path] = PROJECT_ROOT / LOG_DIR_NAME

# Cấp độ log mặc định cho Console (có thể bị ghi đè bởi entrypoint)
CONSOLE_LOG_LEVEL: Final[str] = "INFO"
# Cấp độ log mặc định cho File (thường là DEBUG để ghi chi tiết)
FILE_LOG_LEVEL: Final[str] = "DEBUG"

# --- THÊM MỚI: Language Mapping ---
# Ánh xạ đuôi file (lowercase) sang mã định danh ngôn ngữ dùng bởi cleaners
# Được sử dụng bởi ndoc và pcode
DEFAULT_EXTENSIONS_LANG_MAP: Final[Dict[str, str]] = {
    "py": "python",
    "js": "javascript",
    "sh": "shell",
    "bash": "shell",
    # Thêm các ánh xạ khác khi cần
}

# --- Cấu hình Khác (Ví dụ) ---
# Thư mục mặc định cho việc lưu trữ file (ví dụ)
# DEFAULT_ARCHIVE_FOLDER: Final[str] = "~/Desktop/"