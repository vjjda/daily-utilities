#!/usr/bin/env python
# Path: utils/core.py

import logging
import sys
from pathlib import Path

# Placeholder cho hàm logging sẽ được thiết kế chi tiết sau
def configure_logger(script_name: str, log_dir: str = "logs"):
    """
    Cấu hình logging cho script.
    - Log chi tiết vào file trong thư mục 'logs'.
    - Log tối giản ra console (stdout).
    """
    
    # 1. Tạo thư mục logs nếu chưa tồn tại
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # 2. Định dạng cho file log (chi tiết)
    file_formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)-8s] (%(name)s) %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 3. Định dạng cho console (tối giản, dùng emoji)
    # LƯU Ý: Logging library hơi phức tạp để dùng emoji trực tiếp, nên ta chỉ dùng print() đơn giản cho giao diện người dùng
    console_formatter = logging.Formatter('%(message)s')

    root_logger = logging.getLogger(script_name)
    root_logger.setLevel(logging.DEBUG) # Ghi tất cả vào file

    # --- File Handler (Ghi vào file) ---
    file_handler = logging.FileHandler(log_path / f'{script_name}.log')
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)

    # --- Console Handler (In ra màn hình) ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO) # Chỉ in các thông báo quan trọng ra console
    root_logger.addHandler(console_handler)

    # Tối ưu: Loại bỏ root handler nếu có (tránh in 2 lần)
    if logging.getLogger().hasHandlers():
        logging.getLogger().handlers.clear()

    print(f"✨ [SETUP] Đã cấu hình logging cho script: {script_name}")
    return root_logger

def log_success(logger, message):
    """Ghi log thành công, hiển thị emoji cho người dùng."""
    logger.info(f"✅ {message}")

