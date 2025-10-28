# Path: modules/pack_code/pack_code_core.py

"""
Core logic for pack_code (Orchestrator).
(Refactored for clarity and SRP)
"""

import logging
from pathlib import Path
# --- MODIFIED: Removed 'os' import ---
from typing import Dict, Any, List, Optional, Set, TYPE_CHECKING, Iterable, Tuple
# --- END MODIFIED ---

# Import pathspec for type checking
if TYPE_CHECKING:
    import pathspec

# --- MODIFIED: Import các hàm từ utils và module con ---
from utils.core import (
    find_git_root,
    parse_gitignore, 
    compile_spec_from_patterns, 
    resolve_set_modification,
    get_submodule_paths,
    parse_comma_list,
    resolve_config_list, 
    resolve_config_value
)

# Import các module con mới
from .pack_code_scanner import scan_files
from .pack_code_tree import generate_tree_string
# Import loader và config
from .pack_code_loader import load_files_content
from .pack_code_config import (
    DEFAULT_EXTENSIONS, DEFAULT_IGNORE, DEFAULT_START_PATH,
    DEFAULT_OUTPUT_DIR
)
# --- END MODIFIED ---

__all__ = ["process_pack_code_logic"]


# --- NEW: Helper 1 - Path Resolution ---
def _resolve_start_and_scan_paths(
    logger: logging.Logger,
    start_path_from_cli: Optional[Path],
) -> Tuple[Path, Path]:
    """
    Xác định start_path và scan_root (Git root hoặc fallback).
    Ném FileNotFoundError nếu start_path cuối cùng không tồn tại.
    """
    
    # 1. Xác định Start Path
    # (Logic này [cite: 249] được giữ lại để đảm bảo tính tương thích
    #  với entrypoint, vốn có thể truyền None)
    start_path: Path
    if start_path_from_cli:
        start_path = start_path_from_cli
    else:
        # Giữ lại logic expand/resolve cho default,
        # vì entrypoint không xử lý default này.
        start_path = Path(DEFAULT_START_PATH).expanduser().resolve()

    # 2. Xác định Scan Root [cite: 249]
    scan_root: Path
    if start_path.is_file():
        scan_root = find_git_root(start_path.parent) or start_path.parent
    else:
        # Phải kiểm tra start_path.exists() trước khi tìm git root
        effective_start_dir = start_path if start_path.exists() else Path.cwd()
        scan_root = find_git_root(effective_start_dir) or effective_start_dir

    # 3. Validation
    if not start_path.exists():
         logger.error(f"❌ Lỗi: Đường dẫn bắt đầu không tồn tại: {start_path.as_posix()}")
         raise FileNotFoundError(f"Start path not found: {start_path.as_posix()}")

    logger.debug(f"Scan Root (cho quy tắc .gitignore): {scan_root.as_posix()}")
    logger.debug(f"Start Path (nơi bắt đầu quét): {start_path.as_posix()}")
    
    return start_path, scan_root
# --- END NEW ---


# --- NEW: Helper 2 - Filter Resolution ---
def _resolve_filters(
    logger: logging.Logger,
    cli_args: Dict[str, Any],
    file_config: Dict[str, Any],
    scan_root: Path,
) -> Tuple[Set[str], Optional['pathspec.PathSpec'], Set[Path]]:
    """Hợp nhất các cấu hình filter (extensions, ignore, submodules)."""
    
    # 1. Hợp nhất Extensions [cite: 250-251]
    file_ext_list = file_config.get('extensions') 
    default_ext_set = parse_comma_list(DEFAULT_EXTENSIONS)
    
    tentative_extensions: Set[str]
    if file_ext_list is not None:
        tentative_extensions = set(file_ext_list)
        logger.debug("Sử dụng 'extensions' từ file config làm cơ sở.")
    else:
        tentative_extensions = default_ext_set
        logger.debug("Sử dụng 'extensions' mặc định làm cơ sở.")
        
    ext_filter_set = resolve_set_modification(
        tentative_extensions, cli_args.get("extensions")
    )

    # 2. Hợp nhất Ignore [cite: 252-253]
    default_ignore_set = parse_comma_list(DEFAULT_IGNORE)
    
    final_ignore_list = resolve_config_list(
        cli_str_value=cli_args.get("ignore"),
        file_list_value=file_config.get('ignore'), 
        default_set_value=default_ignore_set
    )
    
    gitignore_patterns: List[str] = []
    if not cli_args.get("no_gitignore", False):
        gitignore_patterns = parse_gitignore(scan_root)
        logger.debug(f"Đã tải {len(gitignore_patterns)} quy tắc từ .gitignore")

    all_ignore_patterns_list: List[str] = final_ignore_list + gitignore_patterns
    ignore_spec = compile_spec_from_patterns(all_ignore_patterns_list, scan_root)

    # 3. Submodules [cite: 254]
    submodule_paths = get_submodule_paths(scan_root, logger)
    
    return ext_filter_set, ignore_spec, submodule_paths
# --- END NEW ---


# --- NEW: Helper 3 - Output Path Resolution ---
def _resolve_output_path(
    logger: logging.Logger,
    cli_args: Dict[str, Any],
    file_config: Dict[str, Any],
    start_path: Path,
) -> Optional[Path]:
    """
    Xác định đường dẫn output cuối cùng.
    Trả về None nếu là stdout hoặc dry_run.
    KHÔNG expanduser ('~'), đó là việc của Executor.
    """
    if cli_args.get("stdout", False) or cli_args.get("dry_run", False):
        return None
        
    output_path_from_cli: Optional[Path] = cli_args.get("output")
    if output_path_from_cli:
        return output_path_from_cli

    # Hợp nhất Default Output Dir (File > Default) [cite: 259-260]
    default_output_dir_str = resolve_config_value(
        cli_value=None,
        file_value=file_config.get("output_dir"),
        default_value=DEFAULT_OUTPUT_DIR
    )
    
    # --- MODIFIED: Loại bỏ os.path.expanduser ---
    # Executor sẽ chịu trách nhiệm expanduser()
    default_output_dir_path = Path(default_output_dir_str)
    # --- END MODIFIED ---
    
    # Tính toán tên file [cite: 261]
    start_name = start_path.stem if start_path.is_file() else start_path.name
    final_output_path = default_output_dir_path / f"{start_name}_context.txt"

    logger.debug(f"Sử dụng đường dẫn output mặc định (chưa expand): {final_output_path.as_posix()}")
    return final_output_path
# --- END NEW ---


# --- NEW: Helper 4 - Content Assembly ---
def _assemble_packed_content(
    files_to_pack: List[Path],
    files_content: Dict[Path, str],
    scan_root: Path,
    tree_str: str,
    no_header: bool,
    dry_run: bool,
) -> str:
    """Xây dựng chuỗi nội dung output cuối cùng từ các phần."""
    
    final_content_lines: List[str] = []
    
    # 1. Thêm cây (nếu có) [cite: 256]
    if tree_str:
        final_content_lines.append(tree_str)
        final_content_lines.append("\n" + ("=" * 80) + "\n")

    # 2. Thêm nội dung file (nếu không phải dry_run) [cite: 257-258]
    if not dry_run:
        for file_path in files_to_pack:
            content = files_content.get(file_path)
            if content is None:
                continue # Bỏ qua file không đọc được (đã log trong loader)

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

    return "\n".join(final_content_lines)
# --- END NEW ---


# --- MODIFIED: Hàm chính (Orchestrator) ---
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

        # 2. Xác định đường dẫn
        start_path, scan_root = _resolve_start_and_scan_paths(
            logger, cli_args.get("start_path")
        )

        # 3. Hợp nhất các bộ lọc
        ext_filter_set, ignore_spec, submodule_paths = _resolve_filters(
            logger, cli_args, file_config, scan_root
        )

        # 4. Quét File [cite: 254]
        files_to_pack = scan_files(
            logger, start_path, ignore_spec, ext_filter_set, submodule_paths, scan_root
        )
        if not files_to_pack:
            logger.warning("Không tìm thấy file nào khớp với tiêu chí.")
            return {'status': 'empty'}
        logger.info(f"Tìm thấy {len(files_to_pack)} file để đóng gói.")

        # 5. Tạo cây [cite: 255]
        tree_str = ""
        if not no_tree:
            logger.debug("Đang tạo cây thư mục...")
            tree_str = generate_tree_string(start_path, files_to_pack, scan_root)

        # 6. Đọc nội dung file [cite: 255]
        files_content: Dict[Path, str] = {}
        # Chỉ đọc nếu không phải dry-run HOẶC (cần cây và dry-run)
        if not (dry_run and no_tree): 
            files_content = load_files_content(logger, files_to_pack, scan_root)

        # 7. Đóng gói
        final_content = _assemble_packed_content(
            files_to_pack=files_to_pack,
            files_content=files_content,
            scan_root=scan_root,
            tree_str=tree_str,
            no_header=cli_args.get("no_header", False),
            dry_run=dry_run,
        )

        # 8. Tính toán Output Path
        final_output_path = _resolve_output_path(
            logger, cli_args, file_config, start_path
        )

        # 9. Trả về Result Object [cite: 262]
        return {
            'status': 'ok',
            'final_content': final_content,
            'output_path': final_output_path, # Có thể chứa '~'
            'stdout': cli_args.get("stdout", False),
            'dry_run': dry_run,
            'file_list_relative': [p.relative_to(scan_root) for p in files_to_pack],
            'scan_root': scan_root,
            'tree_string': tree_str,
            'no_tree': no_tree
        }

    except FileNotFoundError as e:
        # Bắt lỗi từ _resolve_start_and_scan_paths
        return {'status': 'error', 'message': str(e)}
    except Exception as e:
        logger.error(f"Lỗi không mong muốn trong pack_code core: {e}")
        logger.debug("Traceback:", exc_info=True)
        return {'status': 'error', 'message': f"Lỗi không mong muốn: {e}"}
# --- END MODIFIED ---