# Path: scripts/stubgen.py

import sys
import logging
from pathlib import Path
from typing import Optional, List, Set, Dict, Any

import typer

# --- Thêm PROJECT_ROOT vào sys.path để import utils/modules ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from utils.logging_config import setup_logging, log_success
    
    # --- MODIFIED: Xóa parse_comma_list (chuyển vào core) ---
    # --- END MODIFIED ---
    
    # --- NEW: Import helper từ utils.cli ---
    from utils.cli import handle_project_root_validation, handle_config_init_request
    # --- END NEW ---
    
    # --- MODULE IMPORTS (SRP) ---
    from modules.stubgen import (
        # Configs
        DEFAULT_IGNORE, 
        SCAN_ROOTS, 
        DYNAMIC_IMPORT_INDICATORS,
        AST_MODULE_LIST_NAME,
        AST_ALL_LIST_NAME,
        PROJECT_CONFIG_FILENAME,
        CONFIG_FILENAME,
        CONFIG_SECTION_NAME,
        
        # Functions
        load_config_files,
        process_stubgen_logic,
        execute_stubgen_action
    )
    # ----------------------
except ImportError as e:
    print(f"Error: Could not import project utilities/modules. Ensure PROJECT_ROOT is correct: {PROJECT_ROOT}. Error: {e}", file=sys.stderr)
    sys.exit(1)

# --- CONSTANTS ---
THIS_SCRIPT_PATH = Path(__file__).resolve()
# --- NEW: Constants cho config init ---
MODULE_DIR = PROJECT_ROOT / "modules" / "stubgen"
TEMPLATE_FILENAME = "stubgen.toml.template" 
SGEN_DEFAULTS: Dict[str, Any] = {
    "ignore": DEFAULT_IGNORE,
    "restrict": SCAN_ROOTS,
    "dynamic_import_indicators": DYNAMIC_IMPORT_INDICATORS,
    "ast_module_list_name": AST_MODULE_LIST_NAME,
    "ast_all_list_name": AST_ALL_LIST_NAME
}
# --- END NEW ---

# --- TYPER APP ---
app = typer.Typer(
    help="Automatically generates .pyi stub files for dynamic module gateways.",
    epilog="Ví dụ: sgen . -f -R modules/auth,utils/core",
    add_completion=False,
    context_settings={
        'help_option_names': ['--help', '-h'],
        'allow_interspersed_args': True
    }
)

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    
    # --- NEW: Config Init Flags ---
    config_project: bool = typer.Option(
        False, "-c", "--config-project",
        help=f"Khởi tạo/cập nhật section [{CONFIG_SECTION_NAME}] trong {PROJECT_CONFIG_FILENAME}.",
    ),
    config_local: bool = typer.Option(
        False, "-C", "--config-local",
        help=f"Khởi tạo/cập nhật file {CONFIG_FILENAME} (scope 'local').",
    ),
    # --- END NEW ---
    
    target_dir: Path = typer.Argument(
        Path("."),
        help="Đường dẫn thư mục để bắt đầu quét (base directory). Mặc định là thư mục hiện tại (.)."
    ),
    force: bool = typer.Option(
        False,
        "-f", "--force",
        help="Ghi đè file .pyi nếu đã tồn tại (không hỏi xác nhận)."
    ),
    ignore: Optional[str] = typer.Option(
        None,
        "-I", "--ignore",
        help="Danh sách pattern (fnmatch) ngăn cách bởi dấu phẩy để bỏ qua (THÊM vào config)." 
    ),
    restrict: Optional[str] = typer.Option(
        None,
        "-R", "--restrict",
        help="Danh sách thư mục con (so với target_dir) ngăn cách bởi dấu phẩy để giới hạn quét (GHI ĐÈ config)." 
    ),
):
    """
    Main orchestration function. Parses args, sets up logging, and calls core logic.
    """
    if ctx.invoked_subcommand: return

    # 1. Setup Logging
    logger = setup_logging(script_name="SGen")
    logger.debug("SGen script started.")

    # --- 2. Xử lý Config Init (Tái sử dụng 100%) ---
    try:
        config_action_taken = handle_config_init_request(
            logger=logger,
            config_project=config_project,
            config_local=config_local,
            module_dir=MODULE_DIR,
            template_filename=TEMPLATE_FILENAME,
            config_filename=CONFIG_FILENAME,
            project_config_filename=PROJECT_CONFIG_FILENAME,
            config_section_name=CONFIG_SECTION_NAME,
            base_defaults=SGEN_DEFAULTS
        )
        if config_action_taken:
            raise typer.Exit(code=0) # Thoát an toàn
            
    except typer.Exit as e:
        raise e
    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi khi khởi tạo config: {e}")
        logger.debug("Traceback:", exc_info=True)
        raise typer.Exit(code=1)
    # --- KẾT THÚC ---
    
    # 3. Mở rộng `~` và resolve đường dẫn tuyệt đối
    scan_root = target_dir.expanduser().resolve()

    if not scan_root.exists() or not scan_root.is_dir():
        logger.error(f"❌ Error: Target directory does not exist or is not a directory: {scan_root.as_posix()}")
        raise typer.Exit(code=1)

    # 4. Xác thực Project Root (R/C/Q)
    effective_scan_root: Optional[Path]
    effective_scan_root, _ = handle_project_root_validation(
        logger=logger,
        scan_root=scan_root,
        force_silent=force 
    )
    
    if effective_scan_root is None:
        raise typer.Exit(code=0)

    # --- 5. Tải Config và Chuẩn bị Args cho Core ---
    
    # 5.1. Tải file config
    file_config = load_config_files(effective_scan_root, logger)
    
    # 5.2. Chuẩn bị config từ CLI
    cli_config: Dict[str, Optional[str]] = {
        "ignore": ignore,
        "restrict": restrict
    }
    
    # 6. Execute Core Logic
    try:
        # --- MODIFIED: Cập nhật lời gọi hàm ---
        results = process_stubgen_logic(
            logger=logger,
            scan_root=effective_scan_root,
            cli_config=cli_config,
            file_config=file_config,
            script_file_path=THIS_SCRIPT_PATH
        )
        # --- END MODIFIED ---
        
        # 7. Execute Action
        if results:
            execute_stubgen_action(
                logger=logger,
                results=results,
                force=force
            )
        else:
            log_success(logger, "No dynamic module gateways found to process.")
       
        # (Xóa log "Operation completed." vì execute_stubgen_action đã log)
            
    except typer.Exit:
        pass
    except Exception as e:
        logger.error(f"❌ An unexpected error occurred: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        app()
    except KeyboardInterrupt:
        print("\n\n❌ [Stop Command] Stub generation operation stopped.")
        sys.exit(1)