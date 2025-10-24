# Path: scripts/clip_diag.py

import sys
import argparse
import logging
from pathlib import Path

# Common utilities
from utils.logging_config import setup_logging

# --- MODULE IMPORTS ---
# --- MODIFIED: Import from module gateway ---
from modules.clip_diag import (
    process_clipboard_content,
    execute_diagram_generation,
    DEFAULT_TO_ARG
)
# --- END MODIFIED ---
# ----------------------

# --- CONSTANTS ---
THIS_SCRIPT_PATH = Path(__file__).resolve()

def main():
    """
    Main orchestration function.
    Parses args, sets up logging, and calls core logic.
    """
    
    parser = argparse.ArgumentParser(
        description="Process diagram code (Graphviz/Mermaid) from clipboard and generate files.",
        epilog="Default action opens the source file. Use -t to generate and open an image."
    )
    
    parser.add_argument(
        '-t', '--to',
        choices=['svg', 'png'],
        default=DEFAULT_TO_ARG,
        help='Convert source code to an image file (svg or png) and open it.'
    )
    parser.add_argument(
        '-f', '--filter',
        action='store_true',
        help='Filter out emojis from the clipboard content before processing.'
    )
    args = parser.parse_args()

    # 1. Setup Logging
    logger = setup_logging(script_name="CDiag")
    logger.debug("CDiag script started.")
    
    # 2. Execute Core Logic
    try:
        # Lấy nội dung, phân tích và chuẩn bị tên file
        result = process_clipboard_content(
            logger=logger,
            filter_emoji=args.filter,
        )
        
        if result:
            # Thực thi chuyển đổi và mở file
            execute_diagram_generation(logger, result, args.to)
        else:
            # Nếu process_clipboard_content trả về None, lỗi/cảnh báo đã được log
            pass
            
    except Exception as e:
        logger.error(f"❌ An unexpected error occurred: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ [Stop Command] Diagram utility stopped.")
        sys.exit(1)