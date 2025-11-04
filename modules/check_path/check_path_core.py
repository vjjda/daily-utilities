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
    load_config_files,
)
from .check_path_executor import execute_check_path_action

from utils.constants import MAX_THREAD_WORKERS
from utils.cli import (
    resolve_input_paths,
    resolve_reporting_root,
)


__all__ = ["process_check_path_logic", "orchestrate_check_path"]

FileResult = Dict[str, Any]


def orchestrate_check_path(
    logger: logging.Logger, cli_args: argparse.Namespace, this_script_path: Path
) -> None:

    validated_paths: List[Path] = resolve_input_paths(
        logger=logger, raw_paths=cli_args.start_paths_arg, default_path_str="."
    )
    if not validated_paths:
        logger.warning("Không tìm thấy đường dẫn hợp lệ nào để quét. Đã dừng.")
        sys.exit(0)

    reporting_root = resolve_reporting_root(logger, validated_paths, cli_args.root)

    try:
        files_to_fix = process_check_path_logic(
            logger=logger,
            validated_paths=validated_paths,
            cli_args=cli_args,
            script_file_path=this_script_path,
            reporting_root=reporting_root,
        )

        execute_check_path_action(
            logger=logger,
            all_files_to_fix=files_to_fix,
            cli_args=cli_args,
            scan_root=reporting_root,
        )

    except Exception as e:
        logger.error(
            f"❌ Đã xảy ra lỗi không mong muốn trong 'orchestrate_check_path': {e}"
        )
        logger.debug("Traceback:", exc_info=True)
        raise


def process_check_path_logic(
    logger: logging.Logger,
    validated_paths: List[Path],
    cli_args: argparse.Namespace,
    script_file_path: Path,
    reporting_root: Path,
) -> List[FileResult]:

    all_results: List[FileResult] = []
    processed_files: Set[Path] = set()

    files_to_process: List[Path] = [p for p in validated_paths if p.is_file()]
    dirs_to_scan: List[Path] = [p for p in validated_paths if p.is_dir()]

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
            all_results.extend(file_only_results)

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
