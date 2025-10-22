#!/usr/bin/env python
# Path: utils/logging_config.py

import logging
import sys
from pathlib import Path
# --- MODIFIED: Import các hằng số mới ---
from .constants import LOG_DIR_PATH, FILE_LOG_LEVEL, CONSOLE_LOG_LEVEL
# --- END MODIFIED ---

# Cấp độ logging tùy chỉnh cho console:
# ...

# --- MODIFIED: Đơn giản hóa chữ ký hàm ---
def setup_logging(script_name: str, console_level_str: str = CONSOLE_LOG_LEVEL):
# --- END MODIFIED ---
    """
    Cấu hình logging cho script.
    - Ghi chi tiết (DEBUG) vào file log.
    - Ghi tối giản (INFO/WARNING/ERROR) ra console (stdout).
    """
    
    # 1. Khởi tạo logger
    logger = logging.getLogger(script_name)
    logger.setLevel(logging.DEBUG) # Mức thấp nhất

    if logger.hasHandlers():
        logger.handlers.clear()

    # --- MODIFIED: Sử dụng hằng số LOG_DIR_PATH ---
    # 2. Tạo thư mục logs (dùng đường dẫn tuyệt đối)
    LOG_DIR_PATH.mkdir(exist_ok=True)
    # --- END MODIFIED ---
    
    # --- Định dạng cho File Log (Chi tiết) ---
    file_formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)-8s] (%(name)s) %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # --- File Handler ---
    # --- MODIFIED: Sử dụng LOG_DIR_PATH ---
    file_handler = logging.FileHandler(LOG_DIR_PATH / f'{script_name}.log')
    file_handler.setFormatter(file_formatter)
    # --- MODIFIED: Sử dụng hằng số FILE_LOG_LEVEL ---
    file_handler.setLevel(getattr(logging, FILE_LOG_LEVEL.upper(), logging.DEBUG))
    logger.addHandler(file_handler)
    # --- END MODIFIED ---

    # --- Console Handler (Thân thiện với người dùng) ---
    console_formatter = logging.Formatter('%(message)s')
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    # --- MODIFIED: Sử dụng hằng số CONSOLE_LOG_LEVEL ---
    console_handler.setLevel(getattr(logging, console_level_str.upper(), logging.INFO))
    logger.addHandler(console_handler)
    # --- END MODIFIED ---

    return logger

# ----------------------------------------------------------------------
# Hàm Helper để tạo đầu ra console thân thiện
# ----------------------------------------------------------------------

def log_start(logger, message: str):
    """Logs start message with emoji to INFO level (visible on console)."""
    logger.info(f"🚀 {message}")

def log_success(logger, message: str):
    """Logs success message with emoji to INFO level (visible on console)."""
    logger.info(f"✅ {message}")
    
# Ta loại bỏ log_warning, log_error. 
# Người dùng sẽ dùng: logger.warning("⚠️ Warning message"), logger.error("❌ Error message")