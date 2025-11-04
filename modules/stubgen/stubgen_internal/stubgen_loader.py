# Path: modules/stubgen/stubgen_internal/stubgen_loader.py
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple

try:
    import pathspec
except ImportError:
    pathspec = None

if TYPE_CHECKING:
    import pathspec

from utils.core import (
    compile_spec_from_patterns,
    get_submodule_paths,
    is_path_matched,
    load_and_merge_configs,
    parse_gitignore,
)

from ..stubgen_config import (
    CONFIG_FILENAME,
    CONFIG_SECTION_NAME,
    PROJECT_CONFIG_FILENAME,
    PROJECT_CONFIG_ROOT_KEY,
)

__all__ = ["find_gateway_files", "load_config_files"]


def load_config_files(start_dir: Path, logger: logging.Logger) -> Dict[str, Any]:
    return load_and_merge_configs(
        start_dir=start_dir,
        logger=logger,
        project_config_filename=PROJECT_CONFIG_FILENAME,
        local_config_filename=CONFIG_FILENAME,
        config_section_name=CONFIG_SECTION_NAME,
        root_key=PROJECT_CONFIG_ROOT_KEY,
    )


def _is_dynamic_gateway(path: Path, dynamic_import_indicators: List[str]) -> bool:
    try:
        content = path.read_text(encoding="utf-8")

        return any(indicator in content for indicator in dynamic_import_indicators)
    except Exception:
        return False


def _scan_for_inits_recursive(
    logger: logging.Logger,
    directory: Path,
    scan_root: Path,
    ignore_spec: Optional["pathspec.PathSpec"],
    submodule_paths: Set[Path],
    dynamic_import_indicators: List[str],
    script_file_path: Path,
) -> List[Path]:
    found_files: List[Path] = []

    try:

        contents = list(os.scandir(directory))
    except (FileNotFoundError, NotADirectoryError, PermissionError) as e:
        logger.debug(f"Không thể truy cập thư mục: {directory.as_posix()} ({e})")
        return []

    for entry in contents:
        path = Path(entry.path)

        if is_path_matched(path, ignore_spec, scan_root):
            continue

        abs_path = path.resolve()
        if abs_path in submodule_paths:
            continue

        if entry.is_dir(follow_symlinks=False):

            found_files.extend(
                _scan_for_inits_recursive(
                    logger=logger,
                    directory=path,
                    scan_root=scan_root,
                    ignore_spec=ignore_spec,
                    submodule_paths=submodule_paths,
                    dynamic_import_indicators=dynamic_import_indicators,
                    script_file_path=script_file_path,
                )
            )
        elif entry.is_file(follow_symlinks=False) and entry.name == "__init__.py":

            if abs_path.samefile(script_file_path):
                continue

            if _is_dynamic_gateway(path, dynamic_import_indicators):
                found_files.append(path)

    return found_files


def find_gateway_files(
    logger: logging.Logger,
    scan_root: Path,
    ignore_list: List[str],
    dynamic_import_indicators: List[str],
    script_file_path: Path,
) -> Tuple[List[Path], Dict[str, bool]]:

    scan_status = {"gitignore_found": False, "gitmodules_found": False}

    gitignore_patterns: List[str] = parse_gitignore(scan_root)
    if gitignore_patterns:
        scan_status["gitignore_found"] = True

    all_ignore_patterns_list: List[str] = ignore_list + gitignore_patterns
    ignore_spec = compile_spec_from_patterns(all_ignore_patterns_list, scan_root)

    submodule_paths = get_submodule_paths(scan_root, logger)
    if submodule_paths:
        scan_status["gitmodules_found"] = True

    logger.debug(f"Scanning for dynamic '__init__.py' within: {scan_root.as_posix()}")

    gateway_files: List[Path] = _scan_for_inits_recursive(
        logger=logger,
        directory=scan_root,
        scan_root=scan_root,
        ignore_spec=ignore_spec,
        submodule_paths=submodule_paths,
        dynamic_import_indicators=dynamic_import_indicators,
        script_file_path=script_file_path,
    )

    return gateway_files, scan_status
