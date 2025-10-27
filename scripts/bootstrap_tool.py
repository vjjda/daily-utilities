# Path: scripts/bootstrap_tool.py

"""
Script nội bộ để bootstrap (khởi tạo) một tool utility mới.
(Đã refactor để dùng module gateway 'bootstrap' theo SRP)
"""

import sys
import argparse
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

# --- (tomllib import đã bị XÓA, chuyển vào loader) ---

# --- MODIFIED: Cập nhật PROJECT_ROOT và sys.path ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))
# --- END MODIFIED ---

try:
    from utils.logging_config import setup_logging, log_success # type: ignore[reportUnknownVariableType]
    
    # --- MODIFIED: Import các hàm SRP từ 'modules.bootstrap' ---
    from modules.bootstrap import (
        # Configs
        DEFAULT_BIN_DIR_NAME,
        DEFAULT_SCRIPTS_DIR_NAME,
        DEFAULT_MODULES_DIR_NAME,
        DEFAULT_DOCS_DIR_NAME,
        
        # SRP Functions
        load_bootstrap_config,
        load_spec_file,
        process_bootstrap_logic,
        execute_bootstrap_action
    )
    # --- END MODIFIED ---
except ImportError as e:
    print(f"Lỗi: Không thể import utils hoặc bootstrap gateway: {e}", file=sys.stderr)
    sys.exit(1)

def main():
    """Hàm chính chạy script bootstrap"""
    
    logger = setup_logging(script_name="Bootstrap", console_level_str="INFO")
    logger.debug("Bootstrap script started.")
    
    # --- MODIFIED: Phân tích đối số ---
    parser = argparse.ArgumentParser(description="Bootstrap (khởi tạo) một tool utility mới từ file *.spec.toml.")
    parser.add_argument(
        "spec_file_path_str", 
        type=str, 
        help="Đường dẫn đầy đủ đến file *.spec.toml (ví dụ: docs/drafts/new_tool.spec.toml)."
    )
    
    # --- NEW: Thêm cờ --force ---
    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Ghi đè (overwrite) các file đã tồn tại nếu có."
    )
    # --- END NEW ---
    
    args = parser.parse_args()
    
    try:
        # --- 1. LOAD (Đọc I/O) ---
        
        # 1.1. Tải cấu hình đường dẫn dự án (từ .project.toml)
        toml_config = load_bootstrap_config(logger, PROJECT_ROOT)
        
        bin_dir_name = toml_config.get("bin_dir", DEFAULT_BIN_DIR_NAME)
        scripts_dir_name = toml_config.get("scripts_dir", DEFAULT_SCRIPTS_DIR_NAME)
        modules_dir_name = toml_config.get("modules_dir", DEFAULT_MODULES_DIR_NAME)
        docs_dir_name = toml_config.get("docs_dir", DEFAULT_DOCS_DIR_NAME)
        
        # Xây dựng các đường dẫn tuyệt đối
        configured_paths = {
            "BIN_DIR": PROJECT_ROOT / bin_dir_name,
            "SCRIPTS_DIR": PROJECT_ROOT / scripts_dir_name,
            "MODULES_DIR": PROJECT_ROOT / modules_dir_name,
            "DOCS_DIR": PROJECT_ROOT / docs_dir_name
        }
        logger.debug(f"Configured paths loaded: {configured_paths}")

        # 1.2. Tải file spec (từ CLI arg)
        spec_file_path = Path(args.spec_file_path_str).resolve()
        if not spec_file_path.is_file() or not spec_file_path.name.endswith(".spec.toml"):
            logger.error(f"❌ Lỗi: Đường dẫn cung cấp không phải là file *.spec.toml hợp lệ.")
            logger.error(f"   Đã nhận: {spec_file_path.as_posix()}")
            sys.exit(1)
            
        logger.info(f"🚀 Bắt đầu bootstrap:")
        try:
            spec_rel_path = spec_file_path.relative_to(PROJECT_ROOT).as_posix()
        except ValueError:
            spec_rel_path = spec_file_path.as_posix()
        logger.info(f"   File Spec: {spec_rel_path}")

        config_spec = load_spec_file(logger, spec_file_path)

        # --- 2. CORE (Logic thuần túy) ---
        
        # 2.1. Xử lý logic, tạo nội dung và đường dẫn
        (
            generated_content, 
            target_paths, 
            module_path
        ) = process_bootstrap_logic(
            logger=logger, 
            config=config_spec, 
            configured_paths=configured_paths
        )
        
        logger.info(f"   Thư mục Module: {module_path.relative_to(PROJECT_ROOT).as_posix()}")

        # --- 3. EXECUTOR (Ghi I/O) ---
        
        # 3.1. Thực hiện kiểm tra an toàn và ghi file
        execute_bootstrap_action(
            logger=logger,
            generated_content=generated_content,
            target_paths=target_paths,
            module_path=module_path,
            project_root=PROJECT_ROOT,
            force=args.force # <-- MODIFIED: Truyền cờ force
        )
        
        logger.info("\n✨ Bootstrap hoàn tất! Cấu trúc file cho tool mới đã sẵn sàng.")

    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn trong quá trình bootstrap: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()