# Path: modules/pack_code/pack_code_core.py
"""
Logic cốt lõi cho pack_code (Orchestrator).
# ... (docstring không đổi)
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
from .pack_code_config import DEFAULT_START_PATH

# THÊM IMPORT: clean_code và bản đồ ngôn ngữ
from utils.core import clean_code
from utils.constants import DEFAULT_EXTENSIONS_LANG_MAP # Import bản đồ tập trung

__all__ = ["process_pack_code_logic"]


def process_pack_code_logic(
    logger: logging.Logger,
    cli_args: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Hàm logic chính (Orchestrator) cho pack_code.
    Điều phối việc tải config, quét, lọc, tạo cây, đọc, LÀM SẠCH (mới) và đóng gói nội dung.
    # ... (rest of docstring)
    """
    logger.info("Đang chạy logic cốt lõi...")

    try:
        # 1. Xác định thư mục tải config (Không đổi)
        start_path_from_cli: Optional[Path] = cli_args.get("start_path")
        temp_path_for_config = start_path_from_cli if start_path_from_cli else Path.cwd().resolve()
        config_load_dir: Path = temp_path_for_config.parent if temp_path_for_config.is_file() else temp_path_for_config
        logger.debug(f"Đang tải cấu hình từ: {config_load_dir.as_posix()}")
        file_config = load_config_files(config_load_dir, logger)

        # 2. Trích xuất các cờ boolean chính (THÊM all_clean)
        dry_run: bool = cli_args.get("dry_run", False)
        no_tree: bool = cli_args.get("no_tree", False)
        all_clean: bool = cli_args.get("all_clean", False) # <-- THÊM MỚI

        if all_clean:
            logger.info("⚠️ Chế độ ALL-CLEAN đã bật: Nội dung file sẽ được làm sạch trước khi đóng gói.")

        # 3. Xác định đường dẫn bắt đầu và gốc quét (Không đổi)
        start_path, scan_root = resolve_start_and_scan_paths(
            logger, start_path_from_cli
        )

        # 4. Xác định các bộ lọc cuối cùng (THÊM clean_extensions_set)
        # SỬA: Nhận thêm clean_extensions_set từ resolver
        ext_filter_set, ignore_spec, submodule_paths, clean_extensions_set = resolve_filters(
            logger, cli_args, file_config, scan_root
        )

        # 5. Quét tìm file (Không đổi)
        files_to_pack = scan_files(
            logger, start_path, ignore_spec, ext_filter_set, submodule_paths, scan_root
        )
        if not files_to_pack:
            logger.warning("Không tìm thấy file nào khớp với tiêu chí.")
            return {'status': 'empty'}
        logger.info(f"Tìm thấy {len(files_to_pack)} file để đóng gói.")

        # 6. Tạo cây thư mục (Không đổi)
        tree_str = ""
        if not no_tree:
            logger.debug("Đang tạo cây thư mục...")
            tree_str = generate_tree_string(start_path, files_to_pack, scan_root)

        # 7. Đọc nội dung file (SỬA: Thêm logic clean)
        files_content: Dict[Path, str] = {}
        if not (dry_run and no_tree): # Chỉ đọc nếu không phải dry-run hoàn toàn
            logger.info(f"Đang đọc nội dung từ {len(files_to_pack)} file...")
            skipped_count = 0
            cleaned_count = 0 # Đếm số file đã clean

            for file_path in files_to_pack:
                try:
                    content = file_path.read_text(encoding='utf-8')

                    # --- LOGIC LÀM SẠCH ---
                    file_ext = "".join(file_path.suffixes).lstrip('.')
                    # Chỉ clean nếu -a bật VÀ extension có trong clean_extensions_set
                    if all_clean and file_ext in clean_extensions_set:
                        language_id = DEFAULT_EXTENSIONS_LANG_MAP.get(file_ext)
                        if language_id:
                            logger.debug(f"   -> Đang làm sạch '{file_path.relative_to(scan_root).as_posix()}' (ngôn ngữ: {language_id})...")
                            cleaned_content = clean_code(
                                code_content=content,
                                language=language_id, # Sử dụng ID từ map
                                logger=logger,
                                all_clean=True # Luôn all_clean khi gọi từ đây
                            )
                            if cleaned_content != content:
                                cleaned_count += 1
                                content = cleaned_content # Sử dụng nội dung đã clean
                        else:
                            logger.debug(f"   -> Bỏ qua làm sạch '{file_path.relative_to(scan_root).as_posix()}': Không tìm thấy language ID cho extension '{file_ext}'.")
                    # --- KẾT THÚC LOGIC LÀM SẠCH ---

                    files_content[file_path] = content

                except UnicodeDecodeError:
                    logger.warning(f"   -> Bỏ qua (lỗi encoding): {file_path.relative_to(scan_root).as_posix()}")
                    skipped_count += 1
                except IOError as e:
                    logger.warning(f"   -> Bỏ qua (lỗi I/O: {e}): {file_path.relative_to(scan_root).as_posix()}")
                    skipped_count += 1
                except Exception as e:
                    logger.warning(f"   -> Bỏ qua (lỗi không xác định: {e}): {file_path.relative_to(scan_root).as_posix()}")
                    skipped_count += 1

            if skipped_count > 0: logger.warning(f"Đã bỏ qua tổng cộng {skipped_count} file không thể đọc.")
            if all_clean and cleaned_count > 0: logger.info(f"Đã làm sạch nội dung của {cleaned_count} file.")

        # 8. Ghép nối nội dung cuối cùng (Không đổi)
        final_content = assemble_packed_content(
            files_to_pack=files_to_pack, files_content=files_content,
            scan_root=scan_root, tree_str=tree_str,
            no_header=cli_args.get("no_header", False), dry_run=dry_run,
        )

        # 9. Xác định đường dẫn file output (Không đổi)
        final_output_path = resolve_output_path(
            logger, cli_args, file_config, start_path
        )

        # 10. Trả về Result Object cho Executor (Không đổi)
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
            # Thêm 'all_clean' nếu Executor cần biết? (Hiện tại không cần)
        }

    except FileNotFoundError as e:
        logger.error(f"❌ {e}")
        return {'status': 'error', 'message': str(e)}
    except Exception as e:
        logger.error(f"Lỗi không mong muốn trong logic cốt lõi pack_code: {e}")
        logger.debug("Traceback:", exc_info=True)
        return {'status': 'error', 'message': f"Lỗi không mong muốn: {e}"}