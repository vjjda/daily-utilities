# Path: modules/pack_code/pack_code_core.py
"""
Core logic for pack_code (Orchestrator).
(Refactored for clarity and SRP)
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, TYPE_CHECKING, Iterable, Tuple

# Import các module con
from .pack_code_scanner import scan_files
from .pack_code_tree import generate_tree_string
from .pack_code_loader import load_files_content

# --- NEW: Import từ các file helper mới ---
from .pack_code_resolver import (
    resolve_start_and_scan_paths,
    resolve_filters,
    resolve_output_path
)
from .pack_code_builder import assemble_packed_content
# --- END NEW ---

__all__ = ["process_pack_code_logic"]


def process_pack_code_logic(
    logger: logging.Logger,
    cli_args: Dict[str, Any],
    file_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Hàm logic chính (Orchestrator).
    Điều phối việc quét, lọc, tạo cây, đọc và đóng gói nội dung.
    """
    logger.info("Core logic running...")

    try:
        # 1. Trích xuất các cờ boolean chính
        dry_run: bool = cli_args.get("dry_run", False)
        no_tree: bool = cli_args.get("no_tree", False)

        # 2. Xác định đường dẫn (Dùng Resolver)
        start_path, scan_root = resolve_start_and_scan_paths(
            logger, cli_args.get("start_path")
        )

        # 3. Hợp nhất các bộ lọc (Dùng Resolver)
        ext_filter_set, ignore_spec, submodule_paths = resolve_filters(
            logger, cli_args, file_config, scan_root
        )

        # 4. Quét File
        files_to_pack = scan_files(
            logger, start_path, ignore_spec, ext_filter_set, submodule_paths, scan_root
        )
        if not files_to_pack:
            logger.warning("Không tìm thấy file nào khớp với tiêu chí.")
            return {'status': 'empty'}
        logger.info(f"Tìm thấy {len(files_to_pack)} file để đóng gói.")

        # 5. Tạo cây
        tree_str = ""
        if not no_tree:
            logger.debug("Đang tạo cây thư mục...")
            tree_str = generate_tree_string(start_path, files_to_pack, scan_root)

        # 6. Đọc nội dung file
        files_content: Dict[Path, str] = {}
        if not (dry_run and no_tree):
            files_content = load_files_content(logger, files_to_pack, scan_root)

        # 7. Đóng gói (Dùng Builder)
        final_content = assemble_packed_content(
            files_to_pack=files_to_pack,
            files_content=files_content,
            scan_root=scan_root,
            tree_str=tree_str,
            no_header=cli_args.get("no_header", False),
            dry_run=dry_run,
        )

        # 8. Tính toán Output Path (Dùng Resolver)
        final_output_path = resolve_output_path(
            logger, cli_args, file_config, start_path
        )

        # 9. Trả về Result Object
        return {
            'status': 'ok',
            'final_content': final_content,
            'output_path': final_output_path,
            'stdout': cli_args.get("stdout", False),
            'dry_run': dry_run,
            'file_list_relative': [p.relative_to(scan_root) for p in files_to_pack],
            'scan_root': scan_root,
            'tree_string': tree_str,
            'no_tree': no_tree
        }

    except FileNotFoundError as e:
        # Bắt lỗi từ resolve_start_and_scan_paths
        return {'status': 'error', 'message': str(e)}
    except Exception as e:
        logger.error(f"Lỗi không mong muốn trong pack_code core: {e}")
        logger.debug("Traceback:", exc_info=True)
        return {'status': 'error', 'message': f"Lỗi không mong muốn: {e}"}