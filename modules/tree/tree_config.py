#!/usr/bin/env python3
# Path: modules/tree/tree_config.py

import configparser
import logging
from pathlib import Path
from typing import Set, Dict, Any, Optional
import argparse

# Import các hằng số và hàm tiện ích từ file core
from .tree_core import (
    get_submodule_paths, parse_comma_list,
    DEFAULT_IGNORE, DEFAULT_PRUNE, DEFAULT_DIRS_ONLY,
    DEFAULT_MAX_LEVEL, CONFIG_FILENAME, PROJECT_CONFIG_FILENAME,
    CONFIG_SECTION_NAME
)

def load_and_merge_config(
    args: argparse.Namespace, 
    start_dir: Path, 
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Tải cấu hình từ file .ini và hợp nhất chúng với các đối số CLI.
    Thứ tự ưu tiên: CLI > .tree.ini > .project.ini > Mặc định.
    """
    
    # 1. Đọc Cấu hình từ File (.tree.ini Tối ưu > .project.ini Fallback)
    config = configparser.ConfigParser()
    
    tree_config_path = start_dir / CONFIG_FILENAME
    project_config_path = start_dir / PROJECT_CONFIG_FILENAME

    files_to_read = []
    if project_config_path.exists():
        files_to_read.append(project_config_path)
    if tree_config_path.exists():
        files_to_read.append(tree_config_path)

    if files_to_read:
        try:
            config.read(files_to_read) 
            logger.debug(f"Đã tải cấu hình từ các file: {[p.name for p in files_to_read]}")
        except Exception as e:
            logger.warning(logger, f"⚠️ Could not read config files: {e}")
    else:
        logger.debug("Không tìm thấy file cấu hình .tree.ini hoặc .project.ini. Sử dụng mặc định.")

    # Đảm bảo section [tree] tồn tại
    if CONFIG_SECTION_NAME not in config:
        config.add_section(CONFIG_SECTION_NAME)
        logger.debug(f"Đã thêm section '{CONFIG_SECTION_NAME}' trống để xử lý fallback an toàn.")

    # 2. Hợp nhất Cấu hình (CLI > File > Mặc định)
    
    # Mức sâu (Level)
    level_from_config_file = config.getint(CONFIG_SECTION_NAME, 'level', fallback=DEFAULT_MAX_LEVEL)
    final_level = args.level if args.level is not None else level_from_config_file
    
    # Submodules
    show_submodules = args.show_submodules if args.show_submodules is not None else \
                      config.getboolean(CONFIG_SECTION_NAME, 'show-submodules', fallback=False)

    # Ignore List
    ignore_cli = parse_comma_list(args.ignore)
    ignore_file = parse_comma_list(config.get(CONFIG_SECTION_NAME, 'ignore', fallback=None))
    final_ignore_list = DEFAULT_IGNORE.union(ignore_file).union(ignore_cli)

    # Prune List
    prune_cli = parse_comma_list(args.prune) 
    prune_file = parse_comma_list(config.get(CONFIG_SECTION_NAME, 'prune', fallback=None))
    final_prune_list = DEFAULT_PRUNE.union(prune_file).union(prune_cli)

    # Dirs Only List
    dirs_only_cli = args.dirs_only
    dirs_only_file = config.get(CONFIG_SECTION_NAME, 'dirs-only', fallback=None)
    final_dirs_only_mode = dirs_only_cli if dirs_only_cli is not None else dirs_only_file
    
    global_dirs_only = final_dirs_only_mode == '_ALL_'
    dirs_only_list_custom = set()
    if final_dirs_only_mode is not None and not global_dirs_only:
        dirs_only_list_custom = parse_comma_list(final_dirs_only_mode)
    final_dirs_only_list = DEFAULT_DIRS_ONLY.union(dirs_only_list_custom)
    
    # Tính toán Submodule Names
    submodule_names: Set[str] = set()
    if not show_submodules: 
        submodule_paths = get_submodule_paths(start_dir, logger=logger)
        submodule_names = submodule_paths

    # 3. Trả về một dict chứa các cài đặt đã được xử lý
    return {
        "max_level": final_level,
        "ignore_list": final_ignore_list,
        "submodules": submodule_names,
        "prune_list": final_prune_list,
        "dirs_only_list": final_dirs_only_list,
        "is_in_dirs_only_zone": global_dirs_only,
        # Thêm các thông tin khác để in ra cho người dùng
        "global_dirs_only_flag": global_dirs_only,
        "filter_lists": {
            "ignore": final_ignore_list,
            "prune": final_prune_list,
            "dirs_only": final_dirs_only_list,
            "submodules": submodule_names
        }
    }