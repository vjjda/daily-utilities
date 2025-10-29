# Path: scripts/pack_code.py

"""
Cổng vào (entrypoint) cho pcode (Pack Code).

Script này xử lý:
1. Thiết lập `sys.path` để import các module dự án.
2. Phân tích đối số dòng lệnh (Argparse).
3. Cấu hình logging.
4. Xử lý yêu cầu khởi tạo config (--config-local, --config-project).
5. Chuẩn bị dict `cli_args` cơ bản cho Core.
6. Gọi logic cốt lõi (`process_pack_code_logic`).
7. Gọi logic thực thi (`execute_pack_code_action`) dựa trên kết quả.
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Final

# Thiết lập sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from utils.logging_config import setup_logging, log_success
    from utils.cli import handle_config_init_request
    from utils.core import parse_comma_list
    from modules.pack_code.pack_code_config import (
        DEFAULT_START_PATH, DEFAULT_EXTENSIONS, DEFAULT_IGNORE,
        DEFAULT_CLEAN_EXTENSIONS,
        DEFAULT_OUTPUT_DIR,
        PROJECT_CONFIG_FILENAME, CONFIG_FILENAME, CONFIG_SECTION_NAME
    )
    from modules.pack_code import (
        process_pack_code_logic,
        execute_pack_code_action,
    )
except ImportError as e:
    print(f"Lỗi: Không thể import các tiện ích/module dự án. Lỗi: {e}", file=sys.stderr)
    sys.exit(1)

MODULE_DIR: Final[Path] = PROJECT_ROOT / "modules" / "pack_code"
TEMPLATE_FILENAME: Final[str] = "pack_code.toml.template"
PCODE_DEFAULTS: Final[Dict[str, Any]] = {
    "output_dir": DEFAULT_OUTPUT_DIR,
    "extensions": list(parse_comma_list(DEFAULT_EXTENSIONS)),
    "ignore": list(parse_comma_list(DEFAULT_IGNORE)),
    "clean_extensions": sorted(list(DEFAULT_CLEAN_EXTENSIONS))
}

def main():
    """Hàm điều phối chính cho CLI."""

    # 1. Định nghĩa Parser
    parser = argparse.ArgumentParser(
        description="Đóng gói nội dung của nhiều file/thư mục thành một file văn bản duy nhất.",
        epilog="Ví dụ: pcode ./src -e 'py,md' -o context.txt"
    )

    # --- Nhóm Tùy chọn Đóng gói ---
    pack_group = parser.add_argument_group("Tùy chọn Đóng gói") #
    pack_group.add_argument(
        "start_path",
        type=str,
        nargs="?", # Tùy chọn
        default=None, # Core sẽ xử lý default/config
        help='Đường dẫn (file hoặc thư mục) để bắt đầu quét. Mặc định: "." hoặc giá trị trong config.'
    )
    pack_group.add_argument(
        "-o", "--output",
        type=str,
        default=None, # Core sẽ tính toán nếu None
        help="File output để ghi. Mặc định: '[output_dir]/<start_name>_context.txt' (từ config)."
    )
    pack_group.add_argument(
        "-a", "--all-clean",
        action="store_true",
        help="Làm sạch (xóa docstring/comment) nội dung của các file có đuôi trong 'clean_extensions' trước khi đóng gói."
    )
    pack_group.add_argument(
        "-e", "--extensions",
        type=str,
        default=None, # Core sẽ hợp nhất
        help="Chỉ bao gồm các đuôi file này (vd: 'py,md'). Hỗ trợ +/-/~."
    )
    pack_group.add_argument(
        "-x", "--clean-extensions",
        type=str,
        default=None, # Core sẽ hợp nhất
        help="Chỉ định/sửa đổi danh sách đuôi file cần làm sạch KHI -a được bật (vd: 'py,js'). Hỗ trợ +/-/~."
    )
    pack_group.add_argument(
        "-I", "--ignore",
        type=str,
        default=None, # Core sẽ hợp nhất
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
        "--stdout",
        action="store_true",
        help='In kết quả ra stdout (console) thay vì ghi file.'
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

    # --- Nhóm Khởi tạo Config (chạy riêng) ---
    config_group = parser.add_argument_group("Khởi tạo Cấu hình (chạy riêng)") #
    config_group.add_argument(
        "-c", "--config-project",
        action="store_true",
        help=f"Khởi tạo/cập nhật section [{CONFIG_SECTION_NAME}] trong {PROJECT_CONFIG_FILENAME}."
    )
    config_group.add_argument(
        "-C", "--config-local",
        action="store_true",
        help=f"Khởi tạo/cập nhật file {CONFIG_FILENAME} cục bộ." #
    )

    args = parser.parse_args()

    # 2. Cấu hình Logging
    logger = setup_logging(script_name="pcode")
    logger.debug("Script pcode bắt đầu.") #

    # 3. Xử lý Yêu cầu Khởi tạo Config
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
            sys.exit(0) # Kết thúc thành công sau khi init config
    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi khi khởi tạo config: {e}") #
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)

    # 4. Chuẩn bị Path Objects từ CLI (chỉ expanduser)
    start_path_obj = Path(args.start_path).expanduser() if args.start_path else None
    output_path_obj = Path(args.output).expanduser() if args.output else None

    # 5. Chuẩn bị dict `cli_args` cho Core
    cli_args_dict = {
        "start_path": start_path_obj,
        "output": output_path_obj,
        "stdout": args.stdout,
        "extensions": args.extensions, # Dùng để chọn file
        "ignore": args.ignore,
        "no_gitignore": args.no_gitignore,
        "dry_run": args.dry_run,
        "no_header": args.no_header,
        "no_tree": args.no_tree,
        "copy_to_clipboard": args.copy,
        "all_clean": args.all_clean, # Bật/tắt clean
        "clean_extensions": args.clean_extensions, # <-- THÊM MỚI: String từ CLI (-x)
    }

    # 6. Chạy Core Logic và Executor
    try:
        result = process_pack_code_logic(
            logger=logger,
            cli_args=cli_args_dict,
        )
        if result:
            execute_pack_code_action(
                logger=logger,
                result=result
            )
        if not (args.dry_run or args.stdout) and result and result.get('status') == 'ok':
            log_success(logger, "Hoạt động hoàn tất thành công.")
    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Hoạt động bị dừng bởi người dùng.")
        sys.exit(1)