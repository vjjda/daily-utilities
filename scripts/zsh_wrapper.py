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
        # --- MODIFIED: Chỉ giữ lại các hằng số cần thiết ---
        process_zsh_wrapper_logic,
        execute_zsh_wrapper_action,
        # --- NEW: Import helpers ---
        resolve_output_path_interactively,
        resolve_root_interactively
        # --- END NEW ---
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
    output_arg: Optional[Path] = typer.Option( 
        None, "-o", "--output", 
        help="Đường dẫn tạo wrapper. [Mặc định: $HOME/bin (cho absolute) hoặc bin/ (cho relative)]. Use '~' for home directory.",
    ),
    mode: str = typer.Option(
        DEFAULT_MODE, "-m", "--mode", 
        help="Loại wrapper: 'relative' (project di chuyển được) hoặc 'absolute' (wrapper di chuyển được)."
    ),
    root_arg: Optional[Path] = typer.Option( 
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

    # --- 2. Mở rộng `~` thủ công cho tất cả Path & Validation ---
    # Cần expanduser cho các tham số Path
    script_path = script_path_arg.expanduser()
    output = output_arg.expanduser() if output_arg else None
    root = root_arg.expanduser() if root_arg else None
    
    # --- 3. Xử lý output mặc định + Xác nhận (via Helper) ---
    final_output_path: Path = resolve_output_path_interactively(
        logger=logger, 
        script_path=script_path, 
        output_arg=output, 
        mode=mode,
        project_root=PROJECT_ROOT 
    )
    # Helper sẽ tự động thoát nếu người dùng chọn 'Q'
    
    # --- 4. Tạo 'args' object giả lập cho core logic (Lần 1) ---
    args_for_core = argparse.Namespace(
        script_path=str(script_path), 
        output=str(final_output_path), 
        mode=mode,
        root=str(root) if root else None, 
        venv=venv,
        force=force
    )

    # 5. Execute Core Logic & Handle Fallback (Project Root S/I/Q - via Helper)
    try:
        result = process_zsh_wrapper_logic( logger=logger, args=args_for_core )

        # Logic xử lý Fallback Project Root (S/I/Q)
        if result and result.get("status") == "fallback_required":
            
            fallback_path: Path = result["fallback_path"]
            
            # --- NEW: Gọi helper cho tương tác root ---
            selected_root: Path = resolve_root_interactively(
                logger=logger,
                fallback_path=fallback_path
            )
            # Helper sẽ tự động thoát nếu người dùng chọn 'Q'
            
            # --- Tái xử lý với Root đã chọn ---
            args_for_core_2 = argparse.Namespace(
                script_path=str(result["script_path"]), 
                output=str(result["output_path"]),
                mode=result["mode"],
                root=str(selected_root), # <-- SỬ DỤNG ROOT MỚI ĐÃ CHỌN
                venv=result["venv"],
                force=result["force"]
            )
            
            result = process_zsh_wrapper_logic( logger=logger, args=args_for_core_2 )

        # 6. Execute Action (Chỉ chạy nếu status là 'ok')
        if result and result.get("status") == "ok": 
            execute_zsh_wrapper_action( logger=logger, result=result )
            log_success(logger, "Hoàn thành.")
        elif result and result.get("status") != "fallback_required":
             logger.error("❌ Core logic failed with unknown status.")
             sys.exit(1)
             
    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try: typer.run(main)
    except KeyboardInterrupt: print("\n\n❌ [Lệnh dừng] Hoạt động của tool đã bị dừng."); sys.exit(1)