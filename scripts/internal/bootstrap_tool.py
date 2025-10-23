#!/usr/bin/env python3
# Path: scripts/internal/bootstrap_tool.py

"""
Script nội bộ để bootstrap (khởi tạo) một tool utility mới.

File này chỉ làm nhiệm vụ "điều phối":
1. Đọc args (đường dẫn module)
2. Load file .toml
3. Gọi các hàm từ `bootstrap_generator.py`
4. Ghi file ra đĩa (I/O)
"""

import sys
import argparse
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

# --- Tương thích TOML cho Python < 3.11 ---
try:
    import tomllib
except ImportError:
    try:
        import toml as tomllib
    except ImportError:
        print("Lỗi: Cần gói 'toml'. Chạy 'pip install toml' (cho Python < 3.11)", file=sys.stderr)
        sys.exit(1)

# --- Thêm PROJECT_ROOT vào sys.path để import utils ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from utils.logging_config import setup_logging, log_success
    # Import "bộ não" generator
    from scripts.internal.bootstrap_generator import (
        generate_bin_wrapper,
        generate_script_entrypoint,
        generate_module_file,
        generate_doc_file
    )
except ImportError as e:
    print(f"Lỗi: Không thể import utils hoặc generator: {e}", file=sys.stderr)
    sys.exit(1)

# --- Định nghĩa các thư mục gốc ---
BIN_DIR = PROJECT_ROOT / "bin"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
MODULES_DIR = PROJECT_ROOT / "modules"
DOCS_DIR = PROJECT_ROOT / "docs"

# --- HÀM MAIN (ĐIỀU PHỐI) ---

def main():
    """Hàm chính chạy script bootstrap"""
    
    logger = setup_logging(script_name="Bootstrap", console_level_str="INFO")
    logger.debug("Bootstrap script started.")

    # 1. Phân tích đối số
    parser = argparse.ArgumentParser(description="Bootstrap (khởi tạo) một tool utility mới từ file tool.spec.toml.")
    parser.add_argument(
        "module_path_str", 
        type=str, 
        help="Đường dẫn đến thư mục module mới (ví dụ: modules/new_tool) chứa file tool.spec.toml."
    )
    args = parser.parse_args()

    # 2. Load và xác thực file TOML
    module_path = Path(args.module_path_str).resolve()
    spec_file_path = module_path / "tool.spec.toml"
    
    logger.info(f"🚀 Bắt đầu bootstrap từ: {module_path.name}/tool.spec.toml")

    if not module_path.is_dir():
        logger.warning(f"Thư mục module '{module_path.name}' chưa tồn tại. Đang tạo...")
        module_path.mkdir(parents=True, exist_ok=True)
    
    if not spec_file_path.exists():
        logger.error(f"❌ Không tìm thấy file 'tool.spec.toml' trong:")
        logger.error(f"   {module_path.as_posix()}")
        logger.error(f"Vui lòng tạo file spec trước khi chạy (tham khảo: docs/internal/tool_spec.template.toml)")
        sys.exit(1)

    try:
        with open(spec_file_path, 'rb') as f:
            config = tomllib.load(f)
    except Exception as e:
        logger.error(f"❌ Lỗi khi đọc file TOML: {e}")
        sys.exit(1)

    # 3. Xác thực config và chuẩn bị dữ liệu
    try:
        config['module_name'] = module_path.name
        tool_name = config['meta']['tool_name']
        script_file = config['meta']['script_file']
        
        logger.debug(f"Tool Name: {tool_name}")
        logger.debug(f"Module Name: {config['module_name']}")
        
    except KeyError as e:
        logger.error(f"❌ File 'tool.spec.toml' thiếu key bắt buộc trong [meta]: {e}")
        sys.exit(1)
    if 'argparse' not in config:
        logger.error("❌ File 'tool.spec.toml' thiếu section [argparse] bắt buộc.")
        sys.exit(1)

    # 4. Tạo nội dung (gọi generator)
    try:
        generated_content = {
            "bin": generate_bin_wrapper(config),
            "script": generate_script_entrypoint(config),
            "config": generate_module_file(config, "config"),
            "core": generate_module_file(config, "core"),
            "executor": generate_module_file(config, "executor"),
        }
        
        target_paths = {
            "bin": BIN_DIR / tool_name,
            "script": SCRIPTS_DIR / script_file,
            "config": module_path / f"{config['module_name']}_config.py",
            "core": module_path / f"{config['module_name']}_core.py",
            "executor": module_path / f"{config['module_name']}_executor.py",
        }
        
        if config.get('docs', {}).get('enabled', False):
            generated_content["docs"] = generate_doc_file(config)
            target_paths["docs"] = DOCS_DIR / "tools" / f"{tool_name}.md"

    except Exception as e:
        logger.error(f"❌ Lỗi nghiêm trọng khi tạo nội dung code: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)

    # 5. KIỂM TRA AN TOÀN (Không đổi)
    existing_files = [p for p in target_paths.values() if p.exists()]
    if existing_files:
        logger.error(f"❌ Dừng lại! Các file sau đã tồn tại. Sẽ không ghi đè:")
        for p in existing_files:
            logger.error(f"   -> {p.relative_to(PROJECT_ROOT).as_posix()}")
        sys.exit(1)

    # 6. GHI FILE (I/O)
    try:
        for key, path in target_paths.items():
            content = generated_content[key]
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