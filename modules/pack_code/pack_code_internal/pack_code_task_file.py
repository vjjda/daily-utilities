# Path: modules/pack_code/pack_code_internal/pack_code_task_file.py
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple


from . import load_config_files, resolve_filters, scan_files, load_files_content

__all__ = ["process_pack_code_task_file"]

FileResult = Dict[str, Any]


def process_pack_code_task_file(
    file_path: Path,
    cli_args: Dict[str, Any],
    logger: logging.Logger,
    processed_files: Set[Path],
    reporting_root: Optional[Path],
    script_file_path: Path,
) -> List[FileResult]:
    logger.info(f"--- 📄 Đang xử lý file: {file_path.name} ---")

    resolved_file = file_path.resolve()
    if resolved_file in processed_files:
        logger.info("   -> Bỏ qua (đã xử lý).")
        logger.info("")
        return []

    scan_dir = file_path.parent
    file_config = load_config_files(scan_dir, logger)

    (
        ext_filter_set,
        ignore_spec,
        include_spec,  # <-- THÊM BIẾN
        submodule_paths,
        clean_extensions_set,
        format_extensions_set,
    ) = resolve_filters(logger, cli_args, file_config, scan_dir)

    files_to_pack = scan_files(
        logger,
        file_path,
        ignore_spec,
        include_spec,
        ext_filter_set,
        submodule_paths,
        scan_dir,
        script_file_path,
    )

    if not files_to_pack:
        logger.warning(f"  -> ⚠️ Bỏ qua '{file_path.name}' (không khớp filter).")
        logger.info("")
        return []

    logger.info(f"  -> ⚡ Phân tích 1 file...")

    files_content = load_files_content(
        logger=logger,
        file_paths=files_to_pack,
        base_dir=scan_dir,
        all_clean=cli_args.get("all_clean", False),
        clean_extensions_set=clean_extensions_set,
        format_flag=cli_args.get("format", False),
        format_extensions_set=format_extensions_set,
    )

    processed_files.add(resolved_file)
    final_results: List[FileResult] = []

    for f_path, f_content in files_content.items():
        rel_path: str
        if reporting_root:
            try:
                rel_path = f_path.relative_to(reporting_root).as_posix()
            except ValueError:
                rel_path = f_path.as_posix()
        else:
            rel_path = f_path.as_posix()

        final_results.append(
            {"path": f_path, "content": f_content, "rel_path": rel_path}
        )

    logger.info(f"--- ✅ Kết thúc {file_path.name} ---")
    logger.info("")
    return final_results