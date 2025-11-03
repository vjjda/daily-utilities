# Path: utils/cli/entrypoint_handler.py
import logging
import sys
import argparse
from typing import Callable, Any

__all__ = ["run_cli_app"]


def run_cli_app(
    logger: logging.Logger,
    orchestrator_func: Callable[..., None],
    cli_args: argparse.Namespace,
    **kwargs: Any,
) -> None:
    try:

        orchestrator_func(logger=logger, cli_args=cli_args, **kwargs)

    except KeyboardInterrupt:
        print("\n\n❌ [Lệnh dừng] Hoạt động đã bị dừng bởi người dùng.")
        sys.exit(1)
    except SystemExit as e:

        sys.exit(e.code)
    except Exception as e:

        logger.error(f"❌ Đã xảy ra lỗi không mong muốn: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)
