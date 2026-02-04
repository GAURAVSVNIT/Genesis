lines = []
with open("apps/backend/api/v1/content.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# 1-indexed to 0-indexed: 414 -> 413, 802 -> 801
start_idx = 413
end_idx = 802

with open("apps/backend/api/v1/content.py", "w", encoding="utf-8") as f:
    for i, line in enumerate(lines):
        if start_idx <= i <= end_idx:
            # Add 4 spaces only if line is not empty (preserve empty lines logic if needed, but python tolerates indented empty lines)
            if line.strip():
                f.write("    " + line)
            else:
                f.write(line)
        else:
            f.write(line)

print("Indentation fixed.")
