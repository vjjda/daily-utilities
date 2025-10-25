# Path: scripts/tree.py

import sys
import argparse 
import logging
from pathlib import Path
from typing import Optional, Set 

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))
# --- END BOOTSTRAPPING ---

import typer

from utils.logging_config import setup_logging, log_success
from utils.core import run_command, is_git_repository

# Module Imports
from modules.tree import (
    CONFIG_FILENAME,
    PROJECT_CONFIG_FILENAME,
    CONFIG_SECTION_NAME, 
    
    load_config_files,
    load_config_template,
    
    merge_config_sources,
    generate_dynamic_config,
    
    generate_tree,
    print_status_header,
    print_final_result,

    write_config_file,
    overwrite_or_append_project_config_section
)

# Khởi tạo Typer App
app = typer.Typer(
    help="Một công cụ tạo cây thư mục thông minh hỗ trợ file cấu hình .tree.toml.",
    add_completion=False,
    context_settings={"help_option_names": ["--help", "-h"]}
)

# Command chính (mặc định)
@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    config_scope: Optional[str] = typer.Option(
        None, "-c", "--config",
        help="Khởi tạo hoặc cập nhật file cấu hình: 'local' (tạo .tree.toml) hoặc 'project' (cập nhật .project.toml).",
        case_sensitive=False
    ),
    start_path_arg: Path = typer.Argument( 
        Path("."), 
        help="Đường dẫn bắt đầu (file hoặc thư mục). Dùng '~' cho thư mục home.",
    ),
    level: Optional[int] = typer.Option( None, "-L", "--level", help="Giới hạn độ sâu hiển thị.", min=1 ),
    ignore: Optional[str] = typer.Option( None, "-I", "--ignore", help="Danh sách pattern (phân cách bởi dấu phẩy) để bỏ qua." ),
    prune: Optional[str] = typer.Option( None, "-P", "--prune", help="Danh sách pattern (phân cách bởi dấu phẩy) để cắt tỉa (prune)." ),
    all_dirs: bool = typer.Option( False, "-d", "--dirs-only", help="Chỉ hiển thị thư mục cho toàn bộ cây." ),
    dirs_patterns: Optional[str] = typer.Option( None, "--dirs-patterns", help="Chỉ hiển thị thư mục con cho các pattern cụ thể (ví dụ: 'assets')." ),
    show_submodules: bool = typer.Option( False, "-s", "--show-submodules", help="Hiển thị nội dung của các submodule." ),
    no_gitignore: bool = typer.Option( False, "--no-gitignore", help="Không tôn trọng file .gitignore." ),
    full_view: bool = typer.Option( False, "-f", "--full-view", help="Bỏ qua tất cả bộ lọc (.gitignore, rules, level) và hiển thị tất cả." )
):
    """ Hàm điều phối chính: Phân tích đối số, gọi xử lý config, và chạy tạo cây. """
    if ctx.invoked_subcommand: return

    # --- Logic khởi tạo Config (Đã refactor cho TOML) ---
    if config_scope:
        scope = config_scope.lower()
        logger = setup_logging(script_name="CTree")
        
        if scope == "local" or scope == "tree": 
            config_file_path = Path.cwd() / CONFIG_FILENAME # .tree.toml
            file_existed = config_file_path.exists()
            
            should_write = False
            if file_existed:
                try:
                    should_write = typer.confirm(f"'{CONFIG_FILENAME}' đã tồn tại. Ghi đè?", abort=True)
                    logger.debug(f"Người dùng chọn ghi đè '{CONFIG_FILENAME}'.")
                except typer.Abort:
                    logger.warning("Hoạt động bị hủy bởi người dùng.")
                    raise typer.Exit(code=0)
            else:
                should_write = True
                logger.debug(f"Đang tạo mới '{CONFIG_FILENAME}'.")
                
            if should_write:
                try:
                    template_str = load_config_template()
                    content = generate_dynamic_config(template_str)
                    write_config_file(config_file_path, content, logger, file_existed)
                except (IOError, KeyError) as e:
                    logger.error(f"❌ Đã xảy ra lỗi khi tạo file: {e}")
                    raise typer.Exit(code=1)
                    
        elif scope == "project":
            config_file_path = Path.cwd() / PROJECT_CONFIG_FILENAME # .project.toml
            
            try:
                template_str = load_config_template()
                content_with_placeholders = generate_dynamic_config(template_str)
                
                # Trích xuất nội dung *bên trong* section [tree]
                start_index = content_with_placeholders.find(f"[{CONFIG_SECTION_NAME}]") + len(f"[{CONFIG_SECTION_NAME}]")
                content_section_only = content_with_placeholders[start_index:].strip()
                
                overwrite_or_append_project_config_section(
                    config_file_path, 
                    content_section_only, 
                    logger
                )
                
            except (IOError, KeyError) as e:
                logger.error(f"❌ Đã xảy ra lỗi khi thao tác file: {e}")
                raise typer.Exit(code=1)
                
        else:
            logger.error(f"❌ Đối số scope không hợp lệ cho --config: '{config_scope}'. Phải là 'local', 'tree', hoặc 'project'.")
            raise typer.Exit(code=1)

        # Mở file
        try:
            logger.info(f"Đang mở '{config_file_path.name}' trong trình soạn thảo mặc định...")
            typer.launch(str(config_file_path))
        except Exception as e:
            logger.error(f"❌ Đã xảy ra lỗi không mong muốn khi mở file: {e}")
            logger.warning(f"⚠️ Không thể tự động mở file. Vui lòng mở thủ công.")
            
        raise typer.Exit(code=0)
    # --- END LOGIC CONFIG ---

    # --- 2. Setup & Validate ---
    logger = setup_logging(script_name="CTree")
    start_path = start_path_arg.expanduser()
    
    if not start_path.exists():
        logger.error(f"❌ Lỗi: Đường dẫn bắt đầu không tồn tại: {start_path}")
        raise typer.Exit(code=1)

    logger.debug(f"Đã nhận đường dẫn: {start_path}")
    
    # 3. Build 'args' object (Namespace)
    cli_dirs_only = "_ALL_" if all_dirs else dirs_patterns
    args = argparse.Namespace(
        level=level, ignore=ignore, prune=prune, dirs_only=cli_dirs_only,
        show_submodules=show_submodules, no_gitignore=no_gitignore, full_view=full_view,
        init=False, start_path=str(start_path) 
    )

    # 4. Process Path & Git
    initial_path: Path = start_path
    start_dir = initial_path.parent if initial_path.is_file() else initial_path
    is_git_repo = is_git_repository(start_dir)
    
    # 5. Orchestrate Module Calls
    try: 
        # 5.1 Load (từ loader, trả về Dict)
        file_config = load_config_files(start_dir, logger)
        
        # 5.2 Process (từ core, nhận Dict)
        config_params = merge_config_sources(
            args=args, 
            file_config=file_config,
            start_dir=start_dir, 
            logger=logger, 
            is_git_repo=is_git_repo
        )
        
        # 5.3 Execute (từ executor)
        print_status_header(
            config_params=config_params, 
            start_dir=start_dir, 
            is_git_repo=is_git_repo,
            cli_no_gitignore=args.no_gitignore
        )

        counters = {'dirs': 0, 'files': 0}
        generate_tree(
            start_dir, start_dir, counters=counters, 
            max_level=config_params["max_level"],
            ignore_list=config_params["ignore_list"], 
            submodules=config_params["submodules"],
            prune_list=config_params["prune_list"], 
            gitignore_spec=config_params["gitignore_spec"],
            dirs_only_list=config_params["dirs_only_list"], 
            is_in_dirs_only_zone=config_params["is_in_dirs_only_zone"]
        )

        print_final_result(
            counters=counters, 
            global_dirs_only=config_params["global_dirs_only_flag"]
        )
        
    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn: {e}")
        logger.debug("Traceback:", exc_info=True)
        raise typer.Exit(code=1)

    
if __name__ == "__main__":
    try: app()
    except KeyboardInterrupt: print("\n\n❌ [Lệnh dừng] Đã dừng tạo cây."); sys.exit(1)