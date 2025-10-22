#!/usr/bin/env python
# Path: scripts/clean_desktop.py

# ----------------------------------------------------------------------
# BOOTSTRAP MODULE HANDLING (Giúp import nội bộ package 'utils')
# ----------------------------------------------------------------------
import sys
from pathlib import Path
import os
import argparse

# Tính toán đường dẫn gốc của dự án:
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Thêm thư mục gốc dự án vào sys.path
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# ----------------------------------------------------------------------

# Import từ package nội bộ 'utils'
from utils.core import configure_logger, log_success


def main():
    # 1. Cấu hình Argparse để nhận đối số từ Terminal
    parser = argparse.ArgumentParser(description="Tiện ích dọn dẹp màn hình và thư mục.")
    parser.add_argument(
        "target", 
        nargs="?",
        default=".", 
        help="Thư mục mục tiêu để dọn dẹp. Mặc định là thư mục hiện tại (.)."
    )
    args = parser.parse_args()

    # 2. Cấu hình Logging
    logger = configure_logger(script_name="clean_desktop")
    
    # 3. Xử lý đường dẫn
    # .resolve() giúp chuyển đổi '.' thành đường dẫn tuyệt đối (dựa trên CWD của Shell)
    target_path = Path(args.target).resolve()
    logger.info(f"🚀 Bắt đầu dọn dẹp tại: {target_path}")

    # --- Logic Tự động hóa macOS ---
    # Ví dụ:
    # files_moved = do_cleanup(target_path) 
    
    # --- Kết thúc ---
    
    log_success(logger, f"Dọn dẹp thành công! {target_path}")

if __name__ == "__main__":
    main()
