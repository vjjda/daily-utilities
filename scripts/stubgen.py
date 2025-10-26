# Path: scripts/stubgen.py

import sys
import logging
from pathlib import Path
from typing import Optional, List, Set

import typer

# --- Thêm PROJECT_ROOT vào sys.path để import utils/modules ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from utils.logging_config import setup_logging, log_success
    
    # --- MODIFIED: Xóa find_git_root/is_git_repository ---
    from utils.core import parse_comma_list
    # --- END MODIFIED ---
    
    # --- NEW: Import helper từ utils.cli ---
    from utils.cli import handle_project_root_validation
    # --- END NEW ---
    
    # --- MODULE IMPORTS (SRP) ---
    from modules.stubgen import (
        process_stubgen_logic,
        execute_stubgen_action
    )
    # ----------------------
except ImportError as e:
    # Log error tiếng Anh theo quy tắc.
    print(f"Error: Could not import project utilities/modules. Ensure PROJECT_ROOT is correct: {PROJECT_ROOT}. Error: {e}", file=sys.stderr)
    sys.exit(1)

# --- CONSTANTS ---
THIS_SCRIPT_PATH = Path(__file__).resolve()

# --- TYPER APP ---
# ... (Định nghĩa app giữ nguyên) ...
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
    
    # ... (Các tham số Typer giữ nguyên) ...
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
        help="Danh sách pattern (fnmatch) ngăn cách bởi dấu phẩy để bỏ qua."
    ),
    restrict: Optional[str] = typer.Option(
        None,
        "-R", "--restrict",
        help="Danh sách thư mục con (so với target_dir) ngăn cách bởi dấu phẩy để giới hạn quét. Mặc định là SCAN_ROOTS."
    ),
):
    """
    Main orchestration function. Parses args, sets up logging, and calls core logic.
    """
    if ctx.invoked_subcommand: return

    # 1. Setup Logging
    logger = setup_logging(script_name="SGen")
    logger.debug("SGen script started.")
    
    # Mở rộng `~` và resolve đường dẫn tuyệt đối
    scan_root = target_dir.expanduser().resolve()

    if not scan_root.exists() or not scan_root.is_dir():
        logger.error(f"❌ Error: Target directory does not exist or is not a directory: {scan_root.as_posix()}")
        raise typer.Exit(code=1)

    # --- MODIFIED: Thay thế khối R/C/Q bằng hàm helper ---
    # sgen tôn trọng cờ --force để bỏ qua prompt
    effective_scan_root: Optional[Path]
    effective_scan_root, _ = handle_project_root_validation(
        logger=logger,
        scan_root=scan_root,
        force_silent=force 
    )
    
    # --- NEW: Xử lý Quit (None) ---
    if effective_scan_root is None:
        # (Logger đã in thông báo hủy)
        raise typer.Exit(code=0)
    # --- END NEW ---
    # (Chúng ta không cần git_warning_str ở đây)
    # --- END MODIFIED ---

    # 3. Prepare Args for Core
    cli_ignore_patterns: Set[str] = parse_comma_list(ignore)
    cli_restrict_patterns: Set[str] = parse_comma_list(restrict)
    
    # 4. Execute Core Logic
    try:
        results = process_stubgen_logic(
            logger=logger,
            scan_root=effective_scan_root, # <-- Sử dụng root đã được xác định
            cli_ignore=cli_ignore_patterns,
            cli_restrict=cli_restrict_patterns,
            script_file_path=THIS_SCRIPT_PATH
        )
        
        # 5. Execute Action
        if results:
            execute_stubgen_action(
                logger=logger,
                results=results,
                force=force
            )
        else:
            log_success(logger, "No dynamic module gateways found to process.")
       
        if not results:
            log_success(logger, "Operation completed.")
            
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