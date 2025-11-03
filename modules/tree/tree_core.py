# Path: modules/tree/tree_core.py
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional
import sys

from utils.core import is_git_repository

from .tree_internal import (
    load_config_files,
    merge_config_sources,
)

from .tree_executor import (
    generate_tree,
    print_status_header,
    print_final_result,
)


__all__ = ["process_tree_logic", "orchestrate_tree"]


def orchestrate_tree(logger: logging.Logger, cli_args: argparse.Namespace) -> None:
    start_path_obj = Path(cli_args.start_path).expanduser()
    if not start_path_obj.exists():
        logger.error(f"❌ Lỗi: Đường dẫn bắt đầu không tồn tại: {start_path_obj}")
        sys.exit(1)

    try:
        result_data = process_tree_logic(
            logger=logger, cli_args=cli_args, start_path_obj=start_path_obj
        )

        if result_data is None:
            sys.exit(1)

        config_params = result_data["config_params"]
        start_dir = result_data["start_dir"]
        is_git_repo = result_data["is_git_repo"]
        cli_no_gitignore = result_data["cli_no_gitignore"]

        print_status_header(
            config_params=config_params,
            start_dir=start_dir,
            is_git_repo=is_git_repo,
            cli_no_gitignore=cli_no_gitignore,
        )

        counters = {"dirs": 0, "files": 0}

        generate_tree(
            start_dir,
            start_dir,
            counters=counters,
            max_level=config_params["max_level"],
            ignore_spec=config_params["ignore_spec"],
            submodules=config_params["submodules"],
            prune_spec=config_params["prune_spec"],
            dirs_only_spec=config_params["dirs_only_spec"],
            extensions_filter=config_params["extensions_filter"],
            is_in_dirs_only_zone=config_params["is_in_dirs_only_zone"],
        )

        print_final_result(
            counters=counters, global_dirs_only=config_params["global_dirs_only_flag"]
        )

    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn trong 'orchestrate_tree': {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)


def process_tree_logic(
    logger: logging.Logger, cli_args: argparse.Namespace, start_path_obj: Path
) -> Optional[Dict[str, Any]]:

    initial_path: Path = start_path_obj
    start_dir = initial_path.parent if initial_path.is_file() else initial_path
    is_git_repo = is_git_repository(start_dir)

    try:

        file_config = load_config_files(start_dir, logger)

        cli_dirs_only: Optional[str] = None
        if getattr(cli_args, "all_dirs", False):
            cli_dirs_only = "_ALL_"
        elif getattr(cli_args, "dirs_patterns", None):
            cli_dirs_only = cli_args.dirs_patterns

        merge_cli_args = argparse.Namespace(
            level=getattr(cli_args, "level", None),
            extensions=getattr(cli_args, "extensions", None),
            ignore=getattr(cli_args, "ignore", None),
            prune=getattr(cli_args, "prune", None),
            dirs_only=cli_dirs_only,
            show_submodules=getattr(cli_args, "show_submodules", False),
            no_gitignore=getattr(cli_args, "no_gitignore", False),
            full_view=getattr(cli_args, "full_view", False),
        )

        config_params = merge_config_sources(
            args=merge_cli_args,
            file_config=file_config,
            start_dir=start_dir,
            logger=logger,
            is_git_repo=is_git_repo,
        )

        return {
            "config_params": config_params,
            "start_dir": start_dir,
            "is_git_repo": is_git_repo,
            "cli_no_gitignore": getattr(cli_args, "no_gitignore", False),
        }

    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn trong core logic: {e}")
        logger.debug("Traceback:", exc_info=True)
        return None
