# Path: modules/no_doc/no_doc_analyzer.py
"""
Docstring Removal logic using Python's AST (Abstract Syntax Tree)
để trích xuất vị trí, sau đó xóa bằng cách chỉnh sửa nội dung gốc (string)
để bảo toàn định dạng.
"""

import logging
import ast
import re 
from typing import Optional, Dict, Any, List, cast
from pathlib import Path
# Thêm import cho Pygments
from pygments.token import Comment, Token
from pygments.lexers import PythonLexer
from pygments.formatters import RawTokenFormatter # Chỉ dùng cho Lexing/Untokenizing
# Thêm import cho module native Python để Lexing an toàn
import io
import tokenize

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
    """
    Loại bỏ tất cả comments (#) khỏi nội dung bằng Pygments Lexer an toàn.
    """
    lexer = PythonLexer()
    
    # 1. Tách token
    tokens = list(lexer.get_tokens(content))
    
    new_tokens = []
    
    # Dùng cờ để kiểm tra và giữ lại Shebang
    shebang_kept = False
    
    # Vị trí dòng/cột để theo dõi và thêm khoảng trắng
    last_end_row = 1
    last_end_col = 0
    
    for token_type, value in tokens:
        start_row, start_col = lexer.get_pos() # Pygments trả về vị trí sau token trước đó

        # 1. Kiểm tra Shebang: Pygments coi Shebang là Comment.
        if token_type is Comment.Hashbang and not shebang_kept:
             new_tokens.append((token_type, value))
             shebang_kept = True
             continue
             
        # 2. Bỏ qua tất cả các token COMMENT khác
        if token_type in [Comment, Comment.Single, Comment.Multiline]:
            continue

        # 3. Xử lý khoảng trắng/newline (để giữ format)
        
        # Nếu token là newline hoặc khoảng trắng, giữ nguyên
        if token_type is Token.Text:
             new_tokens.append((token_type, value))
             continue
             
        # Token code: Chỉ cần giữ lại code, Pygments đã xử lý khoảng trắng.
        new_tokens.append((token_type, value))
        
    # Lỗi: Pygments Lexer không có hàm untokenize. Phải dùng module `tokenize` 
    # của Python để nối lại, điều này có thể phá vỡ định dạng.
    # Tuy nhiên, ta có thể nối thủ công các giá trị token lại.
    
    new_content_lines: List[str] = []
    current_line = ""
    
    for token_type, value in new_tokens:
        if token_type is Token.Text:
            # Token Text bao gồm khoảng trắng và newline
            current_line += value
        else:
            # Nếu là token code, chỉ cần nối vào dòng hiện tại
            current_line += value

        # Nếu dòng kết thúc, bắt đầu dòng mới
        if current_line.endswith('\n'):
            new_content_lines.append(current_line)
            current_line = ""
            
    # Thêm dòng cuối cùng (nếu có)
    if current_line:
         new_content_lines.append(current_line)

    # Loại bỏ dòng chỉ chứa khoảng trắng/tab
    output_lines: List[str] = []
    for line in new_content_lines:
        if line.strip() or line == '\n':
            output_lines.append(line)
            
    # Loại bỏ các dòng trống liên tiếp > 1
    final_output: List[str] = []
    for line in output_lines:
        # Nếu dòng hiện tại là trống và dòng cuối cùng cũng trống -> Bỏ qua
        if not line.strip() and final_output and not final_output[-1].strip():
            continue
        final_output.append(line)
        
    return "".join(final_output)

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