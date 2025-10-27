# Path: scripts/clip_diag.py

import sys
# --- MODIFIED: Thay thế Typer bằng Argparse ---
import argparse
import logging
from pathlib import Path
from typing import Optional
# (Xóa import Enum và typer)
# --- END MODIFIED ---

# Common utilities
from utils.logging_config import setup_logging

# --- MODULE IMPORTS ---
from modules.clip_diag import (
    process_clipboard_content,
    execute_diagram_generation,
    DEFAULT_TO_ARG
)
# ----------------------

# --- CONSTANTS ---
THIS_SCRIPT_PATH = Path(__file__).resolve()

# --- REMOVED: Typer Enum ---
# class DiagramFormat(str, Enum):
#     svg = "svg"
#     png = "png"
# --- END REMOVED ---


# --- MODIFIED: Hàm chính sử dụng Argparse ---
def main():
    """
    Hàm điều phối chính. Xử lý diagram code (Graphviz/Mermaid) từ clipboard.
    """
    
    # 1. Định nghĩa Parser
    parser = argparse.ArgumentParser(
        description="Xử lý code diagram (Graphviz/Mermaid) từ clipboard và tạo file.",
        epilog="Mặc định: Mở file nguồn. Sử dụng -t để tạo và mở file ảnh.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument(
        "-t", "--to",
        default=DEFAULT_TO_ARG,
        choices=['svg', 'png'],
        help='Convert source code to an image file (svg or png) and open it. [Choices: svg, png]'
    )
    
    # Argparse dùng action="store_true" cho cờ boolean
    parser.add_argument(
        "-f", "--filter",
        action="store_true",
        help='Filter out emojis from the clipboard content before processing.'
    )

    args = parser.parse_args()

    # 2. Setup Logging
    logger = setup_logging(script_name="CDiag")
    logger.debug("CDiag script started.")
    
    # 3. Execute Core Logic
    try:
        # Lấy nội dung, phân tích và chuẩn bị tên file
        result = process_clipboard_content(
            logger=logger,
            filter_emoji=args.filter, # <-- Sử dụng args.filter (bool)
        )
        
        if result:
            # Truyền giá trị chuỗi (args.to là str hoặc None)
            output_format = args.to
            execute_diagram_generation(logger, result, output_format)
            
        else:
            # Nếu process_clipboard_content trả về None, lỗi/cảnh báo đã được log
            pass
            
    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)
# --- END MODIFIED ---


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ [Lệnh dừng] Hoạt động của tool đã bị dừng bởi người dùng.")
        sys.exit(1)