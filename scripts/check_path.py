# Path: scripts/check_path.py
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Optional, Set, Dict, Any, Final
import os

try:
    import tomllib
except ImportError:
    try:
        import toml as tomllib
    except ImportError:
        tomllib = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from utils.logging_config import setup_logging, log_success

from utils.cli import (
    handle_config_init_request,
    resolve_input_paths,
    resolve_reporting_root,
)


from modules.check_path import (
    process_check_path_logic,
    execute_check_path_action,
    DEFAULT_EXTENSIONS,
    DEFAULT_IGNORE,
    PROJECT_CONFIG_FILENAME,
    CONFIG_SECTION_NAME,
    CONFIG_FILENAME,
)

THIS_SCRIPT_PATH: Final[Path] = Path(__file__).resolve()
MODULE_DIR: Final[Path] = THIS_SCRIPT_PATH.parent.parent / "modules" / "check_path"
TEMPLATE_FILENAME: Final[str] = "check_path.toml.template"

CPATH_DEFAULTS: Final[Dict[str, Any]] = {
    "extensions": DEFAULT_EXTENSIONS,
    "ignore": DEFAULT_IGNORE,
}


def main():

    parser = argparse.ArgumentParser(
        description="Kiểm tra (và tùy chọn sửa) các comment '# Path:' trong file nguồn.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    path_check_group = parser.add_argument_group("Path Checking Options")
    path_check_group.add_argument(
        "start_paths_arg",
        type=str,
        nargs="*",
        default=[],
        help='Các đường dẫn (file hoặc thư mục) để quét (mặc định: ".").',
    )
    path_check_group.add_argument(
        "-r",
        "--root",
        type=str,
        default=None,
        help="Đường dẫn gốc (Project Root) tường minh để tính toán '# Path:'.\nMặc định: Tự động tìm gốc Git từ các đường dẫn đầu vào.",
    )

    path_check_group.add_argument(
        "-e",
        "--extensions",
        type=str,
        default=None,
        help="Các đuôi file. Hỗ trợ +/-/~.",
    )
    path_check_group.add_argument(
        "-I",
        "--ignore",
        type=str,
        default=None,
        help="Danh sách pattern để bỏ qua (THÊM vào config/default).",
    )
    path_check_group.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Chỉ chạy ở chế độ 'dry-run' (kiểm tra). Mặc định là chạy 'fix'.",
    )
    path_check_group.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Tự động sửa file mà không hỏi xác nhận.",
    )

    config_group = parser.add_argument_group("Config Initialization (Chạy riêng lẻ)")

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
        help=f"Khởi tạo/cập nhật file {CONFIG_FILENAME} (scope 'local').",
    )

    args = parser.parse_args()

    logger = setup_logging(script_name="CPath")
    logger.debug("CPath script started.")

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
            base_defaults=CPATH_DEFAULTS,
        )
        if config_action_taken:
            sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi khi khởi tạo config: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)

    validated_paths: List[Path] = resolve_input_paths(
        logger=logger, raw_paths=args.start_paths_arg, default_path_str="."
    )
    if not validated_paths:
        logger.warning("Không tìm thấy đường dẫn hợp lệ nào để quét. Đã dừng.")
        sys.exit(0)

    reporting_root = resolve_reporting_root(logger, validated_paths, args.root)

    files_to_process: List[Path] = [p for p in validated_paths if p.is_file()]
    dirs_to_scan: List[Path] = [p for p in validated_paths if p.is_dir()]

    check_mode = args.dry_run
    force_mode = args.force

    try:
        files_to_fix = process_check_path_logic(
            logger=logger,
            files_to_process=files_to_process,
            dirs_to_scan=dirs_to_scan,
            cli_args=args,
            script_file_path=THIS_SCRIPT_PATH,
            reporting_root=reporting_root,
        )

        execute_check_path_action(
            logger=logger,
            all_files_to_fix=files_to_fix,
            dry_run=check_mode,
            force=force_mode,
            scan_root=reporting_root,
        )

    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ [Lệnh dừng] Đã dừng kiểm tra đường dẫn.")
        sys.exit(1)