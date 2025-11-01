# Path: scripts/zsh_wrapper.py
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, Final, Dict, Any

try:
    import argcomplete
except ImportError:
    argcomplete = None


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from utils.logging_config import setup_logging, log_success
    from utils.cli import handle_config_init_request

    from modules.zsh_wrapper import (
        DEFAULT_MODE,
        DEFAULT_VENV,
        run_zsh_wrapper,
        CONFIG_FILENAME,
        PROJECT_CONFIG_FILENAME,
        CONFIG_SECTION_NAME,
        ZRAP_DEFAULTS,
        TEMPLATE_FILENAME,
    )

except ImportError as e:
    print(
        f"Lỗi: Không thể import utils/modules. Đảm bảo bạn đang chạy từ Project Root: {e}",
        file=sys.stderr,
    )
    sys.exit(1)


THIS_SCRIPT_PATH = Path(__file__).resolve()

MODULE_DIR: Final[Path] = PROJECT_ROOT / "modules" / "zsh_wrapper"


def main():

    parser = argparse.ArgumentParser(
        description="Tạo một wrapper Zsh cho một script Python, tự động quản lý venv và PYTHONPATH.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    wrapper_group = parser.add_argument_group("Tùy chọn Tạo Wrapper")

    wrapper_group.add_argument(
        "script_path_arg",
        type=str,
        nargs="?",
        default=None,
        help="Đường dẫn đến file Python cần wrap (TÙY CHỌN nếu dùng -n).\nUse '~' for home directory.",
    )
    wrapper_group.add_argument(
        "-n",
        "--name",
        type=str,
        default=None,
        help="Tên của tool (ví dụ: 'ndoc'). Sẽ tự động tìm 'scripts/ndoc.py'.\nƯu tiên hơn 'script_path_arg'.",
    )
    wrapper_group.add_argument(
        "-M",
        "--multi-mode",
        action="store_true",
        help="Tạo cả hai wrapper 'relative' (cho bin/) và 'absolute' (cho ~/bin).",
    )
    wrapper_group.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Đường dẫn tạo wrapper. [Mặc định: bin/ (cho relative) hoặc $HOME/bin (cho absolute)].\nUse '~' for home directory.",
    )
    wrapper_group.add_argument(
        "-m",
        "--mode",
        type=str,
        default=DEFAULT_MODE,
        choices=["relative", "absolute"],
        help="Loại wrapper: 'relative' (project di chuyển được) hoặc 'absolute' (wrapper di chuyển được).",
    )
    wrapper_group.add_argument(
        "-r",
        "--root",
        type=str,
        default=None,
        help="Chỉ định Project Root. Mặc định: tự động tìm (find_git_root() từ file script).\nUse '~' for home directory.",
    )
    wrapper_group.add_argument(
        "-v",
        "--venv",
        type=str,
        default=None,
        help=f"Tên thư mục virtual environment (Mặc định: {DEFAULT_VENV}).",
    )
    wrapper_group.add_argument(
        "-f", "--force", action="store_true", help="Ghi đè file output nếu đã tồn tại."
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

    logger = setup_logging(script_name="Zrap")
    logger.debug("Zrap script started.")

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
            base_defaults=ZRAP_DEFAULTS,
        )
        if config_action_taken:
            sys.exit(0)

        success = run_zsh_wrapper(
            logger=logger, cli_args=args, project_root=PROJECT_ROOT
        )
        if success:
            log_success(logger, "Hoàn thành.")
        else:
            sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn ở entrypoint: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(
            "\n\n❌ [Lệnh dừng] Hoạt động của tool đã bị dừng bởi người dùng (Ctrl+C)."
        )
        sys.exit(1)
