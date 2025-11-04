# Path: tools/bootstrap_tool.py
import argparse
import sys
from pathlib import Path
from typing import Final

try:
    import argcomplete
except ImportError:
    argcomplete = None

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from modules.bootstrap import (
        BOOTSTRAP_DEFAULTS,
        CONFIG_SECTION_NAME,
        MODULE_DIR,
        PROJECT_CONFIG_FILENAME,
        PROJECT_CONFIG_ROOT_KEY,
        TEMPLATE_FILENAME,
        orchestrate_bootstrap,
    )
    from utils.cli import ConfigInitializer, run_cli_app
    from utils.logging_config import setup_logging
except ImportError as e:
    print(f"Lỗi: Không thể import utils hoặc gateway bootstrap: {e}", file=sys.stderr)
    sys.exit(1)


def main():
    logger = setup_logging(script_name="Btool", console_level_str="INFO")
    logger.debug("Script bootstrap bắt đầu.")

    parser = argparse.ArgumentParser(
        description="Bootstrap (khởi tạo) một tool utility mới từ file *.spec.toml.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "spec_file_path_str",
        type=str,
        nargs="?",
        default=None,
        help="Đường dẫn đến file *.spec.toml (ví dụ: docs/drafts/new_tool.spec.toml).\n"
        "Bắt buộc cho chế độ chạy (run), bị bỏ qua nếu dùng -s hoặc -c.",
    )

    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Ghi đè (overwrite) các file/thư mục đã tồn tại.",
    )

    run_group = parser.add_argument_group("Tùy chọn Chế độ Run (Mặc định)")
    run_group.add_argument(
        "-i",
        "--interface",
        type=str,
        choices=["typer", "argparse"],
        default=None,
        help="(Chế độ Run) Ghi đè loại interface (typer/argparse) được định nghĩa trong file spec.",
    )

    init_group = parser.add_argument_group("Tùy chọn Khởi tạo (Chạy riêng lẻ)")
    init_group.add_argument(
        "-s",
        "--init-spec",
        type=str,
        nargs="?",
        const="new_tool.spec.toml",
        dest="init_spec_path_str",
        help="Khởi tạo một file .spec.toml mới từ template.\n"
        "Tùy chọn cung cấp đường dẫn (ví dụ: -s 'path/to/my_spec.toml').\n"
        "Nếu không có đường dẫn, sẽ tạo 'new_tool.spec.toml' ở thư mục hiện tại.",
    )
    init_group.add_argument(
        "-c",
        "--config-project",
        action="store_true",
        help=f"Khởi tạo/cập nhật section [bootstrap] trong {PROJECT_CONFIG_FILENAME}.",
    )

    if argcomplete:
        argcomplete.autocomplete(parser)

    args = parser.parse_args()

    try:
        config_initializer = ConfigInitializer(
            logger=logger,
            module_dir=MODULE_DIR,
            template_filename=TEMPLATE_FILENAME,
            config_filename="",
            project_config_filename=PROJECT_CONFIG_FILENAME,
            config_section_name=CONFIG_SECTION_NAME,
            base_defaults=BOOTSTRAP_DEFAULTS,
        )

        config_initializer.check_and_handle_requests(
            argparse.Namespace(config_project=args.config_project, config_local=False)
        )
    except SystemExit:
        sys.exit(0)
    except Exception as e:
        logger.error(f"Lỗi khi chạy ConfigInitializer: {e}")
        sys.exit(1)

    run_cli_app(
        logger=logger,
        orchestrator_func=orchestrate_bootstrap,
        cli_args=args,
        project_root=PROJECT_ROOT,
    )


if __name__ == "__main__":
    main()
