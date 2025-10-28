# Path: modules/check_path/check_path_rules.py

"""
Rule implementation logic for the Path Checker module.

Chứa logic cụ thể để áp dụng các quy tắc comment
(ví dụ: line comment, block comment) vào nội dung file.
"""

from typing import List, Dict, Any

__all__ = ["apply_line_comment_rule", "apply_block_comment_rule"]

def apply_line_comment_rule(
    lines: List[str], 
    correct_path_comment: str, 
    check_prefix: str,
    is_executable: bool
) -> List[str]:
    """
    Áp dụng logic sửa/chèn comment cho các file dùng line comment (#, //).
    
    Xử lý các trường hợp:
    - Shebang (#!) ở dòng 1.
    - Shebang ở dòng 1 nhưng file không executable (sẽ bị xóa).
    - Shebang ở dòng 2 (bị lỗi, sẽ swap hoặc xóa).
    - Path comment ở dòng 1 hoặc 2 (sửa nếu sai).
    - Không có path comment (chèn).

    Args:
        lines: List các dòng (có newline) của file.
        correct_path_comment: Chuỗi comment đúng (đã có newline).
        check_prefix: Tiền tố comment (ví dụ: "#" hoặc "//").
        is_executable: True nếu file có quyền execute.

    Returns:
        List các dòng mới (đã sửa).
    """
    
    line1_is_shebang = lines[0].startswith('#!')
    
    # Xử lý Shebang "mồ côi" (file có shebang nhưng không executable)
    if line1_is_shebang and not is_executable:
        lines.pop(0) # Xóa shebang
        
        if not lines:
            return lines # File rỗng sau khi pop
            
        line1_is_shebang = False # Cập nhật lại chẩn đoán
    
    # Chẩn đoán (sau khi đã dọn dẹp shebang mồ côi)
    line1_is_path = lines[0].startswith(f"{check_prefix} Path:")
    line2_is_path = False
    
    if len(lines) > 1 and lines[1].startswith(f"{check_prefix} Path:"):
        line2_is_path = True

    # Áp dụng logic sửa
    if line1_is_shebang:
        # File có shebang hợp lệ ở dòng 1
        if line2_is_path:
            if lines[1] != correct_path_comment:
                lines[1] = correct_path_comment # Sửa dòng 2
        else:
            lines.insert(1, correct_path_comment) # Chèn vào dòng 2
            
    elif line1_is_path:
        # Path ở dòng 1
        # Kiểm tra xem có shebang lỗi ở dòng 2 không
        if len(lines) > 1 and lines[1].startswith('#!'):
            if is_executable:
                lines[0], lines[1] = lines[1], lines[0] # Swap
                if lines[1] != correct_path_comment: # Sửa path (giờ ở dòng 2)
                    lines[1] = correct_path_comment
            else:
                lines.pop(1) # Xóa shebang lỗi ở dòng 2
                if lines[0] != correct_path_comment: # Sửa path (ở dòng 1)
                    lines[0] = correct_path_comment
        else:
            # Path ở dòng 1, không có shebang
            if lines[0] != correct_path_comment:
                 lines[0] = correct_path_comment # Sửa dòng 1
                 
    else: 
        # Không có shebang, không có path
        lines.insert(0, correct_path_comment) # Chèn vào dòng 1
        
    return lines

def apply_block_comment_rule(
    lines: List[str], 
    correct_path_comment: str,
    rule: Dict[str, Any]
) -> List[str]:
    """
    Áp dụng logic sửa/chèn comment cho các file dùng block comment (/*...*/).
    
    Block comments luôn được giả định phải ở Dòng 1.

    Args:
        lines: List các dòng (có newline) của file.
        correct_path_comment: Chuỗi comment đúng (đã có newline).
        rule: Dict quy tắc (để lấy prefix và padding).

    Returns:
        List các dòng mới (đã sửa).
    """
    
    prefix = rule["comment_prefix"]
    padding = " " if rule.get("padding", False) else ""
    
    # Chẩn đoán: Dòng 1 có phải là path comment không?
    line1_is_path = lines[0].startswith(f"{prefix}{padding}Path:")

    if line1_is_path:
        if lines[0] != correct_path_comment:
            lines[0] = correct_path_comment # Sửa dòng 1
    else:
        lines.insert(0, correct_path_comment) # Chèn vào dòng 1
        
    return lines