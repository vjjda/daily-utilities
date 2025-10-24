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
        DEFAULT_WRAPPER_RELATIVE_DIR,
        DEFAULT_WRAPPER_ABSOLUTE_PATH,
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

    
    # --- 4. Xử lý output mặc định + Xác nhận (MODIFIED to S/I/Q) ---
    final_output_path: Optional[Path] = output
    if final_output_path is None:
        
        script_name_without_ext = script_path.stem
        
        default_output_path: Path
        # Tính toán đường dẫn mặc định
        if mode == "absolute":
            default_output_path = DEFAULT_WRAPPER_ABSOLUTE_PATH / script_name_without_ext
            logger.warning(f"⚠️  Output path (-o) not specified for 'absolute' mode.")
        else:
            default_output_path = PROJECT_ROOT / DEFAULT_WRAPPER_RELATIVE_DIR / script_name_without_ext
            logger.warning("⚠️  Output path (-o) not specified.")

        
        # --- NEW S/I/Q selection logic for Output Path ---
        selected_output: Optional[Path] = None
        
        logger.warning(f"\n⚠️ Output Path (-o) was not specified.")
        logger.warning(f"   Please select the destination for the Zsh wrapper:")
        
        while selected_output is None:
            # 1. Hiển thị các lựa chọn
            print(f"     [S] Use Suggested Path: {default_output_path.as_posix()}")
            print("     [I] Input Custom Path")
            print("     [Q] Quit / Cancel")

            try:
                # Chấp nhận S, I, Q (case-insensitive)
                choice = input("   Enter your choice (S/I/Q): ").lower().strip()
            except (EOFError, KeyboardInterrupt):
                choice = 'q'
            
            if choice == 's':
                selected_output = default_output_path
                logger.info(f"✅ Option [S] selected. Using suggested path: {selected_output.as_posix()}")
                
            elif choice == 'i':
                while True:
                    try:
                        # Chờ input đường dẫn tùy chỉnh
                        custom_path_str = input("   Enter custom Output path (absolute or relative): ").strip()
                        if not custom_path_str:
                            print("   Lỗi: Đường dẫn không được để trống.")
                            continue

                        # Mở rộng user path và resolve tuyệt đối
                        custom_path = Path(custom_path_str).expanduser().resolve()
                        
                        # Kiểm tra thư mục cha có tồn tại không và là thư mục
                        parent_dir = custom_path.parent
                        if not parent_dir.exists():
                            logger.error(f"❌ Lỗi: Thư mục cha của đường dẫn Output không tồn tại: {parent_dir.as_posix()}")
                            continue
                        if not parent_dir.is_dir():
                            logger.error(f"❌ Lỗi: Đường dẫn cha không phải là thư mục: {parent_dir.as_posix()}")
                            continue

                        selected_output = custom_path
                        logger.info(f"✅ Option [I] selected. Using custom path: {selected_output.as_posix()}")
                        break
                    except Exception as e:
                        logger.error(f"❌ Lỗi khi xử lý đường dẫn: {e}")
                        
            elif choice == 'q':
                logger.error("❌ Operation cancelled by user.")
                sys.exit(0) 
                
            else:
                print("   Lựa chọn không hợp lệ. Vui lòng nhập S, I, hoặc Q.")
                
        final_output_path = selected_output
        if final_output_path is None: 
            logger.error("❌ Output path was not set due to unexpected error.")
            sys.exit(1)
    # --- END Xử lý output mặc định + Xác nhận ---

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

    # 6. Execute Core Logic & Handle Fallback (Project Root S/I/Q - Giữ nguyên)
    try:
        result = process_zsh_wrapper_logic( logger=logger, args=args_for_core )

        # Logic xử lý Fallback Project Root (S/I/Q)
        if result and result.get("status") == "fallback_required":
            
            fallback_path: Path = result["fallback_path"]
            selected_root: Optional[Path] = None

            logger.warning(f"\n⚠️ Project Root (Git Root) was not found automatically.")
            logger.warning(f"   Please select the Project Root for this wrapper:")
            
            while selected_root is None:
                # 1. Hiển thị các lựa chọn
                print(f"     [S] Use Suggested Root: {fallback_path.as_posix()} (Script Parent Directory)")
                print("     [I] Input Custom Path")
                print("     [Q] Quit / Cancel")

                try:
                    choice = input("   Enter your choice (S/I/Q): ").lower().strip()
                except (EOFError, KeyboardInterrupt):
                    choice = 'q'
                
                if choice == 's':
                    selected_root = fallback_path
                    logger.info(f"✅ Option [S] selected. Using suggested root.")
                    
                elif choice == 'i':
                    while True:
                        try:
                            custom_path_str = input("   Enter custom Project Root path (absolute or relative): ").strip()
                            if not custom_path_str:
                                print("   Lỗi: Đường dẫn không được để trống.")
                                continue

                            custom_path = Path(custom_path_str).expanduser().resolve()

                            if not custom_path.exists() or not custom_path.is_dir():
                                logger.error(f"❌ Lỗi: Đường dẫn nhập không tồn tại hoặc không phải là thư mục: {custom_path.as_posix()}")
                                continue
                            
                            selected_root = custom_path
                            logger.info(f"✅ Option [I] selected. Using custom root: {selected_root.as_posix()}")
                            break
                        except Exception as e:
                            logger.error(f"❌ Lỗi khi xử lý đường dẫn: {e}")
                            
                elif choice == 'q':
                    logger.error("❌ Operation cancelled by user.")
                    sys.exit(0) 
                    
                else:
                    print("   Lựa chọn không hợp lệ. Vui lòng nhập S, I, hoặc Q.")
            
            # --- Tái xử lý với Root đã chọn ---
            if selected_root:
                args_for_core = argparse.Namespace(
                    script_path=str(result["script_path"]), 
                    output=str(result["output_path"]),
                    mode=result["mode"],
                    root=str(selected_root),
                    venv=result["venv"],
                    force=result["force"]
                )
                
                result = process_zsh_wrapper_logic( logger=logger, args=args_for_core )
            else:
                 logger.error("❌ Operation cancelled or selection failed unexpectedly.")
                 sys.exit(1)
        # --- END Project Root Fallback ---

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