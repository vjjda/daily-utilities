#!/usr/bin/env python3
# Path: scripts/tree.py


import sys
import argparse
import configparser
from pathlib import Path
# Bổ sung import các kiểu dữ liệu cần thiết
from utils.logging_config import setup_logging, log_success
from typing import Set 

# ----------------------------------------------------------------------

# --- THAY ĐỔI IMPORT ---
# Import các tiện ích từ module 'modules.tree' thay vì 'utils'
from modules.tree.core import (
    generate_tree, get_submodule_paths, parse_comma_list, 
    CONFIG_TEMPLATE, DEFAULT_IGNORE, DEFAULT_PRUNE, DEFAULT_DIRS_ONLY,
    DEFAULT_MAX_LEVEL, CONFIG_FILENAME, PROJECT_CONFIG_FILENAME, CONFIG_SECTION_NAME
)
# ---------------------

def main():
    """Main function to handle arguments, configuration, and run the tree generator."""
    
    parser = argparse.ArgumentParser(description="A smart directory tree generator with support for a .treeconfig.ini file.")
    parser.add_argument("start_path", nargs='?', 
                        default=".", help="Starting path (file or directory).") 
    parser.add_argument("-L", "--level", type=int, help="Limit the display depth.")
    parser.add_argument("-I", "--ignore", type=str, help="Comma-separated list of patterns to ignore.")
    parser.add_argument("-P", "--prune", type=str, help="Comma-separated list of patterns to prune.")
    parser.add_argument("-d", "--dirs-only", nargs='?', const='_ALL_', default=None, type=str, help="Show directories only.")
    parser.add_argument("-s", "--show-submodules", action='store_true', default=None, help="Show the contents of submodules.")
    parser.add_argument("--init", action='store_true', help="Create a sample .treeconfig.ini file and exit.")
    args = parser.parse_args()

    # 1. Cấu hình Logging
    logger = setup_logging(script_name="CTree")
    
    # Ghi log DEBUG về đường dẫn khởi động
    logger.debug(f"Đã nhận đường dẫn khởi động: {args.start_path}")
    
    # 2. Xử lý cờ --init
    if args.init: 
        # Sử dụng CONFIG_FILENAME đã import
        config_file_path = Path.cwd() / CONFIG_FILENAME 
        if config_file_path.exists():
            overwrite = input(f"'{CONFIG_FILENAME}' already exists. Overwrite? (y/n): ").lower() 
            if overwrite != 'y':
                logger.info("Operation cancelled.")
                return
        with open(config_file_path, 'w', encoding='utf-8') as f:
            f.write(CONFIG_TEMPLATE)
        log_success(logger, f"Successfully created '{CONFIG_FILENAME}'.")
        return

    # 3. Xử lý Đường dẫn Khởi động
    initial_path = Path(args.start_path).resolve() 
    if not initial_path.exists():
        # --- THAY ĐỔI LOGGING ---
        # Thêm emoji cảnh báo cho lỗi người dùng
        logger.error(f"❌ Path does not exist: '{args.start_path}'")
        # -------------------------
        return
    start_dir = initial_path.parent if initial_path.is_file() else initial_path

    # 4. Đọc Cấu hình từ File (.tree.ini Tối ưu > .project.ini Fallback)
    
    # configparser sẽ được dùng để đọc cả hai file
    config = configparser.ConfigParser()
    
    # 4.1. Đường dẫn file cấu hình của script (Ưu tiên cao)
    tree_config_path = start_dir / CONFIG_FILENAME
    
    # 4.2. Đường dẫn file cấu hình dự án (Fallback)
    project_config_path = start_dir / PROJECT_CONFIG_FILENAME

    files_to_read = []
    
    # Đọc file cấu hình dự án (Fallback) trước, để các giá trị của nó
    # có thể bị ghi đè bởi file cấu hình riêng (tree) sau
    if project_config_path.exists():
        files_to_read.append(project_config_path)
    
    # Đọc file cấu hình riêng (Ưu tiên)
    if tree_config_path.exists():
        files_to_read.append(tree_config_path)

    if files_to_read:
        try:
            # configparser.read() đọc danh sách file theo thứ tự. 
            # Các giá trị trong file sau sẽ ghi đè các giá trị trong file trước.
            config.read(files_to_read) 
            logger.debug(f"Đã tải cấu hình từ các file: {[p.name for p in files_to_read]}")
        except Exception as e:
            # --- THAY ĐỔI LOGGING ---
            # Thêm emoji cảnh báo
            logger.warning(logger, f"⚠️ Could not read config files: {e}")
            # -------------------------
    else:
        logger.debug("Không tìm thấy file cấu hình .tree.ini hoặc .project.ini. Sử dụng mặc định.")


    # Đảm bảo section [tree] tồn tại để config.get() không bị lỗi KeyError
    if CONFIG_SECTION_NAME not in config:
        config.add_section(CONFIG_SECTION_NAME)
        logger.debug(f"Đã thêm section '{CONFIG_SECTION_NAME}' trống để xử lý fallback an toàn.")

    # 5. Hợp nhất Cấu hình (CLI > File > Mặc định)
    
    # Mức sâu (Level)
    level_from_config_file = config.getint('tree', 'level', fallback=DEFAULT_MAX_LEVEL)
    level = args.level if args.level is not None else level_from_config_file
    # Submodules
    show_submodules = args.show_submodules if args.show_submodules is not None else config.getboolean('tree', 'show-submodules', fallback=False)

    # Ignore List
    ignore_cli = parse_comma_list(args.ignore)
    ignore_file = parse_comma_list(config.get('tree', 'ignore', fallback=None))
    final_ignore_list = DEFAULT_IGNORE.union(ignore_file).union(ignore_cli)

    # Prune List
    prune_cli = parse_comma_list(args.prune) 
    prune_file = parse_comma_list(config.get('tree', 'prune', fallback=None))
    final_prune_list = DEFAULT_PRUNE.union(prune_file).union(prune_cli)

    # Dirs Only List
    dirs_only_cli = args.dirs_only
    dirs_only_file = config.get('tree', 'dirs-only', fallback=None)
    final_dirs_only = dirs_only_cli if dirs_only_cli is not None else dirs_only_file
    
    global_dirs_only = final_dirs_only == '_ALL_'
    dirs_only_list_custom = set()
    if final_dirs_only is not None and not global_dirs_only:
        dirs_only_list_custom = parse_comma_list(final_dirs_only)
    final_dirs_only_list = DEFAULT_DIRS_ONLY.union(dirs_only_list_custom)
    
    submodule_names: Set[str] = set()
    if not show_submodules: 
        # --- THAY ĐỔI LOGIC ---
        # Truyền logger vào hàm
        submodule_paths = get_submodule_paths(start_dir, logger=logger)
        # ---------------------
        submodule_names = submodule_paths


    # 6. Thông báo Trạng thái (Sử dụng logger.info)
    is_truly_full_view = not final_ignore_list and not final_prune_list and not final_dirs_only_list and not global_dirs_only and not submodule_names
    filter_info = "Full view" if is_truly_full_view else "Filtered view"
    
    level_info = "full depth" if level is None else f"depth limit: {level}"
    mode_info = ", directories only" if global_dirs_only else ""
    
    # Ghi lại thông tin tổng quan vào file log
    print(f"{start_dir.name}/ [{filter_info}, {level_info}{mode_info}]")

    # 7. Chạy Logic Đệ quy
    counters = {'dirs': 0, 'files': 0}
    generate_tree(
        start_dir, start_dir, max_level=level, 
        ignore_list=final_ignore_list, submodules=submodule_names, 
        prune_list=final_prune_list, dirs_only_list=final_dirs_only_list, 
        is_in_dirs_only_zone=global_dirs_only, counters=counters
    )

    # 8. Kết quả cuối cùng
    files_info = "0 files (hidden)" if global_dirs_only and counters['files'] == 0 else f"{counters['files']} files" 
    print(f"\n{counters['dirs']} directories, {files_info}")
    
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Thêm print() trực tiếp vì tại đây logger chưa chắc đã được khởi tạo.
        # Hoặc ta chỉ in ra một thông báo đơn giản.
        print("\n\n❌ [Stop Command] Stop generating tree.")
        sys.exit(1) # Thoát với mã lỗi 1 để báo hiệu ngắt lệnh