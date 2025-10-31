# Path: modules/stubgen/stubgen_internal/stubgen_task_dir.py

import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pathspec


from . import (
    load_config_files,
    merge_stubgen_configs,
    find_gateway_files,
    process_single_gateway,
)


from ..stubgen_executor import classify_and_report_stub_changes


from utils.core import compile_spec_from_patterns


__all__ = ["process_stubgen_task_dir"]


def process_stubgen_task_dir(
    scan_dir: Path,
    cli_args: argparse.Namespace,
    stub_template_str: str,
    logger: logging.Logger,
    processed_files: Set[Path],
    reporting_root: Path,
    script_file_path: Path,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    logger.info(f"--- 📁 Quét thư mục: {scan_dir.name} ---")

    file_config = load_config_files(scan_dir, logger)
    cli_config = {
        "ignore": getattr(cli_args, "ignore", None),
        "include": getattr(cli_args, "include", None),
    }
    merged_config = merge_stubgen_configs(logger, cli_config, file_config)

    final_include_spec: Optional["pathspec.PathSpec"] = compile_spec_from_patterns(
        merged_config["include_list"], scan_dir
    )

    gateway_files, scan_status = find_gateway_files(
        logger=logger,
        scan_root=scan_dir,
        ignore_list=merged_config["ignore_list"],
        include_spec=final_include_spec,
        dynamic_import_indicators=merged_config["indicators"],
        script_file_path=script_file_path,
    )

    logger.info(f"  [Cấu hình áp dụng]")
    logger.info(f"    - Ignore (từ config/CLI): {merged_config['ignore_list']}")
    logger.info(f"    - Include (từ config/CLI): {merged_config['include_list']}")
    logger.info(
        f"    - Tải .gitignore cục bộ: {'Có' if scan_status['gitignore_found'] else 'Không'}"
    )
    logger.info(
        f"    - Tải .gitmodules cục bộ: {'Có' if scan_status['gitmodules_found'] else 'Không'}"
    )

    if not gateway_files:
        logger.info(
            f"  -> 🤷 Không tìm thấy file '__init__.py' (gateway động) nào khớp tiêu chí."
        )
        logger.info(f"--- ✅ Kết thúc {scan_dir.name} ---")
        logger.info("")
        return [], []

    logger.info(f"  -> ⚡ Tìm thấy {len(gateway_files)} gateway, đang phân tích...")

    dir_raw_results: List[Dict[str, Any]] = []
    for init_file in gateway_files:
        resolved_file = init_file.resolve()
        if resolved_file in processed_files:
            continue

        stub_content, symbols_count = process_single_gateway(
            init_file=init_file,
            scan_root=scan_dir,
            merged_config=merged_config,
            stub_template_str=stub_template_str,
            logger=logger,
        )

        if stub_content:
            stub_path = init_file.with_suffix(".pyi")
            dir_raw_results.append(
                {
                    "init_path": init_file,
                    "stub_path": stub_path,
                    "content": stub_content,
                    "symbols_count": symbols_count,
                    "rel_path": stub_path.relative_to(reporting_root).as_posix(),
                }
            )
        processed_files.add(resolved_file)

    create, overwrite, _ = classify_and_report_stub_changes(
        logger, scan_dir.name, dir_raw_results, reporting_root
    )

    logger.info(f"--- ✅ Kết thúc {scan_dir.name} ---")
    logger.info("")

    return create, overwrite
