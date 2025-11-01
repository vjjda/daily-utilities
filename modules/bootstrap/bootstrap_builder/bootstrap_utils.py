# Path: modules/bootstrap/bootstrap_builder/bootstrap_utils.py
from typing import Dict, Any, List

__all__ = ["get_cli_args"]


def get_cli_args(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Trích xuất danh sách các đối số CLI từ cấu hình spec.
    """
    return config.get("cli", {}).get("args", [])