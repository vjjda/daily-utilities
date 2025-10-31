# Path: utils/core/cleaners/cleaner_python.py
import logging
from typing import Union, Sequence, Optional

try:
    import libcst as cst
    from libcst import BaseStatement, RemovalSentinel, RemoveFromParent

    LIBCST_AVAILABLE = True
except ImportError:
    LIBCST_AVAILABLE = False

    class CSTNode:
        pass

    class Comment(CSTNode):
        pass

    class Module(CSTNode):
        pass

    class ClassDef(CSTNode):
        pass

    class FunctionDef(CSTNode):
        pass

    class AsyncFunctionDef(CSTNode):
        pass

    BaseStatement = CSTNode
    RemovalSentinel = object()
    RemoveFromParent = object()

    class ParserSyntaxError(Exception):
        pass

    class VersionCannotParseError(Exception):
        pass


__all__ = ["clean_python_code"]

if LIBCST_AVAILABLE:

    class DocstringAndCommentRemover(cst.CSTTransformer):
        def __init__(self, all_clean: bool = False):
            super().__init__()
            self.all_clean = all_clean

        def _find_docstring_index(self, body: Sequence[BaseStatement]) -> int:
            if not body:
                return -1
            node = body[0]
            if isinstance(node, cst.SimpleStatementLine):
                if len(node.body) == 1 and isinstance(node.body[0], cst.Expr):
                    if isinstance(
                        node.body[0].value, (cst.SimpleString, cst.ConcatenatedString)
                    ):
                        return 0
            return -1

        def leave_Comment(
            self, original_node: cst.Comment, updated_node: cst.Comment
        ) -> Union[cst.Comment, RemovalSentinel]:

            if not self.all_clean:
                return updated_node

            comment_text = original_node.value.strip()

            if (
                comment_text.startswith("#!")
                or comment_text.startswith("# Path:")
                or comment_text.startswith("# type: ignore")
                or comment_text.startswith("# pyright: ignore")
            ):
                return updated_node

            return RemoveFromParent()  # pyright: ignore[reportCallIssue]

        def _remove_docstring_from_body(
            self, body: Sequence[BaseStatement]
        ) -> Optional[Sequence[BaseStatement]]:
            docstring_index = self._find_docstring_index(body)
            if docstring_index == 0:
                return body[1:]
            return None

        def leave_Module(
            self, original_node: cst.Module, updated_node: cst.Module
        ) -> cst.Module:
            new_body_tuple = self._remove_docstring_from_body(updated_node.body)
            if new_body_tuple is not None:
                return updated_node.with_changes(body=new_body_tuple)
            return updated_node

        def leave_ClassDef(
            self, original_node: cst.ClassDef, updated_node: cst.ClassDef
        ) -> cst.ClassDef:
            new_inner_body_tuple = self._remove_docstring_from_body(
                updated_node.body.body
            )
            if new_inner_body_tuple is not None:
                new_indented_block = updated_node.body.with_changes(
                    body=new_inner_body_tuple
                )
                return updated_node.with_changes(body=new_indented_block)
            return updated_node

        def leave_FunctionDef(
            self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
        ) -> cst.FunctionDef:
            new_inner_body_tuple = self._remove_docstring_from_body(
                updated_node.body.body
            )
            if new_inner_body_tuple is not None:
                new_indented_block = updated_node.body.with_changes(
                    body=new_inner_body_tuple
                )
                return updated_node.with_changes(body=new_indented_block)
            return updated_node

        def leave_AsyncFunctionDef(
            self,
            original_node: cst.AsyncFunctionDef,  # pyright: ignore[reportAttributeAccessIssue]
            updated_node: cst.AsyncFunctionDef,  # pyright: ignore[reportAttributeAccessIssue]
        ) -> cst.AsyncFunctionDef:  # pyright: ignore[reportAttributeAccessIssue]
            new_inner_body_tuple = self._remove_docstring_from_body(
                updated_node.body.body
            )
            if new_inner_body_tuple is not None:
                new_indented_block = updated_node.body.with_changes(
                    body=new_inner_body_tuple
                )
                return updated_node.with_changes(body=new_indented_block)
            return updated_node

else:

    def clean_python_code(
        code_content: str, logger: logging.Logger, all_clean: bool = False
    ) -> str:
        logger.error(
            "❌ Thư viện 'libcst' không được cài đặt. Không thể làm sạch code Python."
        )
        return code_content


if LIBCST_AVAILABLE:

    def clean_python_code(
        code_content: str, logger: logging.Logger, all_clean: bool = False
    ) -> str:
        if not code_content.strip():
            return code_content

        try:
            cst_module = cst.parse_module(code_content)
            transformer = DocstringAndCommentRemover(all_clean=all_clean)
            modified_tree = cst_module.visit(transformer)
            new_content = modified_tree.code
            return new_content
        except getattr(cst, "ParserSyntaxError", AttributeError) as e:
            if isinstance(e, AttributeError):
                raise e from None
            line = getattr(e, "raw_line", "?")
            col = getattr(e, "raw_column", "?")
            logger.warning(
                f"⚠️ Lỗi cú pháp Python (LibCST) tại dòng {line}, cột {col} khi làm sạch code: {getattr(e, 'message', str(e))}"
            )
            return code_content
        except getattr(cst, "VersionCannotParseError", AttributeError) as e:
            if isinstance(e, AttributeError):
                raise e from None
            logger.warning(f"⚠️ Lỗi phiên bản grammar (LibCST) khi làm sạch code: {e}")
            return code_content
        except Exception as e:
            logger.warning(
                f"⚠️ Lỗi không xác định khi làm sạch code Python bằng LibCST: {e}"
            )
            logger.debug("Traceback:", exc_info=True)
            return code_content
