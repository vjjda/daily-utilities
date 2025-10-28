# Path: modules/pack_code/pack_code_core.py
"""
Logic cốt lõi cho pack_code (Orchestrator).

Chịu trách nhiệm điều phối quá trình đóng gói bao gồm tải cấu hình,
quét file, xử lý bộ lọc, tạo cây thư mục, đọc nội dung file,
và ghép nối chuỗi output cuối cùng. Module này chứa logic nghiệp vụ thuần túy
với I/O đọc cho cấu hình và nội dung file.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, TYPE_CHECKING, Iterable, Tuple

# Import các thành phần của module
from .pack_code_scanner import scan_files
from .pack_code_tree import generate_tree_string
from .pack_code_loader import load_files_content, load_config_files
from .pack_code_resolver import (
    resolve_start_and_scan_paths,
    resolve_filters,
    resolve_output_path
)
from .pack_code_builder import assemble_packed_content
from .pack_code_config import DEFAULT_START_PATH # Cần để xử lý đường dẫn mặc định

__all__ = ["process_pack_code_logic"]


def process_pack_code_logic(
    logger: logging.Logger,
    cli_args: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Hàm logic chính (Orchestrator) cho pack_code.

    Điều phối việc tải config, quét, lọc, tạo cây, đọc và đóng gói nội dung.
    Xử lý I/O đọc cho config và content.

    Args:
        logger: Instance logger.
        cli_args: Một dict chứa các đối số CLI đã xử lý từ entrypoint.
                  Bao gồm 'start_path' (Optional[Path]), 'output' (Optional[Path]),
                  và các cờ boolean/string khác.

    Returns:
        Một dict ("Result Object") chứa dữ liệu cho Executor:
        {
            'status': 'ok' | 'empty' | 'error',
            'final_content': str (nếu status='ok'),
            'output_path': Optional[Path] (đường dẫn chưa expand, nếu status='ok'),
            'stdout': bool,
            'dry_run': bool,
            'copy_to_clipboard': bool,
            'file_list_relative': List[Path] (tương đối so với scan_root),
            'scan_root': Path (đường dẫn tuyệt đối đã resolve),
            'tree_string': str (có thể rỗng),
            'no_tree': bool,
            'message': str (nếu status='error')
        }
    """
    logger.info("Đang chạy logic cốt lõi...") #

    try:
        # 1. Xác định thư mục để tải cấu hình từ đó
        start_path_from_cli: Optional[Path] = cli_args.get("start_path")
        # Dùng start_path nếu có, nếu không thì dùng CWD
        temp_path_for_config = start_path_from_cli if start_path_from_cli else Path.cwd().resolve()

        config_load_dir: Path
        if temp_path_for_config.is_file():
            config_load_dir = temp_path_for_config.parent
        else: # Là thư mục (hoặc CWD)
            config_load_dir = temp_path_for_config

        logger.debug(f"Đang tải cấu hình từ: {config_load_dir.as_posix()}") #
        file_config = load_config_files(config_load_dir, logger)

        # 2. Trích xuất các cờ boolean chính
        dry_run: bool = cli_args.get("dry_run", False)
        no_tree: bool = cli_args.get("no_tree", False)

        # 3. Xác định đường dẫn bắt đầu quét và gốc quét (Git root hoặc fallback)
        start_path, scan_root = resolve_start_and_scan_paths(
            logger, start_path_from_cli # Truyền Optional[Path]
        )

        # 4. Xác định các bộ lọc cuối cùng (extensions, ignore, submodules)
        ext_filter_set, ignore_spec, submodule_paths = resolve_filters(
            logger, cli_args, file_config, scan_root
        )

        # 5. Quét tìm các file khớp với bộ lọc
        files_to_pack = scan_files(
            logger, start_path, ignore_spec, ext_filter_set, submodule_paths, scan_root
        )

        if not files_to_pack:
            logger.warning("Không tìm thấy file nào khớp với tiêu chí.") #
            return {'status': 'empty'}
        logger.info(f"Tìm thấy {len(files_to_pack)} file để đóng gói.") #

        # 6. Tạo chuỗi cây thư mục (nếu cần)
        tree_str = ""
        if not no_tree:
            logger.debug("Đang tạo cây thư mục...") #
            tree_str = generate_tree_string(start_path, files_to_pack, scan_root)

        # 7. Đọc nội dung các file đã tìm thấy (trừ khi dry-run hoàn toàn)
        files_content: Dict[Path, str] = {}
        # Chỉ bỏ qua đọc nếu là dry run VÀ không cần cây
        if not (dry_run and no_tree):
            files_content = load_files_content(logger, files_to_pack, scan_root)

        # 8. Ghép nối nội dung cuối cùng
        final_content = assemble_packed_content(
            files_to_pack=files_to_pack,
            files_content=files_content,
            scan_root=scan_root,
            tree_str=tree_str,
            no_header=cli_args.get("no_header", False),
            dry_run=dry_run, # Builder bỏ qua content nếu dry_run
        )

        # 9. Xác định đường dẫn file output (ưu tiên CLI)
        final_output_path = resolve_output_path(
            logger, cli_args, file_config, start_path
        )

        # 10. Trả về Result Object cho Executor
        return {
            'status': 'ok',
            'final_content': final_content,
            'output_path': final_output_path, # Có thể là None
            'stdout': cli_args.get("stdout", False),
            'dry_run': dry_run,
            'copy_to_clipboard': cli_args.get("copy_to_clipboard", False),
            'file_list_relative': [p.relative_to(scan_root) for p in files_to_pack],
            'scan_root': scan_root,
            'tree_string': tree_str, # Có thể rỗng
            'no_tree': no_tree
        }

    except FileNotFoundError as e:
        # Lỗi từ resolve_start_and_scan_paths nếu start_path không hợp lệ
        logger.error(f"❌ {e}")
        return {'status': 'error', 'message': str(e)}
    except Exception as e:
        logger.error(f"Lỗi không mong muốn trong logic cốt lõi pack_code: {e}") #
        logger.debug("Traceback:", exc_info=True)
        return {'status': 'error', 'message': f"Lỗi không mong muốn: {e}"} #