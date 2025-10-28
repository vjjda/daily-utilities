# Path: modules/bootstrap/bootstrap_utils.py
"""
Các tiện ích nội bộ, thuần túy cho module Bootstrap.
Được tách ra để tránh phụ thuộc vòng (circular dependency).
"""

from typing import Dict, Any, List

__all__ = ["get_cli_args"]

def get_cli_args(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Helper: Lấy danh sách các đối số `[[cli.args]]` từ dict config.

    Args:
        config: Dict chứa nội dung đã parse của file `.spec.toml`.

    Returns:
        List các dict định nghĩa đối số, hoặc list rỗng nếu không có.
    """
    # config.get('cli', {}) trả về dict cli hoặc dict rỗng nếu 'cli' không tồn tại
    # .get('args', []) trả về list args hoặc list rỗng nếu 'args' không tồn tại
    return config.get('cli', {}).get('args', [])