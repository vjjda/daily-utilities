#!/usr/bin/env python3
# Path: scripts/zsh_wrapper.py

import sys
import argparse
import logging
from pathlib import Path

# --- Thêm PROJECT_ROOT vào sys.path để import utils/modules ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from utils.logging_config import setup_logging, log_success
    # --- MODULE IMPORTS ---
    from modules.zsh_wrapper.zsh_wrapper_core import process_zsh_wrapper_logic
    from modules.zsh_wrapper.zsh_wrapper_executor import execute_zsh_wrapper_action
    # ----------------------
except ImportError as e:
    print(f"Lỗi: Không thể import utils/modules: {e}", file=sys.stderr)
    sys.exit(1)

# --- CONSTANTS ---
THIS_SCRIPT_PATH = Path(__file__).resolve()

def main():
    """
    Main orchestration function.
    Parses args, sets up logging, and calls core logic.
    """
    
    # --- 1. Phân tích đối số (Parse args) ---
    parser = argparse.ArgumentParser(
        description="Tạo một wrapper Zsh cho một script Python, tự động quản lý venv và PYTHONPATH.",
        epilog="Ví dụ: zrap scripts/check_path.py -o bin/cpath -m relative"
    )

    parser.add_argument("script_path", help="Đường dẫn đến file Python cần wrap.")
    parser.add_argument("-o", "--output", required=True, help="Đường dẫn để tạo file wrapper Zsh.")
    parser.add_argument("-m", "--mode", choices=["relative", "absolute"], default="relative", help="Loại wrapper: 'relative' (project di chuyển được) hoặc 'absolute' (wrapper di chuyển được).")
    parser.add_argument("-r", "--root", help="Chỉ định Project Root. Mặc định: tự động tìm (find_git_root() từ file script).")
    parser.add_argument("-v", "--venv", default=".venv", help="Tên thư mục virtual environment.")
    parser.add_argument("-f", "--force", action="store_true", help="Ghi đè file output nếu đã tồn tại.")

    args = parser.parse_args()

    # 2. Setup Logging
    logger = setup_logging(script_name="Zrap")
    logger.debug("Zrap script started.")
    
    # 3. Execute Core Logic
    try:
        # --- GỌI LOGIC TỪ MODULES ---
        
        result = process_zsh_wrapper_logic(
            logger=logger,
            args=args
        )
        
        if result:
            execute_zsh_wrapper_action(
                logger=logger,
                result=result
            )
        
        # --------------------------------
        
        log_success(logger, "Hoàn thành.")
            
    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ [Lệnh dừng] Hoạt động của tool đã bị dừng.")
        sys.exit(1)