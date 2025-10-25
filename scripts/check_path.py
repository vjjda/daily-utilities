#!/usr/bin/env python3
# Path: scripts/check_path.py

import sys
import argparse
import logging
from pathlib import Path
from typing import List, Optional, Set, Dict, Any
import shlex

try:
    import tomllib 
except ImportError:
    try:
        import toml as tomllib
    except ImportError:
        tomllib = None

import typer

# Common utilities
from utils.logging_config import setup_logging, log_success
from utils.core import (
    parse_comma_list, is_git_repository, find_git_root,
    load_config_template, 
    format_value_to_toml,
    load_project_config_section, 
    load_toml_file,
    write_toml_file
)
# --- MODIFIED: Thêm import utils.cli ---
from utils.cli import prompt_config_overwrite, launch_editor
# --- END MODIFIED ---

# Module Imports
from modules.path_checker import (
    process_path_updates,
    handle_results,
    DEFAULT_EXTENSIONS_STRING,
    DEFAULT_IGNORE,
    PROJECT_CONFIG_FILENAME, 
    CONFIG_SECTION_NAME,
)

# --- CONSTANTS ---
THIS_SCRIPT_PATH = Path(__file__).resolve()
MODULE_DIR = THIS_SCRIPT_PATH.parent.parent / "modules" / "path_checker" 
TEMPLATE_FILENAME = "cpath.toml.template" 

app = typer.Typer(
    help="Kiểm tra (và tùy chọn sửa) các comment '# Path:' trong file nguồn.",
    add_completion=False,
    rich_markup_mode=None, 
    context_settings={"help_option_names": ["--help", "-h"]}
)

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    # (Các tham số Typer giữ nguyên)
    config_project: bool = typer.Option(
        False, "-c", "--config",
        help="Khởi tạo/cập nhật section [cpath] trong .project.toml. (Tương đương --config project)",
    ),
    target_directory_arg: Optional[Path] = typer.Argument(
        None,
        help="Thư mục để quét (mặc định: thư mục làm việc hiện tại, tôn trọng .gitignore). Dùng '~' cho thư mục home.",
        file_okay=False,
        dir_okay=True,
    ),
    extensions: Optional[str] = typer.Option( None, "-e", "--extensions", help=f"Các đuôi file để quét (ghi đè .project.toml)." ),
    ignore: Optional[str] = typer.Option( None, "-I", "--ignore", help="Danh sách pattern (phân cách bởi dấu phẩy) để bỏ qua (thêm vào .project.toml)." ),
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

    # --- Logic cho cờ --config (ĐÃ REFACTOR VỚI O/R/Q) ---
    if config_project: 
        
        if tomllib is None:
             logger.error("❌ Thiếu thư viện 'tomli'. Vui lòng cài đặt: 'pip install tomli tomli-w'")
             raise typer.Exit(code=1)
             
        scope = 'project' 
        config_file_path = Path.cwd() / PROJECT_CONFIG_FILENAME
        
        try:
            # (Logic tạo 'new_section_dict' giữ nguyên)
            template_str = load_config_template(MODULE_DIR, TEMPLATE_FILENAME, logger)
            cpath_defaults = {
                "extensions": DEFAULT_EXTENSIONS_STRING,
                "ignore": DEFAULT_IGNORE
            }
            format_dict: Dict[str, str] = {}
            for key, value in cpath_defaults.items():
                format_dict[f"toml_{key}"] = format_value_to_toml(value)
            content_section_only = template_str.format(**format_dict)
            full_toml_string = f"[{CONFIG_SECTION_NAME}]\n{content_section_only}"
            new_section_dict = tomllib.loads(full_toml_string).get(CONFIG_SECTION_NAME, {})
            if not new_section_dict:
                    raise ValueError("Nội dung section mới bị rỗng.")
            
            config_data = load_toml_file(config_file_path, logger)
            
            should_write = True
            
            # --- MODIFIED: Sử dụng helper O/R/Q ---
            if CONFIG_SECTION_NAME in config_data:
                should_write = prompt_config_overwrite(
                    logger,
                    config_file_path,
                    f"Section [{CONFIG_SECTION_NAME}]"
                )
            # --- END MODIFIED ---
            
            if should_write:
                config_data[CONFIG_SECTION_NAME] = new_section_dict
                if write_toml_file(config_file_path, config_data, logger):
                    log_success(logger, f"✅ Đã tạo/cập nhật thành công '{config_file_path.name}'.")
                else:
                    raise IOError(f"Không thể ghi file TOML: {config_file_path.name}")

        except (IOError, KeyError, ValueError) as e:
            logger.error(f"❌ Đã xảy ra lỗi khi thao tác file config: {e}")
            raise typer.Exit(code=1)

        # --- MODIFIED: Sử dụng helper launch ---
        launch_editor(logger, config_file_path)
        # --- END MODIFIED ---

        raise typer.Exit(code=0)
    # --- KẾT THÚC LOGIC CONFIG ---


    # (Logic chạy tool giữ nguyên)
    # ...
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
    
    project_config_path = effective_scan_root / PROJECT_CONFIG_FILENAME
    file_config_data = load_project_config_section(project_config_path, CONFIG_SECTION_NAME, logger)
    
    extensions_str: str
    if extensions:
        extensions_str = extensions
        logger.debug("Sử dụng danh sách 'extensions' từ CLI.")
    elif 'extensions' in file_config_data:
        extensions_str = file_config_data['extensions']
        logger.debug("Sử dụng danh sách 'extensions' từ .project.toml.")
    else:
        extensions_str = DEFAULT_EXTENSIONS_STRING
        logger.debug("Sử dụng danh sách 'extensions' mặc định.")
    final_extensions_list = [ext.strip() for ext in extensions_str.split(',') if ext.strip()]
    
    cli_ignore_set = parse_comma_list(ignore)
    file_ignore_set = set(file_config_data.get('ignore', []))
    final_ignore_set = DEFAULT_IGNORE.union(file_ignore_set).union(cli_ignore_set)
    logger.debug(f"Danh sách 'ignore' cuối cùng (đã merge): {sorted(list(final_ignore_set))}")
    
    original_args = sys.argv[1:]
    filtered_args = [
        shlex.quote(arg) for arg in original_args
        if arg not in ('-d', '--dry-run', '--fix', '-c', '--config')
    ]
    fix_command_str = "cpath " + " ".join(filtered_args)

    try:
        files_to_fix = process_path_updates(
            logger=logger, project_root=effective_scan_root,
            target_dir_str=str(target_directory_arg) if effective_scan_root == scan_root and target_directory_arg else None,
            extensions=final_extensions_list,
            ignore_set=final_ignore_set, 
            script_file_path=THIS_SCRIPT_PATH,
            check_mode=check_mode
        )
        
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