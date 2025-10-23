#!/usr/bin/env python3
# Path: modules/clip_diag/clip_diag_config.py

"""
Configuration constants for the Clip Diagram utility (cdiag).
Defines paths for output, external tools, and viewing applications.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional # <-- Thêm Optional

# --- CẤU HÌNH ĐƯỜNG DẪN CỐ ĐỊNH ---
# Thư mục mặc định để lưu file diagram.
# Tên thư mục được đặt theo logic cũ: ~/Documents/graphviz
DEFAULT_OUTPUT_DIR: Path = Path(os.path.expanduser("~/Documents/graphviz"))

# --- CẤU HÌNH CÔNG CỤ VÀ ỨNG DỤNG ---
# Đường dẫn tuyệt đối đến các công cụ dòng lệnh (nếu đã cài qua Homebrew)
# Mặc định là path thường thấy trên MacOS dùng Homebrew
DOT_PATH: str = "/opt/homebrew/bin/dot" # Graphviz
MMC_PATH: str = "/opt/homebrew/bin/mmc" # Mermaid

# Ứng dụng để mở file nguồn/ảnh (trên MacOS)
APP_CONFIG: Dict[str, str] = {
    # Ứng dụng mở file nguồn
    "dot_app": "DotChart",
    "mermaid_app": "MarkChart",
    
    # Ứng dụng mở file ảnh
    "svg_viewer_app": "Google Chrome",
    "png_viewer_app": "Preview"
}

# --- CẤU HÌNH CHUNG ---
# Tên tiền tố file nguồn/ảnh
GRAPHVIZ_PREFIX: str = "graphviz"
MERMAID_PREFIX: str = "mermaid"

# --- NEW: Argparse Default ---
DEFAULT_TO_ARG: Optional[str] = None