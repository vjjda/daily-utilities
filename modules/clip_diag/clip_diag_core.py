#!/usr/bin/env python3
# Path: modules/clip_diag/clip_diag_core.py

"""
Core logic for Clip Diagram utility (cdiag).
Handles reading clipboard, diagram type detection, content cleaning,
and file preparation.
"""

import hashlib
import re
import pyperclip
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

# --- MODULE IMPORTS ---
from .clip_diag_config import (
    GRAPHVIZ_PREFIX, MERMAID_PREFIX, DEFAULT_OUTPUT_DIR
)
# ----------------------

# --- TYPING FOR RESULT ---
DiagramResult = Dict[str, Any]

# --- HÀM 1: NHẬN DIỆN LOẠI BIỂU ĐỒ (Detect Diagram Type) ---

def _detect_diagram_type(content: str) -> Optional[str]:
    """Nhận diện loại biểu đồ (graphviz hoặc mermaid)."""
    stripped_content = content.strip()
    lower_content = stripped_content.lower()

    # Logic Mermaid (Giữ nguyên từ file gốc)
    unambiguous_mermaid = [
        'sequencediagram', 'gantt', 'classdiagram', 'statediagram',
        'pie', 'erdiagram', 'flowchart'
    ]
    if any(lower_content.startswith(kw) for kw in unambiguous_mermaid):
        return 'mermaid'

    if lower_content.startswith('graph '):
        first_line = lower_content.split('\n', 1)[0].strip()
        parts = first_line.split()
        if len(parts) > 1 and parts[1] in ['td', 'lr', 'bt', 'rl']:
            return 'mermaid'

    # Logic Graphviz (Giữ nguyên từ file gốc)
    graphviz_pattern = re.compile(r'^\s*(strict\s+)?(graph|digraph)(\s+([a-zA-Z0-9_]+|"[^"]*"))?\s*\{', re.IGNORECASE)
    if graphviz_pattern.match(stripped_content):
        return 'graphviz'
        
    return None

# --- HÀM 2: LỌC BỎ COMMENT (Remove Comments) ---

def _remove_comments(content: str, diagram_type: str) -> str:
    """Lọc bỏ các comment khỏi mã nguồn Graphviz hoặc Mermaid."""
    if diagram_type == 'graphviz':
        # Sử dụng pattern phức tạp để tránh xóa chuỗi bên trong ngoặc kép/đơn
        pattern = re.compile(
            r'("(\\"|[^"])*")|(\'(\\\'|[^\'])*\')|(/\*[\s\S]*?\*/)|(#.*|//.*)',
            re.MULTILINE 
        )
        
        def replacer(match):
            # Giữ nguyên chuỗi
            if match.group(1) is not None or match.group(3) is not None:
                return match.group(0) # Trả về toàn bộ match (gồm cả dấu ngoặc kép/đơn)
            # Xóa comment (nhóm 5 hoặc 6)
            return ""

        content = pattern.sub(replacer, content)

    elif diagram_type == 'mermaid':
        # Comment Mermaid luôn bắt đầu bằng %%
        content = re.sub(r'%%.*', '', content)
    
    # Xóa các dòng trắng thừa được tạo ra sau khi xóa comment
    cleaned_lines = [line for line in content.splitlines() if line.strip()]
    return '\n'.join(cleaned_lines)

# --- HÀM 3: LỌC BỎ EMOJI (Filter Emoji) ---

def _filter_emoji(content: str, logger: logging.Logger) -> str:
    """Lọc bỏ emoji khỏi nội dung clipboard."""
    logger.info("🔍 Filtering emoji...")
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F" "\U0001F300-\U0001F5FF" "\U0001F680-\U0001F6FF"
        "\U0001F700-\U0001F77F" "\U0001F780-\U0001F7FF" "\U0001F800-\U0001F8FF"
        "\U0001F900-\U0001F9FF" "\U0001FA00-\U0001FA6F" "\U0001FA70-\U0001FAFF"
        "\U00002702-\U000027B0" "\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', content)

# --- HÀM ĐIỀU PHỐI CHÍNH (Orchestrator) ---

def process_clipboard_content(
    logger: logging.Logger, 
    filter_emoji: bool
) -> Optional[DiagramResult]:
    """
    Xử lý toàn bộ luồng lấy, làm sạch và chuẩn bị dữ liệu.
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

    processed_content = clipboard_content
    
    # 2. Lọc Emoji (nếu được yêu cầu)
    if filter_emoji:
        processed_content = _filter_emoji(processed_content, logger)

    if not processed_content.strip():
        logger.info("Content is empty after filtering.")
        return None

    # 3. Nhận diện loại biểu đồ
    diagram_type = _detect_diagram_type(processed_content)
    if not diagram_type:
        logger.error("❌ Could not find valid Graphviz or Mermaid code in clipboard.")
        return None
    
    logger.info(f"✨ Detected diagram type: {diagram_type.capitalize()}")

    # 4. Lọc Comment (Luôn luôn)
    logger.info("🧹 Filtering comments...")
    processed_content = _remove_comments(processed_content, diagram_type)

    # Thoát nếu nội dung rỗng sau khi lọc
    if not processed_content.strip():
        logger.warning("Content is empty after comment filtering.")
        return None
        
    # 5. Tạo Hash và Tên file
    # Hash chỉ được tạo sau khi nội dung đã được làm sạch hoàn toàn
    hashval = hashlib.sha1(processed_content.encode("utf-8")).hexdigest()[:12]
    
    if diagram_type == 'graphviz':
        file_prefix = GRAPHVIZ_PREFIX
        source_ext = ".dot"
    elif diagram_type == 'mermaid':
        file_prefix = MERMAID_PREFIX
        source_ext = ".mmd"

    source_filename = f"{file_prefix}-{hashval}{source_ext}"
    source_path = DEFAULT_OUTPUT_DIR / source_filename
    
    # 6. Tạo thư mục đầu ra nếu chưa có
    DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 7. Lưu file nguồn (nếu chưa tồn tại)
    if not source_path.exists():
        with open(source_path, "w", encoding="utf-8") as f:
            f.write(processed_content)
        logger.info(f"✍️  Saved new source file: {source_path.name}")
    else:
        logger.info(f"🔄 Source file already exists: {source_path.name}")
    
    # 8. Trả về kết quả
    return {
        "diagram_type": diagram_type,
        "content": processed_content,
        "source_path": source_path,
        "hash": hashval,
        "file_prefix": file_prefix
    }