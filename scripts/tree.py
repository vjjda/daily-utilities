# Path: scripts/tree.py

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, Set, Dict, Any # <-- Thêm Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))
# --- END BOOTSTRAPPING ---

import typer

# Common utilities
from utils.logging_config import setup_logging, log_success
# --- MODIFIED: Import hàm config I/O từ utils.core ---
from utils.core import (
    run_command, is_git_repository,
    load_config_template, generate_dynamic_config,
    overwrite_or_append_project_config_section,
    write_config_file
)
# --- END MODIFIED ---

# Module Imports
from modules.tree import (
    CONFIG_FILENAME,
    PROJECT_CONFIG_FILENAME,
    CONFIG_SECTION_NAME,
    DEFAULT_IGNORE, DEFAULT_PRUNE, DEFAULT_DIRS_ONLY_LOGIC, # <-- Cần defaults cho generate_dynamic_config
    DEFAULT_MAX_LEVEL, FALLBACK_SHOW_SUBMODULES, FALLBACK_USE_GITIGNORE, # <-- Cần defaults cho generate_dynamic_config

    load_config_files, # Vẫn dùng loader của tree để merge 2 file
    # load_config_template, # Đã chuyển

    merge_config_sources,
    # generate_dynamic_config, # Đã chuyển

    generate_tree,
    print_status_header,
    print_final_result,

    # write_config_file, # Đã chuyển
    # overwrite_or_append_project_config_section # Đã chuyển
)

# --- CONSTANTS ---
MODULE_DIR = PROJECT_ROOT / "modules" / "tree" # Path đến thư mục module tree
TEMPLATE_FILENAME = "tree.toml.template" # Tên file template

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

    # --- Logic khởi tạo Config (Đã refactor cho utils) ---
    if config_scope:
        scope = config_scope.lower()
        logger = setup_logging(script_name="CTree")

        # --- Chuẩn bị dict defaults cho tree ---
        tree_defaults: Dict[str, Any] = {
            "level": DEFAULT_MAX_LEVEL,
            "show-submodules": FALLBACK_SHOW_SUBMODULES,
            "use-gitignore": FALLBACK_USE_GITIGNORE,
            "ignore": DEFAULT_IGNORE,
            "prune": DEFAULT_PRUNE,
            "dirs-only": DEFAULT_DIRS_ONLY_LOGIC
        }
        # ---

        if scope == "local" or scope == "tree":
            config_file_path = Path.cwd() / CONFIG_FILENAME # .tree.toml
            file_existed = config_file_path.exists()

            should_write = False
            if file_existed:
                try:
                    should_write = typer.confirm(f"'{CONFIG_FILENAME}' đã tồn tại. Ghi đè?", abort=True)
                except typer.Abort:
                    logger.warning("Hoạt động bị hủy bởi người dùng.")
                    raise typer.Exit(code=0)
            else:
                should_write = True

            if should_write:
                try:
                    template_str = load_config_template(MODULE_DIR, TEMPLATE_FILENAME, logger)
                    if "# LỖI" in template_str: raise IOError("Không thể tải template.")

                    # Dùng generate_dynamic_config chung
                    content = generate_dynamic_config(template_str, tree_defaults, logger)
                    if "# LỖI" in content: raise ValueError("Không thể tạo nội dung config.")

                    # Dùng write_config_file chung
                    write_config_file(config_file_path, content, logger, file_existed)
                except (IOError, KeyError, ValueError) as e:
                    logger.error(f"❌ Đã xảy ra lỗi khi tạo file: {e}")
                    raise typer.Exit(code=1)

        elif scope == "project":
            config_file_path = Path.cwd() / PROJECT_CONFIG_FILENAME # .project.toml

            try:
                template_str = load_config_template(MODULE_DIR, TEMPLATE_FILENAME, logger)
                if "# LỖI" in template_str: raise IOError("Không thể tải template.")

                # Dùng generate_dynamic_config chung
                content_with_placeholders = generate_dynamic_config(template_str, tree_defaults, logger)
                if "# LỖI" in content_with_placeholders: raise ValueError("Không thể tạo nội dung config.")

                # Trích xuất nội dung *bên trong* section [tree]
                start_marker = f"[{CONFIG_SECTION_NAME}]"
                start_index = content_with_placeholders.find(start_marker)
                if start_index == -1: raise ValueError("Template thiếu header section.")
                content_section_only = content_with_placeholders[start_index + len(start_marker):].strip()

                # Dùng overwrite_or_append_project_config_section chung
                overwrite_or_append_project_config_section(
                    config_path=config_file_path,
                    config_section_name=CONFIG_SECTION_NAME, # Truyền "tree"
                    new_section_content_str=content_section_only,
                    logger=logger
                )

            except (IOError, KeyError, ValueError) as e:
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

    # --- 2. Setup & Validate (Giữ nguyên) ---
    logger = setup_logging(script_name="CTree")
    start_path = start_path_arg.expanduser()
    if not start_path.exists():
        logger.error(f"❌ Lỗi: Đường dẫn bắt đầu không tồn tại: {start_path}")
        raise typer.Exit(code=1)
    logger.debug(f"Đã nhận đường dẫn: {start_path}")

    # --- 3. Build 'args' object (Giữ nguyên) ---
    cli_dirs_only = "_ALL_" if all_dirs else dirs_patterns
    args = argparse.Namespace(
        level=level, ignore=ignore, prune=prune, dirs_only=cli_dirs_only,
        show_submodules=show_submodules, no_gitignore=no_gitignore, full_view=full_view,
        init=False, start_path=str(start_path)
    )

    # --- 4. Process Path & Git (Giữ nguyên) ---
    initial_path: Path = start_path
    start_dir = initial_path.parent if initial_path.is_file() else initial_path
    is_git_repo = is_git_repository(start_dir)

    # --- 5. Orchestrate Module Calls (Giữ nguyên) ---
    try:
        # 5.1 Load (từ loader của tree, trả về Dict đã merge)
        file_config = load_config_files(start_dir, logger)

        # 5.2 Process (từ core của tree, nhận Dict)
        config_params = merge_config_sources(
            args=args,
            file_config=file_config,
            start_dir=start_dir,
            logger=logger,
            is_git_repo=is_git_repo
        )

        # 5.3 Execute (từ executor của tree)
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