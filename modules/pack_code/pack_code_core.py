# Path: modules/pack_code/pack_code_core.py
"""
Logic cốt lõi cho pack_code (Orchestrator).
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, TYPE_CHECKING, Iterable, Tuple

# SỬA: Import từ facade nội bộ '.pack_code_internal'
from .pack_code_internal import (
    scan_files,
    generate_tree_string,
    load_files_content, 
    load_config_files,
    resolve_start_and_scan_paths,
    resolve_filters,
    resolve_output_path,
    assemble_packed_content
)
from .pack_code_config import DEFAULT_START_PATH

# SỬA: Không cần import clean_code/constants ở đây nữa
# from utils.core import clean_code
# from utils.constants import DEFAULT_EXTENSIONS_LANG_MAP

__all__ = ["process_pack_code_logic"]


def process_pack_code_logic(
    logger: logging.Logger,
    cli_args: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Hàm logic chính (Orchestrator) cho pack_code.
    Điều phối việc tải config, quét, lọc, tạo cây, đọc, LÀM SẠCH và đóng gói nội dung.
    """
    logger.info("Đang chạy logic cốt lõi...")

    try:
        # 1. Xác định thư mục tải config
        start_path_from_cli: Optional[Path] = cli_args.get("start_path")
        temp_path_for_config = start_path_from_cli if start_path_from_cli else Path.cwd().resolve()
        config_load_dir: Path = temp_path_for_config.parent if temp_path_for_config.is_file() else temp_path_for_config
        logger.debug(f"Đang tải cấu hình từ: {config_load_dir.as_posix()}")
        file_config = load_config_files(config_load_dir, logger)

        # 2. Trích xuất các cờ boolean chính
        dry_run: bool = cli_args.get("dry_run", False)
        no_tree: bool = cli_args.get("no_tree", False)
        all_clean: bool = cli_args.get("all_clean", False) 

        if all_clean:
            logger.info("⚠️ Chế độ ALL-CLEAN đã bật: Nội dung file sẽ được làm sạch trước khi đóng gói.")

         # 3. Xác định đường dẫn bắt đầu và gốc quét
        start_path, scan_root = resolve_start_and_scan_paths(
            logger, start_path_from_cli
        )

        # 4. Xác định các bộ lọc cuối cùng
        ext_filter_set, ignore_spec, submodule_paths, clean_extensions_set = resolve_filters(
            logger, cli_args, file_config, scan_root
        )

        # 5. Quét tìm file
        files_to_pack = scan_files(
            logger, start_path, ignore_spec, ext_filter_set, submodule_paths, scan_root
        )
        if not files_to_pack:
            logger.warning("Không tìm thấy file nào khớp với tiêu chí.")
            return {'status': 'empty'}
        logger.info(f"Tìm thấy {len(files_to_pack)} file để đóng gói.")

        # 6. Tạo cây thư mục
        tree_str = ""
        if not no_tree:
            logger.debug("Đang tạo cây thư mục...")
            tree_str = generate_tree_string(start_path, files_to_pack, scan_root)

        # 7. Đọc và Làm sạch nội dung file (SỬA: Logic đã chuyển vào loader)
        files_content: Dict[Path, str] = {}
        if not (dry_run and no_tree):
            files_content = load_files_content(
                logger=logger,
                file_paths=files_to_pack,
                base_dir=scan_root,
                all_clean=all_clean,
                clean_extensions_set=clean_extensions_set
            )

        # 8. Ghép nối nội dung cuối cùng
        final_content = assemble_packed_content(
            files_to_pack=files_to_pack, files_content=files_content,
            scan_root=scan_root, tree_str=tree_str,
            no_header=cli_args.get("no_header", False), dry_run=dry_run,
        )

        # 9. Xác định đường dẫn file output
        final_output_path = resolve_output_path(
            logger, cli_args, file_config, start_path
        )

        # 10. Trả về Result Object cho Executor
        return {
            'status': 'ok',
            'final_content': final_content,
             'output_path': final_output_path,
            'stdout': cli_args.get("stdout", False),
            'dry_run': dry_run,
            'copy_to_clipboard': cli_args.get("copy_to_clipboard", False),
            'file_list_relative': [p.relative_to(scan_root) for p in files_to_pack],
            'scan_root': scan_root,
            'tree_string': tree_str,
             'no_tree': no_tree
        }

    except FileNotFoundError as e:
        logger.error(f"❌ {e}")
        return {'status': 'error', 'message': str(e)}
    except Exception as e:
        logger.error(f"Lỗi không mong muốn trong logic cốt lõi pack_code: {e}")
        logger.debug("Traceback:", exc_info=True)
        return {'status': 'error', 'message': f"Lỗi không mong muốn: {e}"}