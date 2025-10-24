# Path: modules/tree/tree_executor.py

from pathlib import Path
import logging 
from typing import List, Set, Optional, Dict

# --- MODIFIED: Thêm pathspec ---
try:
    import pathspec
except ImportError:
    pathspec = None
# --- END MODIFIED ---

# --- IMPORT UTILITIES FROM CENTRAL LOCATION ---
from utils.core import is_path_matched
# --------------------------------------------

# --- MODULE-SPECIFIC CONSTANTS (IMPORTED) ---
from .tree_config import (
    DEFAULT_IGNORE, DEFAULT_PRUNE, DEFAULT_DIRS_ONLY_LOGIC,
    DEFAULT_MAX_LEVEL
)
# ------------------------------------------

__all__ = ["generate_tree"]


# --- MAIN RECURSIVE LOGIC (MOVED FROM CORE) ---
def generate_tree(
    directory: Path, 
    start_dir: Path, 
    prefix: str = "", 
    level: int = 0, 
    max_level: Optional[int] = DEFAULT_MAX_LEVEL, 
    ignore_list: Set[str] = DEFAULT_IGNORE, 
    submodules: Set[str] = None, 
    prune_list: Set[str] = DEFAULT_PRUNE,
    # --- MODIFIED: Thêm gitignore_spec ---
    gitignore_spec: Optional['pathspec.PathSpec'] = None,
    # --- END MODIFIED ---
    dirs_only_list: Set[str] = DEFAULT_DIRS_ONLY_LOGIC, 
    is_in_dirs_only_zone: bool = False, 
    counters: Dict[str, int] = None
):
    """
    Recursive function to generate and print the directory tree.
    (This function has side-effects: print())
    """
    if max_level is not None and level >= max_level: 
        return
    
    try: 
        contents = [path for path in directory.iterdir() if not path.name.startswith('.')]
    except (FileNotFoundError, NotADirectoryError): 
        return
        
    # --- NEW: Helper function for combined filtering ---
    def is_ignored(path: Path) -> bool:
        # 1. Check fnmatch list (từ .tree.ini)
        if is_path_matched(path, ignore_list, start_dir):
            return True
        
        # 2. Check pathspec list (từ .gitignore)
        if gitignore_spec:
            try:
                rel_path = path.relative_to(start_dir)
                # pathspec cần POSIX path
                rel_path_str = rel_path.as_posix()
                
                # pathspec xử lý thư mục tốt hơn nếu có dấu /
                if path.is_dir() and not rel_path_str.endswith('/'):
                    rel_path_str += '/'
                
                if rel_path_str == './': # Bỏ qua thư mục gốc
                    return False

                return gitignore_spec.match_file(rel_path_str)
            except Exception:
                # Bỏ qua lỗi nếu không thể lấy đường dẫn tương đối
                # (ví dụ: pathspec không xử lý tốt path='.')
                return False
                
        return False
    # --- END NEW ---
        
    # --- MODIFIED: Sử dụng hàm is_ignored ---
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
    # --- END MODIFIED ---
        
    items_to_print = dirs + files
    pointers = ["├── "] * (len(items_to_print) - 1) + ["└── "]

    for pointer, path in zip(pointers, items_to_print):
        if path.is_dir(): 
            counters['dirs'] += 1
        else: 
            counters['files'] += 1

        is_submodule = path.is_dir() and path.name in submodules
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
            
            # --- MODIFIED: Truyền gitignore_spec đệ quy ---
            generate_tree(
                path, start_dir, prefix + extension, level + 1, max_level, 
                ignore_list, submodules, prune_list, 
                gitignore_spec, # <-- Tham số mới
                dirs_only_list, 
                next_is_in_dirs_only_zone, counters
            )
            # --- END MODIFIED ---