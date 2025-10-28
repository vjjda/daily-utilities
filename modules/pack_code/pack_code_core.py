# Path: modules/pack_code/pack_code_core.py

"""
Core logic for pack_code (Orchestrator).
"""

import logging
from pathlib import Path
import os
# --- MODIFIED: Thêm Iterable ---
from typing import Dict, Any, List, Optional, Set, TYPE_CHECKING, Iterable
# --- END MODIFIED ---

# Import pathspec for type checking
if TYPE_CHECKING:
    import pathspec

# --- MODIFIED: Import các hàm từ utils và module con ---
from utils.core import (
    find_git_root,
    parse_gitignore, # Trả về List[str]
    compile_spec_from_patterns, # Nhận Iterable[str]
    resolve_set_modification,
    get_submodule_paths,
    parse_comma_list
)

# Import các module con mới
from .pack_code_scanner import scan_files
from .pack_code_tree import generate_tree_string
# Import loader và config
from .pack_code_loader import load_files_content
from .pack_code_config import (
    DEFAULT_EXTENSIONS, DEFAULT_IGNORE, DEFAULT_START_PATH,
    DEFAULT_OUTPUT_DIR # <-- THÊM MỚI
)
# --- END MODIFIED ---

__all__ = ["process_pack_code_logic"]


def process_pack_code_logic(logger: logging.Logger, **cli_args) -> Dict[str, Any]:
    """
    Hàm logic chính (Orchestrator).
    Điều phối việc quét, lọc, tạo cây, đọc và đóng gói nội dung.
    """
    logger.info("Core logic running...")

    # 1. Trích xuất tham số CLI (Giữ nguyên)
    start_path_from_args = cli_args.get("start_path")
    start_path: Path = start_path_from_args if isinstance(start_path_from_args, Path) else Path(DEFAULT_START_PATH).resolve()

    output_path_arg: Optional[Path] = cli_args.get("output") # Đã expanduser
    stdout: bool = cli_args.get("stdout", False)
    ext_cli_str: Optional[str] = cli_args.get("extensions")
    ignore_cli_str: Optional[str] = cli_args.get("ignore")
    no_gitignore: bool = cli_args.get("no_gitignore", False)
    dry_run: bool = cli_args.get("dry_run", False)
    no_header: bool = cli_args.get("no_header", False)
    no_tree: bool = cli_args.get("no_tree", False)

    # 2. Xác định Scan Root (Giữ nguyên)
    scan_root: Path
    if start_path.is_file():
        scan_root = find_git_root(start_path.parent) or start_path.parent
    else:
        effective_start_dir = start_path if start_path.exists() else Path.cwd()
        scan_root = find_git_root(effective_start_dir) or effective_start_dir

    if not start_path.exists():
         logger.error(f"❌ Lỗi: Đường dẫn bắt đầu không tồn tại: {start_path.as_posix()}")
         return {'status': 'error', 'message': f"Start path not found: {start_path.as_posix()}"}

    logger.debug(f"Scan Root (cho quy tắc .gitignore): {scan_root.as_posix()}")
    logger.debug(f"Start Path (nơi bắt đầu quét): {start_path.as_posix()}")


    # 3. Hợp nhất bộ lọc
    # 3.1. Extensions (Giữ nguyên)
    default_ext_set = parse_comma_list(DEFAULT_EXTENSIONS)
    ext_filter_set = resolve_set_modification(default_ext_set, ext_cli_str)

    # 3.2. Ignore
    default_ignore_set = parse_comma_list(DEFAULT_IGNORE)
    cli_ignore_set = parse_comma_list(ignore_cli_str)
    gitignore_patterns: List[str] = [] # <-- List
    if not no_gitignore:
        gitignore_patterns = parse_gitignore(scan_root) # <-- List
        logger.debug(f"Đã tải {len(gitignore_patterns)} quy tắc từ .gitignore")

    # --- MODIFIED: Gộp thành List ---
    # Ưu tiên: Default -> CLI -> Gitignore
    all_ignore_patterns_list: List[str] = (
        sorted(list(default_ignore_set)) +
        sorted(list(cli_ignore_set)) +
        gitignore_patterns
    )
    ignore_spec = compile_spec_from_patterns(all_ignore_patterns_list, scan_root)
    # --- END MODIFIED ---

    # 3.3. Submodules (Giữ nguyên)
    submodule_paths = get_submodule_paths(scan_root, logger)

    # 4. Quét File (Gọi Scanner - Giữ nguyên)
    files_to_pack = scan_files(
        logger, start_path, ignore_spec, ext_filter_set, submodule_paths, scan_root
    )

    if not files_to_pack:
        logger.warning("Không tìm thấy file nào khớp với tiêu chí.")
        return {'status': 'empty'}

    logger.info(f"Tìm thấy {len(files_to_pack)} file để đóng gói.")

    # 5. Tạo cây (Gọi Tree Generator - Giữ nguyên)
    tree_str = ""
    if not no_tree:
        logger.debug("Đang tạo cây thư mục...")
        tree_str = generate_tree_string(start_path, files_to_pack, scan_root)

    # 6. Đọc nội dung file (Gọi Loader - Giữ nguyên)
    files_content: Dict[Path, str] = {}
    if not (dry_run and no_tree): # Chỉ đọc nếu không phải dry-run HOẶC cần cây
        files_content = load_files_content(logger, files_to_pack, scan_root)

    # 7. Đóng gói (Packing - Giữ nguyên)
    final_content_lines: List[str] = []
    # ... (logic đóng gói giữ nguyên) ...
    if tree_str:
        final_content_lines.append(tree_str)
        final_content_lines.append("\n" + ("=" * 80) + "\n")

    if not dry_run:
        for file_path in files_to_pack:
            content = files_content.get(file_path)
            if content is None:
                continue

            try:
                rel_path_str = file_path.relative_to(scan_root).as_posix()
            except ValueError:
                 rel_path_str = file_path.as_posix() # Fallback

            if not no_header:
                header = f"===== Path: {rel_path_str} ====="
                final_content_lines.append(header)

            final_content_lines.append(content)

            if not no_header:
                final_content_lines.append("\n")

    final_content = "\n".join(final_content_lines)


    # 8. Tính toán Output Path
    final_output_path: Optional[Path] = None
    if not stdout and not dry_run:
        if output_path_arg:
            final_output_path = output_path_arg
        else:
            # --- MODIFIED: Sử dụng DEFAULT_OUTPUT_DIR ---
            start_name = start_path.stem if start_path.is_file() else start_path.name
            # Sử dụng hằng số mới từ config
            final_output_path = DEFAULT_OUTPUT_DIR / f"{start_name}_context.txt"
            # Log đường dẫn tuyệt đối vì nó không còn tương đối với scan_root
            logger.debug(f"Sử dụng đường dẫn output mặc định: {final_output_path.as_posix()}")
            # --- END MODIFIED ---

    # 9. Trả về Result Object (Giữ nguyên)
    return {
        'status': 'ok',
        'final_content': final_content,
        'output_path': final_output_path,
        'stdout': stdout,
        'dry_run': dry_run,
        'file_list_relative': [p.relative_to(scan_root) for p in files_to_pack],
        'scan_root': scan_root
    }