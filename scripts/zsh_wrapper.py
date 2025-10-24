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
    # --- 1. Setup Logging (sớm) ---
    logger = setup_logging(script_name="Zrap")
    logger.debug("Zrap script started.")

    # --- 2. Mở rộng `~` thủ công cho tất cả Path ---
    script_path = script_path_arg.expanduser()
    output = output_arg.expanduser() if output_arg else None
    root = root_arg.expanduser() if root_arg else None
    # --- END ---

    # --- 3. KIỂM TRA TỒN TẠI (thủ công) (Giữ nguyên) ---
    if not script_path.exists():
        logger.error(f"❌ Lỗi: File script không tồn tại (sau khi expanduser): {script_path}")
        raise typer.Exit(code=1)
    if not script_path.is_file():
        logger.error(f"❌ Lỗi: Đường dẫn script không phải là file: {script_path}")
        raise typer.Exit(code=1)
    # ... (Kiểm tra root giữ nguyên) ...
    if root and not root.is_dir():
        logger.error(f"❌ Lỗi: Đường dẫn root không phải là thư mục: {root}")
        raise typer.Exit(code=1)
    # --- KẾT THÚC KIỂM TRA ---

    
    # --- 4. Xử lý output mặc định + Xác nhận (Giữ nguyên) ---
    final_output_path = output
    if final_output_path is None:
        try:
            script_name_without_ext = script_path.stem
            
            default_output_path: Path
            if mode == "absolute":
                default_output_path = DEFAULT_WRAPPER_ABSOLUTE_PATH / script_name_without_ext
                logger.warning(f"⚠️  Output path (-o) not specified for 'absolute' mode.")
                logger.info(f"   Defaulting to: {default_output_path.as_posix()}")
            else:
                default_output_path = PROJECT_ROOT / DEFAULT_WRAPPER_RELATIVE_DIR / script_name_without_ext
                logger.warning("⚠️  Output path (-o) not specified.")
                logger.info(f"   Defaulting to: {default_output_path.relative_to(PROJECT_ROOT).as_posix()}")

            logger.info("   (You can use -o <path> to specify a custom name)")
            if not typer.confirm("   Proceed with this default path?", abort=True): pass 
            final_output_path = default_output_path
        except typer.Abort: logger.warning("Operation cancelled by user."); sys.exit(0)
        except EOFError: logger.warning("\nOperation cancelled by user (EOF)."); sys.exit(1)
        except KeyboardInterrupt: print("\n\n❌ [Lệnh dừng] Hoạt động của tool đã bị dừng."); sys.exit(1)
    # --- END ---

    # --- 5. Tạo 'args' object giả lập cho core logic (Lần 1) ---
    args_for_core = argparse.Namespace(
        script_path=str(script_path), 
        output=str(final_output_path),
        mode=mode,
        root=str(root) if root else None,
        venv=venv,
        force=force
    )
    # --- END ---

    # 6. Execute Core Logic & Handle Fallback (MODIFIED)
    try:
        result = process_zsh_wrapper_logic( logger=logger, args=args_for_core )

        # --- NEW: Logic xử lý Fallback (3 Lựa chọn) ---
        if result and result.get("status") == "fallback_required":
            
            fallback_path: Path = result["fallback_path"]
            selected_root: Optional[Path] = None

            logger.warning(f"\n⚠️ Project Root (Git Root) was not found automatically.")
            logger.warning(f"   Please select the Project Root for this wrapper:")
            
            while selected_root is None:
                # 1. Hiển thị các lựa chọn
                print(f"     [1] Use Suggested Root: {fallback_path.as_posix()} (Script Parent Directory)")
                print("     [2] Input Custom Path")
                print("     [Q] Quit / Cancel")

                try:
                    choice = input("   Enter your choice (1/2/Q): ").lower().strip()
                except (EOFError, KeyboardInterrupt):
                    choice = 'q'
                
                if choice == '1':
                    selected_root = fallback_path
                    logger.info(f"✅ Option 1 selected. Using suggested root.")
                    
                elif choice == '2':
                    while True:
                        try:
                            # Chờ input đường dẫn tùy chỉnh
                            custom_path_str = input("   Enter custom Project Root path (absolute or relative): ").strip()
                            if not custom_path_str:
                                print("   Lỗi: Đường dẫn không được để trống.")
                                continue

                            # Mở rộng user path và resolve tuyệt đối
                            custom_path = Path(custom_path_str).expanduser().resolve()

                            if not custom_path.exists() or not custom_path.is_dir():
                                logger.error(f"❌ Lỗi: Đường dẫn nhập không tồn tại hoặc không phải là thư mục: {custom_path.as_posix()}")
                                continue
                            
                            selected_root = custom_path
                            logger.info(f"✅ Option 2 selected. Using custom root: {selected_root.as_posix()}")
                            break
                        except Exception as e:
                            logger.error(f"❌ Lỗi khi xử lý đường dẫn: {e}")
                            
                elif choice == 'q':
                    logger.error("❌ Operation cancelled by user.")
                    sys.exit(0) 
                    
                else:
                    print("   Lựa chọn không hợp lệ. Vui lòng nhập 1, 2, hoặc Q.")
            
            # --- Tái xử lý với Root đã chọn ---
            if selected_root:
                # Tạo một args mới, đặt root tường minh để bỏ qua tìm kiếm Git
                args_for_core = argparse.Namespace(
                    script_path=str(result["script_path"]), 
                    output=str(result["output_path"]),
                    mode=result["mode"],
                    root=str(selected_root), # <-- Ghi đè root tường minh
                    venv=result["venv"],
                    force=result["force"]
                )
                
                # Chạy lại core logic lần 2
                result = process_zsh_wrapper_logic( logger=logger, args=args_for_core )
            else:
                 logger.error("❌ Operation cancelled or selection failed unexpectedly.")
                 sys.exit(1)
        # --- END NEW ---

        # 7. Execute Action (Chỉ chạy nếu status là 'ok')
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