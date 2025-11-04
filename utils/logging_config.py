# Path: utils/logging_config.py
import logging
import sys

from .constants import CONSOLE_LOG_LEVEL, FILE_LOG_LEVEL, LOG_DIR_PATH


def setup_logging(
    script_name: str, console_level_str: str = CONSOLE_LOG_LEVEL
) -> logging.Logger:

    logger = logging.getLogger(script_name)
    logger.setLevel(logging.DEBUG)

    if logger.hasHandlers():
        logger.handlers.clear()

    try:
        LOG_DIR_PATH.mkdir(exist_ok=True)
    except OSError as e:
        print(
            f"Lỗi: Không thể tạo thư mục log tại '{LOG_DIR_PATH}': {e}", file=sys.stderr
        )

    try:
        file_formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)-8s] (%(name)s) %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler = logging.FileHandler(
            LOG_DIR_PATH / f"{script_name}.log", encoding="utf-8"
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(getattr(logging, FILE_LOG_LEVEL.upper(), logging.DEBUG))
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Lỗi: Không thể cấu hình ghi log vào file: {e}", file=sys.stderr)

    try:

        console_formatter = logging.Formatter("%(message)s")
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)

        console_level = getattr(logging, console_level_str.upper(), logging.INFO)
        console_handler.setLevel(console_level)
        logger.addHandler(console_handler)
    except Exception as e:
        print(f"Lỗi: Không thể cấu hình ghi log ra console: {e}", file=sys.stderr)

    return logger


def log_start(logger: logging.Logger, message: str) -> None:
    logger.info(f"🚀 {message}")


def log_success(logger: logging.Logger, message: str) -> None:
    logger.info(f"✅ {message}")
