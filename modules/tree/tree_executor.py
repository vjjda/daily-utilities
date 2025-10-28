# Path: modules/tree/tree_executor.py

"""
Logic thực thi cho module Tree (ctree).
(Chịu trách nhiệm cho các side-effect: print)
"""

from pathlib import Path
import logging 
from typing import List, Set, Optional, Dict, Any, TYPE_CHECKING

try:
    import pathspec
except ImportError:
    pathspec = None

if TYPE_CHECKING:
    import pathspec

from utils.core import is_path_matched
from utils.logging_config import log_success 

from .tree_config import DEFAULT_MAX_LEVEL

__all__ = [
    "generate_tree", 
    "print_status_header", 
    "print_final_result",
]


def print_status_header(
    config_params: Dict[str, Any], 
    start_dir: Path, 
    is_git_repo: bool,
    cli_no_gitignore: bool
) -> None:
    """
    In dòng trạng thái (header) trước khi in cây.
    (Side-effect: print)
    """
    filter_lists = config_params["filter_lists"]
    
    # Kiểm tra xem có bất kỳ filter nào đang hoạt động không
    is_truly_full_view = (
        not any(filter_lists.values()) and 
        not config_params["using_gitignore"] and 
        config_params["max_level"] is None
    )
    
    filter_info = "Full view" if is_truly_full_view else "Filtered view"
    level_info = "full depth" if config_params["max_level"] is None else f"depth limit: {config_params['max_level']}"
    mode_info = ", dirs only" if config_params["global_dirs_only_flag"] else ""
    
    # Thêm thông tin filter extensions (nếu có)
    ext_filter = filter_lists.get("extensions")
    ext_info = ""
    if ext_filter is not None: # Chỉ hiển thị nếu filter được kích hoạt
        if ext_filter:
             ext_info = f", extensions: {','.join(sorted(list(ext_filter)))}"
        else:
             ext_info = ", extensions: (none)" # Hiển thị nếu filter rỗng
    
    # Thông tin Git
    git_info = ""
    if is_git_repo: 
        git_info = (
            ", Git project (.gitignore enabled)" if config_params["using_gitignore"] 
            else (", Git project (.gitignore disabled by flag)" if cli_no_gitignore 
                  else ", Git project")
        )
        
    print(f"{start_dir.name}/ [{filter_info}, {level_info}{mode_info}{ext_info}{git_info}]")


def print_final_result(
    counters: Dict[str, int], 
    global_dirs_only: bool
) -> None:
    """
    In dòng thống kê tổng kết ở cuối.
    (Side-effect: print)
    """
    files_count = counters['files']
    dirs_count = counters['dirs']

    files_info = (
        "0 files (hidden)" if global_dirs_only and files_count == 0 
        else f"{files_count} file{'s' if files_count != 1 else ''}"
    )
    dirs_info = f"{dirs_count} director{'ies' if dirs_count != 1 else 'y'}"
    
    print(f"\n{dirs_info}, {files_info}")


def generate_tree(
    directory: Path, 
    start_dir: Path, 
    prefix: str = "", 
    level: int = 0, 
    max_level: Optional[int] = DEFAULT_MAX_LEVEL, 
    ignore_spec: Optional['pathspec.PathSpec'] = None,
    submodules: Optional[Set[Path]] = None, 
    prune_spec: Optional['pathspec.PathSpec'] = None,
    dirs_only_spec: Optional['pathspec.PathSpec'] = None,
    extensions_filter: Optional[Set[str]] = None,
    is_in_dirs_only_zone: bool = False, 
    counters: Optional[Dict[str, int]] = None
) -> None:
    """
    Hàm đệ quy để tạo và in cây thư mục.
    (Side-effect: print)

    Args:
        directory: Thư mục hiện tại đang quét (thay đổi theo đệ quy).
        start_dir: Thư mục gốc của toàn bộ lần quét (không đổi).
        prefix: Chuỗi prefix (ví dụ: "│   ") để vẽ cây (thay đổi theo đệ quy).
        level: Cấp độ đệ quy hiện tại.
        max_level: Cấp độ tối đa được phép.
        ignore_spec: PathSpec đã biên dịch cho các quy tắc 'ignore'.
        submodules: Set các đường dẫn tuyệt đối đến các submodule.
        prune_spec: PathSpec đã biên dịch cho các quy tắc 'prune'.
        dirs_only_spec: PathSpec đã biên dịch cho các quy tắc 'dirs-only'.
        extensions_filter: Set các đuôi file (đã lột ".") được phép.
        is_in_dirs_only_zone: True nếu thư mục cha đã khớp 'dirs-only'.
        counters: Dict để đếm tổng số file/thư mục.
    """
    if submodules is None:
        submodules = set()
    
    if counters is None:
        counters = {'dirs': 0, 'files': 0}
    
    # Điều kiện dừng đệ quy
    if max_level is not None and level >= max_level: 
        return
    
    try: 
        # Lấy nội dung thư mục, bỏ qua các file ẩn (dotfiles)
        contents = [path for path in directory.iterdir() if not path.name.startswith('.')]
    except (FileNotFoundError, NotADirectoryError): 
        # Bỏ qua nếu không thể đọc thư mục
        return
        
    def is_ignored(path: Path) -> bool:
        """Hàm helper nội bộ để kiểm tra quy tắc ignore."""
        return is_path_matched(path, ignore_spec, start_dir)
    
    # 1. Tách thư mục
    dirs = sorted(
        [d for d in contents if d.is_dir() and not is_ignored(d)], 
        key=lambda p: p.name.lower()
    )
    
    # 2. Tách file (chỉ khi không ở trong 'dirs-only' zone)
    files: List[Path] = []
    if not is_in_dirs_only_zone: 
        files_unfiltered = [f for f in contents if f.is_file() and not is_ignored(f)]
        
        # Áp dụng bộ lọc extension (nếu có)
        if extensions_filter is not None:
            files_filtered = []
            for f in files_unfiltered:
                # Dùng "".join(suffixes) để xử lý đuôi kép (ví dụ: .tar.gz)
                file_ext = "".join(f.suffixes).lstrip('.') 
                if file_ext in extensions_filter:
                    files_filtered.append(f)
            files = sorted(files_filtered, key=lambda p: p.name.lower())
        else:
            # Không filter, chỉ sort
            files = sorted(files_unfiltered, key=lambda p: p.name.lower())
        
    # 3. In kết quả
    items_to_print = dirs + files
    pointers = ["├── "] * (len(items_to_print) - 1) + ["└── "]

    for pointer, path in zip(pointers, items_to_print):
        if path.is_dir(): 
            counters['dirs'] += 1
        else: 
            counters['files'] += 1

        is_submodule = path.is_dir() and path.resolve() in submodules
        is_pruned = path.is_dir() and is_path_matched(path, prune_spec, start_dir)
        
        # Kiểm tra xem đây có phải là điểm bắt đầu của 1 'dirs-only' zone không
        is_dirs_only_entry = (
            path.is_dir() and 
            is_path_matched(path, dirs_only_spec, start_dir) and 
            not is_in_dirs_only_zone # Chỉ kích hoạt 1 lần
        ) 
        
        line = f"{prefix}{pointer}{path.name}{'/' if path.is_dir() else ''}"
        
        # Thêm các hậu tố (suffix)
        if is_submodule: 
            line += " [submodule]"
        elif is_pruned: 
            line += " [...]"
        elif is_dirs_only_entry: 
            line += " [dirs only]"
        
        print(line)

        # 4. Đệ quy (nếu là thư mục hợp lệ)
        if path.is_dir() and not is_submodule and not is_pruned:
            extension = "│   " if pointer == "├── " else "    " 
            next_is_in_dirs_only_zone = is_in_dirs_only_zone or is_dirs_only_entry
            
            generate_tree(
                path, start_dir, prefix + extension, level + 1, max_level, 
                ignore_spec, submodules, prune_spec, 
                dirs_only_spec, 
                extensions_filter, # Truyền bộ lọc extension xuống
                next_is_in_dirs_only_zone, counters
            )