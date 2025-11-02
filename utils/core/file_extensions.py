# Path: utils/core/file_extensions.py
"""
Các hàm tiện ích để xử lý và so khớp đuôi file (extensions) 
một cách nhất quán, hỗ trợ các trường hợp phức tạp như 
.py.template hoặc .gitignore.
"""

from pathlib import Path
from typing import Set

__all__ = ["is_extension_matched"]


def is_extension_matched(
    file_path: Path, 
    extensions_set: Set[str]
) -> bool:
    """
    Kiểm tra xem một file có khớp với bộ extension được 
    cung cấp hay không.

    Hàm này kiểm tra ba trường hợp (theo thứ tự ưu tiên):
    1. Toàn bộ chuỗi extension (ví dụ: 'py.template').
    2. Chỉ extension cuối cùng (ví dụ: 'template' từ 'file.py.template').
    3. Tên file nếu nó bắt đầu bằng dấu '.' (ví dụ: 'gitignore' từ '.gitignore'
       hoặc 'template.toml' từ '.template.toml').
    4. Trường hợp không có extension (so khớp với "").
    """
    
    # 1. Lấy tên file
    file_name = file_path.name
    
    # 2. Xử lý trường hợp đặc biệt (ví dụ: .gitignore, .project.toml)
    if file_name.startswith("."):
        # Lấy 'gitignore' từ '.gitignore'
        # Lấy 'project.toml' từ '.project.toml'
        ext_special = file_name.lstrip(".")
        if ext_special in extensions_set:
            return True

    # 3. Lấy full extension (ví dụ: 'py.template' từ 'file.py.template')
    full_ext = "".join(file_path.suffixes).lstrip(".")

    if full_ext in extensions_set:
        return True

    # 4. Lấy last extension (ví dụ: 'template' từ 'file.py.template')
    last_ext = file_path.suffix.lstrip(".")
    
    if last_ext in extensions_set:
        return True

    # 5. Xử lý trường hợp không có extension (ví dụ: 'README')
    # Cả full_ext và last_ext đều là ""
    if not full_ext and not last_ext and "" in extensions_set:
        return True

    return False