# Path: modules/stubgen/stubgen_internal/stubgen_loader.py
"""
File Scanning and Config Loading logic for the Stub Generator (sgen) module.
"""

import logging
from pathlib import Path
# SỬA: Import thêm Tuple, Dict
from typing import List, Set, Dict, Any, TYPE_CHECKING, Iterable, Optional, Tuple

try:
    import pathspec
except ImportError:
    pathspec = None

if TYPE_CHECKING:
    import pathspec

from utils.core import (
    get_submodule_paths,
    parse_gitignore, 
    is_path_matched,
    load_and_merge_configs,
    compile_spec_from_patterns 
)

from .stubgen_config import (
    PROJECT_CONFIG_FILENAME, CONFIG_FILENAME, CONFIG_SECTION_NAME
)

__all__ = ["find_gateway_files", "load_config_files"]


def load_config_files(
    start_dir: Path,
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Tải và hợp nhất cấu hình từ .project.toml và .sgen.toml.
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
    Kiểm tra (heuristic) xem file __init__.py có phải là gateway động không.
    """
    try:
        content = path.read_text(encoding='utf-8')
        return all(indicator in content for indicator in dynamic_import_indicators)
    except Exception:
        return False

# SỬA: Thay đổi chữ ký hàm và kiểu trả về
def find_gateway_files(
    logger: logging.Logger,
    scan_root: Path,
    ignore_list: List[str], 
    include_spec: Optional['pathspec.PathSpec'],
    dynamic_import_indicators: List[str],
    script_file_path: Path
) -> Tuple[List[Path], Dict[str, bool]]:
    """
    Tìm tất cả các file __init__.py là "gateway động".
    Args:
        ... (các args không đổi) ...
    Returns:
        Tuple[List[Path], Dict[str, bool]]:
            - Danh sách các file __init__.py hợp lệ.
            - Dict trạng thái (gitignore_found, gitmodules_found).
    """

    # SỬA: Thêm dict trạng thái
    scan_status = {
        'gitignore_found': False,
        'gitmodules_found': False
    }

    gitignore_patterns: List[str] = parse_gitignore(scan_root) 
    if gitignore_patterns: # SỬA: Cập nhật trạng thái
        scan_status['gitignore_found'] = True

    all_ignore_patterns_list: List[str] = ignore_list + gitignore_patterns
    ignore_spec = compile_spec_from_patterns(all_ignore_patterns_list, scan_root)

    submodule_paths = get_submodule_paths(scan_root, logger)
    if submodule_paths: # SỬA: Cập nhật trạng thái
        scan_status['gitmodules_found'] = True
    
    logger.debug(f"Scanning for '__init__.py' within: {scan_root.as_posix()}")
    
    if include_spec:
        logger.debug(f"Applying inclusion filter (include).")
    
    gateway_files: List[Path] = []

    for path in scan_root.rglob('*'):
        if not path.is_file() or path.name != '__init__.py':
            continue

        abs_path = path.resolve() 

        if abs_path.samefile(script_file_path): continue

        is_in_submodule = any(abs_path.is_relative_to(p) for p in submodule_paths)
        if is_in_submodule: continue

        # 1. Lọc Âm (Ignore)
        if is_path_matched(path.parent, ignore_spec, scan_root) or \
            is_path_matched(path, ignore_spec, scan_root):
            continue

        # 2. Lọc Dương (Include)
        if include_spec:
            if not is_path_matched(path, include_spec, scan_root):
                logger.debug(f"Skipping (not in include_spec): {path.relative_to(scan_root).as_posix()}")
                continue

        # 3. Kiểm tra Gateway
        if _is_dynamic_gateway(path, dynamic_import_indicators):
            gateway_files.append(path)

    # SỬA: Trả về tuple
    return gateway_files, scan_status