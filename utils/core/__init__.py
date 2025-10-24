# Path: utils/core/__init__.py

"""
Utility Core (Facade Pattern)

Đây là cổng giao tiếp chính (Facade). Nó import logic từ các
module phụ trợ trong cùng thư mục 'utils/core/' và 
"tái xuất" (re-export) chúng.

Các script khác (ctree, cpath) vẫn import như cũ:
from utils.core import run_command
"""

import logging
from pathlib import Path
from typing import List, Tuple, Union, Set, Optional

# Type hint for logger
Logger = logging.Logger

# --- Tái xuất (Re-export) từ các module "anh em" ---

# Từ utils/core/process.py
from .process import * # MODIFIED

# Từ utils/core/git.py
from .git import * # MODIFIED

# Từ utils/core/parsing.py
from .parsing import * # MODIFIED

# Từ utils/core/filter.py (Logic này sẽ được thay thế ở Giai đoạn 1)
from .filter import * # MODIFIED