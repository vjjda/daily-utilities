

import logging
from pathlib import Path
from typing import Optional, Dict, Any, Union, Sequence 

try:
    import libcst as cst
    from libcst import BaseStatement, RemovalSentinel, RemoveFromParent 
    LIBCST_AVAILABLE = True
except ImportError:
    LIBCST_AVAILABLE = False
    
    class BaseStatement: pass
    class RemovalSentinel: pass
    class RemoveFromParent: pass


__all__ = ["analyze_file_for_docstrings"]


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
                     if isinstance(node.body[0].value, (cst.SimpleString, cst.ConcatenatedString)):
                         return 0 
            
            return -1

        
        def leave_Comment(
            self, original_node: cst.Comment, updated_node: cst.Comment
        ) -> Union[cst.Comment, RemoveFromParent]:
            if not self.all_clean or original_node.value.startswith("#!"):
                return updated_node
            return RemoveFromParent()

        
        
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
            
            new_inner_body_tuple = self._remove_docstring_from_body(updated_node.body.body)
            if new_inner_body_tuple is not None:
                new_indented_block = updated_node.body.with_changes(body=new_inner_body_tuple)
                return updated_node.with_changes(body=new_indented_block)
            return updated_node

        def leave_FunctionDef(
            self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
        ) -> cst.FunctionDef:
            
            new_inner_body_tuple = self._remove_docstring_from_body(updated_node.body.body)
            if new_inner_body_tuple is not None:
                new_indented_block = updated_node.body.with_changes(body=new_inner_body_tuple)
                return updated_node.with_changes(body=new_indented_block)
            return updated_node

        def leave_AsyncFunctionDef(
            self, original_node: cst.AsyncFunctionDef, updated_node: cst.AsyncFunctionDef
        ) -> cst.AsyncFunctionDef:
            
            new_inner_body_tuple = self._remove_docstring_from_body(updated_node.body.body)
            if new_inner_body_tuple is not None:
                new_indented_block = updated_node.body.with_changes(body=new_inner_body_tuple)
                return updated_node.with_changes(body=new_indented_block)
            return updated_node


def analyze_file_for_docstrings(
    file_path: Path,
    logger: logging.Logger,
    all_clean: bool
) -> Optional[Dict[str, Any]]:

    if not LIBCST_AVAILABLE:
        logger.error("❌ Lỗi: Tính năng này yêu cầu thư viện 'libcst'.")
        logger.error("   Vui lòng cài đặt: pip install libcst")
        raise ImportError("Không tìm thấy LibCST. Vui lòng cài đặt: pip install libcst")

    try:
        original_content = file_path.read_text(encoding='utf-8')
        cst_module = cst.parse_module(original_content)
    except (IOError, UnicodeDecodeError) as e:
        logger.warning(f"⚠️ Bỏ qua file '{file_path.name}' do lỗi đọc/encoding: {e}")
        return None
    except cst.ParserSyntaxError as e:
        
        line = getattr(e, 'raw_line', '?')
        col = getattr(e, 'raw_column', '?')
        logger.warning(f"⚠️ Bỏ qua file '{file_path.name}' do lỗi cú pháp (LibCST) tại dòng {line}, cột {col}: {e.message}")
        return None
    except Exception as e:
        logger.warning(f"⚠️ Bỏ qua file '{file_path.name}' do lỗi parse không xác định: {e}")
        return None

    try:
        transformer = DocstringAndCommentRemover(all_clean=all_clean)
        modified_tree = cst_module.visit(transformer)
        new_content = modified_tree.code

        if new_content != original_content:
            return {
                "path": file_path,
                "original_content": original_content,
                "new_content": new_content,
            }
        return None
    except Exception as e:
        logger.error(f"❌ Lỗi không mong muốn khi biến đổi CST file '{file_path.name}': {e}")
        return None