# Path: tools/pack_code.py
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

    from modules.pack_code import (
        process_pack_code_logic,
        execute_pack_code_action,
        MODULE_DIR,
        TEMPLATE_FILENAME,
        PCODE_DEFAULTS,
        DEFAULT_START_PATH,
        CONFIG_FILENAME,
        PROJECT_CONFIG_FILENAME,
        CONFIG_SECTION_NAME,
    )
except ImportError as e:
    print(f"Lỗi: Không thể import project utilities/modules: {e}", file=sys.stderr)
    sys.exit(1)

THIS_SCRIPT_PATH: Final[Path] = Path(__file__).resolve()


def main():
    parser = argparse.ArgumentParser(
        description="Đóng gói mã nguồn thành một file context duy nhất cho LLM.",
        epilog="Ví dụ: pcode . -e 'py,md' -a -o 'my_context.txt'",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    pack_group = parser.add_argument_group("Tùy chọn Đóng gói Code")
    pack_group.add_argument(
        "start_paths_arg",
        type=str,
        nargs="*",
        default=[],
        help=f'Các đường dẫn (file hoặc thư mục) để quét. Mặc định: "{DEFAULT_START_PATH}".',
    )
    pack_group.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Chỉ định file output. Mặc định: tự động tạo trong 'output_dir'.",
    )
    pack_group.add_argument(
        "-e",
        "--extensions",
        type=str,
        default=None,
        help="Danh sách đuôi file cần BAO GỒM. Hỗ trợ + (thêm) và ~ (bớt).",
    )
    pack_group.add_argument(
        "-I",
        "--ignore",
        type=str,
        default=None,
        help="Danh sách pattern (giống .gitignore) để BỎ QUA (THÊM vào config).",
    )
    pack_group.add_argument(
        "-i",
        "--include",
        type=str,
        default=None,
        help="Bộ lọc dương (inclusion filter). CHỈ giữ lại file/thư mục khớp (THÊM vào config).",
    )
    pack_group.add_argument(
        "-N",
        "--no-gitignore",
        action="store_true",
        help="Không tự động đọc và áp dụng các quy tắc từ file .gitignore.",
    )
    pack_group.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Chế độ chạy thử. Chỉ hiển thị cây thư mục và danh sách file, không đọc/ghi nội dung.",
    )
    pack_group.add_argument(
        "-a",
        "--all-clean",
        action="store_true",
        help="Làm sạch nội dung (xóa docstring/comment) của các file trong 'clean_extensions'.",
    )
    pack_group.add_argument(
        "-x",
        "--clean-extensions",
        type=str,
        default=None,
        help="Ghi đè/sửa đổi danh sách đuôi file cần LÀM SẠCH (khi -a được bật). Hỗ trợ + và ~.",
    )
    pack_group.add_argument(
        "-b",
        "--beautify",
        action="store_true",
        dest="format",
        help="Định dạng (format) code TRƯỚC KHI đóng gói (ví dụ: chạy Black cho .py).",
    )
    pack_group.add_argument(
        "--stdout",
        action="store_true",
        help="In kết quả ra màn hình (stdout) thay vì ghi vào file.",
    )
    pack_group.add_argument(
        "--no-header",
        action="store_true",
        help="Không in dòng header '[[START_FILE_CONTENT: ...]]' trước nội dung mỗi file.",
    )
    pack_group.add_argument(
        "--no-tree",
        action="store_true",
        help="Không hiển thị cây thư mục ở đầu file output.",
    )
    pack_group.add_argument(
        "--copy",
        action="store_true",
        dest="copy_to_clipboard",
        help="Tự động sao chép ĐƯỜNG DẪN file output vào clipboard.",
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

    if argcomplete:
        argcomplete.autocomplete(parser)

    args = parser.parse_args()

    logger = setup_logging(script_name="PCode")
    logger.debug("PCode script started.")

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

    validated_paths: List[Path] = resolve_input_paths(
        logger=logger,
        raw_paths=args.start_paths_arg,
        default_path_str=DEFAULT_START_PATH,
    )

    if not validated_paths:
        logger.warning("Không tìm thấy đường dẫn hợp lệ nào để quét. Đã dừng.")
        sys.exit(0)

    reporting_root = resolve_reporting_root(logger, validated_paths, cli_root_arg=None)

    try:
        cli_args_dict = vars(args)

        results_from_core = process_pack_code_logic(
            logger=logger,
            cli_args=cli_args_dict,
            validated_paths=validated_paths,
            reporting_root=reporting_root,
            script_file_path=THIS_SCRIPT_PATH,
        )

        execute_pack_code_action(logger=logger, result=results_from_core)

    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ [Lệnh dừng] Đã dừng đóng gói Code.")
        sys.exit(1)
