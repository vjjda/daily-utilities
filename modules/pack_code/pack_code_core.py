# Path: modules/pack_code/pack_code_core.py

"""
Core logic for pack_code.
"""

import logging
from pathlib import Path
import os
from typing import Dict, Any, List, Optional, Set, TYPE_CHECKING

# --- MODIFIED: Thêm imports ---
try:
    import pathspec
except ImportError:
    pathspec = None

if TYPE_CHECKING:
    import pathspec

# Import các tiện ích cốt lõi
from utils.core import (
    find_git_root,
    parse_gitignore,
    compile_spec_from_patterns,
    is_path_matched,
    resolve_set_modification,
    get_submodule_paths,
    parse_comma_list
)

# Import loader
from .pack_code_loader import load_files_content
# Import config
from .pack_code_config import DEFAULT_EXTENSIONS, DEFAULT_IGNORE
# --- END MODIFIED ---

__all__ = ["process_pack_code_logic"]


# --- NEW: Hàm quét file (Dựa trên scanner của cpath) ---
def _scan_files(
    logger: logging.Logger,
    start_path: Path,
    ignore_spec: Optional['pathspec.PathSpec'],
    ext_filter_set: Set[str],
    submodule_paths: Set[Path],
    scan_root: Path
) -> List[Path]:
    """
    Quét và lọc file dựa trên các bộ lọc đã được biên dịch.
    """
    files_to_pack: List[Path] = []
    
    if start_path.is_file():
        all_files = [start_path]
    elif start_path.is_dir():
        all_files = list(start_path.rglob("*"))
    else:
        logger.error(f"Đường dẫn bắt đầu không hợp lệ: {start_path}")
        return []

    for file_path in all_files:
        if file_path.is_dir():
            continue

        # 1. Bỏ qua file trong submodule
        if any(file_path.is_relative_to(p) for p in submodule_paths):
            continue
            
        # 2. Bỏ qua file bị ignore (Config + .gitignore)
        if is_path_matched(file_path, ignore_spec, scan_root):
            continue
            
        # 3. Lọc theo đuôi file
        file_ext = file_path.suffix.lstrip('.')
        if file_ext not in ext_filter_set:
            continue
            
        files_to_pack.append(file_path)
        
    # Sắp xếp file theo thứ tự alphabet
    files_to_pack.sort()
    return files_to_pack
# --- END NEW ---


# --- NEW: Hàm tạo cây thư mục (dạng string) ---
def _generate_tree_string(
    start_path: Path, 
    file_paths: List[Path]
) -> str:
    """
    Tạo một cây thư mục dạng string từ danh sách các file.
    """
    tree_lines: List[str] = []
    
    # Sử dụng dict để lưu cấu trúc cây
    tree_structure: Dict[Path, Dict[str, Any]] = {}

    # Thư mục gốc (có thể là file hoặc thư mục)
    root_node_name = start_path.name
    tree_lines.append(f"{root_node_name}{'/' if start_path.is_dir() else ''}")

    # Chỉ xây dựng cây nếu start_path là thư mục và có file
    if not start_path.is_dir() or not file_paths:
        return "".join(tree_lines)

    # Chuyển đổi paths sang relative_paths
    relative_paths = [p.relative_to(start_path) for p in file_paths]
    
    # Sắp xếp file/thư mục
    # Tạo một set chứa tất cả các phần (thư mục và file)
    all_parts = set()
    for rel_path in relative_paths:
        all_parts.add(rel_path)
        for parent in rel_path.parents:
            if parent != Path('.'):
                all_parts.add(parent)
    
    sorted_parts = sorted(list(all_parts), key=lambda p: p.parts)
    
    # Dùng một dict để theo dõi các thư mục đã in
    printed_parents: Dict[Path, str] = {}
    
    for part in sorted_parts:
        # Xác định indent
        level = len(part.parts) - 1
        indent_prefix = "".join(printed_parents.get(p, "    ") for p in part.parents if p != Path('.'))
        
        # Xác định pointer (├── hoặc └──)
        # Kiểm tra xem đây có phải là entry cuối cùng trong thư mục cha của nó không
        siblings = [
            p for p in sorted_parts 
            if p.parent == part.parent and len(p.parts) == len(part.parts)
        ]
        is_last = (part == siblings[-1])
        pointer = "└── " if is_last else "├── "
        
        # Cập nhật dict 'printed_parents' cho các cấp độ con
        if part.is_dir(): # (pathspec coi 'a/b' là file, 'a/b/' là dir)
             # Thực tế, 'part' từ 'relative_paths' luôn là file
             # Chúng ta cần kiểm tra xem nó có phải là thư mục trong `all_parts` không
             is_dir = any(p.parent == part for p in sorted_parts)
             
             line = f"{indent_prefix}{pointer}{part.name}{'/' if is_dir else ''}"
             
             # Nếu là thư mục, lưu lại indent cho con
             if is_dir:
                 printed_parents[part] = "    " if is_last else "│   "
        else:
            line = f"{indent_prefix}{pointer}{part.name}"

        tree_lines.append(line)

    return "\n".join(tree_lines)
# --- END NEW ---


# --- MODIFIED: Hàm logic chính ---
def process_pack_code_logic(logger: logging.Logger, **cli_args) -> Dict[str, Any]:
    """
    Hàm logic chính, chỉ phân tích, không có side-effect.
    """
    logger.info("Core logic running...")
    
    # 1. Trích xuất tham số từ CLI (đã được parse bởi entrypoint)
    start_path: Path = cli_args.get("start_path") # Đã expanduser
    output_path_arg: Optional[Path] = cli_args.get("output") # Đã expanduser
    stdout: bool = cli_args.get("stdout", False)
    ext_cli_str: Optional[str] = cli_args.get("extensions")
    ignore_cli_str: Optional[str] = cli_args.get("ignore")
    no_gitignore: bool = cli_args.get("no_gitignore", False)
    dry_run: bool = cli_args.get("dry_run", False)
    no_header: bool = cli_args.get("no_header", False)
    no_tree: bool = cli_args.get("no_tree", False)
    
    # 2. Xác định gốc quét (Scan Root) cho các quy tắc
    # (Giống logic cpath: dùng git root nếu có, hoặc thư mục cha)
    scan_root: Path
    if start_path.is_file():
        scan_root = find_git_root(start_path.parent) or start_path.parent
    else:
        scan_root = find_git_root(start_path) or start_path
    logger.debug(f"Scan Root (cho quy tắc .gitignore): {scan_root.as_posix()}")
    logger.debug(f"Start Path (nơi bắt đầu quét): {start_path.as_posix()}")

    # 3. Hợp nhất các bộ lọc (Tái sử dụng utils.core)
    
    # 3.1. Lọc Extensions
    default_ext_set = parse_comma_list(DEFAULT_EXTENSIONS)
    ext_filter_set = resolve_set_modification(default_ext_set, ext_cli_str)
    
    # 3.2. Lọc Ignore
    default_ignore_set = parse_comma_list(DEFAULT_IGNORE)
    # (Logic ignore của pcode là THÊM vào, không phải +/-)
    cli_ignore_set = parse_comma_list(ignore_cli_str)
    
    gitignore_patterns: Set[str] = set()
    if not no_gitignore:
        gitignore_patterns = parse_gitignore(scan_root)
        logger.debug(f"Đã tải {len(gitignore_patterns)} quy tắc từ .gitignore")
        
    all_ignore_patterns = default_ignore_set.union(cli_ignore_set).union(gitignore_patterns)
    ignore_spec = compile_spec_from_patterns(all_ignore_patterns)
    
    # 3.3. Submodules
    submodule_paths = get_submodule_paths(scan_root, logger)

    # 4. Quét File (Logic nội bộ)
    files_to_pack = _scan_files(
        logger, start_path, ignore_spec, ext_filter_set, submodule_paths, scan_root
    )
    
    if not files_to_pack:
        logger.warning("Không tìm thấy file nào khớp với tiêu chí.")
        return {'status': 'empty'}

    logger.info(f"Tìm thấy {len(files_to_pack)} file để đóng gói.")

    # 5. Tạo cây (Nếu cần)
    tree_str = ""
    if not no_tree:
        logger.debug("Đang tạo cây thư mục...")
        tree_str = _generate_tree_string(start_path, files_to_pack)

    # 6. Đọc nội dung file (Gọi Loader)
    # (Bỏ qua đọc file nếu là dry_run và không cần cây)
    files_content: Dict[Path, str] = {}
    if not (dry_run and no_tree):
        files_content = load_files_content(logger, files_to_pack, scan_root)
    
    # 7. Đóng gói (Pack)
    final_content_lines: List[str] = []
    
    if tree_str:
        final_content_lines.append(tree_str)
        final_content_lines.append("\n" + ("=" * 80) + "\n")

    # (Chỉ thêm nội dung file nếu không phải dry_run)
    if not dry_run:
        for file_path in files_to_pack:
            content = files_content.get(file_path)
            if content is None:
                continue # File đã bị bỏ qua (ví dụ: lỗi encoding)

            rel_path_str = file_path.relative_to(scan_root).as_posix()
            
            if not no_header:
                header = f"===== Path: {rel_path_str} ====="
                final_content_lines.append(header)
            
            final_content_lines.append(content)
            
            if not no_header:
                final_content_lines.append("\n") # Thêm dòng trống sau file
    
    final_content = "\n".join(final_content_lines)

    # 8. Tính toán đường dẫn Output (Nếu cần)
    final_output_path: Optional[Path] = None
    if not stdout and not dry_run:
        if output_path_arg:
            final_output_path = output_path_arg
        else:
            # Mặc định: tmp/<start_path_name>.txt
            tmp_dir = scan_root / "tmp"
            start_name = start_path.stem if start_path.is_file() else start_path.name
            final_output_path = tmp_dir / f"{start_name}_context.txt"
            logger.debug(f"Sử dụng đường dẫn output mặc định: {final_output_path.relative_to(scan_root).as_posix()}")

    return {
        'status': 'ok',
        'final_content': final_content,
        'output_path': final_output_path,
        'stdout': stdout,
        'dry_run': dry_run,
        'file_list_relative': [p.relative_to(scan_root) for p in files_to_pack],
        'scan_root': scan_root # Cần cho Executor
    }

# --- END MODIFIED ---