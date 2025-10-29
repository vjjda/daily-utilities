# Path: utils/core/code_cleaner.py
"""
Tiện ích làm sạch mã nguồn Python, loại bỏ docstring và comment.
Sử dụng LibCST để đảm bảo giữ nguyên định dạng.
(Module nội bộ, được import bởi utils.core)
"""

import logging
from typing import Union, Sequence, Optional

# --- Import libcst ---
try:
    import libcst as cst
    # KHÔNG import AsyncFunctionDef, exceptions ở đây
    from libcst import BaseStatement, RemovalSentinel, RemoveFromParent
    LIBCST_AVAILABLE = True
except ImportError:
    LIBCST_AVAILABLE = False
    # Định nghĩa các lớp giả chỉ khi libcst KHÔNG cài đặt
    class CSTNode: pass
    class Comment(CSTNode): pass
    class Module(CSTNode): pass
    class ClassDef(CSTNode): pass
    class FunctionDef(CSTNode): pass
    class AsyncFunctionDef(CSTNode): pass
    BaseStatement = CSTNode # type: ignore [misc]
    RemovalSentinel = object() # type: ignore [misc, assignment]
    RemoveFromParent = object() # type: ignore [misc, assignment]
    class ParserSyntaxError(Exception): pass
    class VersionCannotParseError(Exception): pass

__all__ = ["clean_python_code"]

if LIBCST_AVAILABLE:
    class DocstringAndCommentRemover(cst.CSTTransformer):
        """
        Một CST Transformer tùy chỉnh để loại bỏ:
        1. Luôn luôn: Docstrings từ Module, Class, và Function.
        2. Tùy chọn (nếu all_clean=True): Tất cả các comments (trừ shebang).
        """
        def __init__(self, all_clean: bool = False):
            super().__init__()
            self.all_clean = all_clean

        def _find_docstring_index(self, body: Sequence[BaseStatement]) -> int:
            """Tìm index của statement là docstring trong body, nếu có."""
            if not body: return -1
            node = body[0]
            if isinstance(node, cst.SimpleStatementLine):
                if len(node.body) == 1 and isinstance(node.body[0], cst.Expr):
                    if isinstance(node.body[0].value, (cst.SimpleString, cst.ConcatenatedString)):
                        return 0
            return -1

        def leave_Comment(
            self, original_node: cst.Comment, updated_node: cst.Comment # type: ignore [valid-type]
        ) -> Union[cst.Comment, RemovalSentinel]: # type: ignore [valid-type]
            """Xóa comment nếu all_clean=True (trừ shebang)."""
            if not self.all_clean or original_node.value.startswith("#!"):
                return updated_node
            # SỬA LỖI: Trả về thể hiện RemoveFromParent()
            return RemoveFromParent() # pyright: ignore[reportCallIssue]

        def _remove_docstring_from_body(
            self, body: Sequence[BaseStatement]
        ) -> Optional[Sequence[BaseStatement]]:
            """Trả về body mới (tuple) nếu docstring được tìm thấy và xóa."""
            docstring_index = self._find_docstring_index(body)
            if docstring_index == 0: return body[1:]
            return None

        def leave_Module(
            self, original_node: cst.Module, updated_node: cst.Module # type: ignore [valid-type]
        ) -> cst.Module: # type: ignore [valid-type]
            """Xóa docstring ở cấp độ module."""
            new_body_tuple = self._remove_docstring_from_body(updated_node.body)
            if new_body_tuple is not None:
                return updated_node.with_changes(body=new_body_tuple)
            return updated_node

        def leave_ClassDef(
            self, original_node: cst.ClassDef, updated_node: cst.ClassDef # type: ignore [valid-type]
        ) -> cst.ClassDef: # type: ignore [valid-type]
            """Xóa docstring ở cấp độ class."""
            new_inner_body_tuple = self._remove_docstring_from_body(updated_node.body.body)
            if new_inner_body_tuple is not None:
                new_indented_block = updated_node.body.with_changes(body=new_inner_body_tuple)
                return updated_node.with_changes(body=new_indented_block)
            return updated_node

        def leave_FunctionDef(
            self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef # type: ignore [valid-type]
        ) -> cst.FunctionDef: # type: ignore [valid-type]
            """Xóa docstring ở cấp độ hàm (đồng bộ)."""
            new_inner_body_tuple = self._remove_docstring_from_body(updated_node.body.body)
            if new_inner_body_tuple is not None:
                new_indented_block = updated_node.body.with_changes(body=new_inner_body_tuple)
                return updated_node.with_changes(body=new_indented_block)
            return updated_node

        def leave_AsyncFunctionDef(
            # Sử dụng cst.AsyncFunctionDef và thêm type: ignore
            self, original_node: cst.AsyncFunctionDef, updated_node: cst.AsyncFunctionDef # type: ignore [attr-defined]
        ) -> cst.AsyncFunctionDef: # type: ignore [attr-defined]
            """Xóa docstring ở cấp độ hàm (bất đồng bộ)."""
            new_inner_body_tuple = self._remove_docstring_from_body(updated_node.body.body)
            if new_inner_body_tuple is not None:
                new_indented_block = updated_node.body.with_changes(body=new_inner_body_tuple)
                # Vẫn giữ ignore cho unbound-variable sai
                return updated_node.with_changes(body=new_indented_block) # type: ignore [unbound-variable]
            return updated_node

def clean_python_code(
    code_content: str,
    logger: logging.Logger,
    all_clean: bool = False
) -> str:
    """
    Loại bỏ docstring và tùy chọn comment khỏi một chuỗi mã nguồn Python.
    Args:
        code_content: Chuỗi chứa mã nguồn Python.
        logger: Logger để ghi log lỗi.
        all_clean: True để xóa cả comments (trừ shebang).
    Returns:
        Chuỗi mã nguồn đã được làm sạch, hoặc chuỗi gốc nếu có lỗi hoặc libcst không cài đặt.
    """
    if not LIBCST_AVAILABLE:
        # logger.error("...") # Đã log trước đó
        return code_content

    if not code_content.strip(): return code_content

    try:
        cst_module = cst.parse_module(code_content)
        transformer = DocstringAndCommentRemover(all_clean=all_clean)
        modified_tree = cst_module.visit(transformer)
        new_content = modified_tree.code
        return new_content

    # --- SỬA LỖI EXCEPTION HANDLING ---
    # Bắt các lỗi cụ thể của libcst nếu có thể, dùng AttributeError làm fallback
    except (getattr(cst, 'ParserSyntaxError', AttributeError)) as e: # type: ignore
        # Kiểm tra xem có phải là lỗi cú pháp thực sự không
        # (AttributeError sẽ không có raw_line/raw_column)
        if isinstance(e, AttributeError):
             # Nếu là AttributeError, có thể là lỗi khác, ném lại để except Exception bắt
             raise e from None

        # Xử lý ParserSyntaxError
        line = getattr(e, 'raw_line', '?')
        col = getattr(e, 'raw_column', '?')
        logger.warning(f"⚠️ Lỗi cú pháp Python (LibCST) tại dòng {line}, cột {col} khi làm sạch code: {getattr(e, 'message', str(e))}")
        return code_content # Trả về gốc
    except (getattr(cst, 'VersionCannotParseError', AttributeError)) as e: # type: ignore
        # Kiểm tra xem có phải là lỗi phiên bản thực sự không
        if isinstance(e, AttributeError):
             # Nếu là AttributeError, ném lại để except Exception bắt
             raise e from None

        # Xử lý VersionCannotParseError
        logger.warning(f"⚠️ Lỗi phiên bản grammar (LibCST) khi làm sạch code: {e}")
        return code_content # Trả về gốc
    except Exception as e:
        # Bắt tất cả các lỗi khác, bao gồm cả AttributeError từ các khối trên
        logger.warning(f"⚠️ Lỗi không xác định khi làm sạch code bằng LibCST: {e}")
        logger.debug("Traceback:", exc_info=True) # Log traceback để gỡ lỗi
        return code_content # Trả về gốc