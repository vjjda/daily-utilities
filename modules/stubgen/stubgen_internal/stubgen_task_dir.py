# Path: modules/stubgen/stubgen_internal/stubgen_task_dir.py

import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


from . import (
    load_config_files,
    merge_stubgen_configs,
    find_gateway_files,
    process_single_gateway,
)


from .stubgen_classifier import classify_and_report_stub_changes


from utils.constants import MAX_THREAD_WORKERS


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
    }
    merged_config = merge_stubgen_configs(logger, cli_config, file_config)

    gateway_files, scan_status = find_gateway_files(
        logger=logger,
        scan_root=scan_dir,
        ignore_list=merged_config["ignore_list"],
        dynamic_import_indicators=merged_config["indicators"],
        script_file_path=script_file_path,
    )

    logger.info("  [Cấu hình áp dụng]")
    logger.info(f"    - Ignore (từ config/CLI): {merged_config['ignore_list']}")
    logger.info(
        f"    - Tải .gitignore cục bộ: {'Có' if scan_status['gitignore_found'] else 'Không'}"
    )
    logger.info(
        f"    - Tải .gitmodules cục bộ: {'Có' if scan_status['gitmodules_found'] else 'Không'}"
    )

    if not gateway_files:
        logger.info(
            "  -> 🤷 Không tìm thấy file '__init__.py' (gateway động) nào khớp tiêu chí."
        )
        logger.info(f"--- ✅ Kết thúc {scan_dir.name} ---")
        logger.info("")
        return [], []

    logger.info(
        f"  -> ⚡ Tìm thấy {len(gateway_files)} gateway, đang phân tích (song song)..."
    )

    dir_raw_results: List[Dict[str, Any]] = []

    files_to_submit: List[Path] = []
    for init_file in gateway_files:
        resolved_file = init_file.resolve()
        if resolved_file in processed_files:
            continue

        processed_files.add(resolved_file)
        files_to_submit.append(init_file)

    if not files_to_submit:
        logger.info("  -> ✅ Tất cả file đã được xử lý (do là file input riêng lẻ).")
    else:

        max_workers = MAX_THREAD_WORKERS
        logger.debug(f"Sử dụng ThreadPoolExecutor với max_workers={max_workers}")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {
                executor.submit(
                    process_single_gateway,
                    init_file,
                    scan_dir,
                    merged_config,
                    stub_template_str,
                    logger,
                ): init_file
                for init_file in files_to_submit
            }

            for future in as_completed(future_to_file):
                init_file = future_to_file[future]
                try:
                    stub_content, symbols_count = future.result()

                    if stub_content:
                        stub_path = init_file.with_suffix(".pyi")
                        dir_raw_results.append(
                            {
                                "init_path": init_file,
                                "stub_path": stub_path,
                                "content": stub_content,
                                "symbols_count": symbols_count,
                                "rel_path": stub_path.relative_to(
                                    reporting_root
                                ).as_posix(),
                            }
                        )
                except Exception as e:
                    logger.error(
                        f"❌ Lỗi khi xử lý file song song '{init_file.name}': {e}"
                    )

    dir_raw_results.sort(key=lambda r: r["stub_path"])

    create, overwrite, _ = classify_and_report_stub_changes(
        logger, scan_dir.name, dir_raw_results, reporting_root
    )

    logger.info(f"--- ✅ Kết thúc {scan_dir.name} ---")
    logger.info("")

    return create, overwrite
