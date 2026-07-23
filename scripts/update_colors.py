import os
import glob

# Old colors to new modern colors
replacements = {
    '"#3b9eff"': '"#6366f1"', # Indigo
    '"#00c9a7"': '"#10b981"', # Emerald
    '"#ffb347"': '"#f59e0b"', # Amber
    '"#51cf66"': '"#10b981"', # Emerald (merge with success)
    '"#ff6b6b"': '"#ef4444"', # Red
    '"#5c7a94"': '"#94a3b8"', # Muted slate for neutral lines
    'rgba(59, 158, 255, 0.1)': 'rgba(99, 102, 241, 0.1)', # Light indigo fill
    'rgba(255,179,71,0.1)': 'rgba(245, 158, 11, 0.1)', # Light amber fill
    'rgba(52, 152, 219, 0.1)': 'rgba(99, 102, 241, 0.1)', # Used in dynamic graph
}

for filepath in glob.glob("src/ui/**/*.py", recursive=True):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    modified = content
    for old, new in replacements.items():
        modified = modified.replace(old, new)
        
    if modified != content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(modified)
        print(f"Updated colors in {filepath}")
