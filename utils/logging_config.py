#!/usr/bin/env python
# Path: utils/logging_config.py

import logging
import sys
from pathlib import Path

# Cấp độ logging tùy chỉnh cho console:
# INFO: Thông báo thành công/khởi động (dùng emoji)
# WARNING: Cảnh báo
# ERROR: Lỗi

def configure_project_logger(script_name: str, log_dir: str = "logs", console_level=logging.INFO):
    """
    Cấu hình logging cho script.
    - Ghi chi tiết (DEBUG) vào file log.
    - Ghi tối giản (INFO/WARNING/ERROR) ra console (stdout).
    """
    
    # 1. Khởi tạo logger
    logger = logging.getLogger(script_name)
    logger.setLevel(logging.DEBUG) # Mức thấp nhất để đảm bảo tất cả đều được ghi vào file

    # Loại bỏ các handler cũ nếu có, để tránh logger bị cấu hình lại nhiều lần
    if logger.hasHandlers():
        logger.handlers.clear()

    # 2. Tạo thư mục logs
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # --- Định dạng cho File Log (Chi tiết) ---
    file_formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)-8s] (%(name)s) %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # --- File Handler ---
    file_handler = logging.FileHandler(log_path / f'{script_name}.log')
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    # --- Console Handler (Thân thiện với người dùng) ---
    # Ta dùng định dạng đơn giản, và sẽ dùng hàm helper để thêm emoji khi cần
    console_formatter = logging.Formatter('%(message)s')
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(console_level) # Chỉ hiển thị INFO trở lên
    logger.addHandler(console_handler)

    return logger

# ----------------------------------------------------------------------
# Hàm Helper để tạo đầu ra console thân thiện
# ----------------------------------------------------------------------

def log_start(logger, message: str):
    """Ghi log bắt đầu, hiển thị emoji khởi động."""
    logger.info(f"🚀 {message}")

def log_success(logger, message: str):
    """Ghi log thành công, hiển thị emoji thành công."""
    logger.info(f"✅ {message}")
    
def log_warning(logger, message: str):
    """Ghi log cảnh báo, hiển thị emoji cảnh báo."""
    logger.warning(f"⚠️ CẢNH BÁO: {message}")

def log_error(logger, message: str):
    """Ghi log lỗi, hiển thị emoji lỗi."""
    logger.error(f"❌ LỖI: {message}")

# Sau khi cấu hình, ta có thể dùng logger.debug(), logger.error(), v.v...