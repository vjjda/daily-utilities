# Path: scripts/zsh_wrapper.py

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from utils.logging_config import setup_logging, log_success

    from modules.zsh_wrapper import DEFAULT_MODE, DEFAULT_VENV, run_zsh_wrapper

except ImportError as e:
    print(
        f"Lỗi: Không thể import utils/modules. Đảm bảo bạn đang chạy từ Project Root: {e}",
        file=sys.stderr,
    )
    sys.exit(1)


THIS_SCRIPT_PATH = Path(__file__).resolve()


def main():

    parser = argparse.ArgumentParser(
        description="Tạo một wrapper Zsh cho một script Python, tự động quản lý venv và PYTHONPATH.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "script_path_arg",
        type=str,
        help="Đường dẫn đến file Python cần wrap.\nUse '~' for home directory.",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Đường dẫn tạo wrapper. [Mặc định: bin/ (cho relative) hoặc $HOME/bin (cho absolute)].\nUse '~' for home directory.",
    )

    parser.add_argument(
        "-m",
        "--mode",
        type=str,
        default=DEFAULT_MODE,
        choices=["relative", "absolute"],
        help="Loại wrapper: 'relative' (project di chuyển được) hoặc 'absolute' (wrapper di chuyển được).",
    )

    parser.add_argument(
        "-r",
        "--root",
        type=str,
        default=None,
        help="Chỉ định Project Root. Mặc định: tự động tìm (find_git_root() từ file script).\nUse '~' for home directory.",
    )

    parser.add_argument(
        "-v",
        "--venv",
        type=str,
        default=DEFAULT_VENV,
        help="Tên thư mục virtual environment.",
    )

    parser.add_argument(
        "-f", "--force", action="store_true", help="Ghi đè file output nếu đã tồn tại."
    )

    args = parser.parse_args()

    logger = setup_logging(script_name="Zrap")
    logger.debug("Zrap script started.")

    try:

        success = run_zsh_wrapper(logger=logger, cli_args=args)

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