# Path: utils/core.py

"""
Utility Core (Facade Pattern)

Đây là cổng giao tiếp chính. Nó import logic từ các
module phụ trợ (bắt đầu bằng _) và "xuất" chúng ra
cho các script khác trong dự án.

Các script khác (ctree, cpath) chỉ cần:
from utils.core import run_command
"""

import logging # <-- Giữ lại import logging để tương thích

# Type hint for logger
Logger = logging.Logger

# --- Tái xuất (Re-export) từ các module nội bộ ---

# Từ utils/_process.py
from ._process import run_command

# Từ utils/_git.py
from ._git import is_git_repository, find_git_root, get_submodule_paths

# Từ utils/_parsing.py
from ._parsing import parse_comma_list

# Từ utils/_filter.py (Logic này sẽ được thay thế ở Giai đoạn 1)
from ._filter import is_path_matched, parse_gitignore