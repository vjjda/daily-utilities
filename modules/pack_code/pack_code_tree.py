# Path: modules/pack_code/pack_code_tree.py

"""
Logic tạo cây thư mục cho module Pack Code.
(Module nội bộ, được import bởi pack_code_core)
"""

from pathlib import Path
from typing import List, Dict, Any, Set

__all__ = ["generate_tree_string"]

def generate_tree_string(
    start_path: Path,
    file_paths: List[Path],
    scan_root: Path
) -> str:
    """
    Tạo một cây thư mục dạng string từ danh sách các file.
    Paths trong cây sẽ tương đối so với scan_root.

    Args:
        start_path: Đường dẫn bắt đầu (file hoặc thư mục) mà người dùng chỉ định.
        file_paths: Danh sách các file thực tế sẽ được đóng gói (đã lọc).
        scan_root: Thư mục gốc của dự án (dùng để hiển thị root của cây).

    Returns:
        Một chuỗi string chứa cây thư mục hoặc chuỗi rỗng nếu không có file.
    """
    if not file_paths:
        return ""

    tree_lines: List[str] = []

    # Xác định gốc hiển thị (tương đối so với scan_root)
    try:
        # Nếu start_path là con của scan_root
        root_display = start_path.relative_to(scan_root).as_posix()
        if root_display == ".":
            # Nếu quét từ gốc, hiển thị tên thư mục gốc
            root_display = scan_root.name
    except ValueError:
        # Nếu start_path nằm ngoài scan_root, chỉ hiển thị tên của nó
        root_display = start_path.name

    tree_lines.append(f"{root_display}{'/' if start_path.is_dir() else ''}")

    # Nếu start_path là file, chỉ cần hiển thị tên file đó
    if not start_path.is_dir():
        return "\n".join(tree_lines)

    # --- Logic xây dựng cây ---

    # Tạo tập hợp tất cả các thành phần (file và thư mục cha)
    # tương đối so với start_path (để xây dựng cấu trúc)
    all_relative_parts: Set[Path] = set()
    for p in file_paths:
        try:
            rel_p = p.relative_to(start_path)
            all_relative_parts.add(rel_p)
            # Thêm tất cả thư mục cha của file vào set
            for parent in rel_p.parents:
                if parent != Path('.'): # Bỏ qua gốc '.'
                    all_relative_parts.add(parent)
        except ValueError:
            # Bỏ qua file nếu nó không nằm trong start_path (hiếm khi xảy ra)
            continue

    if not all_relative_parts:
        return "\n".join(tree_lines) # Chỉ có root, không có gì bên trong

    # Sắp xếp các thành phần theo thứ tự hiển thị (theo cấu trúc thư mục)
    sorted_parts = sorted(list(all_relative_parts), key=lambda p: p.parts)

    # Dùng dict để lưu prefix ("│   " hoặc "    ") cho từng cấp độ
    level_prefixes: Dict[int, str] = {}

    for i, part in enumerate(sorted_parts):
        level = len(part.parts) - 1 # Cấp độ 0 là con trực tiếp của root

        # Xác định prefix dựa trên prefix của các cấp cha
        prefix = ""
        for l in range(level):
            prefix += level_prefixes.get(l, "    ") # Lấy prefix đã lưu hoặc mặc định

        # Xác định các "anh em" cùng cấp và vị trí của 'part' trong đó
        siblings = [
            p for p in sorted_parts
            if p.parent == part.parent and len(p.parts) == len(part.parts)
        ]
        is_last = (part == siblings[-1])
        pointer = "└── " if is_last else "├── "

        # Xác định xem 'part' này có phải là thư mục không
        # (Nó là thư mục nếu nó là cha của một 'part' khác trong danh sách)
        is_directory = any(p.parent == part for p in sorted_parts)

        # Tạo dòng hiển thị
        line = f"{prefix}{pointer}{part.name}{'/' if is_directory else ''}"
        tree_lines.append(line)

        # Cập nhật/Xóa prefix cho các cấp độ sau
        if is_directory:
            # Lưu prefix cho cấp độ hiện tại để các cấp con sử dụng
            level_prefixes[level] = "    " if is_last else "│   "
        elif is_last:
            # Nếu là file cuối cùng, xóa prefix của các cấp sâu hơn (nếu có)
            # để tránh vẽ đường dọc thừa
            keys_to_remove = [k for k in level_prefixes if k >= level]
            for k in keys_to_remove:
                del level_prefixes[k]

    return "\n".join(tree_lines)