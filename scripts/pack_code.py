# Path: scripts/pack_code.py

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from utils.logging_config import setup_logging, log_success
    from modules.pack_code.pack_code_config import DEFAULT_START_PATH, DEFAULT_EXTENSIONS, DEFAULT_IGNORE
    from modules.pack_code import (
        process_pack_code_logic,
        execute_pack_code_action
    )
except ImportError:
    print(f"Lỗi: Không thể import utils/modules...", file=sys.stderr)
    sys.exit(1)

def main():
    """Hàm điều phối chính."""

    # 1. Định nghĩa Parser (Giữ nguyên)
    parser = argparse.ArgumentParser(
        description="Đóng gói nội dung của nhiều file/thư mục thành một file văn bản duy nhất.",
        epilog="Ví dụ: pcode ./src -e 'py,md' -o context.txt"
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
        "-o", "--output",
        type=str,
        default=None,
        help="File output để ghi. Mặc định: 'tmp/<input_name>.txt'"
    )
    parser.add_argument(
        "-S", "--stdout",
        action="store_true",
        help='In kết quả ra stdout (console) thay vì ghi file.'
    )
    parser.add_argument(
        "-e", "--extensions",
        type=str,
        default='md,py,txt,json,xml,yaml,yml,ini,cfg,cfg.py,sh,bash,zsh',
        help="Chỉ bao gồm các đuôi file này (vd: 'py,md'). Hỗ trợ +/-."
    )
    parser.add_argument(
        "-I", "--ignore",
        type=str,
        default='.venv,venv,__pycache__,.git,.hg,.svn,.DS_Store',
        help='Các pattern (giống .gitignore) để bỏ qua (THÊM vào config).'
    )
    parser.add_argument(
        "-N", "--no_gitignore",
        action="store_true",
        help='Không tôn trọng các file .gitignore.'
    )
    parser.add_argument(
        "-d", "--dry_run",
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

    # 2. Setup Logging (Giữ nguyên)
    logger = setup_logging(script_name="pcode")
    logger.debug("pcode script started.")

    # --- Mở rộng Path (nếu có) ---
    
    # --- MODIFIED: Thêm .resolve() ---
    start_path_path = Path(args.start_path).expanduser().resolve() if args.start_path else None
    # --- END MODIFIED ---
    
    output_path = Path(args.output).expanduser() if args.output else None
    # --- Hết mở rộng Path ---

    # 3. Chạy Core Logic (Giữ nguyên)
    try:
        result = process_pack_code_logic(
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
            execute_pack_code_action(
                logger=logger,
                result=result
            )

        # --- MODIFIED: Chỉ log "Hoàn thành" nếu không phải dry_run/stdout ---
        if not (args.dry_run or args.stdout) and result and result.get('status') == 'ok':
            log_success(logger, "Hoàn thành.")
        # --- END MODIFIED ---

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