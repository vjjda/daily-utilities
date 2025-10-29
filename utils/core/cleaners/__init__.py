# Path: utils/core/cleaners/__init__.py
"""
Mô-đun này tập hợp các trình làm sạch (cleaner) mã
cụ thể cho từng ngôn ngữ.

Chúng được import bởi 'code_cleaner.py' (orchestrator)
để đăng ký vào registry.
"""

from . import cleaner_python
from . import cleaner_js
from . import cleaner_shell

__all__ = ["cleaner_python", "cleaner_js", "cleaner_shell"]