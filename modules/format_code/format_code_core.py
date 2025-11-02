# Path: modules/format_code/format_code_core.py
import logging
import argparse
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple, Set
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed


if not "PROJECT_ROOT" in locals():
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))


from .format_code_internal import (
    merge_format_code_configs,
    process_format_code_task_dir,
    analyze_file_content_for_formatting,
)


from utils.constants import MAX_THREAD_WORKERS


__all__ = ["process_format_code_logic"]

FileResult = Dict[str, Any]


def process_format_code_logic(
    logger: logging.Logger,
    files_to_process: List[Path],
    dirs_to_scan: List[Path],
    cli_args: argparse.Namespace,
    script_file_path: Path,
) -> List[FileResult]:

    all_results: List[FileResult] = []
    processed_files: Set[Path] = set()
    reporting_root = Path.cwd()

    cli_extensions_str: Optional[str] = getattr(cli_args, "extensions", None)

    default_file_config = merge_format_code_configs(
        logger=logger,
        cli_extensions=cli_extensions_str,
        cli_ignore=None,
        file_config_data={},
    )
    file_extensions = set(default_file_config["final_extensions_list"])

    if files_to_process:
        logger.info(f"Đang xử lý {len(files_to_process)} file riêng lẻ (song song)...")

        file_only_results: List[FileResult] = []
        files_to_submit: List[Path] = []

        for file_path in files_to_process:
            resolved_file = file_path.resolve()
            if resolved_file in processed_files:
                continue

            file_ext = "".join(file_path.suffixes).lstrip(".")
            if file_ext not in file_extensions:
                logger.warning(
                    f"⚠️ Bỏ qua file '{file_path.name}': không khớp extensions (.{file_ext})"
                )
                continue

            processed_files.add(resolved_file)
            files_to_submit.append(file_path)

        if files_to_submit:
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
                            file_only_results.append(result)
                    except Exception as e:
                        logger.error(
                            f"❌ Lỗi khi xử lý file song song '{file_path.name}': {e}"
                        )

        if file_only_results:
            file_only_results.sort(key=lambda r: r["path"])
            all_results.extend(file_only_results)

    if dirs_to_scan:
        logger.info(f"Đang xử lý {len(dirs_to_scan)} thư mục...")
        for scan_dir in dirs_to_scan:

            results = process_format_code_task_dir(
                scan_dir=scan_dir,
                cli_args=cli_args,
                logger=logger,
                processed_files=processed_files,
                reporting_root=reporting_root,
                script_file_path=script_file_path,
            )
            all_results.extend(results)

    if not all_results and (files_to_process or dirs_to_scan):
        logger.info("Quét hoàn tất. Không tìm thấy file nào cần định dạng.")

    return all_results
