#!/usr/bin/env python3
# Path: scripts/zsh_wrapper.py

import sys
import argparse 
import logging
from pathlib import Path
from typing import Optional

# --- MODIFIED: Import Typer trực tiếp ---
import typer
# --- END MODIFIED ---

# --- Thêm PROJECT_ROOT vào sys.path để import utils/modules ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from utils.logging_config import setup_logging, log_success
    
    from modules.zsh_wrapper import (
        DEFAULT_MODE, 
        DEFAULT_VENV, 
        DEFAULT_WRAPPER_DIR,
        process_zsh_wrapper_logic,
        execute_zsh_wrapper_action
    )
    
except ImportError as e:
    print(f"Lỗi: Không thể import utils/modules: {e}", file=sys.stderr)
    sys.exit(1)

# --- CONSTANTS ---
THIS_SCRIPT_PATH = Path(__file__).resolve()

# --- REMOVED: Typer App definition ---
# (Đã xóa app = typer.Typer(...))
# --- END REMOVED ---

# --- MODIFIED: Chuyển main thành hàm bình thường, không callback ---
def main(
    script_path: Path = typer.Argument(
        ..., 
        help="Đường dẫn đến file Python cần wrap.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True
    ),
    output: Optional[Path] = typer.Option(
        None, "-o", "--output", 
        help=f"Đường dẫn để tạo file wrapper Zsh. [Mặc định: {DEFAULT_WRAPPER_DIR}/{{tên_script}}]",
        resolve_path=True
    ),
    mode: str = typer.Option(
        DEFAULT_MODE, "-m", "--mode", 
        help="Loại wrapper: 'relative' (project di chuyển được) hoặc 'absolute' (wrapper di chuyển được)."
    ),
    root: Optional[Path] = typer.Option(
        None, "-r", "--root", 
        help="Chỉ định Project Root. Mặc định: tự động tìm (find_git_root() từ file script).",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True
    ),
    venv: str = typer.Option(
        DEFAULT_VENV, "-v", "--venv", 
        help="Tên thư mục virtual environment."
    ),
    force: bool = typer.Option(
        False, "-f", "--force", 
        help="Ghi đè file output nếu đã tồn tại."
    )
):
    """
    Tạo một wrapper Zsh cho một script Python, tự động quản lý venv và PYTHONPATH.
    """
    
    # 1. Setup Logging
    logger = setup_logging(script_name="Zrap")
    logger.debug("Zrap script started.")
    
    # --- 2. Xử lý output mặc định + Xác nhận (Logic không đổi) ---
    final_output_path = output

    if final_output_path is None:
        try:
            script_name_without_ext = script_path.stem
            default_output_path = PROJECT_ROOT / DEFAULT_WRAPPER_DIR / script_name_without_ext
            
            logger.warning("⚠️  Output path (-o) not specified.")
            logger.info(f"   Defaulting to: {default_output_path.relative_to(PROJECT_ROOT).as_posix()}")
            logger.info("   (You can use -o <path> to specify a custom name)")
            
            if not typer.confirm("   Proceed with this default path?", abort=True):
                pass 
            
            final_output_path = default_output_path
            
        except typer.Abort:
            logger.warning("Operation cancelled by user.")
            sys.exit(0)
        except EOFError:
             logger.warning("\nOperation cancelled by user (EOF).")
             sys.exit(1)
        except KeyboardInterrupt:
            print("\n\n❌ [Lệnh dừng] Hoạt động của tool đã bị dừng.")
            sys.exit(1)
    # --- END ---

    # --- 3. Tạo 'args' object giả lập cho core logic (Logic không đổi) ---
    args_for_core = argparse.Namespace(
        script_path=str(script_path),
        output=str(final_output_path.resolve()),
        mode=mode,
        root=str(root) if root else None,
        venv=venv,
        force=force
    )
    # --- END ---

    # 4. Execute Core Logic (Logic không đổi)
    try:
        result = process_zsh_wrapper_logic(
            logger=logger,
            args=args_for_core
        )
        
        if result:
            execute_zsh_wrapper_action(
                logger=logger,
                result=result
            )
        
        log_success(logger, "Hoàn thành.")
            
    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)
# --- END MODIFIED ---


if __name__ == "__main__":
    try:
        # --- MODIFIED: Chạy typer.run(main) ---
        typer.run(main)
        # --- END MODIFIED ---
    except KeyboardInterrupt:
        print("\n\n❌ [Lệnh dừng] Hoạt động của tool đã bị dừng.")
        sys.exit(1)