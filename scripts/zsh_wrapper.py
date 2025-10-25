# Path: scripts/zsh_wrapper.py
import sys
import argparse 
import logging
from pathlib import Path
from typing import Optional

import typer

# --- 1. Tự xác định Project Root của tool (daily-utilities) để import ---
# PROJECT_ROOT sẽ là thư mục cha của thư mục scripts.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from utils.logging_config import setup_logging, log_success
    
    from modules.zsh_wrapper import (
        DEFAULT_MODE, 
        DEFAULT_VENV, 
        process_zsh_wrapper_logic,
        execute_zsh_wrapper_action,
        # Import helpers cho logic tương tác
        resolve_output_path_interactively,
        resolve_root_interactively
    )
    
except ImportError as e:
    print(f"Lỗi: Không thể import utils/modules. Đảm bảo bạn đang chạy từ Project Root: {e}", file=sys.stderr)
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
        help="Đường dẫn tạo wrapper. [Mặc định: bin/ (cho relative) hoặc $HOME/bin (cho absolute)]. Use '~' for home directory.",
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
    
    # --- 1. Setup Logging & Initial Path Expansion ---
    logger = setup_logging(script_name="Zrap")
    logger.debug("Zrap script started.")

    # Mở rộng `~` cho tất cả Path
    script_path = script_path_arg.expanduser()
    output = output_arg.expanduser() if output_arg else None
    root = root_arg.expanduser() if root_arg else None
    
    # --- 2. TẠO args Lần 1 (Root Determination) ---
    # Chạy Core Logic lần 1 với output=None chỉ để xác định Project Root/Fallback.
    args_for_core_temp = argparse.Namespace(
        script_path=str(script_path), 
        output=None, # Tạm thời là None
        mode=mode,
        root=str(root) if root else None, 
        venv=venv,
        force=force
    )

    # --- 3. XÁC ĐỊNH & XỬ LÝ PROJECT ROOT (BƯỚC ƯU TIÊN) ---
    final_root: Path
    temp_result = process_zsh_wrapper_logic( logger=logger, args=args_for_core_temp )
    
    if temp_result and temp_result.get("status") == "fallback_required":
        # Cần tương tác để xác định Project Root (S/I/Q)
        fallback_path: Path = temp_result["fallback_path"]
        final_root = resolve_root_interactively(
            logger=logger,
            fallback_path=fallback_path
        )
        # resolve_root_interactively sẽ tự động thoát nếu người dùng chọn 'Q'
    elif temp_result and temp_result.get("status") == "ok":
        # Project Root đã được tìm thấy (hoặc chỉ định) trong lần chạy Core 1
        final_root = temp_result["project_root_abs"] 
    else:
        # Xảy ra lỗi nghiêm trọng khác (Core Logic đã log)
        raise typer.Exit(code=1)
        
    logger.info(f"Root đã xác định cuối cùng: {final_root.as_posix()}")

    # --- 4. XỬ LÝ OUTPUT PATH (Sử dụng final_root đã xác định) ---
    # Logic S/I/Q cho Output Path (-o)
    final_output_path: Path = resolve_output_path_interactively(
        logger=logger, 
        script_path=script_path, 
        output_arg=output, 
        mode=mode,
        project_root=final_root # TRUYỀN ROOT ĐÃ XÁC ĐỊNH CHO HELPER
    )
    # resolve_output_path_interactively sẽ tự động thoát nếu người dùng chọn 'Q'
    
    # --- 5. TẠO args & CHẠY CORE LẦN CUỐI (Tạo wrapper) ---
    args_for_core_final = argparse.Namespace(
        script_path=str(script_path), 
        output=str(final_output_path), 
        mode=mode,
        root=str(final_root), # LUÔN CÓ GIÁ TRỊ TƯỜNG MINH
        venv=venv,
        force=force
    )
    
    # Chạy Core Logic lần cuối để tạo nội dung wrapper
    result = process_zsh_wrapper_logic( logger=logger, args=args_for_core_final )
    
    # --- 6. Execute Action ---
    if result and result.get("status") == "ok": 
        execute_zsh_wrapper_action( logger=logger, result=result )
        log_success(logger, "Hoàn thành.")
    elif result:
         # Log lỗi cuối cùng nếu Core Logic không trả về 'ok'
         logger.error("❌ Core logic failed during final execution.")
         sys.exit(1)
         
    # Nếu result là None, có thể Core Logic đã tự thoát hoặc lỗi nghiêm trọng
    else:
        sys.exit(1)


if __name__ == "__main__":
    try: 
        typer.run(main)
    except KeyboardInterrupt: 
        print("\n\n❌ [Lệnh dừng] Hoạt động của tool đã bị dừng bởi người dùng (Ctrl+C).")
        sys.exit(1)
    except typer.Exit:
        # Bắt ngoại lệ Exit từ helper (khi người dùng chọn 'Q')
        sys.exit(0)