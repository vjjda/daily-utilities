# Path: modules/check_path/check_path_config.py
from pathlib import Path
from typing import Any, Dict, Final, Set

__all__ = [
    "DEFAULT_IGNORE",
    "DEFAULT_EXTENSIONS",
    "COMMENT_RULES",
    "COMMENT_RULES_BY_EXT",
    "PROJECT_CONFIG_FILENAME",
    "PROJECT_CONFIG_ROOT_KEY",
    "CONFIG_SECTION_NAME",
    "CONFIG_FILENAME",
    "MODULE_DIR",
    "TEMPLATE_FILENAME",
    "CPATH_DEFAULTS",
]


DEFAULT_IGNORE: Final[Set[str]] = {
    ".venv",
    "venv",
    "__pycache__",
    ".git",
    "node_modules",
    "dist",
    "build",
    "out",
    ".ruff_cache",
}


DEFAULT_EXTENSIONS: Final[Set[str]] = {
    "py",
    "pyi",
    "js",
    "ts",
    "css",
    "scss",
    "zsh",
    "sh",
    "template.toml",
}


PROJECT_CONFIG_FILENAME: Final[str] = "pyproject.toml"
PROJECT_CONFIG_ROOT_KEY: Final[str] = "tool"
CONFIG_FILENAME: Final[str] = ".cpath.toml"
CONFIG_SECTION_NAME: Final[str] = "cpath"


MODULE_DIR: Final[Path] = Path(__file__).parent
TEMPLATE_FILENAME: Final[str] = "check_path.toml.template"

CPATH_DEFAULTS: Final[Dict[str, Any]] = {
    "extensions": DEFAULT_EXTENSIONS,
    "ignore": DEFAULT_IGNORE,
}


COMMENT_RULES: Final[Dict[str, Dict[str, Any]]] = {
    "hash_line": {
        "type": "line",
        "comment_prefix": "#",
    },
    "slash_line": {
        "type": "line",
        "comment_prefix": "//",
    },
    "css_block": {
        "type": "block",
        "comment_prefix": "/*",
        "comment_suffix": "*/",
        "padding": True,
    },
    "md_block": {
        "type": "block",
        "comment_prefix": "<!--",
        "comment_suffix": "-->",
        "padding": True,
    },
}


COMMENT_RULES_BY_EXT: Final[Dict[str, Dict[str, Any]]] = {
    ".py": COMMENT_RULES["hash_line"],
    ".pyi": COMMENT_RULES["hash_line"],
    ".zsh": COMMENT_RULES["hash_line"],
    ".sh": COMMENT_RULES["hash_line"],
    ".js": COMMENT_RULES["slash_line"],
    ".ts": COMMENT_RULES["slash_line"],
    ".scss": COMMENT_RULES["slash_line"],
    ".css": COMMENT_RULES["css_block"],
    ".md": COMMENT_RULES["md_block"],
    ".py.template": COMMENT_RULES["hash_line"],
    ".template.toml": COMMENT_RULES["hash_line"],
}
