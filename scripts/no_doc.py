# Path: scripts/no_doc.py
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, Final, Dict, Any, List, Set

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from utils.logging_config import setup_logging
    from utils.cli import handle_config_init_request, resolve_input_paths
    from utils.core import parse_comma_list

    from modules.no_doc import (
        process_no_doc_logic,
        execute_ndoc_action,
        DEFAULT_START_PATH,
        DEFAULT_EXTENSIONS,
        DEFAULT_IGNORE,
        DEFAULT_FORMAT_EXTENSIONS,
        CONFIG_FILENAME,
        PROJECT_CONFIG_FILENAME,
        CONFIG_SECTION_NAME,
    )
except ImportError as e:
    print(f"Lỗi: Không thể import project utilities/modules: {e}", file=sys.stderr)
    sys.exit(1)

THIS_SCRIPT_PATH: Final[Path] = Path(__file__).resolve()
MODULE_DIR: Final[Path] = PROJECT_ROOT / "modules" / "no_doc"
TEMPLATE_FILENAME: Final[str] = "no_doc.toml.template"

NDOC_DEFAULTS: Final[Dict[str, Any]] = {
    "extensions": sorted(list(DEFAULT_EXTENSIONS)),
    "ignore": sorted(list(DEFAULT_IGNORE)),
    "format_extensions": sorted(list(DEFAULT_FORMAT_EXTENSIONS)),
}


def main():

    parser = argparse.ArgumentParser(
        description="Công cụ quét và xóa docstring (và tùy chọn comment) khỏi file mã nguồn.",
        epilog="Mặc định: Chạy ở chế độ sửa lỗi. Dùng -d để chạy thử.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    pack_group = parser.add_argument_group("Tùy chọn Xử lý Docstring")
    pack_group.add_argument(
        "start_paths_arg",
        type=str,
        nargs="*",
        default=[],
        help=f'Các đường dẫn (file hoặc thư mục) để quét. Mặc định: "{DEFAULT_START_PATH}".',
    )
    pack_group.add_argument(
        "-a",
        "--all-clean",
        action="store_true",
        help="Loại bỏ cả docstring và tất cả comments (#) khỏi file (ngoại trừ shebang).",
    )

    pack_group.add_argument(
        "-f",
        "--format",
        action="store_true",
        help="Định dạng (format) code SAU KHI làm sạch (ví dụ: chạy Black cho .py).",
    )
    pack_group.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Chỉ chạy ở chế độ kiểm tra (dry-run) và báo cáo các file cần sửa, không thực hiện ghi file.",
    )
    pack_group.add_argument(
        "-e",
        "--extensions",
        type=str,
        default=None,
        help="Danh sách các đuôi file cần quét (phân cách bởi dấu phẩy). Hỗ trợ + (thêm) và ~ (bớt).",
    )
    pack_group.add_argument(
        "-I",
        "--ignore",
        type=str,
        default=None,
        help="Danh sách pattern (giống .gitignore) để bỏ qua khi quét (THÊM vào config).",
    )
    pack_group.add_argument(
        "-F",
        "--force",
        action="store_true",
        help="Ghi đè file mà không hỏi xác nhận (chỉ áp dụng ở chế độ fix).",
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
        help=f"Khởi tạo/cập nhật file {CONFIG_FILENAME} (scope 'local').",
    )

    args = parser.parse_args()

    logger = setup_logging(script_name="Ndoc")
    logger.debug("Ndoc script started.")

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
            base_defaults=NDOC_DEFAULTS,
        )
        if config_action_taken:
            sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi khi khởi tạo config: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)

    validated_paths: List[Path] = resolve_input_paths(
        logger=logger,
        raw_paths=args.start_paths_arg,
        default_path_str=DEFAULT_START_PATH,
    )

    if not validated_paths:
        logger.warning("Không tìm thấy đường dẫn hợp lệ nào để quét. Đã dừng.")
        sys.exit(0)

    files_to_process: List[Path] = []
    dirs_to_scan: List[Path] = []
    for path in validated_paths:
        if path.is_file():
            files_to_process.append(path)
        elif path.is_dir():
            dirs_to_scan.append(path)

    try:
        results_from_core = process_no_doc_logic(
            logger=logger,
            files_to_process=files_to_process,
            dirs_to_scan=dirs_to_scan,
            cli_args=args,
            script_file_path=THIS_SCRIPT_PATH,
        )

        reporting_root = Path.cwd()

        execute_ndoc_action(
            logger=logger,
            all_files_to_fix=results_from_core,
            dry_run=args.dry_run,
            force=args.force,
            scan_root=reporting_root,
            git_warning_str="",
        )
    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ [Lệnh dừng] Đã dừng xóa Docstring.")
        sys.exit(1)