# Path: modules/no_doc/no_doc_analyzer.py
"""
Docstring Removal logic using Python's AST (Abstract Syntax Tree)
để trích xuất vị trí, sau đó xóa bằng cách chỉnh sửa nội dung gốc (string)
để bảo toàn định dạng.
"""

import logging
import ast
from typing import Optional, Dict, Any, List, cast
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
        
        # Thêm khai báo kiểu tường minh cho Type Checker
        constant_node: ast.Constant = cast(ast.Constant, expr_node.value)        
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
            "value": constant_node.value, # Pylance giờ đã biết constant_node có 'value'
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

def _remove_comments_from_content(content: str) -> str:
    """Loại bỏ tất cả comments (#) khỏi nội dung, ngoại trừ Shebang."""
    lines = content.splitlines(True) # Giữ dấu xuống dòng
    new_lines: List[str] = []
    
    if lines and lines[0].startswith('#!'):
        # Giữ lại Shebang
        new_lines.append(lines[0])
        lines.pop(0)

    for line in lines:
        stripped_line = line.lstrip() # Dùng lstrip để giữ indent của code
        if stripped_line.startswith('#'):
            # Bỏ qua dòng comment hoàn toàn
            continue
        
        # Tìm comment nội tuyến
        clean_line = line
        try:
            # Tách chuỗi theo dấu # (cần regex hoặc phân tích cú pháp để tránh string literals)
            # Tuy nhiên, để đơn giản, ta chỉ loại bỏ dấu # đầu tiên (rủi ro với string literal)
            # Dùng regex đơn giản để loại bỏ comment cuối dòng (thô sơ)
            # Vì ta đã xóa docstring (thường là string dài), rủi ro này được giảm bớt.
            # Tìm dấu '#' không nằm trong dấu nháy kép/đơn.
            
            # Giải pháp an toàn hơn: chỉ loại bỏ comment nếu nó đứng sau khoảng trắng
            parts = clean_line.split('#', 1)
            if len(parts) > 1:
                # Nếu phần trước dấu # KHÔNG phải là dấu nháy (heuristic đơn giản)
                if parts[0].strip() and not (parts[0].strip().endswith('"') or parts[0].strip().endswith("'")):
                    clean_line = parts[0].rstrip() + '\n' # Loại bỏ comment và khoảng trắng thừa
                else:
                    # Nếu là comment bên trong string hoặc dấu # là code, giữ nguyên
                    pass

            new_lines.append(clean_line)
        
        except Exception:
            new_lines.append(line) # Fallback

    return "".join(new_lines)


# --- Hàm chính ---

def analyze_file_for_docstrings(
    file_path: Path, 
    logger: logging.Logger,
    all_clean: bool # Thêm cờ all_clean
) -> Optional[Dict[str, Any]]:
    """
    Phân tích file Python, loại bỏ docstring, và tùy chọn comments.
    """
    
    # 1. Đọc nội dung gốc
    original_lines: List[str] = []
    try:
        original_lines = file_path.read_text(encoding='utf-8').splitlines(keepends=True)
    except (IOError, UnicodeDecodeError) as e:
        logger.warning(f"⚠️ Bỏ qua file '{file_path.name}' do lỗi đọc/encoding: {e}")
        return None
        
    original_content = "".join(original_lines)
    content_after_docstring_removal = original_content
    docstring_removed = False

    try:
        # 2. Xóa Docstrings (Dùng AST)
        tree = ast.parse(original_content)
        docstrings = _find_all_docstrings(tree)
        
        if docstrings:
            # Logic xóa docstring (dựa trên sắp xếp ngược, giống code gốc)
            new_lines = list(original_lines)
            docstrings.sort(key=lambda d: d["end_line"], reverse=True)
            
            for doc_info in docstrings:
                start = doc_info["start_line"]
                end = doc_info["end_line"]
                del new_lines[start - 1 : end] # Xóa dòng từ start đến end
            
            content_after_docstring_removal = "".join(new_lines)
            docstring_removed = True
            
        # 3. Xóa Comments (Nếu all_clean=True)
        content_after_all_cleaning = content_after_docstring_removal
        if all_clean:
            content_after_all_cleaning = _remove_comments_from_content(content_after_docstring_removal)
        
        # 4. So sánh và trả về kết quả
        if docstring_removed or (all_clean and content_after_all_cleaning != original_content):
            
            return {
                "path": file_path,
                "original_content": original_content,
                "new_content": content_after_all_cleaning,
            }
        
    except SyntaxError as e:
        logger.warning(f"⚠️ Bỏ qua file '{file_path.name}' do lỗi cú pháp (SyntaxError): {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Lỗi không mong muốn khi phân tích/xóa file '{file_path.name}': {e}")
        return None

    return None