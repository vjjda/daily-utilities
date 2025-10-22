#!/usr/bin/env python3
# Path: modules/path_checker/path_checker_rules.py

"""
Rule implementation logic for the Path Checker module.

Each function here knows how to apply a specific type of
path comment rule (e.g., line comments, block comments).
"""

from typing import List, Dict, Any

def apply_line_comment_rule(
    lines: List[str], 
    correct_path_comment: str, 
    check_prefix: str
) -> List[str]:
    """
    Applies logic to insert/fix path comments for files
    that use single-line comments (e.g., #, //).
    """
    
    # Logic "chẩn đoán"
    line1_is_shebang = lines[0].startswith('#!')
    
    line1_is_path = lines[0].startswith(f"{check_prefix} Path:")
    line2_is_path = False
    if len(lines) > 1 and lines[1].startswith(f"{check_prefix} Path:"):
        line2_is_path = True

    # Logic "điều trị" (Giữ nguyên)
    if line1_is_shebang:
        if line2_is_path:
            if lines[1] != correct_path_comment:
                lines[1] = correct_path_comment # Fix existing
        else:
            lines.insert(1, correct_path_comment) # Insert
    elif line1_is_path:
        # Check for swapped shebang/path
        if len(lines) > 1 and lines[1].startswith('#!'):
            lines[0], lines[1] = lines[1], lines[0] # Swap them
            if lines[1] != correct_path_comment: # Fix path (now on line 2)
                lines[1] = correct_path_comment
        else: # Path on line 1, no shebang
            if lines[0] != correct_path_comment:
                lines[0] = correct_path_comment # Fix existing
    else: # No shebang, no path
        lines.insert(0, correct_path_comment) # Insert at top
        
    return lines

# --- NEW: Logic cho block comments (CSS, MD) ---
def apply_block_comment_rule(
    lines: List[str], 
    correct_path_comment: str,
    rule: Dict[str, Any]
) -> List[str]:
    """
    Applies logic to insert/fix path comments for files
    that use block comments (e.g., /* ... */, ).
    
    Lưu ý: Block comments *luôn* ở Dòng 1. Chúng ta không
    kiểm tra shebang cho các file này (.css, .md).
    """
    
    prefix = rule["comment_prefix"]
    padding = " " if rule.get("padding", False) else ""
    
    # Chẩn đoán: Dòng 1 có phải là path comment không?
    # Chúng ta chỉ kiểm tra prefix, không kiểm tra suffix
    # để bắt được cả trường hợp comment hỏng (ví dụ: /* Path: ... */)
    line1_is_path = lines[0].startswith(f"{prefix}{padding}Path:")

    if line1_is_path:
        # Dòng 1 là path comment, kiểm tra xem nó có đúng không
        if lines[0] != correct_path_comment:
            lines[0] = correct_path_comment # Fix existing
    else:
        # Dòng 1 không phải path comment, chèn vào đầu
        lines.insert(0, correct_path_comment) # Insert at top
        
    return lines
# --- END NEW ---