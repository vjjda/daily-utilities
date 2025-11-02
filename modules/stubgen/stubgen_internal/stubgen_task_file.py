# Path: modules/stubgen/stubgen_internal/stubgen_task_file.py

import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple


from . import (
    merge_stubgen_configs,
    process_single_gateway,
    classify_and_report_stub_changes,  # <-- Thêm
)


__all__ = ["process_stubgen_task_file"]


def process_stubgen_task_file(
    file_path: Path,
    cli_args: argparse.Namespace,
    stub_template_str: str,
    logger: logging.Logger,
    processed_files: Set[Path],
    reporting_root: Path,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    logger.info(
        f"--- 📄 Đang xử lý file: {file_path.relative_to(reporting_root).as_posix()} ---"
    )

    resolved_file = file_path.resolve()
    if resolved_file in processed_files:
        logger.info("   -> Bỏ qua (đã xử lý).")
        logger.info("")
        return [], []

    if file_path.name != "__init__.py":
        logger.warning(
            f"⚠️ Bỏ qua file '{file_path.name}': 'sgen' chỉ xử lý file '__init__.py'."
        )
        logger.info("")
        return [], []

    file_config_data = {}
    cli_config = {
        "ignore": getattr(cli_args, "ignore", None),
        "include": getattr(cli_args, "include", None),
    }
    merged_config = merge_stubgen_configs(logger, cli_config, file_config_data)
    scan_dir = file_path.parent

    logger.info(f"  [Cấu hình áp dụng]")
    logger.info(f"    - Ignore (từ config/CLI): {merged_config['ignore_list']}")
    logger.info(f"    - Include (từ config/CLI): {merged_config['include_list']}")
    logger.info(f"    - (Bỏ qua .gitignore và config file)")

    stub_content, symbols_count = process_single_gateway(
        init_file=file_path,
        scan_root=scan_dir,
        merged_config=merged_config,
        stub_template_str=stub_template_str,
        logger=logger,
    )

    processed_files.add(resolved_file)
    file_raw_results: List[Dict[str, Any]] = []

    if stub_content:
        stub_path = file_path.with_suffix(".pyi")
        file_raw_results.append(
            {
                "init_path": file_path,
                "stub_path": stub_path,
                "content": stub_content,
                "symbols_count": symbols_count,
                "rel_path": stub_path.relative_to(reporting_root).as_posix(),
            }
        )
    else:
        logger.warning(f"  -> 🤷 Không tìm thấy symbols nào trong: {file_path.name}")

    create, overwrite, _ = classify_and_report_stub_changes(
        logger, file_path.name, file_raw_results, reporting_root
    )
    logger.info("")

    return create, overwrite
