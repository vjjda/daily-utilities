# Path: modules/bootstrap/bootstrap_utils.py
"""
Tiện ích nội bộ, thuần túy cho module Bootstrap.
(Tách ra để tránh circular dependency)
"""

from typing import Dict, Any, List

__all__ = ["get_cli_args"]

def get_cli_args(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Helper: Lấy danh sách [[cli.args]] từ config."""
    return config.get('cli', {}).get('args', [])