# Path: scripts/format_code.py

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, Final, Dict, Any, List, Set


try:
    import argcomplete
except ImportError:
    argcomplete = None


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from utils.logging_config import setup_logging

    from utils.cli import (
        handle_config_init_request,
        resolve_input_paths,
        resolve_reporting_root,
    )
    from utils.core import parse_comma_list
    from utils.core.git import find_commit_by_hash, get_diffed_files
    from utils.core.config_helpers import generate_config_hash

    from modules.format_code import (
        process_format_code_logic,
        execute_format_code_action,
        DEFAULT_START_PATH,
        DEFAULT_EXTENSIONS,
        DEFAULT_IGNORE,
        CONFIG_FILENAME,
        PROJECT_CONFIG_FILENAME,
        CONFIG_SECTION_NAME,
    )
    from modules.format_code.format_code_internal import (
        load_config_files,
        merge_format_code_configs,
    )
except ImportError as e:
    print(f"Lỗi: Không thể import project utilities/modules: {e}", file=sys.stderr)
    sys.exit(1)


THIS_SCRIPT_PATH: Final[Path] = Path(__file__).resolve()

MODULE_DIR: Final[Path] = PROJECT_ROOT / "modules" / "format_code"


def main():

    parser = argparse.ArgumentParser(
        description="Công cụ quét và định dạng (format) file mã nguồn.",
        epilog="Mặc định: Chạy ở chế độ sửa lỗi tương tác. Dùng -d để chạy thử.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    pack_group = parser.add_argument_group("Tùy chọn Định dạng Code")
    pack_group.add_argument(
        "start_path_arg",
        type=str,
        nargs="*",
        default=[],
        help=f'Các đường dẫn (file hoặc thư mục) để quét. Mặc định: "{DEFAULT_START_PATH}".',
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
        "-f",
        "--force",
        action="store_true",
        help="Ghi đè file mà không hỏi xác nhận (chỉ áp dụng ở chế độ fix).",
    )
    pack_group.add_argument(
        "-g",
        "--git-commit",
        action="store_true",
        help="Tự động commit các thay đổi vào Git sau khi hoàn tất.",
    )

    pack_group.add_argument(
        "-w",
        "--stepwise",
        action="store_true",
        help="Chế độ gia tăng. Chỉ quét các file đã thay đổi kể từ lần chạy cuối cùng có cùng cài đặt.",
    )

    if argcomplete:
        argcomplete.autocomplete(parser)

    args = parser.parse_args()

    logger = setup_logging(script_name="FormatCode")
    logger.debug("FormatCode script started.")

    stepwise: bool = getattr(args, "stepwise", False)
    validated_paths: List[Path] = []

    preliminary_paths_str = (
        args.start_path_arg if args.start_path_arg else [DEFAULT_START_PATH]
    )
    preliminary_paths = [Path(p).expanduser() for p in preliminary_paths_str]
    reporting_root = resolve_reporting_root(
        logger, preliminary_paths, cli_root_arg=None
    )

    file_config_data = load_config_files(reporting_root, logger)
    merged_config = merge_format_code_configs(
        logger,
        cli_extensions=getattr(args, "extensions", None),
        cli_ignore=getattr(args, "ignore", None),
        file_config_data=file_config_data,
    )

    last_run_sha: Optional[str] = None
    if stepwise:

        settings_to_hash = {
            "extensions": sorted(list(merged_config["final_extensions_list"])),
            "ignore": sorted(list(merged_config["final_ignore_list"])),
        }
        config_hash = generate_config_hash(settings_to_hash, logger)
        logger.info(f"Chế độ Stepwise (-w): Tìm kiếm cài đặt hash: {config_hash}")

        last_run_sha = find_commit_by_hash(logger, reporting_root, config_hash)

    if stepwise and last_run_sha:

        logger.info(f"Tìm thấy commit khớp: {last_run_sha[:7]}. Lấy diff file...")
        diffed_files = get_diffed_files(logger, reporting_root, last_run_sha)

        relevant_extensions = merged_config["final_extensions_list"]

        validated_paths = [
            f
            for f in diffed_files
            if f.is_file() and "".join(f.suffixes).lstrip(".") in relevant_extensions
        ]

        if not validated_paths:
            logger.info(
                "✅ Không có file nào (khớp extension) thay đổi kể từ lần chạy cuối."
            )
            sys.exit(0)

        logger.info(f"Sẽ chỉ quét {len(validated_paths)} file đã thay đổi.")

    else:

        if stepwise:
            logger.warning(
                "Không tìm thấy commit nào khớp. Sẽ thực hiện quét toàn bộ..."
            )

        validated_paths = resolve_input_paths(
            logger=logger,
            raw_paths=args.start_path_arg,
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

        files_to_fix = process_format_code_logic(
            logger=logger,
            files_to_process=files_to_process,
            dirs_to_scan=dirs_to_scan,
            cli_args=args,
            script_file_path=THIS_SCRIPT_PATH,
        )

        execute_format_code_action(
            logger=logger,
            all_files_to_fix=files_to_fix,
            cli_args=args,
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
        print("\n\n❌ [Lệnh dừng] Đã dừng định dạng Code.")
        sys.exit(1)
