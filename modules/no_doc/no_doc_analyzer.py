# Path: modules/no_doc/no_doc_analyzer.py
"""
Docstring Removal logic using Python's AST (Abstract Syntax Tree)
để trích xuất vị trí, sau đó xóa bằng cách chỉnh sửa nội dung gốc (string)
để bảo toàn định dạng.
"""

import logging
import ast
from typing import Optional, Dict, Any, List
from pathlib import Path

__all__ = ["analyze_file_for_docstrings"]

# --- AST Helper: Trích xuất vị trí Docstring ---

def _get_docstring_info(node_body: List[ast.stmt]) -> Optional[Dict[str, Any]]:
    """
    Trích xuất docstring và vị trí dòng/cột của nó.
    Trả về None nếu không phải là docstring hợp lệ.
    """
    if (node_body and 
        isinstance(node_body[0], ast.Expr) and 
        isinstance(node_body[0].value, (ast.Constant))
    ):
        expr_node: ast.Expr = node_body[0]
        constant_node = expr_node.value
        
        # Docstring phải là chuỗi
        if not isinstance(constant_node.value, str):
            return None
            
        # Vị trí dòng bắt đầu và dòng kết thúc
        start_line = expr_node.lineno
        end_line = expr_node.end_lineno
        
        return {
            "start_line": start_line,
            "end_line": end_line,
            "col_offset": expr_node.col_offset,
            "end_col_offset": expr_node.end_col_offset,
            "value": constant_node.value,
        }
    return None

def _find_all_docstrings(tree: ast.Module) -> List[Dict[str, Any]]:
    """Duyệt qua AST để tìm tất cả docstring ở các cấp."""
    docstring_list: List[Dict[str, Any]] = []

    for node in ast.walk(tree):
        doc_info = None
        
        # Xử lý các node có thể chứa docstring
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            doc_info = _get_docstring_info(node.body)
            
        if doc_info:
            docstring_list.append(doc_info)
            
    return docstring_list

# --- Hàm chính ---

def analyze_file_for_docstrings(
    file_path: Path, 
    logger: logging.Logger
) -> Optional[Dict[str, Any]]:
    """
    Phân tích file Python, loại bỏ docstring bằng cách xóa dòng,
    và trả về nội dung mới.
    """
    
    original_lines: List[str] = []
    try:
        # Đọc file và giữ lại dấu xuống dòng (True)
        original_lines = file_path.read_text(encoding='utf-8').splitlines(keepends=True)
    except (IOError, UnicodeDecodeError) as e:
        logger.warning(f"⚠️ Bỏ qua file '{file_path.name}' do lỗi đọc/encoding: {e}")
        return None

    try:
        original_content = "".join(original_lines)
        tree = ast.parse(original_content)
        docstrings = _find_all_docstrings(tree)
        
        if not docstrings:
            return None # Không có docstring để xóa

        new_lines = list(original_lines)
        
        # Vì ta xóa dòng từ trên xuống, việc xóa có thể làm lệch vị trí 
        # dòng của các node bên dưới. Ta phải xóa từ DƯỚI LÊN (Reverse).
        # Docstrings có start_line và end_line khác nhau, nên ta chỉ cần
        # lấy chúng và sắp xếp theo thứ tự giảm dần của dòng bắt đầu.
        
        # Sắp xếp theo dòng kết thúc giảm dần (để xóa từ dưới lên)
        docstrings.sort(key=lambda d: d["end_line"], reverse=True)
        
        docstrings_removed_count = 0
        
        for doc_info in docstrings:
            start = doc_info["start_line"]
            end = doc_info["end_line"]
            
            # Chỉ số trong list (list index) = line number - 1
            start_index = start - 1
            end_index = end - 1
            
            # --- Xử lý xóa dòng ---
            
            # Dòng chứa docstring là: original_lines[start_index] đến original_lines[end_index]
            
            # Giả định: Docstring thường được bao quanh bởi dòng trống.
            # Ta sẽ xóa docstring VÀ dòng trống ngay trước nó (nếu có).
            
            # Chuỗi docstring thô (có thể bao gồm dấu ngoặc kép/ba)
            # Ta cần giữ lại dòng `def function():` 
            
            # Tìm dòng thực sự bắt đầu chuỗi (thường là dấu """)
            
            # Vì ta chỉ có dòng/cột: ta sẽ xóa toàn bộ các dòng từ start_index
            # đến end_index.
            del new_lines[start_index : end_index + 1]
            docstrings_removed_count += 1
            
        if docstrings_removed_count > 0:
            new_content = "".join(new_lines)
            
            logger.debug(f"Đã xóa {docstrings_removed_count} docstring khỏi file '{file_path.name}'")
            
            return {
                "path": file_path,
                "original_content": original_content,
                "new_content": new_content,
            }
        
    except SyntaxError as e:
        logger.warning(f"⚠️ Bỏ qua file '{file_path.name}' do lỗi cú pháp (SyntaxError): {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Lỗi không mong muốn khi phân tích AST/xóa dòng file '{file_path.name}': {e}")
        return None

    return None