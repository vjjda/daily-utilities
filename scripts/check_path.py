#!/usr/bin/env python3
# Path: scripts/check_path.py

import sys
import argparse 
import logging
from pathlib import Path
from typing import List, Optional
import shlex

import typer

# Common utilities
from utils.logging_config import setup_logging
from utils.core import parse_comma_list, is_git_repository, find_git_root

# Module Imports
from modules.path_checker import (
    process_path_updates,
    handle_results,
    DEFAULT_EXTENSIONS_STRING
)

# --- CONSTANTS ---
THIS_SCRIPT_PATH = Path(__file__).resolve()


def main(
    target_directory_arg: Optional[Path] = typer.Argument( 
        None, 
        help="Thư mục để quét (mặc định: thư mục làm việc hiện tại, tôn trọng .gitignore). Dùng '~' cho thư mục home.",
        file_okay=False,
        dir_okay=True,
    ),
    extensions: str = typer.Option( DEFAULT_EXTENSIONS_STRING, "-e", "--extensions", help=f"Các đuôi file để quét (mặc định: '{DEFAULT_EXTENSIONS_STRING}')." ),
    ignore: Optional[str] = typer.Option( None, "-I", "--ignore", help="Danh sách pattern (phân cách bởi dấu phẩy) để bỏ qua." ),
    fix: bool = typer.Option( False, "--fix", help="Sửa file tại chỗ. (Mặc định là chế độ 'check'/chạy thử)." )
):
    """ Kiểm tra (và tùy chọn sửa) các comment '# Path:' trong file nguồn. """
    
    # 1. Setup Logging
    logger = setup_logging(script_name="CPath")
    logger.debug("CPath script started.")

    # Xác định thư mục gốc + Mở rộng ~ thủ công
    if target_directory_arg:
        scan_root = target_directory_arg.expanduser()
    else:
        scan_root = Path.cwd().expanduser() 

    # Kiểm tra tồn tại (thủ công)
    if not scan_root.exists():
        logger.error(f"❌ Lỗi: Thư mục mục tiêu không tồn tại (sau khi expanduser): {scan_root}")
        raise typer.Exit(code=1)
    if not scan_root.is_dir():
        logger.error(f"❌ Lỗi: Đường dẫn mục tiêu không phải là thư mục: {scan_root}")
        raise typer.Exit(code=1)
    
    # --- Logic gợi ý Git Root (Đã Việt hóa) ---
    git_warning_str = ""
    effective_scan_root = scan_root
    if not is_git_repository(scan_root):
        suggested_root = find_git_root(scan_root.parent)
        
        if suggested_root:
            logger.warning(f"⚠️ Thư mục hiện tại '{scan_root.name}/' không phải là gốc Git.")
            logger.warning(f"   Đã tìm thấy gốc Git tại: {suggested_root.as_posix()}")
            logger.warning("   Vui lòng chọn một tùy chọn:")
            logger.warning("     [R] Chạy từ Gốc Git (Khuyên dùng)")
            logger.warning(f"     [C] Chạy từ Thư mục Hiện tại ({scan_root.name}/)")
            logger.warning("     [Q] Thoát / Hủy")
            
            choice = ""
            while choice not in ('r', 'c', 'q'):
                try:
                    choice = input("   Nhập lựa chọn của bạn (R/C/Q): ").lower().strip()
                except (EOFError, KeyboardInterrupt):
                    choice = 'q' 
            
            if choice == 'r':
                effective_scan_root = suggested_root
                logger.info(f"✅ Di chuyển quét đến gốc Git: {effective_scan_root.as_posix()}")
            elif choice == 'c':
                effective_scan_root = scan_root
                logger.info(f"✅ Quét từ thư mục hiện tại: {scan_root.as_posix()}")
                git_warning_str = f"⚠️ Cảnh báo: Đang chạy từ thư mục không phải gốc Git ('{scan_root.name}/'). Quy tắc .gitignore có thể không đầy đủ."
            elif choice == 'q':
                logger.error("❌ Hoạt động bị hủy bởi người dùng.")
                raise typer.Exit(code=0)
        else:
            # (Xác nhận an toàn (y/N) khi không tìm thấy .git nào)
            logger.warning(f"⚠️ Không tìm thấy thư mục '.git' trong '{scan_root.name}/' hoặc các thư mục cha.")
            logger.warning(f"   Quét từ một thư mục không phải dự án (như $HOME) có thể chậm hoặc không an toàn.")
            try:
                confirmation = input(f"   Bạn có chắc muốn quét '{scan_root.as_posix()}'? (y/N): ")
            except (EOFError, KeyboardInterrupt):
                confirmation = 'n' 
            
            if confirmation.lower() == 'y':
                logger.info(f"✅ Tiếp tục quét tại thư mục không phải gốc Git: {scan_root.as_posix()}")
                git_warning_str = f"⚠️ Cảnh báo: Đang chạy từ thư mục không phải gốc Git ('{scan_root.name}/'). Quy tắc .gitignore có thể không đầy đủ."
            else:
                logger.error("❌ Hoạt động bị hủy bởi người dùng.")
                raise typer.Exit(code=0) 
    # --- END Logic gợi ý Git Root ---

    check_mode = not fix

    # Xây dựng lệnh "fix"
    original_args = sys.argv[1:]
    filtered_args = [shlex.quote(arg) for arg in original_args if arg not in ('--check', '--fix')]
    filtered_args.append('--fix')
    fix_command_str = "cpath " + " ".join(filtered_args)

    # Chuẩn bị args cho core
    extensions_to_scan = [ext.strip() for ext in extensions.split(',') if ext.strip()]
    cli_ignore_patterns = parse_comma_list(ignore)

    try:
        # 3. Run the core logic
        files_to_fix = process_path_updates(
            logger=logger, project_root=effective_scan_root,
            target_dir_str=str(target_directory_arg) if effective_scan_root == scan_root and target_directory_arg else None,
            extensions=extensions_to_scan, cli_ignore=cli_ignore_patterns,
            script_file_path=THIS_SCRIPT_PATH, check_mode=check_mode
        )

        # 4. Handle Results
        handle_results(
            logger=logger, files_to_fix=files_to_fix, check_mode=check_mode,
            fix_command_str=fix_command_str, scan_root=effective_scan_root, 
            git_warning_str=git_warning_str
        )

    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    try: typer.run(main)
    except KeyboardInterrupt: print("\n\n❌ [Lệnh dừng] Đã dừng kiểm tra đường dẫn."); sys.exit(1)