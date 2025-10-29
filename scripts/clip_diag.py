# Path: scripts/clip_diag.py

"""
Entrypoint (cổng vào) cho cdiag (Clip Diagram).

Script này chịu trách nhiệm:
1. Thiết lập `sys.path` để import `utils` và `modules`.
2. Phân tích đối số dòng lệnh (Argparse).
3. Cấu hình logging.
4. Gọi `process_clipboard_content` (từ Core) để xử lý logic thuần túy.
5. Gọi `execute_diagram_generation` (từ Executor) để thực hiện side-effects.
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, Final

# Thiết lập `sys.path` để import các module của dự án
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

# Import các tiện ích chung
from utils.logging_config import setup_logging

# Import các thành phần của module 'clip_diag'
from modules.clip_diag import (
    process_clipboard_content,
    execute_diagram_generation,
    DEFAULT_TO_ARG # Giá trị mặc định cho --to
)

# --- HẰNG SỐ CỤ THỂ CHO ENTRYPOINT ---
THIS_SCRIPT_PATH: Final[Path] = Path(__file__).resolve()


def main():
    """
    Hàm điều phối chính.
    Xử lý diagram code (Graphviz/Mermaid) từ clipboard.
    """
    
    # 1. Định nghĩa Parser
    parser = argparse.ArgumentParser(
        description="Xử lý code diagram (Graphviz/Mermaid) từ clipboard và tạo file.",
        epilog="Mặc định: Mở file nguồn. Sử dụng -t để tạo và mở file ảnh.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument(
        "-t", "--to",
        default=DEFAULT_TO_ARG, # Mặc định là None
        choices=['svg', 'png'],
        help='Convert source code to an image file (svg or png) and open it.'
    )
    
    parser.add_argument(
        "-f", "--filter",
        action="store_true", # Cờ boolean, không cần giá trị
        help='Filter out emojis from the clipboard content before processing.'
    )

    args = parser.parse_args()

    # 2. Setup Logging
    logger = setup_logging(script_name="CDiag")
    logger.debug("CDiag script started.")
    
    # 3. Execute Core Logic và Executor
    try:
        # Lấy nội dung, phân tích và chuẩn bị tên file (Logic thuần túy)
        result = process_clipboard_content(
            logger=logger,
            filter_emoji=args.filter, # Giá trị boolean từ action="store_true"
        )
        
        if result:
            # Thực hiện side-effects: ghi file, chạy tool, mở file
            output_format: Optional[str] = args.to # Là 'svg', 'png', hoặc None
            execute_diagram_generation(logger, result, output_format)
            
        else:
            # Nếu process_clipboard_content trả về None,
            # lỗi/cảnh báo đã được log bên trong nó.
            pass
            
    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ [Lệnh dừng] Hoạt động của tool đã bị dừng bởi người dùng.")
        sys.exit(1)