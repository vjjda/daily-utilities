#!/usr/bin/env python3
# Path: scripts/zsh_wrapper.py

import sys
import argparse 
import logging
from pathlib import Path
from typing import Optional

import typer

# --- Thêm PROJECT_ROOT vào sys.path để import utils/modules ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from utils.logging_config import setup_logging, log_success
    
    from modules.zsh_wrapper import (
        DEFAULT_MODE, 
        DEFAULT_VENV, 
        # --- MODIFIED: Import hằng số mới ---
        DEFAULT_WRAPPER_RELATIVE_DIR,
        DEFAULT_WRAPPER_ABSOLUTE_PATH,
        # --- END MODIFIED ---
        process_zsh_wrapper_logic,
        execute_zsh_wrapper_action
    )
    
except ImportError as e:
    print(f"Lỗi: Không thể import utils/modules: {e}", file=sys.stderr)
    sys.exit(1)

# --- CONSTANTS ---
THIS_SCRIPT_PATH = Path(__file__).resolve()


def main(
    script_path_arg: Path = typer.Argument( 
        ..., 
        help="Đường dẫn đến file Python cần wrap. Use '~' for home directory.",
        file_okay=True,
        dir_okay=False,
    ),
    output_arg: Optional[Path] = typer.Option( # <-- Đổi tên biến tạm thời
        None, "-o", "--output", 
        help="Đường dẫn tạo wrapper. [Mặc định: $HOME/bin (cho absolute) hoặc bin/ (cho relative)]. Use '~' for home directory.",
    ),
    mode: str = typer.Option(
        DEFAULT_MODE, "-m", "--mode", 
        help="Loại wrapper: 'relative' (project di chuyển được) hoặc 'absolute' (wrapper di chuyển được)."
    ),
    root_arg: Optional[Path] = typer.Option( # <-- Đổi tên biến tạm thời
        None, "-r", "--root", 
        help="Chỉ định Project Root. Mặc định: tự động tìm (find_git_root() từ file script). Use '~' for home directory.",
        exists=True,
        file_okay=False,
        dir_okay=True,
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
    
    # --- 1. Setup Logging (sớm) ---
    logger = setup_logging(script_name="Zrap")
    logger.debug("Zrap script started.")

    # --- 2. Mở rộng `~` thủ công cho tất cả Path ---
    script_path = script_path_arg.expanduser()
    output = output_arg.expanduser() if output_arg else None
    root = root_arg.expanduser() if root_arg else None
    # --- END ---

    # --- 3. KIỂM TRA TỒN TẠI (thủ công) ---
    if not script_path.exists():
        logger.error(f"❌ Lỗi: File script không tồn tại (sau khi expanduser): {script_path}")
        raise typer.Exit(code=1)
    if not script_path.is_file():
        logger.error(f"❌ Lỗi: Đường dẫn script không phải là file: {script_path}")
        raise typer.Exit(code=1)
        
    if root and not root.exists():
        logger.error(f"❌ Lỗi: Thư mục root chỉ định không tồn tại (sau khi expanduser): {root}")
        raise typer.Exit(code=1)
    if root and not root.is_dir():
        logger.error(f"❌ Lỗi: Đường dẫn root không phải là thư mục: {root}")
        raise typer.Exit(code=1)
    # --- KẾT THÚC KIỂM TRA ---

    
    # --- 4. Xử lý output mặc định + Xác nhận ---
    final_output_path = output # Sử dụng biến đã expand
    if final_output_path is None:
        try:
            script_name_without_ext = script_path.stem
            
            # --- MODIFIED: Logic mặc định dựa trên config ---
            default_output_path: Path
            if mode == "absolute":
                # Mặc định cho 'absolute' từ config
                default_output_path = DEFAULT_WRAPPER_ABSOLUTE_PATH / script_name_without_ext
                logger.warning(f"⚠️  Output path (-o) not specified for 'absolute' mode.")
                logger.info(f"   Defaulting to: {default_output_path.as_posix()}")
            else:
                # Mặc định cho 'relative' từ config
                default_output_path = PROJECT_ROOT / DEFAULT_WRAPPER_RELATIVE_DIR / script_name_without_ext
                logger.warning("⚠️  Output path (-o) not specified.")
                logger.info(f"   Defaulting to: {default_output_path.relative_to(PROJECT_ROOT).as_posix()}")
            # --- END MODIFIED ---

            logger.info("   (You can use -o <path> to specify a custom name)")
            if not typer.confirm("   Proceed with this default path?", abort=True): pass 
            final_output_path = default_output_path
        except typer.Abort: logger.warning("Operation cancelled by user."); sys.exit(0)
        except EOFError: logger.warning("\nOperation cancelled by user (EOF)."); sys.exit(1)
        except KeyboardInterrupt: print("\n\n❌ [Lệnh dừng] Hoạt động của tool đã bị dừng."); sys.exit(1)
    # --- END ---

    # --- 5. Tạo 'args' object giả lập cho core logic ---
    args_for_core = argparse.Namespace(
        script_path=str(script_path), 
        output=str(final_output_path), # Sử dụng biến đã expand/default 
        mode=mode,
        root=str(root) if root else None, # Sử dụng biến đã expand
        venv=venv,
        force=force
    )
    # --- END ---

    # 6. Execute Core Logic 
    try:
        result = process_zsh_wrapper_logic( logger=logger, args=args_for_core )
        if result: execute_zsh_wrapper_action( logger=logger, result=result )
        log_success(logger, "Hoàn thành.")
    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try: typer.run(main)
    except KeyboardInterrupt: print("\n\n❌ [Lệnh dừng] Hoạt động của tool đã bị dừng."); sys.exit(1)