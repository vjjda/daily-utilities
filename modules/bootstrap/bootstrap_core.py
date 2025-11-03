# Path: modules/bootstrap/bootstrap_core.py
import logging
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, Tuple, Optional


from .bootstrap_internal import (
    run_init_spec_logic,
    run_bootstrap_logic,
)

__all__ = [
    "orchestrate_bootstrap",
]


def orchestrate_bootstrap(
    logger: logging.Logger, cli_args: argparse.Namespace, project_root: Path
) -> None:

    try:
        init_spec_path_str = getattr(cli_args, "init_spec_path_str", None)
        spec_file_path_str = getattr(cli_args, "spec_file_path_str", None)
        force = getattr(cli_args, "force", False)

        if init_spec_path_str:
            logger.info(f"🚀 Yêu cầu khởi tạo file spec (chế độ -s)...")
            run_init_spec_logic(
                logger=logger,
                project_root=project_root,
                init_spec_path_str=init_spec_path_str,
                force=force,
            )

        elif spec_file_path_str:
            run_bootstrap_logic(
                logger=logger, cli_args=cli_args, project_root=project_root
            )

        else:
            logger.error(
                "Lỗi: Không có file spec nào được cung cấp và cũng không yêu cầu tạo mới."
            )
            logger.error("Gợi ý: Chạy `btool -s <tên_file>` để tạo file spec mới, hoặc")
            logger.error("       chạy `btool <tên_file.spec.toml>` để khởi tạo tool.")
            sys.exit(1)

    except SystemExit:
        raise
    except Exception as e:
        logger.error(
            f"❌ Đã xảy ra lỗi không mong muốn trong trình điều phối bootstrap: {e}"
        )
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)
