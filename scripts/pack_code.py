#!/usr/bin/env python3
# Path: scripts/pack_code.py

"""
Entrypoint (cổng vào) cho pcode (Pack Code).

Script này chịu trách nhiệm:
1. Thiết lập `sys.path` để import `utils` và `modules`.
2. Phân tích đối số dòng lệnh (Argparse).
3. Cấu hình logging.
4. Xử lý các yêu cầu khởi tạo config (`--config-local`, `--config-project`).
5. Xác định thư mục để tải config dựa trên `start_path` hoặc CWD.
6. Tải config file (gọi Loader).
7. Chuẩn bị dict `cli_args` cho Core.
8. Gọi `process_pack_code_logic` (từ Core) để lấy Result Object.
9. Gọi `execute_pack_code_action` (từ Executor) để thực hiện side-effects.
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Final

# Thiết lập `sys.path` để import các module của dự án
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from utils.logging_config import setup_logging, log_success
    from utils.cli import handle_config_init_request
    from utils.core import parse_comma_list

    # Import các thành phần của module 'pack_code'
    from modules.pack_code.pack_code_config import (
        DEFAULT_START_PATH, DEFAULT_EXTENSIONS, DEFAULT_IGNORE,
        DEFAULT_OUTPUT_DIR,
        PROJECT_CONFIG_FILENAME, CONFIG_FILENAME, CONFIG_SECTION_NAME
    )
    from modules.pack_code import (
        process_pack_code_logic,
        execute_pack_code_action,
        load_config_files # Cần để tải config trước khi gọi core
    )
except ImportError as e:
    print(f"Lỗi: Không thể import utils/modules... Lỗi: {e}", file=sys.stderr)
    sys.exit(1)

# --- HẰNG SỐ CỤ THỂ CHO ENTRYPOINT ---
MODULE_DIR: Final[Path] = PROJECT_ROOT / "modules" / "pack_code"
TEMPLATE_FILENAME: Final[str] = "pack_code.toml.template"

# Cấu hình mặc định để điền vào file template .toml khi khởi tạo
PCODE_DEFAULTS: Final[Dict[str, Any]] = {
    "output_dir": DEFAULT_OUTPUT_DIR,
    "extensions": list(parse_comma_list(DEFAULT_EXTENSIONS)), # Chuyển thành list
    "ignore": list(parse_comma_list(DEFAULT_IGNORE)),       # Chuyển thành list
}

def main():
    """Hàm điều phối chính."""

    # 1. Định nghĩa Parser
    parser = argparse.ArgumentParser(
        [cite_start]description="Đóng gói nội dung của nhiều file/thư mục thành một file văn bản duy nhất.", # [cite: 558]
        epilog="Ví dụ: pcode ./src -e 'py,md' -o context.txt"
    )

    pack_group = parser.add_argument_group("Packing Options")
    pack_group.add_argument(
        "start_path",
        type=str,
        [cite_start]nargs="?", # Tùy chọn, để có thể chạy `pcode` không cần arg [cite: 559]
        [cite_start]default=None, # Mặc định None, sẽ lấy từ config hoặc DEFAULT_START_PATH [cite: 559]
        help='Đường dẫn (file hoặc thư mục) để bắt đầu quét. Mặc định: "." hoặc giá trị trong config.' [cite_start]# [cite: 559]
    )
    pack_group.add_argument(
        "-o", "--output",
        type=str,
        default=None, # Mặc định None, sẽ được tính toán sau
        help="File output để ghi. Mặc định: '[output_dir]/<start_name>_context.txt' (lấy từ config)."
    )
    pack_group.add_argument(
        "-S", "--stdout",
        action="store_true",
        help='In kết quả ra stdout (console) thay vì ghi file.'
    )
    pack_group.add_argument(
        "-e", "--extensions",
        type=str,
        default=None, # Mặc định None, core sẽ hợp nhất với config/default
        help="Chỉ bao gồm các đuôi file này (vd: 'py,md'). Hỗ trợ +/-/~."
    )
    pack_group.add_argument(
        "-I", "--ignore",
        type=str,
        default=None, # Mặc định None, core sẽ hợp nhất với config/default
        help='Các pattern (giống .gitignore) để bỏ qua (THÊM vào config).'
    )
    pack_group.add_argument(
        "-N", "--no-gitignore",
        action="store_true",
        help='Không tôn trọng các file .gitignore.'
    )
    pack_group.add_argument(
        "-d", "--dry-run",
        action="store_true",
        help='Chỉ in danh sách file sẽ được đóng gói (không đọc/in nội dung).'
    )
    pack_group.add_argument(
        "--no-header",
        action="store_true",
        help="Không in header phân tách ('===== path/to/file.py =====')."
    )
    pack_group.add_argument(
        "--no-tree",
        action="store_true",
        help='Không in cây thư mục của các file được chọn ở đầu output.'
    )
    pack_group.add_argument(
        "--copy",
        action="store_true",
        help="Sao chép file output (không phải nội dung) vào clipboard hệ thống."
    )

    config_group = parser.add_argument_group("Config Initialization (Chạy riêng lẻ)")
    config_group.add_argument(
        "-c", "--config-project",
        action="store_true",
        help=f"Khởi tạo/cập nhật section [{CONFIG_SECTION_NAME}] trong {PROJECT_CONFIG_FILENAME}."
    )
    config_group.add_argument(
        "-C", "--config-local",
        action="store_true",
        help=f"Khởi tạo/cập nhật file {CONFIG_FILENAME} (scope 'local')."
    )

    args = parser.parse_args()

    # 2. Setup Logging
    logger = setup_logging(script_name="pcode")
    logger.debug("pcode script started.")

    # 3. Xử lý Config Init
    try:
        config_action_taken = handle_config_init_request(
            logger=logger,
            config_project=args.config_project,
            config_local=args.config_local,
            module_dir=MODULE_DIR,
            template_filename=TEMPLATE_FILENAME,
            config_filename=CONFIG_FILENAME,
            project_config_filename=PROJECT_CONFIG_FILENAME,
            config_section_name=CONFIG_SECTION_NAME,
            base_defaults=PCODE_DEFAULTS
        )
        if config_action_taken:
            sys.exit(0) # Kết thúc nếu đã xử lý config
    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi khi khởi tạo config: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)

    # 4. Chuẩn bị Path Objects (chỉ expanduser, resolve sẽ làm trong core)
    # Nếu args.start_path là None, giữ nguyên None
    start_path_obj = Path(args.start_path).expanduser() if args.start_path else None
    # Nếu args.output là None, giữ nguyên None
    output_path_obj = Path(args.output).expanduser() if args.output else None

    # 5. Xác định thư mục để tải config file
    # Dùng start_path nếu có, nếu không thì dùng CWD
    temp_start_path_for_config = start_path_obj if start_path_obj else Path.cwd().resolve()

    config_load_dir: Path
    # Nếu start_path là file, load config từ thư mục chứa file
    if temp_start_path_for_config.is_file():
        config_load_dir = temp_start_path_for_config.parent
    else: # Nếu là thư mục (hoặc CWD), load config từ chính nó
        config_load_dir = temp_start_path_for_config

    # 6. Tải Config File (I/O Đọc)
    logger.debug(f"Đang tải config từ: {config_load_dir.as_posix()}")
    file_config = load_config_files(config_load_dir, logger)

    # 7. Chuẩn bị dict `cli_args` cho Core
    cli_args_dict = {
        "start_path": start_path_obj, # Path obj hoặc None
        "output": output_path_obj,     # Path obj hoặc None
        "stdout": args.stdout,
        "extensions": args.extensions, # String hoặc None
        "ignore": args.ignore,       # String hoặc None
        "no_gitignore": args.no_gitignore,
        "dry_run": args.dry_run,
        "no_header": args.no_header,
        "no_tree": args.no_tree,
        "copy_to_clipboard": args.copy,
    }

    # 8. Chạy Core Logic và Executor
    try:
        # Core sẽ xử lý logic, trả về Result Object
        result = process_pack_code_logic(
            logger=logger,
            cli_args=cli_args_dict,
            file_config=file_config
        )

        # Executor thực hiện side-effect dựa trên Result Object
        if result:
            execute_pack_code_action(
                logger=logger,
                result=result
            )

        # In thông báo hoàn thành (trừ dry_run và stdout)
        if not (args.dry_run or args.stdout) and result and result.get('status') == 'ok':
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