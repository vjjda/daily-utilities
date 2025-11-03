#!/usr/bin/env zsh
# Path: scripts/vscpath.zsh

# Lấy tên project từ cửa sổ VSCode đang mở đầu tiên
PROJECT_NAME=$(/usr/bin/osascript <<'EOF'
tell application "System Events"
    try
        # Chỉ dùng logic lấy tên (name) từ process "Electron"
        # vì đây là cách duy nhất chạy nhanh (0.19s)
        set firstTitle to name of first window of application process "Electron"

        if firstTitle contains " — " then
            set {TID, AppleScript's text item delimiters} to {AppleScript's text item delimiters, " — "}
            set projectName to last text item of firstTitle
            set AppleScript's text item delimiters to TID
            return projectName
        else
            return firstTitle
        end if
    on error
        return "ERROR: VSCode không mở."
    end try
end tell
EOF
)

# 1. Xử lý lỗi và làm sạch
if [[ "$PROJECT_NAME" == *"ERROR"* ]]; then
    echo "Lỗi: VSCode không mở hoặc không có cửa sổ project." >&2
    exit 1
fi

# 2. Xóa khoảng trắng thừa (trim)
TRIMMED_PROJECT_NAME=$(echo "$PROJECT_NAME" | xargs)

# 3. Nối đường dẫn gốc và trả về (stdout)
if [ -n "$TRIMMED_PROJECT_NAME" ]; then
    PROJECT_PATH="$HOME/Codes/$TRIMMED_PROJECT_NAME"
    
    # Kiểm tra lần cuối xem đường dẫn "đoán" có tồn tại không
    if [ -d "$PROJECT_PATH" ]; then
        echo "$PROJECT_PATH"
    else
        echo "Lỗi: Đường dẫn $PROJECT_PATH không tồn tại (Tên đoán: $TRIMMED_PROJECT_NAME)." >&2
        exit 1
    fi
else
    echo "Lỗi: Không thể trích xuất tên project." >&2
    exit 1
fi