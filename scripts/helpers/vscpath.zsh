#!/usr/bin/env zsh
# Path: scripts/helpers/vscpath.sh

# Đặt biến HOME cho môi trường Keyboard Maestro
HOME="${HOME}"

# Lấy URL, hoặc tên dự phòng
RAW_OUTPUT=$(/usr/bin/osascript <<'EOF'
tell application "System Events"
    try
        # 1. SỬA LỖI: Dùng đúng tên process "Electron" mà bạn đã xác định
        set vsCodeProcess to application process "Electron"
        
        # 2. Lấy cửa sổ đầu tiên (ổn định hơn focused)
        set frontWindow to first window of vsCodeProcess
        
        # 3. CÁCH MỚI (Ưu tiên): Thử lấy đường dẫn đầy đủ
        try
            # AXDocument trả về: "file:///Users/hieucao/Codes/daily-utilities/"
            set docURL to value of attribute "AXDocument" of frontWindow
            if docURL is not "" and docURL starts with "file://" then
                return docURL
            end if
        on error
            # Thất bại, chuyển sang CÁCH 2
        end try
        
        # 4. CÁCH CŨ (Dự phòng): Lấy tên từ tiêu đề
        set firstTitle to name of frontWindow
        if firstTitle contains " — " then
            set {TID, AppleScript's text item delimiters} to {AppleScript's text item delimiters, " — "}
            set projectName to last text item of firstTitle
            set AppleScript's text item delimiters to TID
            return "FALLBACK_NAME:" & projectName
        else if firstTitle is not "" then
             return "FALLBACK_NAME:" & firstTitle
        else
            return "ERROR: Active window has no title."
        end if
        
    on error e
        return "ERROR: " & e
    end try
end tell
EOF
)

# 1. Xử lý lỗi
if [[ "$RAW_OUTPUT" == "ERROR"* ]]; then
    echo "$RAW_OUTPUT" >&2
    exit 1
fi

PROJECT_PATH=""

# 2. Xử lý kết quả
if [[ "$RAW_OUTPUT" == "file://"* ]]; then
    # Trường hợp 1: Lấy được URL (Tốt nhất)
    PROJECT_PATH="${RAW_OUTPUT#file://}"
    # Giải mã URL (ví dụ: %20 -> ' ') bằng Zsh nội bộ
    PROJECT_PATH="${(%)PROJECT_PATH}"
    # Bỏ dấu / ở cuối (nếu có)
    PROJECT_PATH="${PROJECT_PATH%/}"
    
elif [[ "$RAW_OUTPUT" == "FALLBACK_NAME:"* ]]; then
    # Trường hợp 2: Fallback (logic cũ của bạn)
    PROJECT_NAME="${RAW_OUTPUT#FALLBACK_NAME:}"
    TRIMMED_PROJECT_NAME=$(echo "$PROJECT_NAME" | xargs)
    # Giữ nguyên giả định của bạn
    PROJECT_PATH="$HOME/Codes/$TRIMMED_PROJECT_NAME"
else
    # Thêm chi tiết lỗi
    echo "Lỗi: Output không mong đợi từ AppleScript: $RAW_OUTPUT" >&2
    exit 1
fi

# 3. Trả về
if [ -d "$PROJECT_PATH" ]; then
    echo "$PROJECT_PATH"
else
    echo "Lỗi: Đường dẫn $PROJECT_PATH không tồn tại (Output: $RAW_OUTPUT)." >&2
    exit 1
fi