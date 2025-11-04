# Path: tools/pack_code.py
import argparse
import sys
from pathlib import Path
from typing import Final

try:
    import argcomplete
except ImportError:
    argcomplete = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from modules.pack_code import (
        CONFIG_FILENAME,
        CONFIG_SECTION_NAME,
        DEFAULT_START_PATH,
        MODULE_DIR,
        PCODE_DEFAULTS,
        PROJECT_CONFIG_FILENAME,
        TEMPLATE_FILENAME,
        orchestrate_pack_code,
    )
    from utils.cli import (
        ConfigInitializer,
        run_cli_app,
    )
    from utils.logging_config import setup_logging
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

    config_initializer = ConfigInitializer(
        logger=logger,
        module_dir=MODULE_DIR,
        template_filename=TEMPLATE_FILENAME,
        config_filename=CONFIG_FILENAME,
        project_config_filename=PROJECT_CONFIG_FILENAME,
        config_section_name=CONFIG_SECTION_NAME,
        base_defaults=PCODE_DEFAULTS,
    )
    config_initializer.check_and_handle_requests(args)

    run_cli_app(
        logger=logger,
        orchestrator_func=orchestrate_pack_code,
        cli_args=args,
        this_script_path=THIS_SCRIPT_PATH,
    )


if __name__ == "__main__":
    main()
