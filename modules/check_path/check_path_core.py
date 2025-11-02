# Path: modules/check_path/check_path_core.py
import logging
import argparse
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed


if not "PROJECT_ROOT" in locals():
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))


from .check_path_internal import (
    merge_check_path_configs,
    process_check_path_task_dir,
    analyze_single_file_for_path_comment,
    # print_dry_run_report_for_group, # <-- XÓA IMPORT SAI
)
# --- THÊM IMPORT ĐÚNG ---
from .check_path_executor import print_dry_run_report_for_group
# --- KẾT THÚC THÊM IMPORT ---
from .check_path_config import DEFAULT_EXTENSIONS
from utils.constants import MAX_THREAD_WORKERS

__all__ = ["process_check_path_logic"]

FileResult = Dict[str, Any]


def process_check_path_logic(
    logger: logging.Logger,
    files_to_process: List[Path],
    dirs_to_scan: List[Path],
    cli_args: argparse.Namespace,
    script_file_path: Path,
    reporting_root: Path,
) -> List[FileResult]:

    all_results: List[FileResult] = []
    processed_files: Set[Path] = set()

    cli_extensions_str: Optional[str] = getattr(cli_args, "extensions", None)
    default_file_config = merge_check_path_configs(
        logger=logger,
        cli_extensions=cli_extensions_str,
        cli_ignore=None,
        file_config_data={},
    )
    file_extensions = set(default_file_config["final_extensions_list"])

    file_extensions_with_dot = {
        f".{ext}" if not ext.startswith(".") else ext for ext in file_extensions
    }

    if files_to_process:
        logger.info(f"Đang xử lý {len(files_to_process)} file riêng lẻ (song song)...")
        logger.info(f"  [Cấu hình áp dụng cho file lẻ]")
        logger.info(f"    - Extensions: {sorted(list(file_extensions))}")
        logger.info(f"    - (Bỏ qua .gitignore và config file)")

        file_only_results: List[FileResult] = []
        files_to_submit: List[Path] = []

        for file_path in files_to_process:
            resolved_file = file_path.resolve()
            if resolved_file in processed_files:
                continue

            file_ext = "".join(file_path.suffixes)
            if file_ext not in file_extensions_with_dot:
                logger.warning(
                    f"⚠️ Bỏ qua file '{file_path.name}': không khớp extensions ({file_ext})"
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
                        analyze_single_file_for_path_comment,
                        file_path,
                        reporting_root,
                        logger,
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
            print_dry_run_report_for_group(
                logger, "File riêng lẻ (Input)", file_only_results, reporting_root
            )
            all_results.extend(file_only_results)
        elif files_to_submit:
            logger.info(f"  -> ✅ Tất cả {len(files_to_submit)} file riêng lẻ đã tuân thủ.")

    if dirs_to_scan:
        logger.info(f"Đang xử lý {len(dirs_to_scan)} thư mục...")
        for scan_dir in dirs_to_scan:
            results = process_check_path_task_dir(
                scan_dir=scan_dir,
                cli_args=cli_args,
                logger=logger,
                processed_files=processed_files,
                reporting_root=reporting_root,
                script_file_path=script_file_path,
            )
            all_results.extend(results)

    if not all_results and (files_to_process or dirs_to_scan):
        logger.info("Quét hoàn tất. Tất cả file đã tuân thủ.")

    return all_results