# Path: modules/tree/tree_executor.py

"""
Logic thực thi cho module Tree (ctree).
(Chịu trách nhiệm cho các side-effect: print, I/O ghi file)
"""

from pathlib import Path
import logging 
from typing import List, Set, Optional, Dict, Any

try:
    import pathspec
except ImportError:
    pathspec = None

from utils.core import is_path_matched
from utils.logging_config import log_success 

from .tree_config import (
    DEFAULT_IGNORE, DEFAULT_PRUNE, DEFAULT_DIRS_ONLY_LOGIC,
    DEFAULT_MAX_LEVEL, CONFIG_FILENAME
)

__all__ = [
    "generate_tree", 
    "print_status_header", 
    "print_final_result",
]


def print_status_header(
    config_params: Dict[str, Any], 
    start_dir: Path, 
    is_git_repo: bool,
    cli_no_gitignore: bool
) -> None:
    """
    In tiêu đề trạng thái trước khi chạy tạo cây.
    (Side-effect: print)
    """
    is_truly_full_view = (
        not any(config_params["filter_lists"].values()) and 
        not config_params["using_gitignore"] and 
        config_params["max_level"] is None
    )
    
    filter_info = "Xem đầy đủ" if is_truly_full_view else "Xem đã lọc"
    level_info = "toàn bộ độ sâu" if config_params["max_level"] is None else f"giới hạn độ sâu: {config_params['max_level']}"
    mode_info = ", chỉ thư mục" if config_params["global_dirs_only_flag"] else ""
    git_info = ""
    if is_git_repo: 
        git_info = (
            ", Dự án Git (.gitignore bật)" if config_params["using_gitignore"] 
            else (", Dự án Git (.gitignore tắt do cờ)" if cli_no_gitignore 
                  else ", Dự án Git")
        )
        
    print(f"{start_dir.name}/ [{filter_info}, {level_info}{mode_info}{git_info}]")


def print_final_result(
    counters: Dict[str, int], 
    global_dirs_only: bool
) -> None:
    """
    In kết quả thống kê cuối cùng.
    (Side-effect: print)
    """
    files_info = (
        "0 file (bị ẩn)" if global_dirs_only and counters['files'] == 0 
        else f"{counters['files']} file"
    )
    print(f"\n{counters['dirs']} thư mục, {files_info}")


def generate_tree(
    directory: Path, 
    start_dir: Path, 
    prefix: str = "", 
    level: int = 0, 
    max_level: Optional[int] = DEFAULT_MAX_LEVEL, 
    ignore_list: Set[str] = DEFAULT_IGNORE, 
    submodules: Optional[Set[Path]] = None, 
    prune_list: Set[str] = DEFAULT_PRUNE,
    gitignore_spec: Optional['pathspec.PathSpec'] = None,
    dirs_only_list: Set[str] = DEFAULT_DIRS_ONLY_LOGIC, 
    is_in_dirs_only_zone: bool = False, 
    counters: Optional[Dict[str, int]] = None
):
    """
    Hàm đệ quy để tạo và in cây thư mục.
    (Side-effect: print)
    """
    if submodules is None:
        submodules = set()
    
    if counters is None:
        counters = {'dirs': 0, 'files': 0}
    
    if max_level is not None and level >= max_level: 
        return
    
    try: 
        contents = [path for path in directory.iterdir() if not path.name.startswith('.')]
    except (FileNotFoundError, NotADirectoryError): 
        return
        
    def is_ignored(path: Path) -> bool:
        if is_path_matched(path, ignore_list, start_dir):
            return True
        
        if gitignore_spec:
            try:
                rel_path = path.relative_to(start_dir)
                rel_path_str = rel_path.as_posix()
                
                if path.is_dir() and not rel_path_str.endswith('/'):
                    rel_path_str += '/'
                
                if rel_path_str == './':
                    return False

                return gitignore_spec.match_file(rel_path_str) 
            except Exception:
                return False
                
        return False
    
    dirs = sorted(
        [d for d in contents if d.is_dir() and not is_ignored(d)], 
        key=lambda p: p.name.lower()
    )
    
    files: List[Path] = []
    if not is_in_dirs_only_zone: 
        files = sorted(
            [f for f in contents if f.is_file() and not is_ignored(f)], 
            key=lambda p: p.name.lower()
        )
        
    items_to_print = dirs + files
    pointers = ["├── "] * (len(items_to_print) - 1) + ["└── "]

    for pointer, path in zip(pointers, items_to_print):
        if path.is_dir(): 
            counters['dirs'] += 1
        else: 
            counters['files'] += 1

        is_submodule = path.is_dir() and path.resolve() in submodules
        is_pruned = path.is_dir() and is_path_matched(path, prune_list, start_dir)
        is_dirs_only_entry = (
            path.is_dir() and 
            is_path_matched(path, dirs_only_list, start_dir) and 
            not is_in_dirs_only_zone
        ) 
        
        line = f"{prefix}{pointer}{path.name}{'/' if path.is_dir() else ''}"
        
        if is_submodule: 
            line += " [submodule]"
        elif is_pruned: 
            line += " [...]"
        elif is_dirs_only_entry: 
            line += " [dirs only]"
        
        print(line)

        if path.is_dir() and not is_submodule and not is_pruned:
            extension = "│   " if pointer == "├── " else "    " 
            next_is_in_dirs_only_zone = is_in_dirs_only_zone or is_dirs_only_entry
            
            generate_tree(
                path, start_dir, prefix + extension, level + 1, max_level, 
                ignore_list, submodules, prune_list, 
                gitignore_spec,
                dirs_only_list, 
                next_is_in_dirs_only_zone, counters
            )