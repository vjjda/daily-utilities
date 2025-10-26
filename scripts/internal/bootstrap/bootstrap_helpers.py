# Path: scripts/internal/bootstrap/bootstrap_helpers.py
# (Kiểm tra lại - File này đã chính xác từ lần trước, không cần sửa)
"""
Helper utilities for the Bootstrap module.
(Loading templates, parsing config)
"""

import logging
from pathlib import Path
from typing import Dict, Any, List

from .bootstrap_config import TEMPLATE_DIR

# --- MODIFIED: Thêm __all__ cho các hàm mới ---
__all__ = [
    "load_template", "get_cli_args",
    "build_path_expands", "build_args_pass_to_core"
]
# --- END MODIFIED ---


def load_template(template_name: str) -> str:
    """Helper: Đọc nội dung từ một file template."""
    try:
        template_path = TEMPLATE_DIR / template_name
        return template_path.read_text(encoding='utf-8')
    except FileNotFoundError:
        logging.error(f"Lỗi nghiêm trọng: Không tìm thấy template '{template_name}'")
        raise
    except Exception as e:
        logging.error(f"Lỗi khi đọc template '{template_name}': {e}")
        raise

def get_cli_args(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Helper: Lấy danh sách [[cli.args]] từ config."""
    return config.get('cli', {}).get('args', [])

# --- NEW: Hàm build_path_expands (Chuyển từ bootstrap_builder.py) ---
# (Đã đổi tên, bỏ "typer_")
def build_path_expands(config: Dict[str, Any]) -> str:
    """Tạo code để expanduser() cho các tham số loại Path."""
    code_lines: List[str] = []
    path_args = [arg for arg in get_cli_args(config) if arg.get('type') == 'Path']
    if not path_args:
        code_lines.append("    # (No Path arguments to expand)")
        
    for arg in path_args:
        name = arg['name']
        
        # --- MODIFIED: Đổi tên biến để dùng chung ---
        # (Ví dụ: target_dir_arg -> target_dir_path)
        # (Và dùng args.{name} cho argparse)
        var_name = f"{name}_path"
        
        if arg.get('is_argument') and 'default' not in arg:
             # Bắt buộc (VD: c_demo /path)
             code_lines.append(f"    {var_name} = Path(args.{name}).expanduser()")
        else:
             # Tùy chọn (VD: ctree . hoặc ctree /path)
             code_lines.append(f"    {var_name} = Path(args.{name}).expanduser() if args.{name} else None")
        # --- END MODIFIED ---
            
    return "\n".join(code_lines)
# --- END NEW ---

# --- NEW: Hàm build_args_pass_to_core (Chuyển từ bootstrap_builder.py) ---
# (Đã đổi tên, bỏ "typer_")
def build_args_pass_to_core(config: Dict[str, Any]) -> str:
    """Tạo các dòng key=value để truyền args vào hàm core logic."""
    code_lines: List[str] = []
    args = get_cli_args(config)
    if not args:
        code_lines.append("        # (No CLI args to pass)")
        
    for arg in args:
        name = arg['name']
        
        # --- MODIFIED: Dùng biến đã expand (nếu là Path) ---
        if arg.get('type') == 'Path':
            code_lines.append(f"        {name}={name}_path,")
        else:
            code_lines.append(f"        {name}=args.{name},")
        # --- END MODIFIED ---
            
    return "\n".join(code_lines)
# --- END NEW ---