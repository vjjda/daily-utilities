# Path: modules/format_code/format_code_internal/format_code_task_dir.py
import logging
import argparse
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed


from .format_code_loader import load_config_files
from .format_code_merger import merge_format_code_configs
from .format_code_scanner import scan_files
from .format_code_analyzer import analyze_file_content_for_formatting


from utils.constants import MAX_THREAD_WORKERS


__all__ = ["process_format_code_task_dir"]

FileResult = Dict[str, Any]


def process_format_code_task_dir(
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

    merged_config = merge_format_code_configs(
        logger=logger,
        cli_extensions=cli_extensions,
        cli_ignore=cli_ignore,
        file_config_data=file_config_data,
    )
    final_extensions_list = merged_config["final_extensions_list"]
    final_ignore_list = merged_config["final_ignore_list"]

    files_in_dir, scan_status = scan_files(
        logger=logger,
        start_path=scan_dir,
        ignore_list=final_ignore_list,
        extensions=final_extensions_list,
        scan_root=scan_dir,
        script_file_path=script_file_path,
    )

    logger.info(f"  [Cấu hình áp dụng]")
    logger.info(f"    - Extensions: {sorted(list(final_extensions_list))}")
    logger.info(f"    - Ignore (từ config/CLI): {final_ignore_list}")
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

    logger.info(
        f"  -> ⚡ Tìm thấy {len(files_in_dir)} file, đang phân tích (song song)..."
    )

    dir_results: List[FileResult] = []

    files_to_submit: List[Path] = []
    for file_path in files_in_dir:
        resolved_file = file_path.resolve()
        if resolved_file in processed_files:
            continue

        processed_files.add(resolved_file)
        files_to_submit.append(file_path)

    if not files_to_submit:
        logger.info("  -> ✅ Tất cả file đã được xử lý (do là file input riêng lẻ).")
    else:

        max_workers = MAX_THREAD_WORKERS
        logger.debug(f"Sử dụng ThreadPoolExecutor với max_workers={max_workers}")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:

            future_to_file = {
                executor.submit(
                    analyze_file_content_for_formatting, file_path, logger
                ): file_path
                for file_path in files_to_submit
            }

            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    if result:
                        dir_results.append(result)
                except Exception as e:
                    logger.error(
                        f"❌ Lỗi khi xử lý file song song '{file_path.name}': {e}"
                    )

    dir_results.sort(key=lambda r: r["path"])

    if not dir_results and files_to_submit:
        logger.info(f"  -> ✅ Tất cả file trong thư mục đã được định dạng.")

    logger.info(f"--- ✅ Kết thúc {scan_dir.name} ---")
    logger.info("")

    return dir_results
