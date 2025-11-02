# Path: modules/tree/tree_executor.py
from pathlib import Path
import logging
from typing import List, Set, Optional, Dict, Any, TYPE_CHECKING

try:
    import pathspec
except ImportError:
    pathspec = None

if TYPE_CHECKING:
    import pathspec

from utils.core import is_path_matched, is_extension_matched  # <<< ĐÃ THÊM
from utils.logging_config import log_success

from .tree_config import DEFAULT_MAX_LEVEL

__all__ = [
    "generate_tree",
    "print_status_header",
    "print_final_result",
]


def print_status_header(
    config_params: Dict[str, Any],
    start_dir: Path,
    is_git_repo: bool,
    cli_no_gitignore: bool,
) -> None:
    filter_lists = config_params["filter_lists"]

    is_truly_full_view = (
        not any(filter_lists.values())
        and not config_params["using_gitignore"]
        and config_params["max_level"] is None
    )

    filter_info = "Full view" if is_truly_full_view else "Filtered view"
    level_info = (
        "full depth"
        if config_params["max_level"] is None
        else f"depth limit: {config_params['max_level']}"
    )
    mode_info = ", dirs only" if config_params["global_dirs_only_flag"] else ""

    ext_filter = filter_lists.get("extensions")
    ext_info = ""
    if ext_filter is not None:
        if ext_filter:
            ext_info = f", extensions: {','.join(sorted(list(ext_filter)))}"
        else:
            ext_info = ", extensions: (none)"

    git_info = ""
    if is_git_repo:
        git_info = (
            ", Git project (.gitignore enabled)"
            if config_params["using_gitignore"]
            else (
                ", Git project (.gitignore disabled by flag)"
                if cli_no_gitignore
                else ", Git project"
            )
        )

    print(
        f"{start_dir.name}/ [{filter_info}, {level_info}{mode_info}{ext_info}{git_info}]"
    )


def print_final_result(counters: Dict[str, int], global_dirs_only: bool) -> None:
    files_count = counters["files"]
    dirs_count = counters["dirs"]

    files_info = (
        "0 files (hidden)"
        if global_dirs_only and files_count == 0
        else f"{files_count} file{'s' if files_count != 1 else ''}"
    )
    dirs_info = f"{dirs_count} director{'ies' if dirs_count != 1 else 'y'}"

    print(f"\n{dirs_info}, {files_info}")


def generate_tree(
    directory: Path,
    start_dir: Path,
    prefix: str = "",
    level: int = 0,
    max_level: Optional[int] = DEFAULT_MAX_LEVEL,
    ignore_spec: Optional["pathspec.PathSpec"] = None,
    submodules: Optional[Set[Path]] = None,
    prune_spec: Optional["pathspec.PathSpec"] = None,
    dirs_only_spec: Optional["pathspec.PathSpec"] = None,
    extensions_filter: Optional[Set[str]] = None,
    is_in_dirs_only_zone: bool = False,
    counters: Optional[Dict[str, int]] = None,
) -> None:
    if submodules is None:
        submodules = set()

    if counters is None:
        counters = {"dirs": 0, "files": 0}

    if max_level is not None and level >= max_level:
        return

    try:
        contents = [
            path for path in directory.iterdir() if not path.name.startswith(".")
        ]
    except (FileNotFoundError, NotADirectoryError):
        return

    def is_ignored(path: Path) -> bool:
        return is_path_matched(path, ignore_spec, start_dir)

    dirs = sorted(
        [d for d in contents if d.is_dir() and not is_ignored(d)],
        key=lambda p: p.name.lower(),
    )

    files: List[Path] = []
    if not is_in_dirs_only_zone:
        files_unfiltered = [f for f in contents if f.is_file() and not is_ignored(f)]

        if extensions_filter is not None:
            files_filtered = []
            for f in files_unfiltered:
                # --- LOGIC CŨ BỊ XÓA ---
                # file_ext = "".join(f.suffixes).lstrip(".")
                # if file_ext in extensions_filter:
                # --- LOGIC MỚI ---
                if is_extension_matched(f, extensions_filter):
                    files_filtered.append(f)
            files = sorted(files_filtered, key=lambda p: p.name.lower())
        else:
            files = sorted(files_unfiltered, key=lambda p: p.name.lower())

    items_to_print = dirs + files
    pointers = ["├── "] * (len(items_to_print) - 1) + ["└── "]

    for pointer, path in zip(pointers, items_to_print):
        if path.is_dir():
            counters["dirs"] += 1
        else:
            counters["files"] += 1

        is_submodule = path.is_dir() and path.resolve() in submodules
        is_pruned = path.is_dir() and is_path_matched(path, prune_spec, start_dir)

        is_dirs_only_entry = (
            path.is_dir()
            and is_path_matched(path, dirs_only_spec, start_dir)
            and not is_in_dirs_only_zone
        )

        line = f"{prefix}{pointer}{path.name}{'/' if path.is_dir() else ''}"

        if is_submodule:
            line += " [submodule]"
        elif is_pruned:
            line += " [...]"
        elif is_dirs_only_entry:
            line += " [dirs only]"

        print(line)

        if path.is_dir() and not is_submodule and not is_pruned:
            extension = "│   " if pointer == "├── " else "    "
            next_is_in_dirs_only_zone = is_in_dirs_only_zone or is_dirs_only_entry

            generate_tree(
                path,
                start_dir,
                prefix + extension,
                level + 1,
                max_level,
                ignore_spec,
                submodules,
                prune_spec,
                dirs_only_spec,
                extensions_filter,
                next_is_in_dirs_only_zone,
                counters,
            )