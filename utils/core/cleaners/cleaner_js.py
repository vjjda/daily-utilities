# Path: utils/core/cleaners/cleaner_js.py
"""
Trình làm sạch (Cleaner) cho mã nguồn JavaScript.
Sử dụng Regex an toàn để loại bỏ comment mà không làm hỏng các chuỗi (strings).
"""

import logging
import re
from typing import List

__all__ = ["clean_javascript_code"]

# Biểu thức Regex này được thiết kế để "bắt" (match) các token sau:
# 1. (Group 1) Các chuỗi kép (double-quoted strings), xử lý các escape character.
# 2. (Group 2) Các chuỗi đơn (single-quoted strings), xử lý các escape character.
# 3. (Group 3) Các chuỗi mẫu (template literals), xử lý các escape character.
# 4. (Group 4) Các comment khối kiểu JSDoc (/** ... */).
# 5. (Group 5) Các comment khối thông thường (/* ... */).
# 6. (Group 6) Các comment đơn dòng (// ...).
#
# Bằng cách bắt tất cả các token này, chúng ta có thể quyết định giữ lại
# (nếu là string) hoặc loại bỏ (nếu là comment) một cách an toàn.
#
# LƯU Ý: Giải pháp này vẫn có thể thất bại với các JavaScript Regex literal
# (ví dụ: const r = /\/\*/;), vốn rất khó phân biệt với phép chia
# nếu không dùng một bộ phân tích (parser) JavaScript đầy đủ.
# Tuy nhiên, nó giải quyết được 95% vấn đề phổ biến nhất là comment trong string.
SAFE_JS_CLEANER_PATTERN: Final[re.Pattern[str]] = re.compile(
    r'("(\\"|[^"])*")'              # Group 1: Double-quoted strings
    r"|('(\\'|[^'])*')"            # Group 2: Single-quoted strings
    r"|(`(\\`|[^`])*`)"            # Group 3: Template literals
    r"|(/\*\*[\s\S]*?\*/)"          # Group 4: JSDoc comments
    r"|(/\*[\s\S]*?\*/)"          # Group 5: Regular block comments
    r"|(//.*)"                     # Group 6: Line comments
)


def clean_javascript_code(
    code_content: str,
    logger: logging.Logger,
    all_clean: bool = False
) -> str:
    """
    Dọn dẹp mã JavaScript bằng cách loại bỏ JSDoc hoặc tất cả comment.

    Args:
        code_content: Nội dung file mã nguồn JavaScript.
        logger: Logger để ghi lại thông tin.
        all_clean:
            - False (Mặc định): Chỉ loại bỏ JSDoc (/** ... */).
            - True: Loại bỏ TẤT CẢ comment (JSDoc, /* ... */, và // ...).

    Returns:
        Nội dung mã đã được dọn dẹp.
    """
    logger.debug(f"Trình làm sạch JavaScript (Regex an toàn) được gọi (all_clean={all_clean}).")

    def replacer(match: re.Match[str]) -> str:
        """
        Hàm được gọi bởi re.sub cho mỗi token tìm thấy.
        Quyết định giữ lại (string) hay loại bỏ (comment).
        """
        # Group 1, 2, 3 là các loại string. Luôn giữ lại.
        if match.group(1) or match.group(2) or match.group(3):
            return match.group(0) # Giữ nguyên string

        if all_clean:
            # Chế độ --all-clean: Xóa tất cả các loại comment
            # (JSDoc, Block, Line)
            if match.group(4) or match.group(5) or match.group(6):
                return "" # Xóa comment
        else:
            # Chế độ mặc định (chỉ xóa docstring):
            # Chỉ xóa JSDoc (Group 4)
            if match.group(4):
                return "" # Xóa JSDoc
            
            # Giữ lại comment block thông thường (5) và comment dòng (6)
            if match.group(5) or match.group(6):
                return match.group(0) # Giữ nguyên comment

        # Fallback (không nên xảy ra), giữ lại token
        return match.group(0)

    try:
        cleaned_content: str = SAFE_JS_CLEANER_PATTERN.sub(replacer, code_content)
        
        # Dọn dẹp các dòng trống liên tiếp
        cleaned_lines: List[str] = [line for line in cleaned_content.splitlines() if line.strip()]
        
        if not cleaned_lines:
            return ""
            
        final_content = '\n'.join(cleaned_lines)
        # Đảm bảo file kết thúc bằng một dòng mới nếu có nội dung
        return final_content + '\n'
        
    except Exception as e:
        logger.warning(f"Lỗi khi xử lý regex cleaner cho JavaScript: {e}")
        # Fallback về nội dung gốc nếu có lỗi regex
        return code_content