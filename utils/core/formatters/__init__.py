# Path: utils/core/formatters/__init__.py
"""
Mô-đun này tập hợp các trình định dạng (formatter) mã
cụ thể cho từng ngôn ngữ.
Chúng được import bởi 'code_formatter.py' (orchestrator)
để đăng ký vào registry.
"""

from . import formatter_python
# from . import formatter_javascript # (Dành cho tương lai)

__all__ = ["formatter_python"]