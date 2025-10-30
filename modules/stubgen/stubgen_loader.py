# Path: modules/stubgen/stubgen_loader.py
"""
File Scanning and Config Loading logic for the Stub Generator (sgen) module.
"""

import logging
from pathlib import Path
from typing import List, Set, Dict, Any, TYPE_CHECKING, Iterable, Optional

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
    
    Args:
        start_dir: Thư mục bắt đầu quét config.
        logger: Logger để ghi log.

    Returns:
        Một dict chứa cấu hình [sgen] đã được hợp nhất.
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
    Kiểm tra bằng cách đọc nội dung file và tìm tất cả các chuỗi
    trong `dynamic_import_indicators`.
    """
    try:
        content = path.read_text(encoding='utf-8')
        return all(indicator in content for indicator in dynamic_import_indicators)
    except Exception:
        return False

def find_gateway_files(
    logger: logging.Logger,
    scan_root: Path,
    ignore_list: List[str], 
    include_spec: Optional['pathspec.PathSpec'],
    dynamic_import_indicators: List[str],
    script_file_path: Path
) -> List[Path]:
    """
    Tìm tất cả các file __init__.py là "gateway động".
    Logic lọc nhiều bước:
    1. (Đã xóa) Chỉ quét trong các thư mục `restrict_list`.
    2. Áp dụng `ignore_list` (config) và `.gitignore`.
    3. (Nếu có) Áp dụng `include_spec` (bộ lọc dương).
    4. Kiểm tra xem file có phải là gateway động không (`_is_dynamic_gateway`).
    Args:
        logger: Logger.
        scan_root: Thư mục gốc để quét.
        ignore_list: Danh sách pattern (config/cli) để bỏ qua.
        include_spec: PathSpec (đã biên dịch) cho bộ lọc dương.
        dynamic_import_indicators: Danh sách chuỗi để nhận diện gateway động.
        script_file_path: Đường dẫn của chính script sgen (để bỏ qua).
    Returns:
        Danh sách các đối tượng Path đến file __init__.py hợp lệ.
    """

    gitignore_patterns: List[str] = parse_gitignore(scan_root) 

    all_ignore_patterns_list: List[str] = ignore_list + gitignore_patterns
    ignore_spec = compile_spec_from_patterns(all_ignore_patterns_list, scan_root)

    submodule_paths = get_submodule_paths(scan_root, logger)
    
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

    return gateway_files