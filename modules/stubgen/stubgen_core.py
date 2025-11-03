# Path: modules/stubgen/stubgen_core.py
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
import sys

from .stubgen_internal import process_stubgen_task_file, process_stubgen_task_dir
from .stubgen_executor import execute_stubgen_action

from utils.core import load_text_template

from utils.cli import (
    resolve_input_paths,
    resolve_reporting_root,
)

MODULE_DIR = Path(__file__).parent
TEMPLATE_FILENAME = "pyi.py.template"

StubResult = Dict[str, Any]


__all__ = ["process_stubgen_logic", "orchestrate_stubgen"]


def orchestrate_stubgen(
    logger: logging.Logger, cli_args: argparse.Namespace, this_script_path: Path
) -> None:

    validated_paths: List[Path] = resolve_input_paths(
        logger=logger, raw_paths=cli_args.target_paths, default_path_str="."
    )

    if not validated_paths:
        logger.warning("Không tìm thấy đường dẫn hợp lệ nào để quét. Đã dừng.")
        sys.exit(0)

    reporting_root = resolve_reporting_root(logger, validated_paths, cli_root_arg=None)

    try:
        files_to_create, files_to_overwrite = process_stubgen_logic(
            logger=logger,
            cli_args=cli_args,
            script_file_path=this_script_path,
            validated_paths=validated_paths,
        )

        execute_stubgen_action(
            logger=logger,
            files_to_create=files_to_create,
            files_to_overwrite=files_to_overwrite,
            force=cli_args.force,
            scan_root=reporting_root,
            cli_args=cli_args,
        )
    except Exception as e:
        logger.error(
            f"❌ Đã xảy ra lỗi không mong muốn trong 'orchestrate_stubgen': {e}"
        )
        logger.debug("Traceback:", exc_info=True)
        raise


def process_stubgen_logic(
    logger: logging.Logger,
    cli_args: argparse.Namespace,
    script_file_path: Path,
    validated_paths: List[Path],
) -> Tuple[List[StubResult], List[StubResult]]:

    try:
        template_path = MODULE_DIR / TEMPLATE_FILENAME
        stub_template_str = load_text_template(template_path, logger)
    except Exception as e:
        logger.error(f"❌ Không thể tải PYI template: {e}")
        raise

    total_files_to_create: List[StubResult] = []
    total_files_to_overwrite: List[StubResult] = []
    processed_files: Set[Path] = set()
    reporting_root = Path.cwd()

    files_to_process: List[Path] = [p for p in validated_paths if p.is_file()]
    dirs_to_scan: List[Path] = [p for p in validated_paths if p.is_dir()]

    if files_to_process:
        for file_path in files_to_process:

            create, overwrite = process_stubgen_task_file(
                file_path=file_path,
                cli_args=cli_args,
                stub_template_str=stub_template_str,
                logger=logger,
                processed_files=processed_files,
                reporting_root=reporting_root,
            )
            total_files_to_create.extend(create)
            total_files_to_overwrite.extend(overwrite)

    if dirs_to_scan:
        logger.info(f"Đang xử lý {len(dirs_to_scan)} thư mục...")
        for scan_dir in dirs_to_scan:

            create, overwrite = process_stubgen_task_dir(
                scan_dir=scan_dir,
                cli_args=cli_args,
                stub_template_str=stub_template_str,
                logger=logger,
                processed_files=processed_files,
                reporting_root=reporting_root,
                script_file_path=script_file_path,
            )
            total_files_to_create.extend(create)
            total_files_to_overwrite.extend(overwrite)

    return total_files_to_create, total_files_to_overwrite
