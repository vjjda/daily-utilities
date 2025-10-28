# Path: utils/logging_config.py
"""
Cấu hình logging tập trung cho dự án.

Cung cấp hàm `setup_logging` để tạo logger với cấu hình chuẩn:
- Ghi chi tiết (DEBUG) vào file log trong thư mục `logs/`.
- Ghi tối giản (INFO+) ra console (stdout).
- Sử dụng emoji cho các thông báo console quan trọng.
"""

import logging
import sys
from pathlib import Path
from typing import Final

# Import các hằng số cấu hình logging
from .constants import LOG_DIR_PATH, FILE_LOG_LEVEL, CONSOLE_LOG_LEVEL

# Định nghĩa các cấp độ log tùy chỉnh (ví dụ)
# SUCCESS = 25
# logging.addLevelName(SUCCESS, "SUCCESS")

# def log_success(self, message, *args, **kws):
#     if self.isEnabledFor(SUCCESS):
#         self._log(SUCCESS, message, args, **kws)
# logging.Logger.success = log_success


def setup_logging(script_name: str, console_level_str: str = CONSOLE_LOG_LEVEL) -> logging.Logger:
    """
    Cấu hình và trả về một logger cho một script cụ thể.

    Args:
        script_name: Tên của script (sẽ được dùng làm tên logger và tên file log).
        console_level_str: Cấp độ log tối thiểu cho console (ví dụ: "INFO", "DEBUG").

    Returns:
        Đối tượng `logging.Logger` đã được cấu hình.
    """

    # 1. Khởi tạo logger
    logger = logging.getLogger(script_name)
    logger.setLevel(logging.DEBUG) # Luôn bắt tất cả ở logger gốc

    # Xóa các handler cũ nếu có (tránh log lặp lại khi gọi hàm nhiều lần)
    if logger.hasHandlers():
        logger.handlers.clear()

    # 2. Đảm bảo thư mục logs tồn tại
    try:
        LOG_DIR_PATH.mkdir(exist_ok=True)
    except OSError as e:
        print(f"Lỗi: Không thể tạo thư mục log tại '{LOG_DIR_PATH}': {e}", file=sys.stderr) #
        # Có thể thoát ở đây hoặc để logger không ghi file
        # sys.exit(1)

    # --- 3. Cấu hình File Handler (ghi chi tiết) ---
    try:
        file_formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)-8s] (%(name)s) %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler = logging.FileHandler(LOG_DIR_PATH / f'{script_name}.log', encoding='utf-8') #
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(getattr(logging, FILE_LOG_LEVEL.upper(), logging.DEBUG))
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Lỗi: Không thể cấu hình ghi log vào file: {e}", file=sys.stderr) #

    # --- 4. Cấu hình Console Handler (ghi tối giản) ---
    try:
        # Định dạng đơn giản cho console
        console_formatter = logging.Formatter('%(message)s')
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        # Lấy cấp độ từ tham số hoặc hằng số, fallback về INFO nếu không hợp lệ
        console_level = getattr(logging, console_level_str.upper(), logging.INFO)
        console_handler.setLevel(console_level)
        logger.addHandler(console_handler)
    except Exception as e:
        print(f"Lỗi: Không thể cấu hình ghi log ra console: {e}", file=sys.stderr) #

    return logger

# ----------------------------------------------------------------------
# Các hàm Helper để log thông báo console thân thiện
# ----------------------------------------------------------------------

def log_start(logger: logging.Logger, message: str) -> None:
    """Ghi log thông báo bắt đầu (INFO) với emoji 🚀."""
    logger.info(f"🚀 {message}")

def log_success(logger: logging.Logger, message: str) -> None:
    """Ghi log thông báo thành công (INFO) với emoji ✅."""
    logger.info(f"✅ {message}")

# Lưu ý: Các hàm log_warning và log_error không cần thiết vì
# logger.warning() và logger.error() đã đủ rõ ràng.
# Chỉ cần thêm emoji khi gọi: logger.warning(f"⚠️ Cảnh báo...")
#                          logger.error(f"❌ Lỗi...")