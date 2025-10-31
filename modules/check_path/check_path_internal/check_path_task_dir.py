# Path: modules/check_path/check_path_internal/check_path_task_dir.py
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pathspec


from .check_path_loader import load_config_files
from .check_path_merger import merge_check_path_configs
from .check_path_scanner import scan_files
from .check_path_analyzer import analyze_single_file_for_path_comment


from utils.core import parse_gitignore, compile_spec_from_patterns


from ..check_path_executor import print_dry_run_report_for_group

__all__ = ["process_check_path_task_dir"]

FileResult = Dict[str, Any]


def process_check_path_task_dir(
    scan_dir: Path,
    cli_args: argparse.Namespace,
    logger: logging.Logger,
    processed_files: Set[Path],
    reporting_root: Path,
    script_file_path: Path,
) -> List[FileResult]:
    logger.info(f"--- 📁 Quét thư mục: {scan_dir.name} ---")

    file_config_data = load_config_files(scan_dir, logger)
    cli_extensions: Optional[str] = getattr(cli_args, "extensions", None)
    cli_ignore: Optional[str] = getattr(cli_args, "ignore", None)

    merged_config = merge_check_path_configs(
        logger=logger,
        cli_extensions=cli_extensions,
        cli_ignore=cli_ignore,
        file_config_data=file_config_data,
    )
    final_extensions_list = merged_config["final_extensions_list"]
    final_ignore_list = merged_config["final_ignore_list"]

    gitignore_patterns: List[str] = parse_gitignore(scan_dir)
    all_ignore_patterns_list: List[str] = final_ignore_list + gitignore_patterns
    ignore_spec = compile_spec_from_patterns(all_ignore_patterns_list, scan_dir)

    files_in_dir, scan_status = scan_files(
        logger=logger,
        start_path=scan_dir,
        ignore_spec=ignore_spec,
        extensions=final_extensions_list,
        scan_root=scan_dir,
        script_file_path=script_file_path,
    )

    logger.info(f"  [Cấu hình áp dụng]")
    logger.info(f"    - Extensions: {sorted(list(final_extensions_list))}")
    logger.info(f"    - Ignore (từ config): {final_ignore_list}")
    logger.info(
        f"    - Tải .gitignore cục bộ: {'Có' if scan_status['gitignore_found'] else 'Không'}"
    )
    logger.info(
        f"    - Tải .gitmodules cục bộ: {'Có' if scan_status['gitmodules_found'] else 'Không'}"
    )

    if not files_in_dir:
        logger.info(
            f"  -> 🤷 Không tìm thấy file nào khớp tiêu chí trong: {scan_dir.name}"
        )
        logger.info(f"--- ✅ Kết thúc {scan_dir.name} ---")
        logger.info("")
        return []

    logger.info(f"  -> ⚡ Tìm thấy {len(files_in_dir)} file, đang phân tích...")

    dir_results: List[FileResult] = []

    for file_path in files_in_dir:
        resolved_file = file_path.resolve()
        if resolved_file in processed_files:
            continue

        result = analyze_single_file_for_path_comment(file_path, reporting_root, logger)
        if result:
            dir_results.append(result)
        processed_files.add(resolved_file)

    if dir_results:
        print_dry_run_report_for_group(
            logger, scan_dir.name, dir_results, reporting_root
        )
    else:
        logger.info(f"  -> ✅ Tất cả file trong thư mục đã tuân thủ.")

    logger.info(f"--- ✅ Kết thúc {scan_dir.name} ---")
    logger.info("")

    return dir_results