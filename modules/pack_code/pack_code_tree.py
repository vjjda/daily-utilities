# Path: modules/pack_code/pack_code_tree.py

"""
Tree Generation logic for the Pack Code module.
"""

from pathlib import Path
from typing import List, Dict, Any

__all__ = ["generate_tree_string"]

def generate_tree_string(
    start_path: Path,
    file_paths: List[Path],
    scan_root: Path # Thêm scan_root để tính relative path chuẩn
) -> str:
    """
    Tạo một cây thư mục dạng string từ danh sách các file.
    Paths trong cây sẽ tương đối so với scan_root.
    """
    if not file_paths:
        return ""

    tree_lines: List[str] = []
    processed_elements: Dict[Path, str] = {} # Path -> display_name

    # Xác định gốc hiển thị (tương đối so với scan_root)
    try:
        root_display = start_path.relative_to(scan_root).as_posix()
        if root_display == ".":
            root_display = scan_root.name # Hiển thị tên thư mục gốc nếu quét từ '.'
    except ValueError:
        root_display = start_path.name # Fallback nếu không cùng cây thư mục

    tree_lines.append(f"{root_display}{'/' if start_path.is_dir() else ''}")

    # Chỉ xây dựng cây nếu start_path là thư mục
    if not start_path.is_dir():
        return "\n".join(tree_lines)

    # Tạo tập hợp tất cả các thành phần (file và thư mục cha) tương đối so với start_path
    all_relative_parts = set()
    for p in file_paths:
        try:
             # Tính relative path từ start_path để xây dựng cây logic
            rel_p = p.relative_to(start_path)
            all_relative_parts.add(rel_p)
            # Thêm tất cả thư mục cha vào set
            for parent in rel_p.parents:
                if parent != Path('.'):
                    all_relative_parts.add(parent)
        except ValueError:
             # Nếu file không nằm trong start_path (hiếm khi xảy ra), bỏ qua file đó khỏi cây
            continue

    if not all_relative_parts:
        return "\n".join(tree_lines) # Trả về chỉ root nếu không có gì bên trong

    # Sắp xếp các thành phần theo thứ tự hiển thị
    sorted_parts = sorted(list(all_relative_parts), key=lambda p: p.parts)

    # Dùng dict để lưu prefix cho từng cấp độ
    level_prefixes: Dict[int, str] = {}

    for i, part in enumerate(sorted_parts):
        level = len(part.parts) -1

        # Xác định prefix dựa trên các cấp cha
        prefix = ""
        current_parent = Path('.')
        for l in range(level):
            parent_part = Path(*part.parts[:l+1])
            prefix += level_prefixes.get(l, "    ") # Lấy prefix đã lưu hoặc mặc định
            current_parent = parent_part


        # Xác định siblings cùng cấp và vị trí của 'part'
        siblings = [
            p for p in sorted_parts
            if p.parent == part.parent and len(p.parts) == len(part.parts)
        ]

        is_last = (part == siblings[-1])
        pointer = "└── " if is_last else "├── "

        # Xác định xem 'part' này có phải là thư mục không
        # (Nó là thư mục nếu nó là parent của một 'part' khác)
        is_directory = any(p.parent == part for p in sorted_parts)

        line = f"{prefix}{pointer}{part.name}{'/' if is_directory else ''}"
        tree_lines.append(line)

        # Lưu prefix cho cấp độ hiện tại nếu nó là thư mục
        if is_directory:
            level_prefixes[level] = "    " if is_last else "│   "
        # Xóa prefix của các cấp sâu hơn nếu đây là mục cuối cùng của cấp hiện tại
        elif is_last:
            keys_to_remove = [k for k in level_prefixes if k >= level]
            for k in keys_to_remove:
                del level_prefixes[k]


    return "\n".join(tree_lines)