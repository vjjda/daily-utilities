#!/usr/bin/env python3
# Path: modules/tree/tree_core.py

import configparser
import fnmatch
from pathlib import Path
import os
import logging 
from typing import List, Set, Optional, Dict, Union

# --- CÁC HẰNG SỐ NỘI BỘ (Chỉ dùng trong module này) ---
DEFAULT_IGNORE: Set[str] = {
    "__pycache__", ".venv", "venv", "node_modules", 
    ".git"
}
DEFAULT_PRUNE: Set[str] = {"dist", "build"}
DEFAULT_DIRS_ONLY: Set[str] = set()
DEFAULT_MAX_LEVEL: Optional[int] = None
CONFIG_FILENAME = ".tree.ini"
PROJECT_CONFIG_FILENAME = ".project.ini" 
CONFIG_SECTION_NAME = "tree" 

# --- HÀM HỖ TRỢ ---

def get_submodule_paths(root: Path, logger: Optional[logging.Logger] = None) -> Set[str]: 
    """Lấy tên các thư mục submodule dựa trên file .gitmodules."""
    submodule_paths = set()
    gitmodules_path = root / ".gitmodules"
    if gitmodules_path.exists():
        try:
            config = configparser.ConfigParser()
            config.read(gitmodules_path)
            for section in config.sections():
                
                if config.has_option(section, "path"):
                    path_str = config.get(section, "path")
                    # Chỉ cần tên thư mục (relative path)
                    submodule_paths.add(path_str.split(os.sep)[-1]) 
        except configparser.Error as e:
            
            warning_msg = f"Could not parse .gitmodules file: {e}"
            if logger:
                logger.warning(f"⚠️ {warning_msg}")
            else:
                print(f"Warning: {warning_msg}") 
            
    return submodule_paths

def is_path_matched(path: Path, patterns: Set[str], start_dir: Path) -> bool:
    """Kiểm tra xem đường dẫn có khớp với bất kỳ mẫu nào không (sử dụng fnmatch)."""
    if not patterns: return False
    relative_path_str = path.relative_to(start_dir).as_posix()
    for pattern in patterns: 
        if fnmatch.fnmatch(path.name, pattern) or fnmatch.fnmatch(relative_path_str, pattern):
            return True
    return False

def parse_comma_list(value: Union[str, None]) -> Set[str]:
    """Chuyển chuỗi phân cách bằng dấu phẩy thành set các mục."""
    if not value: return set() 
    return {item.strip() for item in value.split(',') if item.strip() != ''}

# --- HÀM CHÍNH (LOGIC ĐỆ QUY) ---

def generate_tree(
    directory: Path, 
    start_dir: Path, 
    prefix: str = "", 
    level: int = 0, 
    max_level: Optional[int] = None, 
    ignore_list: Set[str] = DEFAULT_IGNORE, 
    submodules: Set[str] = None, 
    prune_list: Set[str] = DEFAULT_PRUNE,
    dirs_only_list: Set[str] = DEFAULT_DIRS_ONLY, 
    is_in_dirs_only_zone: bool = False, 
    counters: Dict[str, int] = None
):
    """
    Hàm đệ quy để tạo và in ra biểu đồ cây thư mục.
    """
    if max_level is not None and level >= max_level: return
    
    try: 
        contents = [path for path in directory.iterdir() if not path.name.startswith('.')]
    except (FileNotFoundError, NotADirectoryError): 
        return
        
    dirs = sorted(
        [d for d in contents if d.is_dir() and not is_path_matched(d, ignore_list, start_dir)], 
        key=lambda p: p.name.lower()
    )
    
    files: List[Path] = []
    if not is_in_dirs_only_zone: 
        files = sorted(
            [f for f in contents if f.is_file() and not is_path_matched(f, ignore_list, start_dir)], 
            key=lambda p: p.name.lower()
        )
        
    items_to_print = dirs + files
    pointers = ["├── "] * (len(items_to_print) - 1) + ["└── "]

    for pointer, path in zip(pointers, items_to_print):
        if path.is_dir(): counters['dirs'] += 1
        else: counters['files'] += 1

        is_submodule = path.is_dir() and path.name in submodules
        is_pruned = path.is_dir() and is_path_matched(path, prune_list, start_dir)
        
        is_dirs_only_entry = (
            path.is_dir() and 
            is_path_matched(path, dirs_only_list, start_dir) and 
            not is_in_dirs_only_zone
        ) 
        
        line = f"{prefix}{pointer}{path.name}{'/' if path.is_dir() else ''}"
        
        if is_submodule: line += " [submodule]"
        elif is_pruned: line += " [...]"
        elif is_dirs_only_entry: line += " [dirs only]"
        
        print(line)

        if path.is_dir() and not is_submodule and not is_pruned:
            extension = "│   " if pointer == "├── " else "    " 
            
            next_is_in_dirs_only_zone = is_in_dirs_only_zone or is_dirs_only_entry
            
            generate_tree(
                path, start_dir, prefix + extension, level + 1, max_level, 
                ignore_list, submodules, prune_list, dirs_only_list, 
                next_is_in_dirs_only_zone, counters
            )

# --- NỘI DUNG TEMPLATE CONFIG (Tải từ file) ---

try:
    _CURRENT_DIR = Path(__file__).parent
    _TEMPLATE_PATH = _CURRENT_DIR / "tree.ini.template"
    CONFIG_TEMPLATE = _TEMPLATE_PATH.read_text(encoding="utf-8")
except FileNotFoundError:
    print("FATAL ERROR: Could not find 'tree.ini.template'.")
    CONFIG_TEMPLATE = "; ERROR: Template file missing."
except Exception as e:
    print(f"FATAL ERROR: Could not read 'tree.ini.template': {e}")
    CONFIG_TEMPLATE = "; ERROR: Template file could not be read."