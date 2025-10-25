# Path: modules/tree/tree_loader.py

"""
Tiện ích tải file cho module Tree (ctree).
(Chịu trách nhiệm cho mọi hoạt động I/O đọc)
"""

import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

# --- MODIFIED: Chuyển sang tomllib ---
try:
    import tomllib 
except ImportError:
    try:
        import toml as tomllib # Fallback
    except ImportError:
        print("Lỗi: Cần 'tomli'. Chạy 'pip install tomli'", file=sys.stderr)
        tomllib = None
# --- END MODIFIED ---

from .tree_config import (
    CONFIG_FILENAME, PROJECT_CONFIG_FILENAME, CONFIG_SECTION_NAME
)

__all__ = ["load_config_files", "load_config_template"]


def load_config_files(
    start_dir: Path, 
    logger: logging.Logger
) -> Dict[str, Any]: # <-- MODIFIED: Trả về Dict thay vì ConfigParser
    """
    Tải các file cấu hình .toml (.project.toml và .tree.toml).
    Nó merge section [tree] từ cả hai file, ưu tiên .tree.toml.
    """
    if tomllib is None:
        logger.error("❌ Thư viện 'tomli' (cho Python < 3.11) chưa được cài đặt.")
        return {} # Trả về config rỗng

    project_config_path = start_dir / PROJECT_CONFIG_FILENAME
    tree_config_path = start_dir / CONFIG_FILENAME

    project_data: Dict[str, Any] = {}
    tree_data: Dict[str, Any] = {}
    files_loaded: List[str] = []

    try:
        if project_config_path.exists():
            with open(project_config_path, 'rb') as f:
                project_data = tomllib.load(f)
            files_loaded.append(project_config_path.name)
            
        if tree_config_path.exists():
            with open(tree_config_path, 'rb') as f:
                tree_data = tomllib.load(f)
            files_loaded.append(tree_config_path.name)
            
    except Exception as e:
        logger.warning(f"⚠️ Không thể đọc file cấu hình: {e}")

    if files_loaded:
        logger.debug(f"Đã tải cấu hình từ: {files_loaded}")
    else:
        logger.debug(f"Không tìm thấy {CONFIG_FILENAME} hoặc {PROJECT_CONFIG_FILENAME}. Dùng mặc định.")

    # Lấy section [tree] từ mỗi file
    project_tree_section = project_data.get(CONFIG_SECTION_NAME, {})
    tree_section = tree_data.get(CONFIG_SECTION_NAME, {})

    # Merge: tree_section (cục bộ) sẽ ghi đè project_tree_section
    final_config_section = {**project_tree_section, **tree_section}
        
    return final_config_section


def load_config_template() -> str:
    """
    Đọc nội dung thô của file template .toml.
    """
    try:
        current_dir = Path(__file__).parent
        # --- MODIFIED: Đọc file .toml.template ---
        template_path = current_dir / "tree.toml.template"
        return template_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print("LỖI NGHIÊM TRỌNG: Không tìm thấy 'tree.toml.template'.")
        return "# LỖI: File template bị thiếu."
    except Exception as e:
        print(f"LỖI NGHIÊM TRỌNG: Không thể đọc 'tree.toml.template': {e}")
        return "# LỖI: Không thể đọc file template."