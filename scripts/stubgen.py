# Path: scripts/stubgen.py

import sys
import logging
from pathlib import Path
from typing import Optional, List # (Import các type phổ biến)

import typer # (Sử dụng Typer)

# --- Thêm PROJECT_ROOT vào sys.path để import utils/modules ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from utils.logging_config import setup_logging, log_success
    
    # --- CONFIG DEFAULTS ---
    from modules.stubgen.stubgen_config import DEFAULT_TARGET_DIR
    # --- END CONFIG DEFAULTS ---
    
    # --- MODULE IMPORTS (SRP) ---
    from modules.stubgen import (
        # (Ví dụ: Import các hàm đã được export)
        # load_data, 
        process_stubgen_logic,
        execute_stubgen_action
    )
    # ----------------------
except ImportError:
    print(f"Lỗi: Không thể import utils/modules. Đảm bảo PROJECT_ROOT đúng: {PROJECT_ROOT}", file=sys.stderr)
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
        DEFAULT_TARGET_DIR,
        help="Đường dẫn thư mục để bắt đầu quét (base directory). Mặc định là thư mục hiện tại (.)."
    ),
    force: bool = typer.Option(
        False,
        "-f",
        "--force",
        help="Ghi đè file .pyi nếu đã tồn tại (không hỏi xác nhận)."
    ),
    ignore: Optional[str] = typer.Option(
        None,
        "-I",
        "--ignore",
        help="Danh sách pattern (fnmatch) ngăn cách bởi dấu phẩy để bỏ qua."
    ),
    restrict: Optional[str] = typer.Option(
        None,
        "-R",
        "--restrict",
        help="Danh sách thư mục con (so với target_dir) ngăn cách bởi dấu phẩy để giới hạn quét. Mặc định là SCAN_ROOTS."
    ),
):
    """
    Main orchestration function.
    Parses args, sets up logging, and calls core logic.
    """
    if ctx.invoked_subcommand: return

    # 1. Setup Logging
    logger = setup_logging(script_name="SGen")
    logger.debug("SGen script started.")
    
    # --- NEW: Mở rộng `~` thủ công cho các tham số Path ---
    target_dir_expanded = target_dir.expanduser() if target_dir else None
    # --- END NEW ---

    # 2. Execute Core Logic (SRP)
    try:
        # (Đây là ví dụ, bạn cần tùy chỉnh luồng)
        
        # 2.1. Load (từ _loader)
        # (Ví dụ: data = load_data(logger, target_path_expanded))
        
        # 2.2. Process (từ _core)
        # (Truyền các tham số Typer vào logic core)
        result = process_stubgen_logic(
            logger=logger,
            target_dir=target_dir_expanded,
            force=force,
            ignore=ignore,
            restrict=restrict,
            # (Ví dụ: data=data)
        )
        
        # 2.3. Execute (từ _executor)
        if result:
            execute_stubgen_action(
                logger=logger,
                result=result
            )
        
        log_success(logger, "Hoàn thành.")
            
    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        app() # (Sử dụng Typer runner)
    except KeyboardInterrupt:
        print("\n\n❌ [Lệnh dừng] Hoạt động của tool đã bị dừng.")
        sys.exit(1)