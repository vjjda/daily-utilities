# Path: modules/stubgen/stubgen_loader.py

"""
File Scanning logic for the Stub Generator (sgen) module.
"""

import logging
from pathlib import Path
from typing import List, Set, Final

# Tái sử dụng các tiện ích Git, Filtering
from utils.core import get_submodule_paths, parse_gitignore, is_path_matched

# Import Configs
from .stubgen_config import DEFAULT_IGNORE, SCAN_ROOTS, DYNAMIC_IMPORT_INDICATORS

__all__ = ["find_gateway_files"]

def _is_dynamic_gateway(path: Path) -> bool:
    """
    Checks if an __init__.py file uses dynamic import (import_module + globals()).
    """
    try:
        content = path.read_text(encoding='utf-8')
        return all(indicator in content for indicator in DYNAMIC_IMPORT_INDICATORS)
    except Exception:
        return False
        
def find_gateway_files(
    logger: logging.Logger, 
    scan_root: Path,
    cli_ignore: Set[str],
    cli_restrict: Set[str],
    script_file_path: Path
) -> List[Path]:
    """
    Finds all relevant __init__.py files, respecting ignore rules and scan roots.
    """
    
    # 1. Kết hợp quy tắc lọc (Git + FNMATCH)
    gitignore_spec = parse_gitignore(scan_root)
    submodule_paths = get_submodule_paths(scan_root, logger)
    
    fnmatch_patterns = DEFAULT_IGNORE.union(cli_ignore)
    
    # 2. Xác định phạm vi quét
    search_sub_roots = SCAN_ROOTS
    if cli_restrict:
        # Nếu có cờ --restrict, ghi đè SCAN_ROOTS mặc định
        search_sub_roots = list(cli_restrict)

    logger.debug(f"Scanning within sub-roots: {search_sub_roots}")
    
    gateway_files: List[Path] = []
    
    for sub_root_str in search_sub_roots:
        root_path = (scan_root / sub_root_str).resolve()
        
        if not root_path.exists():
            logger.debug(f"Skipping non-existent root: {sub_root_str}")
            continue

        for path in root_path.rglob('__init__.py'):
            
            # --- LỌC 1: Bỏ qua script entrypoint (dù không phải __init__.py nhưng là phòng thủ)
            if path.resolve().samefile(script_file_path):
                continue
            
            # --- LỌC 2: Submodule Check
            is_in_submodule = any(path.is_relative_to(p) for p in submodule_paths)
            if is_in_submodule:
                logger.debug(f"Skipping file (submodule): {path.relative_to(scan_root).as_posix()}")
                continue
                
            # --- LỌC 3: FNMATCH Check
            if is_path_matched(path.parent, fnmatch_patterns, scan_root) or \
               is_path_matched(path, fnmatch_patterns, scan_root):
                logger.debug(f"Skipping file (fnmatch ignore): {path.relative_to(scan_root).as_posix()}")
                continue

            # --- LỌC 4: Gitignore Check
            if gitignore_spec:
                try:
                    rel_path = path.relative_to(scan_root).as_posix()
                    if gitignore_spec.match_file(rel_path):
                        logger.debug(f"Skipping file (.gitignore): {rel_path}")
                        continue
                except ValueError:
                    pass
            
            # --- LỌC 5: Dynamic Import Check
            if _is_dynamic_gateway(path):
                gateway_files.append(path)
                logger.debug(f"Found dynamic gateway: {path.relative_to(scan_root).as_posix()}")
            else:
                logger.debug(f"Skipping file (not dynamic gateway): {path.relative_to(scan_root).as_posix()}")
                
    return gateway_files