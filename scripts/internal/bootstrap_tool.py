# Path: scripts/internal/bootstrap_tool.py

"""
Script nội bộ để bootstrap (khởi tạo) một tool utility mới.
(Đã refactor để dùng module gateway 'bootstrap')
"""

import sys
import argparse
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

# --- (tomllib import giữ nguyên) ---
try:
    import tomllib
except ImportError:
    try:
        import toml as tomllib
    except ImportError:
        print("Lỗi: Cần gói 'toml'. Chạy 'pip install toml' (cho Python < 3.11)", file=sys.stderr)
        sys.exit(1)

# --- (sys.path import giữ nguyên) ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from utils.logging_config import setup_logging, log_success # type: ignore[reportUnknownVariableType]
    
    # --- (Import gateway giữ nguyên) ---
    from scripts.internal.bootstrap import (
        generate_bin_wrapper,
        generate_script_entrypoint,
        generate_module_file,
        generate_doc_file,
        generate_module_init_file
    )
except ImportError as e:
    print(f"Lỗi: Không thể import utils hoặc bootstrap gateway: {e}", file=sys.stderr)
    sys.exit(1)

# --- (Định nghĩa thư mục giữ nguyên) ---
BIN_DIR = PROJECT_ROOT / "bin"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
MODULES_DIR = PROJECT_ROOT / "modules"
DOCS_DIR = PROJECT_ROOT / "docs"

# --- HÀM MAIN (ĐIỀU PHỐI) ---
def main():
    """Hàm chính chạy script bootstrap"""
    
    logger = setup_logging(script_name="Bootstrap", console_level_str="INFO")
    logger.debug("Bootstrap script started.")

    # --- (1. Phân tích đối số giữ nguyên) ---
    parser = argparse.ArgumentParser(description="Bootstrap (khởi tạo) một tool utility mới từ file *.spec.toml.")
    parser.add_argument(
        "target_path_str", 
        type=str, 
        help="Đường dẫn đến thư mục module MỚI (modules/new) HOẶC file .spec.toml (modules/new/new.spec.toml)."
    )
    args = parser.parse_args()

    # --- (2. Load và xác thực đường dẫn giữ nguyên) ---
    target_path = Path(args.target_path_str).resolve()
    module_path: Optional[Path] = None
    spec_file_path: Optional[Path] = None

    if target_path.is_dir():
        module_path = target_path
        try:
            spec_file_path = next(module_path.glob("*.spec.toml"))
            logger.debug(f"Phát hiện mode thư mục. Đã tìm thấy file spec: {spec_file_path.name}")
        except StopIteration:
            logger.error(f"❌ Không tìm thấy file *.spec.toml nào trong thư mục:")
            logger.error(f"   {module_path.as_posix()}")
            sys.exit(1)
            
    elif target_path.is_file():
        if target_path.name.endswith(".spec.toml"):
            module_path = target_path.parent
            spec_file_path = target_path
            logger.debug(f"Phát hiện mode file. Sử dụng file spec: {spec_file_path.name}")
        else:
            logger.error("❌ Lỗi: Bạn đã cung cấp một file, nhưng nó không phải là file *.spec.toml.")
            sys.exit(1)
            
    else:
        module_path = target_path
        spec_file_path = module_path / "tool.spec.toml" # Mặc định cho tool mới
        logger.warning(f"Đường dẫn '{module_path.name}' không tồn tại. Giả định đây là module mới.")

    # ... (log info giữ nguyên) ...
    logger.info(f"🚀 Bắt đầu bootstrap:")
    logger.info(f"   Thư mục Module: {module_path.relative_to(PROJECT_ROOT).as_posix()}")
    logger.info(f"   File Spec:      {spec_file_path.name}")

    if not module_path.is_dir():
        logger.warning(f"Thư mục module '{module_path.name}' chưa tồn tại. Đang tạo...")
        module_path.mkdir(parents=True, exist_ok=True)
    
    if not spec_file_path.exists():
        logger.error(f"❌ Không tìm thấy file spec: {spec_file_path.name}")
        # ... (log error giữ nguyên) ...
        sys.exit(1)

    # --- (3. Load TOML giữ nguyên) ---
    try:
        with open(spec_file_path, 'rb') as f:
            config = tomllib.load(f) # type: ignore[reportArgumentType]
    except Exception as e:
        logger.error(f"❌ Lỗi khi đọc file TOML: {e}")
        sys.exit(1)

    # --- 4. Xác thực config và chuẩn bị dữ liệu (Đã Hoàn tác) ---
    try:
        config['module_name'] = module_path.name # (ví dụ: 'c_demo')
        
        # --- (Đã xóa logic tạo 'python_module_name') ---
        
        tool_name = config['meta']['tool_name']
        script_file = config['meta']['script_file']
        
        logger.debug(f"Tool Name: {tool_name}")
        logger.debug(f"Module Name: {config['module_name']}")
        
    except KeyError as e:
        logger.error(f"❌ File spec '{spec_file_path.name}' thiếu key bắt buộc trong [meta]: {e}")
        sys.exit(1)
        
    # --- 5. Tạo nội dung (gọi generator) (Đã Hoàn tác) ---
    try:
        # (Lấy tên module gốc)
        mod_name = config['module_name']
        
        generated_content = {
            "bin": generate_bin_wrapper(config),
            "script": generate_script_entrypoint(config),
            "config": generate_module_file(config, "config"),
            "loader": generate_module_file(config, "loader"), 
            "core": generate_module_file(config, "core"),
            "executor": generate_module_file(config, "executor"),
            "init": generate_module_init_file(config), 
        }
        
        # --- MODIFIED: Hoàn tác, dùng 'mod_name' ---
        target_paths = {
            "bin": BIN_DIR / tool_name,
            "script": SCRIPTS_DIR / script_file,
            "config": module_path / f"{mod_name}_config.py",
            "loader": module_path / f"{mod_name}_loader.py", 
            "core": module_path / f"{mod_name}_core.py",
            "executor": module_path / f"{mod_name}_executor.py",
            "init": module_path / "__init__.py", 
        }
        # --- END MODIFIED ---
        
        if config.get('docs', {}).get('enabled', False):
            generated_content["docs"] = generate_doc_file(config)
            target_paths["docs"] = DOCS_DIR / "tools" / f"{tool_name}.md"

    except Exception as e:
        logger.error(f"❌ Lỗi nghiêm trọng khi tạo nội dung code: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)

    # --- (6. KIỂM TRA AN TOÀN giữ nguyên) ---
    existing_files = [p for p in target_paths.values() if p.exists()]
    if existing_files:
        logger.error(f"❌ Dừng lại! Các file sau đã tồn tại. Sẽ không ghi đè:")
        for p in existing_files:
            logger.error(f"   -> {p.relative_to(PROJECT_ROOT).as_posix()}")
        sys.exit(1)

    # --- (7. GHI FILE (I/O) giữ nguyên) ---
    try:
        for key, path in target_paths.items():
            content = generated_content[key]
            path.parent.mkdir(parents=True, exist_ok=True) 
            path.write_text(content, encoding='utf-8')
            
            relative_path = path.relative_to(PROJECT_ROOT).as_posix()
            log_success(logger, f"Đã tạo: {relative_path}")

            if key == "bin":
                os.chmod(path, 0o755) # Cấp quyền thực thi
                logger.info(f"   -> Đã cấp quyền executable (chmod +x)")
            
    except IOError as e:
        logger.error(f"❌ Lỗi I/O khi ghi file: {e}")
        sys.exit(1)
        
    logger.info("\n✨ Bootstrap hoàn tất! Cấu trúc file cho tool mới đã sẵn sàng.")

if __name__ == "__main__":
    main()