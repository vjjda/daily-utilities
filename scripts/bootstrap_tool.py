# Path: scripts/bootstrap_tool.py

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

# --- MODIFIED: Cập nhật PROJECT_ROOT và sys.path ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))
# --- END MODIFIED ---

try:
    from utils.logging_config import setup_logging, log_success # type: ignore[reportUnknownVariableType]
    
    # --- MODIFIED: Import từ 'modules.bootstrap' ---
    from utils.core import load_project_config_section # type: ignore[reportUnknownVariableType]
    
    from modules.bootstrap import (
        generate_bin_wrapper,
        generate_script_entrypoint,
        generate_module_file,
        generate_doc_file,
        generate_module_init_file,
        
        # Import các hằng số config mới
        CONFIG_SECTION_NAME,
        DEFAULT_BIN_DIR_NAME,
        DEFAULT_SCRIPTS_DIR_NAME,
        DEFAULT_MODULES_DIR_NAME,
        DEFAULT_DOCS_DIR_NAME
    )
    # --- END MODIFIED ---
except ImportError as e:
    print(f"Lỗi: Không thể import utils hoặc bootstrap gateway: {e}", file=sys.stderr)
    sys.exit(1)

# --- (Hàm main giữ nguyên, không cần thay đổi logic bên trong) ---
def main():
    """Hàm chính chạy script bootstrap"""
    
    logger = setup_logging(script_name="Bootstrap", console_level_str="INFO")
    logger.debug("Bootstrap script started.")
    
    # --- (Load Configurable Paths giữ nguyên) ---
    config_path = PROJECT_ROOT / ".project.toml"
    toml_config = load_project_config_section(config_path, CONFIG_SECTION_NAME, logger)
    
    bin_dir_name = toml_config.get("bin_dir", DEFAULT_BIN_DIR_NAME)
    scripts_dir_name = toml_config.get("scripts_dir", DEFAULT_SCRIPTS_DIR_NAME)
    modules_dir_name = toml_config.get("modules_dir", DEFAULT_MODULES_DIR_NAME)
    docs_dir_name = toml_config.get("docs_dir", DEFAULT_DOCS_DIR_NAME)
    
    BIN_DIR = PROJECT_ROOT / bin_dir_name
    SCRIPTS_DIR = PROJECT_ROOT / scripts_dir_name
    MODULES_DIR = PROJECT_ROOT / modules_dir_name
    DOCS_DIR = PROJECT_ROOT / docs_dir_name
    
    logger.debug(f"BIN_DIR set to: {BIN_DIR.as_posix()}")
    logger.debug(f"SCRIPTS_DIR set to: {SCRIPTS_DIR.as_posix()}")

    # --- MODIFIED: Phân tích đối số ---
    parser = argparse.ArgumentParser(description="Bootstrap (khởi tạo) một tool utility mới từ file *.spec.toml.")
    parser.add_argument(
        "spec_file_path_str", 
        type=str, 
        help="Đường dẫn đầy đủ đến file *.spec.toml (ví dụ: docs/drafts/new_tool.spec.toml)."
    )
    args = parser.parse_args()
    # --- END MODIFIED ---

    # --- MODIFIED: Load và xác thực đường dẫn ---
    spec_file_path = Path(args.spec_file_path_str).resolve()

    if not spec_file_path.is_file() or not spec_file_path.name.endswith(".spec.toml"):
        logger.error(f"❌ Lỗi: Đường dẫn cung cấp không phải là file *.spec.toml hợp lệ.")
        logger.error(f"   Đã nhận: {spec_file_path.as_posix()}")
        sys.exit(1)
        
    logger.info(f"🚀 Bắt đầu bootstrap:")
    try:
        spec_rel_path = spec_file_path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        spec_rel_path = spec_file_path.as_posix() # Nếu file spec nằm ngoài project
    logger.info(f"   File Spec: {spec_rel_path}")
    # --- END MODIFIED ---

    # --- (Load TOML giữ nguyên) ---
    try:
        with open(spec_file_path, 'rb') as f:
            config = tomllib.load(f) # type: ignore[reportArgumentType]
    except Exception as e:
        logger.error(f"❌ Lỗi khi đọc file TOML: {e}")
        sys.exit(1)

    # --- MODIFIED: Xác thực config ---
    try:
        # Đọc các giá trị meta
        tool_name = config['meta']['tool_name']
        script_file = config['meta']['script_file']
        module_name = config['meta']['module_name']
        
        # Truyền module_name vào config dict để dùng trong generator
        config['module_name'] = module_name 
        
        logger.debug(f"Tool Name: {tool_name}")
        logger.debug(f"Script File: {script_file}")
        logger.debug(f"Module Name: {module_name}")
        
    except KeyError as e:
        logger.error(f"❌ File spec '{spec_file_path.name}' thiếu key bắt buộc trong [meta]: {e}")
        sys.exit(1)
    
    # Xác định đường dẫn module dựa trên config
    module_path = MODULES_DIR / module_name
    logger.info(f"   Thư mục Module: {module_path.relative_to(PROJECT_ROOT).as_posix()}")
    # --- END MODIFIED ---
        
    # --- (Tạo nội dung giữ nguyên) ---
    try:
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
        
        target_paths = {
            "bin": BIN_DIR / tool_name,
            "script": SCRIPTS_DIR / script_file,
            "config": module_path / f"{mod_name}_config.py",
            "loader": module_path / f"{mod_name}_loader.py", 
            "core": module_path / f"{mod_name}_core.py",
            "executor": module_path / f"{mod_name}_executor.py",
            "init": module_path / "__init__.py", 
        }
        
        if config.get('docs', {}).get('enabled', False):
            generated_content["docs"] = generate_doc_file(config)
            target_paths["docs"] = DOCS_DIR / "tools" / f"{tool_name}.md"

    except Exception as e:
        logger.error(f"❌ Lỗi nghiêm trọng khi tạo nội dung code: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)

    # --- MODIFIED: KIỂM TRA AN TOÀN ---
    # Kiểm tra thư mục module trước
    if module_path.exists():
        logger.error(f"❌ Dừng lại! Thư mục module sau đã tồn tại. Sẽ không ghi đè:")
        logger.error(f"   -> {module_path.relative_to(PROJECT_ROOT).as_posix()}")
        sys.exit(1)
        
    existing_files = [p for p in target_paths.values() if p.exists()]
    if existing_files:
        logger.error(f"❌ Dừng lại! Các file sau đã tồn tại. Sẽ không ghi đè:")
        for p in existing_files:
            logger.error(f"   -> {p.relative_to(PROJECT_ROOT).as_posix()}")
        sys.exit(1)
    # --- END MODIFIED ---

    # --- MODIFIED: GHI FILE (I/O) ---
    try:
        # Tạo thư mục module trước
        module_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Đã tạo thư mục: {module_path.relative_to(PROJECT_ROOT).as_posix()}")
            
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
    # --- END MODIFIED ---
        
    logger.info("\n✨ Bootstrap hoàn tất! Cấu trúc file cho tool mới đã sẵn sàng.")

if __name__ == "__main__":
    main()