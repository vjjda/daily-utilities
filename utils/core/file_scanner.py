# Path: utils/core/file_scanner.py
import logging
from pathlib import Path
from typing import List, Set, Optional, TYPE_CHECKING
import os

try:
    import pathspec
except ImportError:
    pathspec = None

if TYPE_CHECKING:
    import pathspec

from .filter import is_path_matched
from .file_extensions import is_extension_matched

__all__ = ["scan_directory_recursive"]


def scan_directory_recursive(
    logger: logging.Logger,
    directory: Path,
    scan_root: Path,
    ignore_spec: Optional["pathspec.PathSpec"],
    include_spec: Optional["pathspec.PathSpec"],
    prune_spec: Optional["pathspec.PathSpec"],
    extensions_filter: Optional[Set[str]],
    submodule_paths: Set[Path],
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

            if is_path_matched(path, prune_spec, scan_root):
                continue

            found_files.extend(
                scan_directory_recursive(
                    logger=logger,
                    directory=path,
                    scan_root=scan_root,
                    ignore_spec=ignore_spec,
                    include_spec=include_spec,
                    prune_spec=prune_spec,
                    extensions_filter=extensions_filter,
                    submodule_paths=submodule_paths,
                )
            )
        elif entry.is_file(follow_symlinks=False):

            if include_spec and not is_path_matched(path, include_spec, scan_root):
                continue

            if extensions_filter is not None:
                if not is_extension_matched(path, extensions_filter):
                    continue

            found_files.append(path)

    return found_files
