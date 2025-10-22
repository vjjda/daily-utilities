#!/usr/bin/env python3
# Path: scripts/tree.py

import sys
import argparse
from pathlib import Path

# Các tiện ích chung
from utils.logging_config import setup_logging, log_success
from utils.core import run_command 

# --- THAY ĐỔI IMPORT ---
# Chỉ import các thành phần cần thiết cho script điều phối
from modules.tree.tree_core import (
    generate_tree, CONFIG_FILENAME, CONFIG_TEMPLATE
)
# Import module xử lý config mới
from modules.tree.tree_config import load_and_merge_config
# ---------------------

def handle_init_command(logger: logging.Logger) -> None:
    """Xử lý logic cho cờ --init."""
    config_file_path = Path.cwd() / CONFIG_FILENAME
    file_existed = config_file_path.exists()
    
    should_write = False
    
    if file_existed:
        overwrite = input(f"'{CONFIG_FILENAME}' already exists. Overwrite? (y/n): ").lower() 
        if overwrite == 'y':
            should_write = True
            logger.debug(f"User chose to overwrite '{CONFIG_FILENAME}'.")
        else:
            logger.info(f"Skipped overwrite for existing '{CONFIG_FILENAME}'.")
    else:
        should_write = True
        logger.debug(f"Creating new '{CONFIG_FILENAME}'.")

    if should_write:
        try:
            with open(config_file_path, 'w', encoding='utf-8') as f:
                f.write(CONFIG_TEMPLATE)
            
            log_msg = f"Successfully created '{CONFIG_FILENAME}'."
            if file_existed:
                log_msg = f"Successfully overwrote '{CONFIG_FILENAME}'."
            log_success(logger, log_msg)
            
        except IOError as e:
            logger.error(f"❌ Failed to write file '{config_file_path}': {e}")
            return # Không thử mở nếu ghi lỗi
    
    # Mở file
    try:
        logger.info(f"Opening '{config_file_path.name}' in default editor...")
        success, output = run_command(
            ["open", str(config_file_path)], 
            logger, 
            description=f"Mở file {CONFIG_FILENAME}"
        )
        if not success:
            logger.warning(f"⚠️ Could not automatically open file. Please open it manually.")
            logger.debug(f"Lỗi khi mở file: {output}")
            
    except Exception as e:
        logger.error(f"❌ An unexpected error occurred while trying to open the file: {e}")

def main():
    """Hàm main điều phối: Phân tích đối số, gọi xử lý config và chạy hàm tree."""
    
    parser = argparse.ArgumentParser(description="A smart directory tree generator with support for a .treeconfig.ini file.")
    parser.add_argument("start_path", nargs='?', 
                        default=".", help="Starting path (file or directory).") 
    parser.add_argument("-L", "--level", type=int, help="Limit the display depth.")
    parser.add_argument("-I", "--ignore", type=str, help="Comma-separated list of patterns to ignore.")
    parser.add_argument("-P", "--prune", type=str, help="Comma-separated list of patterns to prune.")
    parser.add_argument("-d", "--dirs-only", nargs='?', const='_ALL_', default=None, type=str, help="Show directories only.")
    parser.add_argument("-s", "--show-submodules", action='store_true', default=None, help="Show the contents of submodules.")
    parser.add_argument("--init", action='store_true', help="Create a sample .treeconfig.ini file and open it.")
    args = parser.parse_args()

    # 1. Cấu hình Logging
    logger = setup_logging(script_name="CTree")
    logger.debug(f"Đã nhận đường dẫn khởi động: {args.start_path}")
    
    # 2. Xử lý cờ --init (Tách ra hàm riêng)
    if args.init: 
        handle_init_command(logger)
        return # Kết thúc sau khi --init

    # 3. Xử lý Đường dẫn Khởi động
    initial_path = Path(args.start_path).resolve() 
    if not initial_path.exists():
        logger.error(f"❌ Path does not exist: '{args.start_path}'")
        return
    start_dir = initial_path.parent if initial_path.is_file() else initial_path

    # 4. Tải và Hợp nhất Cấu hình (Đã tách ra module riêng)
    try:
        config_params = load_and_merge_config(args, start_dir, logger)
    except Exception as e:
        logger.error(f"❌ Lỗi nghiêm trọng khi xử lý cấu hình: {e}")
        logger.debug("Traceback:", exc_info=True)
        return

    # 5. Thông báo Trạng thái
    is_truly_full_view = not any(config_params["filter_lists"].values())
    filter_info = "Full view" if is_truly_full_view else "Filtered view"
    
    level_info = "full depth" if config_params["max_level"] is None else \
                 f"depth limit: {config_params['max_level']}"
    mode_info = ", directories only" if config_params["global_dirs_only_flag"] else ""
    
    print(f"{start_dir.name}/ [{filter_info}, {level_info}{mode_info}]")

    # 6. Chạy Logic Đệ quy
    counters = {'dirs': 0, 'files': 0}
    
    # Sử dụng dict config đã xử lý để truyền tham số
    generate_tree(
        start_dir, 
        start_dir, 
        counters=counters,
        max_level=config_params["max_level"],
        ignore_list=config_params["ignore_list"],
        submodules=config_params["submodules"],
        prune_list=config_params["prune_list"],
        dirs_only_list=config_params["dirs_only_list"],
        is_in_dirs_only_zone=config_params["is_in_dirs_only_zone"]
    )

    # 7. Kết quả cuối cùng
    files_info = "0 files (hidden)" if config_params["global_dirs_only_flag"] and counters['files'] == 0 else \
                 f"{counters['files']} files" 
    print(f"\n{counters['dirs']} directories, {files_info}")
    
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ [Stop Command] Stop generating tree.")
        sys.exit(1)