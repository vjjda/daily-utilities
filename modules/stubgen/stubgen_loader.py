# Path: modules/stubgen/stubgen_loader.py

"""
File Scanning logic for the Stub Generator (sgen) module.
"""

import logging
from pathlib import Path
from typing import List, Set, Dict, Any, TYPE_CHECKING # <-- Thêm TYPE_CHECKING

# --- NEW: Import pathspec (cho TYPE_CHECKING) ---
try:
    import pathspec
except ImportError:
    pathspec = None

if TYPE_CHECKING:
    import pathspec
# --- END NEW ---


# Tái sử dụng các tiện ích Git, Filtering
# --- MODIFIED: Import thêm compile_spec_from_patterns ---
from utils.core import (
    get_submodule_paths, 
    parse_gitignore, 
    is_path_matched,
    load_and_merge_configs,
    compile_spec_from_patterns
)


# Import Configs
# --- MODIFIED: Import đúng tên hằng số ---
from .stubgen_config import (
    PROJECT_CONFIG_FILENAME, CONFIG_FILENAME, CONFIG_SECTION_NAME
)
# --- END MODIFIED ---


__all__ = ["find_gateway_files", "load_config_files"]


def load_config_files(
    start_dir: Path, 
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Tải file .project.toml VÀ .sgen.toml,
    trích xuất và merge section [sgen].
    """
    return load_and_merge_configs(
        start_dir=start_dir,
        logger=logger,
        project_config_filename=PROJECT_CONFIG_FILENAME,
        local_config_filename=CONFIG_FILENAME,
        config_section_name=CONFIG_SECTION_NAME
    )


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
    
    # --- MODIFIED: Gộp logic ignore ---
    # parse_gitignore giờ trả về Set[str]
    gitignore_patterns = parse_gitignore(scan_root) 
    
    # (ignore_set được truyền vào)
    all_ignore_patterns = ignore_set.union(gitignore_patterns)
    
    # Biên dịch 1 lần
    ignore_spec = compile_spec_from_patterns(all_ignore_patterns) 
    # --- END MODIFIED ---

    submodule_paths = get_submodule_paths(scan_root, logger)
    # (fnmatch_patterns đã bị xóa, chỉ dùng ignore_spec)
    search_sub_roots = restrict_list 
    logger.debug(f"Scanning within sub-roots: {search_sub_roots}")
    gateway_files: List[Path] = []
    
    for sub_root_str in search_sub_roots:
        root_path = (scan_root / sub_root_str).resolve()
        if not root_path.exists():
            logger.debug(f"Skipping non-existent root: {sub_root_str}")
            continue
        for path in root_path.rglob('__init__.py'):
            if path.resolve().samefile(script_file_path): continue
            
            is_in_submodule = any(path.is_relative_to(p) for p in submodule_paths)
            if is_in_submodule: continue
            
            # --- MODIFIED: Gộp 2 bước lọc thành 1 ---
            # (Sử dụng is_path_matched (mới) với ignore_spec)
            # Logic cũ (is_path_matched(path.parent...)
            # là để bắt trường hợp thư mục cha bị ignore)
            if is_path_matched(path.parent, ignore_spec, scan_root) or \
               is_path_matched(path, ignore_spec, scan_root):
                continue
            # --- END MODIFIED ---
            
            if _is_dynamic_gateway(path, dynamic_import_indicators):
                gateway_files.append(path)
            # (else block để debug có thể giữ lại hoặc xóa)
            # else:
            #     logger.debug(f"Skipping file (not dynamic gateway): {path.relative_to(scan_root).as_posix()}")
                
    return gateway_files