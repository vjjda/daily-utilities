# Path: scripts/clip_diag.py

import sys
# --- MODIFIED: Imports ---
import logging
from pathlib import Path
from typing import Optional
from enum import Enum
import typer
# --- END MODIFIED ---

# Common utilities
from utils.logging_config import setup_logging

# --- MODULE IMPORTS ---
from modules.clip_diag import (
    process_clipboard_content,
    execute_diagram_generation,
    DEFAULT_TO_ARG
)
# ----------------------

# --- CONSTANTS ---
THIS_SCRIPT_PATH = Path(__file__).resolve()

# --- NEW: Typer Enum for choices ---
class DiagramFormat(str, Enum):
    svg = "svg"
    png = "png"
# --- END NEW ---


# --- MODIFIED: main() function with Typer ---
def main(
    to: Optional[DiagramFormat] = typer.Option(
        DEFAULT_TO_ARG, 
        "-t", "--to",
        help='Convert source code to an image file (svg or png) and open it.',
        case_sensitive=False
    ),
    filter_emoji: bool = typer.Option(
        False,
        "-f", "--filter",
        help='Filter out emojis from the clipboard content before processing.'
    )
):
    """
    Process diagram code (Graphviz/Mermaid) from clipboard and generate files.
    
    Default action opens the source file. Use -t to generate and open an image.
    """
    
    # --- REMOVED: argparse logic ---

    # 1. Setup Logging
    logger = setup_logging(script_name="CDiag")
    logger.debug("CDiag script started.")
    
    # 2. Execute Core Logic
    try:
        # Lấy nội dung, phân tích và chuẩn bị tên file
        result = process_clipboard_content(
            logger=logger,
            filter_emoji=filter_emoji, # <-- Use Typer variable
        )
        
        if result:
            # --- MODIFIED: Pass enum value ---
            # (Pass 'svg'/'png' string, or None)
            output_format = to.value if to else None
            execute_diagram_generation(logger, result, output_format)
            # --- END MODIFIED ---
        else:
            # Nếu process_clipboard_content trả về None, lỗi/cảnh báo đã được log
            pass
            
    except Exception as e:
        logger.error(f"❌ An unexpected error occurred: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)
# --- END MODIFIED ---


if __name__ == "__main__":
    try:
        # --- MODIFIED: Use Typer to run ---
        typer.run(main)
        # --- END MODIFIED ---
    except KeyboardInterrupt:
        print("\n\n❌ [Stop Command] Diagram utility stopped.")
        sys.exit(1)