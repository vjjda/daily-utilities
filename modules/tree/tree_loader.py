# Path: modules/tree/tree_loader.py

"""
File Loading Utilities for the Tree (ctree) module.
(Responsible for all read I/O)
"""

import logging
import configparser
from pathlib import Path
from typing import List

from .tree_config import (
    CONFIG_FILENAME, PROJECT_CONFIG_FILENAME, CONFIG_SECTION_NAME
)

__all__ = ["load_config_files", "load_config_template"]


def load_config_files(
    start_dir: Path, 
    logger: logging.Logger
) -> configparser.ConfigParser:
    """
    Loads .ini configuration files from the start directory.
    (Code moved from tree_core.py)
    """
    config = configparser.ConfigParser()
    
    tree_config_path = start_dir / CONFIG_FILENAME
    project_config_path = start_dir / PROJECT_CONFIG_FILENAME

    files_to_read: List[Path] = []
    if project_config_path.exists():
        files_to_read.append(project_config_path)
    if tree_config_path.exists():
        files_to_read.append(tree_config_path)

    if files_to_read:
        try:
            config.read(files_to_read) 
            logger.debug(f"Loaded config from files: {[p.name for p in files_to_read]}")
        except Exception as e:
            logger.warning(f"⚠️ Could not read config files: {e}")
    else:
        logger.debug("No .tree.ini or .project.ini config files found. Using defaults.")

    if CONFIG_SECTION_NAME not in config:
        config.add_section(CONFIG_SECTION_NAME)
        logger.debug(f"Added empty '{CONFIG_SECTION_NAME}' section for safe fallback.")
        
    return config


def load_config_template() -> str:
    """
    Reads the raw content of the .ini template file.
    (Code moved from tree_core.py)
    """
    try:
        current_dir = Path(__file__).parent
        template_path = current_dir / "tree.ini.template"
        return template_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print("FATAL ERROR: Could not find 'tree.ini.template'.")
        return "; ERROR: Template file missing."
    except Exception as e:
        print(f"FATAL ERROR: Could not read 'tree.ini.template': {e}")
        return "; ERROR: Template file could not be read."