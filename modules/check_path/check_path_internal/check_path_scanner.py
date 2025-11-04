# Path: modules/check_path/check_path_internal/check_path_scanner.py
import logging
from pathlib import Path
import sys
from typing import List, Optional, TYPE_CHECKING, Tuple, Dict

if "PROJECT_ROOT" not in locals():
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

try:
    import pathspec
except ImportError:
    pathspec = None

if TYPE_CHECKING:
    import pathspec


from utils.core import (
    get_submodule_paths,
    is_path_matched,
    is_extension_matched,
    scan_directory_recursive,
)
from ..check_path_config import DEFAULT_IGNORE

__all__ = ["scan_files"]


def scan_files(
    logger: logging.Logger,
    start_path: Path,
    ignore_spec: Optional["pathspec.PathSpec"],
    extensions: List[str],
    scan_root: Path,
    script_file_path: Path,
) -> Tuple[List[Path], Dict[str, bool]]:
    scan_status = {"gitignore_found": False, "gitmodules_found": False}
    scan_path = start_path.resolve()

    if not scan_path.exists():
        logger.warning(f"Thư mục quét không tồn tại: {scan_path.as_posix()}")
        return [], scan_status

    submodule_paths = get_submodule_paths(scan_root, logger)
    if submodule_paths:
        scan_status["gitmodules_found"] = True

    if (ignore_spec is not None) and (len(ignore_spec.patterns) > len(DEFAULT_IGNORE)):
        scan_status["gitignore_found"] = True
    final_ignore_spec = ignore_spec

    all_files: List[Path] = []
    extensions_set = set(extensions)

    if scan_path.is_dir():
        logger.debug(
            f"Scanner (new): Chạy scan_directory_recursive trên {scan_path.name}"
        )

        all_files = scan_directory_recursive(
            logger=logger,
            directory=scan_path,
            scan_root=scan_root,
            ignore_spec=final_ignore_spec,
            include_spec=None,
            prune_spec=None,
            extensions_filter=extensions_set,
            submodule_paths=submodule_paths,
        )

    elif scan_path.is_file():

        if is_extension_matched(scan_path, extensions_set):
            all_files.append(scan_path)
        else:
            logger.warning(
                f"File '{scan_path.name}' bị bỏ qua do không khớp extension."
            )
            return [], scan_status

    files_to_process: List[Path] = []

    if scan_path.is_file():
        if all_files:
            file_path = all_files[0]
            abs_file_path = file_path.resolve()
            is_in_submodule = any(
                abs_file_path.is_relative_to(p) for p in submodule_paths
            )

            if not is_in_submodule and not is_path_matched(
                file_path, final_ignore_spec, scan_root
            ):
                files_to_process.append(file_path)
    else:

        files_to_process = all_files

    files_to_process.sort(key=lambda p: p.as_posix())
    return files_to_process, scan_status
