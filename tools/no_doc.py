# Path: tools/no_doc.py
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, Final, Dict, Any, List, Set
import hashlib
import json


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
    )
    from utils.core import parse_comma_list
    from utils.core.config_helpers import generate_config_hash

    from modules.no_doc import (
        orchestrate_no_doc,
        MODULE_DIR,
        TEMPLATE_FILENAME,
        NDOC_DEFAULTS,
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
        "-b",
        "--beautify",
        action="store_true",
        dest="format",
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

    logger = setup_logging(script_name="NDoc")
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

    try:
        orchestrate_no_doc(
            logger=logger,
            cli_args=args,
            project_root=PROJECT_ROOT,
            this_script_path=THIS_SCRIPT_PATH,
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
