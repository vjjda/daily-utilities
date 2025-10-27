# Path: scripts/pack.py

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from utils.logging_config import setup_logging, log_success
    from modules.pack.pack_config import DEFAULT_START_PATH
    from modules.pack import (
        process_pack_logic,
        execute_pack_action
    )
except ImportError:
    print(f"Lỗi: Không thể import utils/modules...", file=sys.stderr)
    sys.exit(1)

def main():
    """Hàm điều phối chính."""

    # 1. Định nghĩa Parser
    parser = argparse.ArgumentParser(
        description="Đóng gói nội dung của nhiều file/thư mục thành một file văn bản duy nhất.",
        epilog="Ví dụ: cpack ./src -e 'py,md' -o context.txt"
    )

    # --- Các arguments được tạo tự động ---
        parser.add_argument(
        "start_path",
        type=str,
        nargs="?",
        default='.',
        help='Đường dẫn (file hoặc thư mục) để bắt đầu quét.'
    )
    parser.add_argument(
        "-o",, "--output",
        type=str,
        default=None,
        help="File output để ghi. Mặc định: 'tmp/<input_name>.txt'"
    )
    parser.add_argument(
        "-S",, "--stdout",
        action="store_true",
        help='In kết quả ra stdout (console) thay vì ghi file.'
    )
    parser.add_argument(
        "-e",, "--extensions",
        type=str,
        default=None,
        help="Chỉ bao gồm các đuôi file này (vd: 'py,md'). Hỗ trợ +/-."
    )
    parser.add_argument(
        "-I",, "--ignore",
        type=str,
        default=None,
        help='Các pattern (giống .gitignore) để bỏ qua (THÊM vào config).'
    )
    parser.add_argument(
        "-N",, "--no_gitignore",
        action="store_true",
        help='Không tôn trọng các file .gitignore.'
    )
    parser.add_argument(
        "-d",, "--dry_run",
        action="store_true",
        help='Chỉ in danh sách file sẽ được đóng gói (không in nội dung).'
    )
    parser.add_argument(
        "--no_header",
        action="store_true",
        help="Không in header phân tách ('===== path/to/file.py =====')."
    )
    parser.add_argument(
        "--no_tree",
        action="store_true",
        help='Không in cây thư mục của các file được chọn ở đầu output.'
    )
    # --- Hết arguments ---

    args = parser.parse_args()

    # 2. Setup Logging
    logger = setup_logging(script_name="CPack")
    logger.debug("CPack script started.")

    # --- Mở rộng Path (nếu có) ---
        start_path_path = Path(args.start_path).expanduser() if args.start_path else None
    output_path = Path(args.output).expanduser() if args.output else None
    # --- Hết mở rộng Path ---

    # 3. Chạy Core Logic
    try:
        result = process_pack_logic(
            logger=logger,
        start_path=start_path_path,
        output=output_path,
        stdout=args.stdout,
        extensions=args.extensions,
        ignore=args.ignore,
        no_gitignore=args.no_gitignore,
        dry_run=args.dry_run,
        no_header=args.no_header,
        no_tree=args.no_tree,
        )

        if result:
            execute_pack_action(
                logger=logger,
                result=result
            )

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