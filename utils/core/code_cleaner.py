# Path: utils/core/code_cleaner.py
import logging
from typing import Dict, Final, Protocol, runtime_checkable


@runtime_checkable
class CodeCleaner(Protocol):
    def __call__(
        self, code_content: str, logger: logging.Logger, all_clean: bool = False
    ) -> str: ...


CLEANER_REGISTRY: Final[Dict[str, CodeCleaner]] = {}


def register_cleaner(language_id: str, cleaner_func: CodeCleaner) -> None:
    lang_id_lower = language_id.lower()
    if lang_id_lower in CLEANER_REGISTRY:
        logger = logging.getLogger("CodeCleanerRegistry")
        logger.warning(
            f"⚠️ Đang ghi đè cleaner đã đăng ký cho ngôn ngữ: {lang_id_lower}"
        )
    CLEANER_REGISTRY[lang_id_lower] = cleaner_func


__all__ = ["clean_code", "register_cleaner"]


def clean_code(
    code_content: str, language: str, logger: logging.Logger, all_clean: bool = False
) -> str:

    cleaner = CLEANER_REGISTRY.get(language.lower())

    if not cleaner:
        logger.debug(
            f"Không tìm thấy code cleaner nào được đăng ký cho ngôn ngữ '{language}'. Trả về nội dung gốc."
        )
        return code_content

    try:

        return cleaner(code_content, logger, all_clean)
    except Exception as e:
        logger.error(
            f"❌ Lỗi xảy ra trong quá trình làm sạch code cho '{language}': {e}"
        )
        logger.debug("Traceback:", exc_info=True)
        return code_content


try:
    from . import cleaners

    register_cleaner("python", cleaners.cleaner_python.clean_python_code)

    register_cleaner("javascript", cleaners.cleaner_js.clean_javascript_code)
    register_cleaner("js", cleaners.cleaner_js.clean_javascript_code)

    register_cleaner("shell", cleaners.cleaner_shell.clean_shell_code)
    register_cleaner("bash", cleaners.cleaner_shell.clean_shell_code)
    register_cleaner("sh", cleaners.cleaner_shell.clean_shell_code)
    register_cleaner("zsh", cleaners.cleaner_shell.clean_shell_code)


except ImportError as e:

    _registry_logger = logging.getLogger("CodeCleanerRegistry")
    _registry_logger.error(
        f"❌ Lỗi nghiêm trọng: Không thể import thư mục 'cleaners': {e}"
    )
