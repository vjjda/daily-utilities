#!/usr/bin/env python3
# Path: scripts/check_path.py

import sys
import argparse 
import logging
from pathlib import Path
from typing import List, Optional, Set # <-- Thêm Set
import shlex

import typer

# Common utilities
from utils.logging_config import setup_logging, log_success
from utils.core import parse_comma_list, is_git_repository, find_git_root

# Module Imports
from modules.path_checker import (
    process_path_updates,
    handle_results,
    DEFAULT_EXTENSIONS_STRING,
    DEFAULT_IGNORE, # <-- NEW: Import default
    
    PROJECT_CONFIG_FILENAME,
    CONFIG_SECTION_NAME,
    load_config_template,
    generate_dynamic_config,
    overwrite_or_append_project_config_section,
    load_config_files # <-- NEW: Import loader
)

# --- CONSTANTS ---
THIS_SCRIPT_PATH = Path(__file__).resolve()

app = typer.Typer(
    help="Kiểm tra (và tùy chọn sửa) các comment '# Path:' trong file nguồn.",
    add_completion=False,
    context_settings={"help_option_names": ["--help", "-h"]}
)

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context, 
    
    config: Optional[str] = typer.Option(
        None, "-c", "--config",
        help="Khởi tạo hoặc cập nhật file .project.toml (chỉ hỗ trợ scope 'project').",
        case_sensitive=False
    ),

    target_directory_arg: Optional[Path] = typer.Argument( 
        None, 
        help="Thư mục để quét (mặc định: thư mục làm việc hiện tại, tôn trọng .gitignore). Dùng '~' cho thư mục home.",
        file_okay=False,
        dir_okay=True,
    ),
    # --- MODIFIED: Bỏ default, default sẽ được xử lý khi merge ---
    extensions: Optional[str] = typer.Option( None, "-e", "--extensions", help=f"Các đuôi file để quét (ghi đè .project.toml)." ),
    ignore: Optional[str] = typer.Option( None, "-I", "--ignore", help="Danh sách pattern (phân cách bởi dấu phẩy) để bỏ qua (thêm vào .project.toml)." ),
    # --- END MODIFIED ---
    
    dry_run: bool = typer.Option( 
        False, 
        "-d", "--dry-run", 
        help="Chỉ chạy ở chế độ 'dry-run' (chạy thử). Mặc định là chạy 'fix' (có hỏi xác nhận)." 
    )
):
    """ Hàm chính (callback của Typer) """
    if ctx.invoked_subcommand: return
    
    # 1. Setup Logging
    logger = setup_logging(script_name="CPath")
    logger.debug("CPath script started.")

    # (Logic --config giữ nguyên)
    if config:
        # ... (logic xử lý config)
        scope = config.lower()
        if scope != 'project':
            logger.error(f"❌ Lỗi: Scope '{config}' không được hỗ trợ. cpath chỉ hỗ trợ '--config project'.")
            raise typer.Exit(code=1)
            
        config_file_path = Path.cwd() / PROJECT_CONFIG_FILENAME # .project.toml
        
        try:
            template_str = load_config_template()
            content_section_only = generate_dynamic_config(template_str)
            
            overwrite_or_append_project_config_section(
                config_file_path, 
                content_section_only, 
                logger
            )
            
        except (IOError, KeyError) as e:
            logger.error(f"❌ Đã xảy ra lỗi khi thao tác file: {e}")
            raise typer.Exit(code=1)
        
        try:
            logger.info(f"Đang mở '{config_file_path.name}' trong trình soạn thảo mặc định...")
            typer.launch(str(config_file_path))
        except Exception as e:
            logger.error(f"❌ Đã xảy ra lỗi không mong muốn khi mở file: {e}")
            logger.warning(f"⚠️ Không thể tự động mở file. Vui lòng mở thủ công.")
            
        raise typer.Exit(code=0) 

    # (Logic xác định scan_root và kiểm tra Git giữ nguyên)
    if target_directory_arg:
        scan_root = target_directory_arg.expanduser()
    else:
        scan_root = Path.cwd().expanduser() 

    if not scan_root.exists():
        logger.error(f"❌ Lỗi: Thư mục mục tiêu không tồn tại (sau khi expanduser): {scan_root}")
        raise typer.Exit(code=1)
    if not scan_root.is_dir():
        logger.error(f"❌ Lỗi: Đường dẫn mục tiêu không phải là thư mục: {scan_root}")
        raise typer.Exit(code=1)
    
    git_warning_str = ""
    effective_scan_root = scan_root
    # ... (toàn bộ logic R/C/Q và xác nhận y/N giữ nguyên) ...
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

    check_mode = dry_run 

    # --- NEW: Tải và Merge Cấu hình ---
    
    # 1. Tải cấu hình từ file .project.toml
    file_config_data = load_config_files(effective_scan_root, logger)

    # 2. Merge Extensions (CLI > File > Default)
    extensions_str: str
    if extensions: # Ưu tiên 1: CLI
        extensions_str = extensions
    elif 'extensions' in file_config_data: # Ưu tiên 2: File
        extensions_str = file_config_data['extensions']
    else: # Ưu tiên 3: Default
        extensions_str = DEFAULT_EXTENSIONS_STRING
        
    final_extensions_list = [ext.strip() for ext in extensions_str.split(',') if ext.strip()]

    # 3. Merge Ignore (CLI + File + Default)
    cli_ignore_set = parse_comma_list(ignore)
    file_ignore_set = set(file_config_data.get('ignore', [])) # TOML đọc ra list
    
    final_ignore_set = DEFAULT_IGNORE.union(file_ignore_set).union(cli_ignore_set)
    # --- END NEW: Tải và Merge ---


    # Xây dựng lệnh "fix"
    original_args = sys.argv[1:]
    filtered_args = [
        shlex.quote(arg) for arg in original_args 
        if arg not in ('-d', '--dry-run', '--fix', '-c', '--config') 
    ]
    fix_command_str = "cpath " + " ".join(filtered_args)

    try:
        # 3. Run the core logic (Truyền config đã merge)
        files_to_fix = process_path_updates(
            logger=logger, project_root=effective_scan_root,
            target_dir_str=str(target_directory_arg) if effective_scan_root == scan_root and target_directory_arg else None,
            extensions=final_extensions_list, # <-- MODIFIED
            cli_ignore=final_ignore_set, # <-- MODIFIED
            script_file_path=THIS_SCRIPT_PATH, 
            check_mode=check_mode 
        )

        # 4. Handle Results (Không thay đổi)
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
    try: 
        app()
    except KeyboardInterrupt: 
        print("\n\n❌ [Lệnh dừng] Đã dừng kiểm tra đường dẫn."); sys.exit(1)