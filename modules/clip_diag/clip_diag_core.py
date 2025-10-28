# Path: modules/clip_diag/clip_diag_core.py

"""
Core logic for Clip Diagram utility (cdiag).
Handles reading clipboard, diagram type detection, content cleaning,
and file preparation (pure logic).
"""

import hashlib
import re
import pyperclip
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from .clip_diag_config import (
    GRAPHVIZ_PREFIX, MERMAID_PREFIX, DEFAULT_OUTPUT_DIR
)

__all__ = ["process_clipboard_content"]


# Type hint cho đối tượng kết quả trả về
DiagramResult = Dict[str, Any]

def _detect_diagram_type(content: str) -> Optional[str]:
    """
    Nhận diện loại biểu đồ (graphviz hoặc mermaid) từ nội dung.
    Ưu tiên Mermaid nếu có sự mơ hồ (ví dụ: 'graph LR').

    Args:
        content: Nội dung đã được trim khoảng trắng đầu/cuối.

    Returns:
        'graphviz', 'mermaid', hoặc None nếu không nhận diện được.
    """
    stripped_content = content.strip()
    lower_content = stripped_content.lower()

    # Logic Mermaid
    unambiguous_mermaid = [
        'sequencediagram', 'gantt', 'classdiagram', 'statediagram',
        'pie', 'erdiagram', 'flowchart'
    ]
    if any(lower_content.startswith(kw) for kw in unambiguous_mermaid):
        return 'mermaid'

    # Trường hợp 'graph TD', 'graph LR', etc.
    if lower_content.startswith('graph '):
        first_line = lower_content.split('\n', 1)[0].strip()
        parts = first_line.split()
        if len(parts) > 1 and parts[1] in ['td', 'lr', 'bt', 'rl']:
            return 'mermaid'

    # Logic Graphviz
    graphviz_pattern = re.compile(
        r'^\s*(strict\s+)?(graph|digraph)(\s+([a-zA-Z0-9_]+|"[^"]*"))?\s*\{',
        re.IGNORECASE
    )
    if graphviz_pattern.match(stripped_content):
        return 'graphviz'
        
    return None

def _remove_comments(content: str, diagram_type: str) -> str:
    """
    Lọc bỏ các comment khỏi mã nguồn Graphviz hoặc Mermaid.
    Xóa cả các dòng trắng thừa tạo ra sau khi xóa comment.

    Args:
        content: Nội dung mã nguồn.
        diagram_type: 'graphviz' hoặc 'mermaid'.

    Returns:
        Nội dung đã lọc comment.
    """
    cleaned_content = content
    if diagram_type == 'graphviz':
        # Pattern phức tạp để tránh xóa comment bên trong chuỗi "" hoặc ''
        pattern = re.compile(
            r'("(\\"|[^"])*")|(\'(\\\'|[^\'])*\')|(/\*[\s\S]*?\*/)|(#.*|//.*)',
            re.MULTILINE 
        )
        def replacer(match):
            # Giữ nguyên chuỗi nếu match nhóm 1 hoặc 3
            if match.group(1) is not None or match.group(3) is not None:
                return match.group(0)
            # Xóa comment (nhóm 5 hoặc 6)
            return ""
        cleaned_content = pattern.sub(replacer, content)

    elif diagram_type == 'mermaid':
        # Comment Mermaid luôn bắt đầu bằng %%
        cleaned_content = re.sub(r'%%.*', '', content)
    
    # Xóa các dòng trắng thừa
    cleaned_lines = [line for line in cleaned_content.splitlines() if line.strip()]
    return '\n'.join(cleaned_lines)

def _filter_emoji(content: str, logger: logging.Logger) -> str:
    """Lọc bỏ emoji khỏi nội dung."""
    logger.info("🔍 Filtering emoji...")
    # Pattern regex bao phủ các dải Unicode chứa emoji phổ biến
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # Emoticons
        "\U0001F300-\U0001F5FF"  # Symbols & Pictographs
        "\U0001F680-\U0001F6FF"  # Transport & Map Symbols
        "\U0001F700-\U0001F77F"  # Alchemical Symbols
        "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FA6F"  # Chess Symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251"  # Enclosed Characters
        "]+", flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', content)

def _trim_leading_comments_and_whitespace(content: str) -> str:
    """
    Lọc bỏ các dòng comment (%%, /*, //, #) và dòng trắng
    ở ĐẦU nội dung clipboard để tìm ra dòng code thực sự đầu tiên.
    Điều này giúp `_detect_diagram_type` hoạt động chính xác hơn.

    Args:
        content: Nội dung thô từ clipboard (đã chuẩn hóa non-breaking space).

    Returns:
        Nội dung bắt đầu từ dòng code đầu tiên, hoặc chuỗi rỗng.
    """
    lines = content.splitlines()
    first_code_line_index = -1
    
    for i, line in enumerate(lines):
        stripped_line = line.strip()
        
        if not stripped_line: continue # Bỏ qua dòng trắng
        
        # Bỏ qua các dòng comment phổ biến
        if stripped_line.startswith(('%%', '/*', '//', '#')): continue
        
        # Tìm thấy dòng code đầu tiên
        first_code_line_index = i
        break
    
    if first_code_line_index == -1:
        # Nếu không tìm thấy dòng code nào
        return ""

    # Trả về nội dung từ dòng code đầu tiên trở đi
    return '\n'.join(lines[first_code_line_index:])


# --- HÀM ĐIỀU PHỐI CHÍNH (Orchestrator) ---

def process_clipboard_content(
    logger: logging.Logger, 
    filter_emoji: bool
) -> Optional[DiagramResult]:
    """
    Xử lý toàn bộ luồng lấy, làm sạch và chuẩn bị dữ liệu diagram.
    (Logic thuần túy, không ghi file)

    Luồng xử lý:
    1. Đọc clipboard.
    2. Chuẩn hóa non-breaking spaces.
    3. Lọc emoji (nếu cờ `filter_emoji`=True).
    4. Trim comment/whitespace ở đầu.
    5. Nhận diện loại diagram.
    6. Lọc comment bên trong code.
    7. Tạo hash, tên file, đường dẫn.
    8. Đảm bảo thư mục output tồn tại.
    9. Trả về DiagramResult object.

    Args:
        logger: Logger.
        filter_emoji: True nếu cần lọc emoji.

    Returns:
        Dict DiagramResult nếu thành công, None nếu có lỗi hoặc clipboard rỗng/không hợp lệ.
        DiagramResult = {
            "diagram_type": str,
            "content": str,      # Nội dung đã làm sạch
            "source_path": Path, # Đường dẫn file nguồn dự kiến
            "hash": str,         # Hash SHA1 của content
            "file_prefix": str   # "graphviz" hoặc "mermaid"
        }
    """
    
    # 1. Đọc Clipboard
    try:
        clipboard_content = pyperclip.paste()
        if not clipboard_content:
            logger.info("Clipboard is empty.")
            return None
    except Exception as e:
        logger.error(f"❌ Error reading clipboard: {e}")
        return None

    # 2. Chuẩn hóa Non-Breaking Spaces (U+00A0 -> U+0020)
    processed_content = clipboard_content.replace(u"\xa0", " ")
    
    # 3. Lọc Emoji (nếu được yêu cầu)
    if filter_emoji:
        processed_content = _filter_emoji(processed_content, logger)

    # 4. Lọc comment/dòng trắng ở ĐẦU vào
    logger.info("🧹 Trimming leading comments/whitespace...")
    processed_content = _trim_leading_comments_and_whitespace(processed_content)

    if not processed_content.strip():
        logger.info("Content is empty after filtering and trimming.")
        return None

    # 5. Nhận diện loại biểu đồ
    diagram_type = _detect_diagram_type(processed_content)
    if not diagram_type:
        logger.error("❌ Could not find valid Graphviz or Mermaid code in clipboard.")
        return None
    
    logger.info(f"✨ Detected diagram type: {diagram_type.capitalize()}")

    # 6. Lọc Comment (bên trong code)
    logger.info("🧹 Filtering comments...")
    processed_content = _remove_comments(processed_content, diagram_type)

    if not processed_content.strip():
        logger.warning("Content is empty after comment filtering.")
        return None
        
    # 7. Tạo Hash và Tên file
    # Hash được tạo *sau khi* nội dung đã được làm sạch hoàn toàn
    hashval = hashlib.sha1(processed_content.encode("utf-8")).hexdigest()[:12]
    
    if diagram_type == 'graphviz':
        file_prefix = GRAPHVIZ_PREFIX
        source_ext = ".dot"
    else: # diagram_type == 'mermaid'
        file_prefix = MERMAID_PREFIX
        source_ext = ".mmd"

    source_filename = f"{file_prefix}-{hashval}{source_ext}"
    source_path = DEFAULT_OUTPUT_DIR / source_filename
    
    # 8. Đảm bảo thư mục đầu ra tồn tại (không phải là side-effect chính)
    DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 9. Trả về kết quả
    return {
        "diagram_type": diagram_type,
        "content": processed_content, # Nội dung sạch để Executor ghi file
        "source_path": source_path,
        "hash": hashval,
        "file_prefix": file_prefix
    }