# Path: modules/stubgen/stubgen_loader.py

"""
File Scanning logic for the Stub Generator (sgen) module.
"""

import logging
import sys
from pathlib import Path
from typing import List, Set, Final, Dict, Any

# Tái sử dụng các tiện ích Git, Filtering
from utils.core import get_submodule_paths, parse_gitignore, is_path_matched
# --- MODIFIED: Import helper chung ---
from utils.core import load_and_merge_configs
# --- END MODIFIED ---


# Import Configs
from .stubgen_config import (
    DEFAULT_IGNORE, SCAN_ROOTS, DYNAMIC_IMPORT_INDICATORS,
    PROJECT_CONFIG_FILENAME, CONFIG_FILENAME, CONFIG_SECTION_NAME
)


__all__ = ["find_gateway_files", "load_config_files"]


# --- NEW: Hàm tải config (tương tự cpath/ctree) ---
def load_config_files(
    start_dir: Path, 
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Tải file .project.toml VÀ .sgen.toml,
    trích xuất và merge section [sgen].
    
    (Logic này đã được chuyển vào utils.core.load_and_merge_configs)
    """
    
    # --- MODIFIED: Tái sử dụng logic chung ---
    return load_and_merge_configs(
        start_dir=start_dir,
        logger=logger,
        project_config_filename=PROJECT_CONFIG_FILENAME,
        local_config_filename=CONFIG_FILENAME,
        config_section_name=CONFIG_SECTION_NAME
    )
    # --- END MODIFIED ---


def _is_dynamic_gateway(
    path: Path,
    dynamic_import_indicators: List[str] 
) -> bool:
    """
    Checks if an __init__.py file uses dynamic import (import_module + globals()).
    """
    try:
        content = path.read_text(encoding='utf-8')
        return all(indicator in content for indicator in dynamic_import_indicators)
    except Exception:
        return False
        
def find_gateway_files(
    logger: logging.Logger, 
    scan_root: Path,
    ignore_set: Set[str],
    restrict_list: List[str],
    dynamic_import_indicators: List[str],
    script_file_path: Path
) -> List[Path]:
    """
    Finds all relevant __init__.py files, respecting ignore rules and scan roots.
    """
    
    # (Nội dung hàm này giữ nguyên)
    
    # 1. Kết hợp quy tắc lọc (Git + FNMATCH)
    gitignore_spec = parse_gitignore(scan_root)
    submodule_paths = get_submodule_paths(scan_root, logger)
    
    fnmatch_patterns = ignore_set 
    
    # 2. Xác định phạm vi quét
    search_sub_roots = restrict_list 

    logger.debug(f"Scanning within sub-roots: {search_sub_roots}")
    
    gateway_files: List[Path] = []
    
    for sub_root_str in search_sub_roots:
        root_path = (scan_root / sub_root_str).resolve()
        
        if not root_path.exists():
            logger.debug(f"Skipping non-existent root: {sub_root_str}")
            continue

        for path in root_path.rglob('__init__.py'):
            
            if path.resolve().samefile(script_file_path):
                continue
            
            is_in_submodule = any(path.is_relative_to(p) for p in submodule_paths)
            if is_in_submodule:
                logger.debug(f"Skipping file (submodule): {path.relative_to(scan_root).as_posix()}")
                continue
                
            if is_path_matched(path.parent, fnmatch_patterns, scan_root) or \
               is_path_matched(path, fnmatch_patterns, scan_root):
                logger.debug(f"Skipping file (fnmatch ignore): {path.relative_to(scan_root).as_posix()}")
                continue

            if gitignore_spec:
                try:
                    rel_path = path.relative_to(scan_root).as_posix()
                    if gitignore_spec.match_file(rel_path):
                        logger.debug(f"Skipping file (.gitignore): {rel_path}")
                        continue
                except ValueError:
                    pass
            
            if _is_dynamic_gateway(path, dynamic_import_indicators):
                gateway_files.append(path)
                logger.debug(f"Found dynamic gateway: {path.relative_to(scan_root).as_posix()}")
            else:
                logger.debug(f"Skipping file (not dynamic gateway): {path.relative_to(scan_root).as_posix()}")
                
    return gateway_files