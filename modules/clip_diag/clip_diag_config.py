# Path: modules/clip_diag/clip_diag_config.py

"""
Configuration constants for the Clip Diagram utility (cdiag).
(Single Source of Truth)
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, Final

__all__ = [
    "DEFAULT_OUTPUT_DIR", "DOT_PATH", "MMC_PATH", "APP_CONFIG",
    "GRAPHVIZ_PREFIX", "MERMAID_PREFIX", "DEFAULT_TO_ARG"
]

# --- Đường dẫn Cố định ---

# Thư mục mặc định để lưu file diagram.
DEFAULT_OUTPUT_DIR: Final[Path] = Path(os.path.expanduser("~/Documents/graphviz"))

# --- Công cụ & Ứng dụng ---

# Đường dẫn tuyệt đối đến các công cụ dòng lệnh (ví dụ trên macOS Homebrew).
DOT_PATH: Final[str] = "/opt/homebrew/bin/dot" # Graphviz
MMC_PATH: Final[str] = "/opt/homebrew/bin/mmc" # Mermaid CLI

# Ứng dụng để mở file nguồn/ảnh (ví dụ trên macOS).
APP_CONFIG: Final[Dict[str, str]] = {
    # Ứng dụng mở file nguồn
    "dot_app": "DotChart",
    "mermaid_app": "MarkChart",
    
    # Ứng dụng mở file ảnh
    "svg_viewer_app": "Google Chrome",
    "png_viewer_app": "Preview"
}

# --- Cấu hình Chung ---

# Tiền tố tên file nguồn/ảnh.
GRAPHVIZ_PREFIX: Final[str] = "graphviz"
MERMAID_PREFIX: Final[str] = "mermaid"

# --- Argparse Default ---

# Giá trị mặc định cho tùy chọn '--to'. None nghĩa là mở file nguồn.
DEFAULT_TO_ARG: Final[Optional[str]] = None