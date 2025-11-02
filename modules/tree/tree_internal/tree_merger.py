# Path: modules/tree/tree_internal/tree_merger.py
from pathlib import Path
import logging
import argparse
from typing import Set, Optional, Dict, Any, TYPE_CHECKING, List, Iterable, Tuple, Final

try:
    import pathspec
except ImportError:
    pathspec = None

if TYPE_CHECKING:
    import pathspec

from utils.core import (
    get_submodule_paths,
    parse_gitignore,
    resolve_config_value,
    resolve_config_list,
    compile_spec_from_patterns,
    parse_comma_list,
    resolve_set_modification,
)

from ..tree_config import (
    DEFAULT_IGNORE,
    DEFAULT_PRUNE,
    DEFAULT_DIRS_ONLY_LOGIC,
    DEFAULT_MAX_LEVEL,
    FALLBACK_SHOW_SUBMODULES,
    FALLBACK_USE_GITIGNORE,
    DEFAULT_EXTENSIONS,
)

__all__ = ["merge_config_sources"]


def _resolve_simple_flags(
    args: argparse.Namespace, file_config: Dict[str, Any]
) -> Dict[str, Any]:
    final_level = resolve_config_value(
        cli_value=args.level,
        file_value=file_config.get("level"),
        default_value=DEFAULT_MAX_LEVEL,
    )

    cli_show_submodules_val = args.show_submodules if args.show_submodules else None
    file_show_submodules_val = file_config.get("show-submodules")
    show_submodules = resolve_config_value(
        cli_value=cli_show_submodules_val,
        file_value=file_show_submodules_val,
        default_value=FALLBACK_SHOW_SUBMODULES,
    )

    cli_use_gitignore_val = False if args.no_gitignore else None
    file_use_gitignore_val = file_config.get("use-gitignore")
    final_use_gitignore = resolve_config_value(
        cli_value=cli_use_gitignore_val,
        file_value=file_use_gitignore_val,
        default_value=FALLBACK_USE_GITIGNORE,
    )

    return {
        "max_level": final_level,
        "show_submodules": show_submodules,
        "use_gitignore": final_use_gitignore,
    }


def _resolve_filter_list(
    cli_str_value: Optional[str],
    file_list_value: Optional[List[str]],
    default_set_value: Set[str],
) -> List[str]:
    return resolve_config_list(
        cli_str_value=cli_str_value,
        file_list_value=file_list_value,
        default_set_value=default_set_value,
    )


def _resolve_dirs_only(
    args: argparse.Namespace, file_config: Dict[str, Any]
) -> Tuple[Set[str], bool]:
    dirs_only_cli = args.dirs_only
    dirs_only_file = file_config.get("dirs-only", None)

    final_dirs_only_mode = (
        dirs_only_cli if dirs_only_cli is not None else dirs_only_file
    )

    global_dirs_only = final_dirs_only_mode == "_ALL_"
    dirs_only_list_custom: Set[str] = set()

    if isinstance(final_dirs_only_mode, list):
        dirs_only_list_custom = set(final_dirs_only_mode)
    elif final_dirs_only_mode is not None and not global_dirs_only:
        dirs_only_list_custom = parse_comma_list(final_dirs_only_mode)

    final_dirs_only_set = DEFAULT_DIRS_ONLY_LOGIC.union(dirs_only_list_custom)
    return final_dirs_only_set, global_dirs_only


def _resolve_extensions(
    logger: logging.Logger, args: argparse.Namespace, file_config: Dict[str, Any]
) -> Optional[Set[str]]:
    cli_ext_str = args.extensions
    file_ext_list: Optional[List[str]] = file_config.get("extensions")

    tentative_extensions: Optional[Set[str]]
    if file_ext_list is not None:
        tentative_extensions = set(file_ext_list)
        logger.debug("Sử dụng danh sách 'extensions' từ file config làm cơ sở.")
    else:
        tentative_extensions = DEFAULT_EXTENSIONS
        logger.debug("Sử dụng danh sách 'extensions' mặc định (None) làm cơ sở.")

    extensions_filter: Optional[Set[str]]
    if cli_ext_str is None and tentative_extensions is None:
        extensions_filter = None
        logger.debug("Không áp dụng bộ lọc 'extensions'.")
    else:
        base_set = tentative_extensions if tentative_extensions is not None else set()
        extensions_filter = resolve_set_modification(
            tentative_set=base_set, cli_string=cli_ext_str
        )
        if cli_ext_str:
            logger.debug(
                f"Đã áp dụng logic 'extensions' CLI: '{cli_ext_str}'. Set cuối cùng: {extensions_filter}"
            )
        else:
            logger.debug(
                f"Set 'extensions' cuối cùng (từ config/default): {extensions_filter}"
            )
    return extensions_filter


def _compile_specs(
    start_dir: Path,
    ignore_list: List[str],
    prune_list: List[str],
    dirs_only_set: Set[str],
    gitignore_patterns: List[str],
) -> Dict[str, Optional["pathspec.PathSpec"]]:
    all_ignore_patterns_list: List[str] = ignore_list + gitignore_patterns
    all_prune_patterns_list: List[str] = prune_list
    all_dirs_only_patterns_list: List[str] = sorted(list(dirs_only_set))

    return {
        "ignore_spec": compile_spec_from_patterns(all_ignore_patterns_list, start_dir),
        "prune_spec": compile_spec_from_patterns(all_prune_patterns_list, start_dir),
        "dirs_only_spec": compile_spec_from_patterns(
            all_dirs_only_patterns_list, start_dir
        ),
    }


def _get_submodule_info(
    start_dir: Path, show_submodules: bool, logger: logging.Logger
) -> Tuple[Set[Path], Set[str]]:
    submodule_paths: Set[Path] = set()
    submodule_names: Set[str] = set()
    if not show_submodules:
        submodule_paths = get_submodule_paths(start_dir, logger=logger)
        submodule_names = {p.name for p in submodule_paths}
    return submodule_paths, submodule_names


def merge_config_sources(
    args: argparse.Namespace,
    file_config: Dict[str, Any],
    start_dir: Path,
    logger: logging.Logger,
    is_git_repo: bool,
) -> Dict[str, Any]:
    if args.full_view:
        logger.info("⚡ Chế độ xem đầy đủ. Bỏ qua mọi bộ lọc và giới hạn.")
        return {
            "max_level": None,
            "ignore_spec": None,
            "submodules": set(),
            "prune_spec": None,
            "dirs_only_spec": None,
            "extensions_filter": None,
            "is_in_dirs_only_zone": False,
            "global_dirs_only_flag": False,
            "using_gitignore": False,
            "filter_lists": {
                "ignore": set(),
                "prune": set(),
                "dirs_only": set(),
                "submodules": set(),
                "extensions": set(),
            },
        }

    simple_flags = _resolve_simple_flags(args, file_config)
    final_level = simple_flags["max_level"]
    show_submodules = simple_flags["show_submodules"]
    final_use_gitignore = simple_flags["use_gitignore"]

    gitignore_patterns: List[str] = []
    if is_git_repo and final_use_gitignore:
        logger.debug("Phát hiện kho Git. Đang tải patterns .gitignore.")
        gitignore_patterns = parse_gitignore(start_dir)
    elif is_git_repo and not final_use_gitignore:
        logger.debug(
            "Phát hiện kho Git, nhưng bỏ qua .gitignore (do cờ hoặc cấu hình)."
        )
    else:
        logger.debug("Không phải kho Git. Bỏ qua .gitignore.")

    final_ignore_list = _resolve_filter_list(
        args.ignore, file_config.get("ignore"), DEFAULT_IGNORE
    )
    final_prune_list = _resolve_filter_list(
        args.prune, file_config.get("prune"), DEFAULT_PRUNE
    )
    final_dirs_only_set, global_dirs_only_flag = _resolve_dirs_only(args, file_config)
    final_extensions_filter = _resolve_extensions(logger, args, file_config)

    specs = _compile_specs(
        start_dir,
        final_ignore_list,
        final_prune_list,
        final_dirs_only_set,
        gitignore_patterns,
    )

    submodule_paths, submodule_names = _get_submodule_info(
        start_dir, show_submodules, logger
    )

    return {
        "max_level": final_level,
        "ignore_spec": specs["ignore_spec"],
        "prune_spec": specs["prune_spec"],
        "dirs_only_spec": specs["dirs_only_spec"],
        "extensions_filter": final_extensions_filter,
        "submodules": submodule_paths,
        "is_in_dirs_only_zone": global_dirs_only_flag,
        "using_gitignore": is_git_repo
        and final_use_gitignore
        and (len(gitignore_patterns) > 0),
        "global_dirs_only_flag": global_dirs_only_flag,
        "filter_lists": {
            "ignore": set(final_ignore_list),
            "prune": set(final_prune_list),
            "dirs_only": final_dirs_only_set,
            "submodules": submodule_names,
            "extensions": (
                final_extensions_filter
                if final_extensions_filter is not None
                else set()
            ),
        },
    }
