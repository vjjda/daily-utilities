# Path: utils/core/formatters/formatter_python.py
import logging
import subprocess
from pathlib import Path
from typing import Optional, List


from ..process import run_command
from ..git import find_file_upwards

__all__ = ["format_python_black"]


def _find_pyproject_toml(start_dir: Path, logger: logging.Logger) -> Optional[Path]:
    return find_file_upwards("pyproject.toml", start_dir, logger)


def format_python_black(
    code_content: str, logger: logging.Logger, file_path: Optional[Path] = None
) -> str:
    logger.debug("Trình định dạng Python (Black) được gọi.")

    command: List[str] = ["black", "--fast", "--quiet", "-"]
    description: str = "Đang chạy 'black' từ stdin"

    if file_path:
        start_dir = file_path.parent
        config_path = _find_pyproject_toml(start_dir, logger)
        if config_path:
            logger.debug(f"Đã tìm thấy cấu hình Black tại: {config_path.as_posix()}")
            command.extend(["--config", str(config_path)])
            description += f" (sử dụng config {config_path.name})"
        else:
            logger.debug(
                "Không tìm thấy pyproject.toml, sử dụng cài đặt Black mặc định."
            )

    try:
        success, output = run_command(
            command, logger, description=description, input_content=code_content
        )

        if success:
            return output
        else:

            logger.warning(
                f"⚠️ 'black' thất bại. Code có thể chứa lỗi cú pháp. Trả về nội dung gốc."
            )
            logger.debug(f"Black stderr: {output}")
            return code_content

    except FileNotFoundError:
        logger.error(
            "❌ Lỗi: Không tìm thấy lệnh 'black'. Hãy đảm bảo 'black' đã được cài đặt trong $PATH."
        )
        return code_content
    except Exception as e:
        logger.error(f"❌ Lỗi không mong muốn khi chạy 'black': {e}")
        return code_content
