# Path: utils/core/config_helpers.py

"""
Các tiện ích logic để xử lý template và cấu trúc dữ liệu config.
(Module nội bộ, được import bởi utils/core)
"""

import logging
from pathlib import Path
from typing import Dict, Any, Set, List, Optional

from .toml_io import load_toml_file, write_toml_file
from .parsing import parse_comma_list, parse_cli_set_operators

__all__ = [
    "load_project_config_section",
    "load_and_merge_configs",
    "merge_config_sections",
    "format_value_to_toml",
    "resolve_config_value",
    "resolve_config_list",
    "resolve_set_modification"
]

def format_value_to_toml(value: Any) -> str:
    """
    Helper: Định dạng giá trị Python thành chuỗi TOML hợp lệ.

    Args:
        value: Giá trị Python bất kỳ.

    Returns:
        Chuỗi biểu diễn TOML của giá trị. Trả về chuỗi rỗng cho None.
    """
    if isinstance(value, bool):
        return str(value).lower()
    elif isinstance(value, (set, list)):
        if not value:
            return "[]" # Mảng rỗng
        # Sắp xếp để đảm bảo output ổn định
        return repr(sorted(list(value)))
    elif isinstance(value, (str, Path)):
        return repr(str(value)) # Dùng repr để thêm dấu ngoặc kép
    elif isinstance(value, (int, float)):
        return str(value)
    elif value is None:
        return "" # TOML không có giá trị null tường minh, dùng chuỗi rỗng hoặc bỏ key
    else:
        # Trường hợp khác, thử dùng repr
        return repr(value)

def resolve_config_value(
    cli_value: Any,
    file_value: Any,
    default_value: Any
) -> Any:
    """
    Xác định giá trị config cuối cùng cho các giá trị đơn.
    Ưu tiên: CLI > File Config > Mặc định.

    Args:
        cli_value: Giá trị từ đối số dòng lệnh (hoặc None).
        file_value: Giá trị từ file cấu hình (hoặc None).
        default_value: Giá trị mặc định.

    Returns:
        Giá trị cuối cùng được chọn dựa trên độ ưu tiên.
    """
    if cli_value is not None:
        return cli_value
    if file_value is not None:
        return file_value
    return default_value

def resolve_config_list(
    cli_str_value: Optional[str],
    file_list_value: Optional[List[str]],
    default_set_value: Set[str]
) -> List[str]:
    """
    Xác định danh sách (list) config cuối cùng (ví dụ: cho ignore, prune).
    Logic: (File Config GHI ĐÈ Mặc định) ĐƯỢC NỐI (append) với (CLI).
    Thứ tự được giữ nguyên.

    Args:
        cli_str_value: Chuỗi giá trị từ CLI (ngăn cách bởi dấu phẩy, hoặc None).
        file_list_value: Danh sách giá trị từ file cấu hình (hoặc None).
        default_set_value: Set giá trị mặc định.

    Returns:
        Danh sách (List[str]) cuối cùng đã được hợp nhất.
    """
    # 1. Danh sách cơ sở: Ưu tiên file config (giữ trật tự), nếu không có thì dùng default (sắp xếp).
    base_list: List[str]
    if file_list_value is not None:
        base_list = file_list_value
    else:
        base_list = sorted(list(default_set_value)) # Sắp xếp default cho nhất quán

    # 2. Lấy danh sách từ CLI (chuyển set thành list đã sắp xếp)
    cli_set = parse_comma_list(cli_str_value) # Phân tích chuỗi CLI thành set
    cli_list = sorted(list(cli_set)) # Sắp xếp CLI

    # 3. Nối chúng lại: Base (File/Default) + CLI
    return base_list + cli_list

def resolve_set_modification(
    tentative_set: Set[str],
    cli_string: Optional[str]
) -> Set[str]:
    """
    Xử lý logic +/-/~ (thêm/bớt/ghi đè) cho một set dựa trên chuỗi CLI.

    Quy tắc phân tích `cli_string`:
    - `"a,b"` (Không có toán tử đầu): Ghi đè `tentative_set` bằng `{"a", "b"}`.
    - `"+a,b"` (Bắt đầu bằng '+'): Thêm `{"a", "b"}` vào `tentative_set`.
    - `"~a,b"` (Bắt đầu bằng '~'): Bớt `{"a", "b"}` khỏi `tentative_set`.
    - `"a,b+c,d~a"` (Phức hợp):
        1. Bắt đầu bằng ghi đè: `base = {"a", "b"}`
        2. Thêm: `base = base.union({"c", "d"})` -> `{"a", "b", "c", "d"}`
        3. Bớt: `base = base.difference({"a"})` -> `{"b", "c", "d"}`
        Kết quả: `{"b", "c", "d"}`

    Args:
        tentative_set: Set cơ sở (thường từ file config hoặc default).
        cli_string: Chuỗi từ CLI có thể chứa các toán tử +/-/~.

    Returns:
        Set cuối cùng sau khi áp dụng các toán tử.
    """
    if cli_string is None or cli_string == "":
        return tentative_set # Không thay đổi nếu CLI rỗng

    overwrite_set, add_set, subtract_set = parse_cli_set_operators(cli_string)

    base_set: Set[str]
    if overwrite_set:
        # Chế độ Ghi đè: Bắt đầu từ overwrite_set
        base_set = overwrite_set
    else:
        # Chế độ Chỉnh sửa: Bắt đầu từ tentative_set
        base_set = tentative_set

    # Áp dụng toán tử '+' và '~'
    final_set = (base_set.union(add_set)).difference(subtract_set)

    return final_set


def load_project_config_section(
    config_path: Path,
    section_name: str,
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Tải file .project.toml và trích xuất một section cụ thể.

    Args:
        config_path: Đường dẫn đến file .project.toml.
        section_name: Tên section cần trích xuất (ví dụ: "cpath", "tree").
        logger: Logger để ghi log.

    Returns:
        Một dict chứa nội dung của section, hoặc dict rỗng nếu không tìm thấy.
    """
    config_data = load_toml_file(config_path, logger)
    return config_data.get(section_name, {})

def merge_config_sections(
    project_section: Dict[str, Any],
    local_section: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Hợp nhất hai dict cấu hình, ưu tiên các giá trị từ `local_section`.

    Args:
        project_section: Dict cấu hình từ .project.toml.
        local_section: Dict cấu hình từ file local (ví dụ: .cpath.toml).

    Returns:
        Dict đã được hợp nhất.
    """
    # Toán tử `**` sẽ ghi đè các key trùng lặp từ project_section bằng local_section
    return {**project_section, **local_section}

def load_and_merge_configs(
    start_dir: Path,
    logger: logging.Logger,
    project_config_filename: str,
    local_config_filename: str,
    config_section_name: str
) -> Dict[str, Any]:
    """
    Hàm chung để tải và hợp nhất cấu hình từ .project.toml và
    file .<toolname>.toml cục bộ.

    Args:
        start_dir: Thư mục bắt đầu quét config.
        logger: Logger.
        project_config_filename: Tên file config dự án (ví dụ: ".project.toml").
        local_config_filename: Tên file config cục bộ (ví dụ: ".cpath.toml").
        config_section_name: Tên section cần lấy trong các file config.

    Returns:
        Dict chứa cấu hình đã hợp nhất (local ưu tiên hơn project).
    """
    project_config_path = start_dir / project_config_filename
    local_config_path = start_dir / local_config_filename

    project_section = load_project_config_section(
        project_config_path,
        config_section_name,
        logger
    )

    # File local có thể chứa nhiều section, chỉ lấy section cần thiết
    local_config_data = load_toml_file(local_config_path, logger)
    local_section = local_config_data.get(config_section_name, {})

    # Hợp nhất, ưu tiên local
    return merge_config_sections(project_section, local_section)