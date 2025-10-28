# Path: modules/stubgen/stubgen_loader.py

"""
File Scanning logic for the Stub Generator (sgen) module.
"""

import logging
from pathlib import Path
# --- MODIFIED: Thêm Iterable ---
from typing import List, Set, Dict, Any, TYPE_CHECKING, Iterable
# --- END MODIFIED ---

# --- NEW: Import pathspec (cho TYPE_CHECKING) ---
try:
    import pathspec
except ImportError:
    pathspec = None

if TYPE_CHECKING:
    import pathspec
# --- END NEW ---


# Tái sử dụng các tiện ích Git, Filtering
# --- MODIFIED: Import các hàm cập nhật ---
from utils.core import (
    get_submodule_paths,
    parse_gitignore, # Trả về List[str]
    is_path_matched,
    load_and_merge_configs,
    compile_spec_from_patterns # Nhận Iterable[str]
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
    ignore_set: Set[str], # Ignore từ config/CLI (vẫn là Set)
    restrict_list: List[str],
    dynamic_import_indicators: List[str],
    script_file_path: Path
) -> List[Path]:
    """
    Finds all relevant __init__.py files, respecting ignore rules and scan roots.
    """

    # --- MODIFIED: Gộp logic ignore ---
    gitignore_patterns: List[str] = parse_gitignore(scan_root) # <-- List

    # --- MODIFIED: Gộp thành List ---
    # Ưu tiên: Config/CLI patterns -> Gitignore patterns
    all_ignore_patterns_list: List[str] = sorted(list(ignore_set)) + gitignore_patterns
    ignore_spec = compile_spec_from_patterns(all_ignore_patterns_list, scan_root)
    # --- END MODIFIED ---

    submodule_paths = get_submodule_paths(scan_root, logger)
    search_sub_roots = restrict_list
    logger.debug(f"Scanning within sub-roots: {search_sub_roots}")
    gateway_files: List[Path] = []

    for sub_root_str in search_sub_roots:
        root_path = (scan_root / sub_root_str).resolve()
        if not root_path.exists():
            logger.debug(f"Skipping non-existent root: {sub_root_str}")
            continue
        # --- MODIFIED: Dùng rglob('*') và kiểm tra tên sau ---
        # Điều này đáng tin cậy hơn rglob('__init__.py') trong một số trường hợp
        for path in root_path.rglob('*'):
            # Chỉ xử lý file __init__.py
            if not path.is_file() or path.name != '__init__.py':
                continue
            # --- END MODIFIED ---

            abs_path = path.resolve() # Resolve một lần

            if abs_path.samefile(script_file_path): continue

            is_in_submodule = any(abs_path.is_relative_to(p) for p in submodule_paths)
            if is_in_submodule: continue

            # Sử dụng scan_root làm gốc so sánh cho ignore_spec
            # Kiểm tra cả file và thư mục cha
            if is_path_matched(path.parent, ignore_spec, scan_root) or \
               is_path_matched(path, ignore_spec, scan_root):
                continue

            if _is_dynamic_gateway(path, dynamic_import_indicators):
                gateway_files.append(path)

    return gateway_files