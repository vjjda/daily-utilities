# Path: modules/tree/tree_core.py
"""
Core Orchestration logic for the Tree (ctree) module.
(Internal module, imported by tree gateway)
"""

import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Import utils
from utils.core import is_git_repository

# Import module components
from .tree_loader import load_config_files
from .tree_merger import merge_config_sources

__all__ = ["process_tree_logic"]


def process_tree_logic(
    logger: logging.Logger,
    cli_args: argparse.Namespace,
    start_path_obj: Path
) -> Optional[Dict[str, Any]]:
    """
    Điều phối logic chính của ctree (tải, merge, chuẩn bị).
    Trả về một dict "Result Object" chứa các tham số đã xử lý cho Executor.
    (Logic này được chuyển từ scripts/tree.py)
    """
    
    # 1. Xác định đường dẫn và trạng thái Git
    initial_path: Path = start_path_obj
    start_dir = initial_path.parent if initial_path.is_file() else initial_path
    is_git_repo = is_git_repository(start_dir)

    try:
        # 2. Tải Config
        file_config = load_config_files(start_dir, logger)

        # 3. Chuẩn bị CLI args (Namespace đã có sẵn từ entrypoint)
        # Cần chuẩn bị `dirs_only` từ hai cờ `all_dirs` và `dirs_patterns`
        cli_dirs_only: Optional[str] = None
        if getattr(cli_args, 'all_dirs', False):
            cli_dirs_only = "_ALL_"
        elif getattr(cli_args, 'dirs_patterns', None):
            cli_dirs_only = cli_args.dirs_patterns
        
        # Tạo một Namespace con chỉ chứa các cờ mà merge_config_sources cần
        # để giữ cho hàm merge_config_sources không thay đổi
        merge_cli_args = argparse.Namespace(
            level=getattr(cli_args, 'level', None),
            extensions=getattr(cli_args, 'extensions', None),
            ignore=getattr(cli_args, 'ignore', None),
            prune=getattr(cli_args, 'prune', None),
            dirs_only=cli_dirs_only,
            show_submodules=getattr(cli_args, 'show_submodules', False),
            no_gitignore=getattr(cli_args, 'no_gitignore', False),
            full_view=getattr(cli_args, 'full_view', False),
        )

        # 4. Hợp nhất Config
        config_params = merge_config_sources(
            args=merge_cli_args,
            file_config=file_config,
            start_dir=start_dir,
            logger=logger,
            is_git_repo=is_git_repo
        )
        
        # 5. Trả về Result Object cho Executor
        return {
            "config_params": config_params,
            "start_dir": start_dir,
            "is_git_repo": is_git_repo,
            "cli_no_gitignore": getattr(cli_args, 'no_gitignore', False)
        }

    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn trong core logic: {e}")
        logger.debug("Traceback:", exc_info=True)
        return None