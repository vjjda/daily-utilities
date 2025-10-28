# Path: scripts/zsh_wrapper.py
import sys
import argparse 
import logging
from pathlib import Path
from typing import Optional

# (Xóa import typer)

# --- 1. Tự xác định Project Root của tool (daily-utilities) để import ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent # 
sys.path.append(str(PROJECT_ROOT)) # 

try:
    from utils.logging_config import setup_logging, log_success
    
    # --- MODIFIED: Import hàm điều phối mới ---
    from modules.zsh_wrapper import (
        DEFAULT_MODE, 
        DEFAULT_VENV, 
        run_zsh_wrapper # <-- Hàm điều phối chính
        # (Xóa các import không cần thiết khác)
    )
    # --- END MODIFIED ---
    
except ImportError as e:
    print(f"Lỗi: Không thể import utils/modules. Đảm bảo bạn đang chạy từ Project Root: {e}", file=sys.stderr) # 
    sys.exit(1)

# --- CONSTANTS ---
THIS_SCRIPT_PATH = Path(__file__).resolve()


def main():
    """
    Tạo một wrapper Zsh cho một script Python, tự động quản lý venv và PYTHONPATH.
    (Phiên bản Argparse)
    """
    
    # 1. Định nghĩa Parser (Giữ nguyên)
    parser = argparse.ArgumentParser(
        description="Tạo một wrapper Zsh cho một script Python, tự động quản lý venv và PYTHONPATH.",
        formatter_class=argparse.RawTextHelpFormatter # 
    )
    
    # Arguments
    parser.add_argument(
        "script_path_arg", 
        type=str,
        help="Đường dẫn đến file Python cần wrap.\nUse '~' for home directory." # [cite: 559-560]
    )
    
    # Options
    parser.add_argument(
        "-o", "--output", 
        type=str,
        default=None,
        help="Đường dẫn tạo wrapper. [Mặc định: bin/ (cho relative) hoặc $HOME/bin (cho absolute)].\nUse '~' for home directory." # 
    )
    
    parser.add_argument(
        "-m", "--mode", 
        type=str, # 
        default=DEFAULT_MODE, 
        choices=['relative', 'absolute'],
        help="Loại wrapper: 'relative' (project di chuyển được) hoặc 'absolute' (wrapper di chuyển được)." # 
    )
    
    parser.add_argument(
        "-r", "--root", 
        type=str,
        default=None,
        help="Chỉ định Project Root. Mặc định: tự động tìm (find_git_root() từ file script).\nUse '~' for home directory." # [cite: 561-562]
    )
    
    parser.add_argument(
        "-v", "--venv", 
        type=str,
        default=DEFAULT_VENV, 
        help="Tên thư mục virtual environment." # 
    )
    
    parser.add_argument(
        "-f", "--force", 
        action="store_true",
        help="Ghi đè file output nếu đã tồn tại." # [cite: 562-563]
    )
    
    args = parser.parse_args()
    
    # --- 2. Setup Logging (Giữ nguyên) ---
    logger = setup_logging(script_name="Zrap")
    logger.debug("Zrap script started.")

    # --- REMOVED: Initial Path Expansion (chuyển vào core) ---
    # --- REMOVED: Gọi core lần 1 ---
    # --- REMOVED: Xử lý fallback ---
    # --- REMOVED: Gọi resolve_root_interactively ---
    # --- REMOVED: Gọi resolve_output_path_interactively ---
    # --- REMOVED: Tạo args_for_core_final ---
    # --- REMOVED: Gọi core lần 2 và executor ---

    # --- 3. Gọi Hàm Điều Phối Chính (Mới) ---
    try:
        success = run_zsh_wrapper(logger=logger, cli_args=args)
        
        if success:
            log_success(logger, "Hoàn thành.") # 
        else:
            # Lỗi đã được log bên trong run_zsh_wrapper
            sys.exit(1) # Thoát với mã lỗi
            
    except Exception as e:
        # Bắt các lỗi không mong muốn khác
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn ở entrypoint: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)
    # --- END MODIFIED ---


if __name__ == "__main__":
    try: 
        main()
    except KeyboardInterrupt: 
        print("\n\n❌ [Lệnh dừng] Hoạt động của tool đã bị dừng bởi người dùng (Ctrl+C).") # 
        sys.exit(1)