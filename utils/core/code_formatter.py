# Path: utils/core/code_formatter.py
import logging
from pathlib import Path
from typing import Protocol, runtime_checkable, Dict, Final, Optional


@runtime_checkable
class CodeFormatter(Protocol):
    def __call__(
        self,
        code_content: str,
        logger: logging.Logger,
        file_path: Optional[Path] = None,
    ) -> str: ...


FORMATTER_REGISTRY: Final[Dict[str, CodeFormatter]] = {}


def register_formatter(language_id: str, formatter_func: CodeFormatter) -> None:
    lang_id_lower = language_id.lower()
    if lang_id_lower in FORMATTER_REGISTRY:
        logger = logging.getLogger("CodeFormatterRegistry")
        logger.warning(
            f"⚠️ Đang ghi đè formatter đã đăng ký cho ngôn ngữ: {lang_id_lower}"
        )
    FORMATTER_REGISTRY[lang_id_lower] = formatter_func


__all__ = ["format_code", "register_formatter"]


def format_code(
    code_content: str,
    language: str,
    logger: logging.Logger,
    file_path: Optional[Path] = None,
) -> str:

    formatter = FORMATTER_REGISTRY.get(language.lower())

    if not formatter:
        logger.debug(
            f"Không tìm thấy code formatter nào được đăng ký cho ngôn ngữ '{language}'. Trả về nội dung gốc."
        )
        return code_content

    try:

        return formatter(code_content, logger, file_path)
    except Exception as e:
        logger.error(
            f"❌ Lỗi xảy ra trong quá trình định dạng code cho '{language}': {e}"
        )
        logger.debug("Traceback:", exc_info=True)
        return code_content


try:
    from . import formatters

    register_formatter("python", formatters.formatter_python.format_python_black)


except ImportError as e:
    _registry_logger = logging.getLogger("CodeFormatterRegistry")
    _registry_logger.error(
        f"❌ Lỗi nghiêm trọng: Không thể import thư mục 'formatters': {e}"
    )
