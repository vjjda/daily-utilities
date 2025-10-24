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
        DEFAULT_WRAPPER_DIR,
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
        # exists=True, # <-- Sẽ check thủ công
        file_okay=True,
        dir_okay=False,
        # --- FIX: Đã xóa resolve_path=True ---
        # resolve_path=True,
        # --- END FIX ---
    ),
    output_arg: Optional[Path] = typer.Option( # <-- Đổi tên biến tạm thời
        None, "-o", "--output", 
        help=f"Đường dẫn để tạo file wrapper Zsh. [Mặc định: {DEFAULT_WRAPPER_DIR}/{{tên_script}}]. Use '~' for home directory.",
        # --- FIX: Đã xóa resolve_path=True ---
        # resolve_path=True,
        # --- END FIX ---
    ),
    mode: str = typer.Option(
        DEFAULT_MODE, "-m", "--mode", 
        help="Loại wrapper: 'relative' (project di chuyển được) hoặc 'absolute' (wrapper di chuyển được)."
    ),
    root_arg: Optional[Path] = typer.Option( # <-- Đổi tên biến tạm thời
        None, "-r", "--root", 
        help="Chỉ định Project Root. Mặc định: tự động tìm (find_git_root() từ file script). Use '~' for home directory.",
        # exists=True, # <-- Sẽ check thủ công
        file_okay=False,
        dir_okay=True,
        # --- FIX: Đã xóa resolve_path=True ---
        # resolve_path=True,
        # --- END FIX ---
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
            default_output_path = PROJECT_ROOT / DEFAULT_WRAPPER_DIR / script_name_without_ext
            logger.warning("⚠️  Output path (-o) not specified.")
            logger.info(f"   Defaulting to: {default_output_path.relative_to(PROJECT_ROOT).as_posix()}")
            logger.info("   (You can use -o <path> to specify a custom name)")