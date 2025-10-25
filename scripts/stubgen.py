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
    from utils.core import is_git_repository, parse_comma_list
    
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

    # 2. Git Check & Confirmation (if not force)
    if not force:
        if not is_git_repository(scan_root):
            logger.warning(f"⚠️ Target directory '{scan_root.name}/' is not a Git repository.")
            logger.warning("   Scanning a non-project directory may lead to unexpected results.")
            try:
                confirmation = input("   Are you sure you want to proceed? (y/N): ")
            except (EOFError, KeyboardInterrupt):
                confirmation = 'n'
            
            if confirmation.lower() != 'y':
                logger.error("❌ Operation cancelled by user.")
                raise typer.Exit(code=0)
            else:
                logger.info("✅ Proceeding with scan in non-Git repository.")
        else:
            logger.info("✅ Git repository detected. Proceeding with scan.")

    # 3. Prepare Args for Core
    cli_ignore_patterns: Set[str] = parse_comma_list(ignore)
    cli_restrict_patterns: Set[str] = parse_comma_list(restrict)
    
    # 4. Execute Core Logic
    try:
        # Core logic sẽ thực hiện quét, phân tích và tạo nội dung stub.
        results = process_stubgen_logic(
            logger=logger,
            scan_root=scan_root,
            cli_ignore=cli_ignore_patterns,
            cli_restrict=cli_restrict_patterns,
            script_file_path=THIS_SCRIPT_PATH # Cần loại trừ chính nó
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
       
        # Log_success cuối cùng được thực hiện bởi executor nếu có file được xử lý.
        if not results:
            log_success(logger, "Operation completed.")
            
    except typer.Exit:
        # Typer.Exit đã được xử lý (khi user chọn Quit trong Git check hoặc action)
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