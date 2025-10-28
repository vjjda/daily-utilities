# Path: modules/clip_diag/clip_diag_executor.py

"""
Execution logic for Clip Diagram utility (cdiag).
(Side-effects: Ghi file nguồn, Chạy tool, Mở file kết quả)
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

from utils.core import run_command
from .clip_diag_config import (
    DOT_PATH, MMC_PATH, APP_CONFIG
)

__all__ = ["execute_diagram_generation"]

def _get_app_to_open(result_type: str) -> str:
    """
    Lấy tên ứng dụng mặc định dựa trên loại file muốn mở.
    Sử dụng cấu hình từ `APP_CONFIG`.
    """
    if result_type == 'dot':
        return APP_CONFIG["dot_app"]
    elif result_type == 'mmd':
        return APP_CONFIG["mermaid_app"]
    elif result_type == 'svg':
        return APP_CONFIG["svg_viewer_app"]
    elif result_type == 'png':
        return APP_CONFIG["png_viewer_app"]
    return "Preview" # Mặc định trên macOS

def execute_diagram_generation(
    logger: logging.Logger, 
    result: Dict[str, Any], 
    output_format: Optional[str]
) -> None:
    """
    Thực thi các hành động dựa trên kết quả từ Core.

    Luồng xử lý:
    1. Ghi file nguồn (nếu chưa tồn tại).
    2. Nếu `output_format` được chỉ định (Chế độ Ảnh):
        a. Kiểm tra file ảnh đã tồn tại chưa.
        b. Nếu chưa, chạy `dot` hoặc `mmc` để tạo file ảnh.
        c. Mở file ảnh bằng ứng dụng tương ứng.
    3. Nếu `output_format` là None (Chế độ Nguồn):
        a. Mở file nguồn (.dot hoặc .mmd) bằng ứng dụng tương ứng.

    Args:
        logger: Logger.
        result: Dict DiagramResult từ core.
        output_format: 'svg', 'png', hoặc None.
    """
    
    diagram_type: str = result["diagram_type"]
    source_path_abs: Path = result["source_path"] 
    file_prefix: str = result["file_prefix"]
    hashval: str = result["hash"]
    source_dir: Path = source_path_abs.parent 
    source_content: str = result["content"]
    
    # 1. Đảm bảo file nguồn tồn tại (I/O Ghi)
    try:
        if not source_path_abs.exists():
            with open(source_path_abs, "w", encoding="utf-8") as f:
                f.write(source_content)
            logger.info(f"✍️  Saved new source file: {source_path_abs.name}")
        else:
            logger.info(f"🔄 Source file already exists: {source_path_abs.name}")
    except IOError as e:
        logger.error(f"❌ Failed to write source file {source_path_abs.name}: {e}")
        return # Không thể tiếp tục nếu không ghi được file nguồn
    
    # --- 2. CHẾ ĐỘ ẢNH (Image Mode) ---
    if output_format:
        output_ext = f".{output_format}"
        output_filename = f"{file_prefix}-{hashval}{output_ext}"
        output_path_abs = source_dir / output_filename
        app_to_open_output = _get_app_to_open(output_format)
        
        # 2a. Kiểm tra ảnh đã tồn tại chưa
        if output_path_abs.exists():
            logger.info(f"🖼️  Image file already exists: {output_filename}")
        else:
            # 2b. Tạo file ảnh
            logger.info(f"⏳ Converting to {output_format.upper()}...")
            
            command: List[str] = []
            if diagram_type == 'graphviz':
                command = [
                    DOT_PATH, f"-T{output_format}", 
                    "-Gbgcolor=white", str(source_path_abs), "-o", str(output_path_abs)
                ]
            else: # diagram_type == 'mermaid'
                command = [
                    MMC_PATH, "-i", str(source_path_abs), "-o", str(output_path_abs)
                ]
            
            # Chạy lệnh chuyển đổi
            try:
                success, error_msg = run_command(
                    command, 
                    logger, 
                    description=f"Convert {diagram_type} to {output_format.upper()}"
                )
                
                if not success:
                    logger.error("❌ Error converting diagram. Please check the source code syntax.")
                    logger.debug(f"Conversion command failed: {error_msg}")
                    # In thêm gợi ý nếu lỗi mermaid CLI
                    if diagram_type == 'mermaid' and MMC_PATH not in error_msg:
                         logger.error("   (Mermaid error? Check syntax or try online editor)")
                    elif diagram_type == 'graphviz' and DOT_PATH not in error_msg:
                         logger.error("   (Graphviz error? Check syntax with 'dot -v ...')")
                    return # Dừng nếu chuyển đổi lỗi
                
                logger.info(f"✅ Image file created: {output_filename}")
                 
            except Exception as e:
                logger.error(f"❌ An unexpected error occurred during conversion: {e}")
                return # Dừng nếu có lỗi không mong muốn
        
        # 2c. Mở file ảnh
        logger.info(f"👀 Opening image file with {app_to_open_output}...")
        open_command = ["open", "-a", app_to_open_output, str(output_path_abs)] 
        run_command(open_command, logger, description=f"Opening {output_filename}")
        
    # --- 3. CHẾ ĐỘ NGUỒN (Source Mode) ---
    else:
        source_ext = source_path_abs.suffix.strip('.') # Lấy 'dot' hoặc 'mmd'
        app_to_open_source = _get_app_to_open(source_ext)
        
        # Mở file nguồn
        logger.info(f"👩‍💻 Opening source file with {app_to_open_source}...")
        open_command = ["open", "-a", app_to_open_source, str(source_path_abs)] 
        run_command(open_command, logger, description=f"Opening {source_path_abs.name}")