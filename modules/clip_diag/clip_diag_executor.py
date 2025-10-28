# Path: modules/clip_diag/clip_diag_executor.py

"""
Execution logic for Clip Diagram utility (cdiag).
Handles running external tools (dot, mmc) and opening files.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

# --- MODULE IMPORTS ---
from utils.core import run_command
from .clip_diag_config import (
    DOT_PATH, MMC_PATH, APP_CONFIG,
    GRAPHVIZ_PREFIX, MERMAID_PREFIX
)
# ----------------------

# --- NEW: __all__ definition ---
__all__ = ["execute_diagram_generation"]
# --- END NEW ---

def _get_app_to_open(result_type: str) -> str:
    """Lấy tên ứng dụng dựa trên loại file muốn mở."""
    if result_type == 'dot':
        return APP_CONFIG["dot_app"]
    elif result_type == 'mmd':
        return APP_CONFIG["mermaid_app"]
    elif result_type == 'svg':
        return APP_CONFIG["svg_viewer_app"]
    elif result_type == 'png':
        return APP_CONFIG["png_viewer_app"]
    return "Preview" # Mặc định

def execute_diagram_generation(
    logger: logging.Logger, 
    result: Dict[str, Any], 
    output_format: Optional[str]
) -> None:
    """
    Điều phối việc chuyển đổi sang ảnh và mở file đầu ra.
    """
    
    diagram_type = result["diagram_type"]
    # source_path_abs là đường dẫn tuyệt đối: ~/Documents/graphviz/graphviz-hash.dot
    source_path_abs: Path = result["source_path"] 
    file_prefix = result["file_prefix"]
    hashval = result["hash"]
    source_dir: Path = source_path_abs.parent 
    
    # --- NEW: REFACTOR TỪ CORE ---
    # 1. Đảm bảo file nguồn tồn tại (I/O Ghi)
    # Đây là trách nhiệm của Executor
    source_content = result["content"]
    if not source_path_abs.exists():
        with open(source_path_abs, "w", encoding="utf-8") as f:
            f.write(source_content)
        logger.info(f"✍️  Saved new source file: {source_path_abs.name}")
    else:
        logger.info(f"🔄 Source file already exists: {source_path_abs.name}")
    # --- END REFACTOR ---
    
    # --- 1. CHẾ ĐỘ ẢNH (Image Mode) ---
    if output_format:
        output_ext = f".{output_format}"
        output_filename = f"{file_prefix}-{hashval}{output_ext}"
        # Đường dẫn tuyệt đối của file ảnh
        output_path_abs = source_dir / output_filename
        app_to_open_output = _get_app_to_open(output_format)
        
        if output_path_abs.exists():
            logger.info(f"🖼️  Image file already exists: {output_filename}")
        else:
            logger.info(f"⏳ Converting to {output_format.upper()}...")
            
            command: List[str] = []
            if diagram_type == 'graphviz':
                # --- MODIFIED: Dùng đường dẫn tuyệt đối cho input và output ---
                command = [
                    DOT_PATH, f"-T{output_format}", 
                    "-Gbgcolor=white", str(source_path_abs), "-o", str(output_path_abs)
                ]
                # --- END MODIFIED ---
            elif diagram_type == 'mermaid':
                # --- MODIFIED: Dùng đường dẫn tuyệt đối cho input và output ---
                command = [
                    MMC_PATH, "-i", str(source_path_abs), "-o", str(output_path_abs)
                ]
                # --- END MODIFIED ---
            
            
            # Chạy lệnh (cwd mặc định vẫn là PROJECT_ROOT)
            try:
                success, error_msg = run_command(
                    command, 
                    logger, 
                    description=f"Convert {diagram_type} to {output_format.upper()}"
                )
                
                if not success:
                    logger.error("❌ Error converting diagram. Please check the source code syntax.")
                    logger.debug(f"Conversion command failed: {error_msg}")
                    return 
                
                logger.info(f"✅ Image file created: {output_filename}")
                 
            except Exception as e:
                logger.error(f"❌ An unexpected error during conversion: {e}")
                return
        
        # Mở file ảnh: Sử dụng đường dẫn tuyệt đối
        logger.info(f"👀 Opening image file with {app_to_open_output}...")
        open_command = ["open", "-a", app_to_open_output, str(output_path_abs)]
        run_command(open_command, logger, description=f"Opening {output_filename}")
        
    # --- 2. CHẾ ĐỘ NGUỒN (Source Mode) ---
    else:
        source_ext = source_path_abs.suffix.strip('.')
        app_to_open_source = _get_app_to_open(source_ext)
        
        # Mở file nguồn: Sử dụng đường dẫn tuyệt đối
        logger.info(f"👩‍💻 Opening source file with {app_to_open_source}...")
        open_command = ["open", "-a", app_to_open_source, str(source_path_abs)]
        run_command(open_command, logger, description=f"Opening {source_path_abs.name}")