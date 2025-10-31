# Path: scripts/pack_code.py
"""
Entrypoint (cổng vào) cho pcode (Pack Code).
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Final
import os 

# --- Thiết lập sys.path ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from utils.logging_config import setup_logging, log_success
    from utils.cli import handle_config_init_request, resolve_input_paths, resolve_reporting_root
    from utils.core import parse_comma_list
    from modules.pack_code.pack_code_config import (
        DEFAULT_START_PATH, DEFAULT_EXTENSIONS, DEFAULT_IGNORE,
        DEFAULT_CLEAN_EXTENSIONS, DEFAULT_OUTPUT_DIR,
        PROJECT_CONFIG_FILENAME, CONFIG_FILENAME, CONFIG_SECTION_NAME,
        DEFAULT_FORMAT_EXTENSIONS
    )
    from modules.pack_code import (
        process_pack_code_logic,
        execute_pack_code_action,
    )
except ImportError as e:
    print(f"Lỗi: Không thể import các tiện ích/module dự án: {e}", file=sys.stderr)
    sys.exit(1)

# SỬA: Thêm lại THIS_SCRIPT_PATH
THIS_SCRIPT_PATH: Final[Path] = Path(__file__).resolve()
MODULE_DIR: Final[Path] = PROJECT_ROOT / "modules" / "pack_code"
TEMPLATE_FILENAME: Final[str] = "pack_code.toml.template"
PCODE_DEFAULTS: Final[Dict[str, Any]] = {
    "output_dir": DEFAULT_OUTPUT_DIR,
    "extensions": list(parse_comma_list(DEFAULT_EXTENSIONS)),
    "ignore": list(parse_comma_list(DEFAULT_IGNORE)),
    "clean_extensions": sorted(list(DEFAULT_CLEAN_EXTENSIONS)),
    "format_extensions": sorted(list(DEFAULT_FORMAT_EXTENSIONS)),
}


def main():

    parser = argparse.ArgumentParser(
        description="Đóng gói nội dung của nhiều file/thư mục thành một file văn bản duy nhất.",
        epilog="Ví dụ: pcode ./src -e 'py,md' -o context.txt",
    )

    pack_group = parser.add_argument_group("Tùy chọn Đóng gói")
    pack_group.add_argument(
        "start_paths_arg",
        type=str,
        nargs="*",
        default=[],
        help='Các đường dẫn (file hoặc thư mục) để quét. Mặc định: ".".',
    )
    pack_group.add_argument(
        "-r",
        "--root",
        type=str,
        default=None,
        help="Đường dẫn gốc (Project Root) tường minh để tính toán '# Path:'.\nMặc định: Tự động tìm gốc Git từ các đường dẫn đầu vào.",
    )
    pack_group.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="File output để ghi. Mặc định: '[output_dir]/<start_name>_context.txt' (từ config).",
    )
    pack_group.add_argument(
        "-a",
        "--all-clean",
        action="store_true",
        help="Làm sạch (xóa docstring/comment) nội dung của các file có đuôi trong 'clean_extensions' trước khi đóng gói.",
    )
    pack_group.add_argument(
        "-f",
        "--format",
        action="store_true",
        help="Định dạng (format) nội dung của các file có đuôi trong 'format_extensions' (ví dụ: chạy Black cho .py).",
    )
    pack_group.add_argument(
        "-e",
        "--extensions",
        type=str,
        default=None,
        help="Chỉ bao gồm các đuôi file này (vd: 'py,md'). Hỗ trợ +/-/~.",
    )
    pack_group.add_argument(
        "-x",
        "--clean-extensions",
        type=str,
        default=None,
        help="Chỉ định/sửa đổi danh sách đuôi file cần làm sạch KHI -a được bật (vd: 'py,js'). Hỗ trợ +/-/~.",
    )
    pack_group.add_argument(
        "-I",
        "--ignore",
        type=str,
        default=None,
        help="Các pattern (giống .gitignore) để bỏ qua (THÊM vào config).",
    )
    pack_group.add_argument(
        "-N",
        "--no-gitignore",
        action="store_true",
        help="Không tôn trọng các file .gitignore.",
    )
    pack_group.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Chỉ in danh sách file sẽ được đóng gói (không đọc/in nội dung).",
    )
    pack_group.add_argument(
        "--stdout",
        action="store_true",
        help="In kết quả ra stdout (console) thay vì ghi file.",
    )
    pack_group.add_argument(
        "--no-header",
        action="store_true",
        help="Không in header phân tách ('===== path/to/file.py =====').",
    )
    pack_group.add_argument(
        "--no-tree",
        action="store_true",
        help="Không in cây thư mục của các file được chọn ở đầu output.",
    )
    pack_group.add_argument(
        "--copy",
        action="store_true",
        dest="copy_to_clipboard",
        help="Sao chép file output (không phải nội dung) vào clipboard hệ thống.",
    )

    config_group = parser.add_argument_group("Khởi tạo Cấu hình (chạy riêng)")
    config_group.add_argument(
        "-c",
        "--config-project",
        action="store_true",
        help=f"Khởi tạo/cập nhật section [{CONFIG_SECTION_NAME}] trong {PROJECT_CONFIG_FILENAME}.",
    )
    config_group.add_argument(
        "-C",
        "--config-local",
        action="store_true",
        help=f"Khởi tạo/cập nhật file {CONFIG_FILENAME} cục bộ.",
    )

    args = parser.parse_args()

    logger = setup_logging(script_name="pcode")
    logger.debug("Script pcode bắt đầu.")

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
            base_defaults=PCODE_DEFAULTS,
        )
        if config_action_taken:
            sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi khi khởi tạo config: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)
    
    # 1. Resolve tất cả đường dẫn
    validated_paths: List[Path] = resolve_input_paths(
        logger=logger,
        raw_paths=args.start_paths_arg,
        default_path_str=DEFAULT_START_PATH
    )
    if not validated_paths:
        logger.warning("Không tìm thấy đường dẫn hợp lệ nào để quét. Đã dừng.")
        sys.exit(0)

    # 2. Xác định Gốc Báo Cáo
    reporting_root = resolve_reporting_root(
        logger, 
        validated_paths, 
        args.root 
    )

    # 3. Phân loại file/thư mục
    files_to_process: List[Path] = [p for p in validated_paths if p.is_file()]
    dirs_to_scan: List[Path] = [p for p in validated_paths if p.is_dir()]

    # 4. Chuẩn bị CLI args
    output_path_obj = Path(args.output).expanduser() if args.output else None
    
    cli_args_dict = {
        "output": output_path_obj,
        "stdout": args.stdout,
        "extensions": args.extensions,
        "ignore": args.ignore,
        "no_gitignore": args.no_gitignore,
        "dry_run": args.dry_run,
        "no_header": args.no_header,
        "no_tree": args.no_tree,
        "copy_to_clipboard": args.copy_to_clipboard,
        "all_clean": args.all_clean,
        "clean_extensions": args.clean_extensions,
        "format": args.format,
    }

    try:
        # 5. Gọi Core
        result = process_pack_code_logic(
            logger=logger,
            cli_args=cli_args_dict,
            files_to_process=files_to_process,
            dirs_to_scan=dirs_to_scan,
            reporting_root=reporting_root, 
            script_file_path=THIS_SCRIPT_PATH # SỬA: Giờ đã hợp lệ
        )
        if result:
            execute_pack_code_action(logger=logger, result=result)
        if (
            not (args.dry_run or args.stdout)
            and result
            and result.get("status") == "ok"
        ):
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