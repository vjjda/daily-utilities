# Path: scripts/tree.py

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, Set, Dict, Any

# --- THÊM TOMLLIB ---
try:
    import tomllib 
except ImportError:
    try:
        import toml as tomllib
    except ImportError:
        tomllib = None
# --- KẾT THÚC THÊM ---

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))
# --- END BOOTSTRAPPING ---

import typer

# Common utilities
from utils.logging_config import setup_logging, log_success
from utils.core import (
    is_git_repository,
    # --- IMPORT ĐÃ THAY ĐỔI ---
    load_toml_file, 
    write_toml_file,
    load_config_template, 
    generate_dynamic_config
    # (Đã xóa: overwrite_or_append_project_config_section)
    # (Đã xóa: write_config_file)
    # --- KẾT THÚC THAY ĐỔI ---
)
# Module Imports
from modules.tree import (
    CONFIG_FILENAME,
    PROJECT_CONFIG_FILENAME,
    CONFIG_SECTION_NAME,
    DEFAULT_IGNORE, DEFAULT_PRUNE, DEFAULT_DIRS_ONLY_LOGIC,
    DEFAULT_MAX_LEVEL, FALLBACK_SHOW_SUBMODULES, FALLBACK_USE_GITIGNORE,

    load_config_files, # (Vẫn dùng hàm load của tree để merge 2 file)

    merge_config_sources,

    generate_tree,
    print_status_header,
    print_final_result,
)

# --- CONSTANTS ---
MODULE_DIR = PROJECT_ROOT / "modules" / "tree"
TEMPLATE_FILENAME = "tree.toml.template"

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
        help="Khởi tạo/cập nhật file cấu hình. Gõ '-c' không kèm giá trị sẽ mặc định là scope 'project'. Chấp nhận 'local', 'tree', 'project'.",
        show_default=False,
        callback=lambda value: 'project' if value == "" else value,
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

    # --- Logic khởi tạo Config (ĐÃ REFACTOR) ---
    if config_scope:
        logger = setup_logging(script_name="CTree")
        
        # Thêm kiểm tra tomllib
        if tomllib is None:
             logger.error("❌ Thiếu thư viện 'tomli'. Vui lòng cài đặt: 'pip install tomli tomli-w'")
             raise typer.Exit(code=1)

        scope = config_scope.lower()

        tree_defaults: Dict[str, Any] = {
            "level": DEFAULT_MAX_LEVEL,
             "show-submodules": FALLBACK_SHOW_SUBMODULES,
             "use-gitignore": FALLBACK_USE_GITIGNORE,
             "ignore": DEFAULT_IGNORE,
             "prune": DEFAULT_PRUNE,
             "dirs-only": DEFAULT_DIRS_ONLY_LOGIC
        }

        # --- Tải template (Logic chung) ---
        try:
            template_str = load_config_template(MODULE_DIR, TEMPLATE_FILENAME, logger)
            # (Hàm generate_dynamic_config đã được refactor trong core)
            content_with_placeholders = generate_dynamic_config(template_str, tree_defaults, logger)
        except (KeyError, ValueError) as e:
            logger.error(f"❌ Đã xảy ra lỗi khi tạo nội dung config: {e}")
            raise typer.Exit(code=1)
        # --- Hết Logic chung ---

        if scope == "local" or scope == "tree":
             config_file_path = Path.cwd() / CONFIG_FILENAME
             file_existed = config_file_path.exists()
             should_write = False
             
             # Logic UI (typer.confirm) nằm ở entrypoint
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
                    # Ghi file trực tiếp, không cần hàm helper 'write_config_file'
                    config_file_path.write_text(content_with_placeholders, encoding="utf-8")
                    log_msg = (
                        f"Đã tạo thành công '{config_file_path.name}'." if not file_existed
                        else f"Đã ghi đè thành công '{config_file_path.name}'."
                    )
                    log_success(logger, log_msg)
                 except IOError as e:
                     logger.error(f"❌ Lỗi khi ghi file '{config_file_path.name}': {e}")
                     raise typer.Exit(code=1)

        elif scope == "project":
             config_file_path = Path.cwd() / PROJECT_CONFIG_FILENAME
             try:
                # 1. Parse nội dung section MỚI (logic từ helper cũ)
                start_marker = f"[{CONFIG_SECTION_NAME}]"
                start_index = content_with_placeholders.find(start_marker)
                if start_index == -1: raise ValueError("Template thiếu header section.")
                content_section_only = content_with_placeholders[start_index + len(start_marker):].strip()
                
                # Parse string TOML để lấy dict section mới
                full_toml_string = f"[{CONFIG_SECTION_NAME}]\n{content_section_only}"
                new_section_dict = tomllib.loads(full_toml_string).get(CONFIG_SECTION_NAME, {})
                if not new_section_dict:
                     raise ValueError("Nội dung section mới bị rỗng.")

                # 2. Đọc file config HIỆN TẠI (dùng toml_io)
                config_data = load_toml_file(config_file_path, logger)

                # 3. Logic UI (typer.confirm) nằm ở entrypoint
                if CONFIG_SECTION_NAME in config_data:
                    logger.warning(f"⚠️ Section [{CONFIG_SECTION_NAME}] đã tồn tại trong '{config_file_path.name}'.")
                    try:
                        # Dùng Typer để hỏi xác nhận
                        typer.confirm("   Ghi đè section hiện tại?", abort=True)
                    except typer.Abort:
                        logger.warning("Hoạt động bị hủy bởi người dùng.")
                        raise typer.Exit(code=0) # Thoát nhẹ nhàng
                
                # 4. Merge data
                config_data[CONFIG_SECTION_NAME] = new_section_dict
                
                # 5. Ghi file (dùng toml_io)
                if write_toml_file(config_file_path, config_data, logger):
                    log_success(logger, f"✅ Đã tạo/cập nhật thành công '{config_file_path.name}'.")
                else:
                    # write_toml_file đã log lỗi, chỉ cần raise
                    raise IOError(f"Không thể ghi file TOML: {config_file_path.name}")

             except (IOError, KeyError, ValueError) as e:
                logger.error(f"❌ Đã xảy ra lỗi khi thao tác file: {e}")
                raise typer.Exit(code=1)

        else: # Scope không hợp lệ
            logger.error(f"❌ Đối số scope không hợp lệ cho --config: '{config_scope}'. Phải là 'local', 'tree', 'project', hoặc để trống (mặc định 'project').")
            raise typer.Exit(code=1)

        # Mở file
        try:
            logger.info(f"Đang mở '{config_file_path.name}'...")
            typer.launch(str(config_file_path))
        except Exception as e:
            logger.error(f"❌ Lỗi khi mở file: {e}")
            logger.warning(f"⚠️ Không thể tự động mở file.")

        raise typer.Exit(code=0)
    # --- KẾT THÚC LOGIC CONFIG ---

    # --- 2. Setup & Validate (Logic chạy tool, không đổi) ---
    logger = setup_logging(script_name="CTree")
    start_path = start_path_arg.expanduser()
    if not start_path.exists():
        logger.error(f"❌ Lỗi: Đường dẫn bắt đầu không tồn tại: {start_path}")
        raise typer.Exit(code=1)
    logger.debug(f"Đã nhận đường dẫn: {start_path}")

    # --- 3. Build 'args' object (Không đổi) ---
    cli_dirs_only = "_ALL_" if all_dirs else dirs_patterns
    args = argparse.Namespace(
        level=level, ignore=ignore, prune=prune, dirs_only=cli_dirs_only,
        show_submodules=show_submodules, no_gitignore=no_gitignore, full_view=full_view,
        init=False, start_path=str(start_path)
    )

    # --- 4. Process Path & Git (Không đổi) ---
    initial_path: Path = start_path
    start_dir = initial_path.parent if initial_path.is_file() else initial_path
    is_git_repo = is_git_repository(start_dir)

    # --- 5. Orchestrate Module Calls (Không đổi) ---
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