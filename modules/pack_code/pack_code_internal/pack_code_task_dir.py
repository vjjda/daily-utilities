# Path: modules/pack_code/pack_code_internal/pack_code_task_dir.py
"""
(Internal Task)
Handles the logic for processing a user-specified directory.
"""

import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import pathspec

# Import internal workers
from . import (
    load_config_files,
    resolve_filters,
    scan_files,
    load_files_content
)

__all__ = ["process_pack_code_task_dir"]

FileResult = Dict[str, Any] # Type alias

def process_pack_code_task_dir(
    scan_dir: Path,
    cli_args: Dict[str, Any],
    logger: logging.Logger,
    processed_files: Set[Path],
    reporting_root: Optional[Path],
    script_file_path: Path
) -> List[FileResult]:
    """
    Xử lý logic pack_code cho một thư mục đầu vào.
    """
    logger.info(f"--- 📁 Quét thư mục: {scan_dir.name} ---")
    
    # 1. Tải/Merge Config (cục bộ)
    file_config = load_config_files(scan_dir, logger)
    
    # SỬA: Giải nén 5-tuple
    ext_filter_set, ignore_spec, submodule_paths, clean_extensions_set, format_extensions_set = resolve_filters(
        logger, cli_args, file_config, scan_dir
    )

    # 2. In báo cáo cấu hình
    logger.info(f"  [Cấu hình áp dụng]")
    logger.info(f"    - Extensions: {sorted(list(ext_filter_set))}")
    logger.info(f"    - Ignore (từ config/CLI+Git): {len(ignore_spec.patterns if ignore_spec else [])} quy tắc")
    # SỬA: Thêm log cho clean/format
    logger.info(f"    - Clean Extensions (-a): {sorted(list(clean_extensions_set))}")
    logger.info(f"    - Format Extensions (-f): {sorted(list(format_extensions_set))}")
    
    # 3. Quét file
    files_to_pack = scan_files(
         logger=logger,
         start_path=scan_dir, 
         ignore_spec=ignore_spec, 
         ext_filter_set=ext_filter_set,
         submodule_paths=submodule_paths,
         scan_root=scan_dir, 
         script_file_path=script_file_path
    )

    if not files_to_pack:
        logger.info(f"  -> 🤷 Không tìm thấy file nào khớp tiêu chí trong: {scan_dir.name}")
        logger.info(f"--- ✅ Kết thúc {scan_dir.name} ---")
        logger.info("")
        return []

    logger.info(f"  -> ⚡ Tìm thấy {len(files_to_pack)} file, đang phân tích...")

    # 4. Lọc ra các file đã xử lý
    unique_files_to_pack = []
    for f in files_to_pack:
        if f.resolve() not in processed_files:
            unique_files_to_pack.append(f)
        
    if not unique_files_to_pack:
        logger.info(f"  -> ✅ Tất cả file trong thư mục này đã được xử lý (do là file input riêng lẻ).")
        logger.info(f"--- ✅ Kết thúc {scan_dir.name} ---")
        logger.info("")
        return []

    # 5. Đọc & Làm sạch & Định dạng
    # SỬA: Truyền cờ/set mới
    files_content = load_files_content(
        logger=logger,
        file_paths=unique_files_to_pack,
        base_dir=scan_dir,
        all_clean=cli_args.get("all_clean", False),
        clean_extensions_set=clean_extensions_set,
        format_flag=cli_args.get("format", False),
        format_extensions_set=format_extensions_set
    )
    
    final_results: List[FileResult] = []
    
    # 6. Tính toán Path và tạo Result Object
    for f_path in unique_files_to_pack:
        if f_path in files_content:
            f_content = files_content[f_path]
            
            rel_path: str
            if reporting_root:
                try:
                    rel_path = f_path.relative_to(reporting_root).as_posix()
                except ValueError:
                    rel_path = f_path.as_posix()
            else:
                rel_path = f_path.as_posix()

            final_results.append({
                "path": f_path,
                "content": f_content,
                "rel_path": rel_path
            })
            processed_files.add(f_path.resolve())

    logger.info(f"--- ✅ Kết thúc {scan_dir.name} ---")
    logger.info("")
    
    return final_results