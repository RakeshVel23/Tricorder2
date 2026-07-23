import os
import glob

replacements = {
    '"#6366f1"': '"#1a73e8"', # Indigo -> Google Blue
    '"#10b981"': '"#34a853"', # Emerald -> Google Green
    '"#f59e0b"': '"#fbbc04"', # Amber -> Google Yellow
    '"#ef4444"': '"#ea4335"', # Red -> Google Red
    '"#94a3b8"': '"#dadce0"', # Slate -> Google Border Gray
    'rgba(99, 102, 241, 0.1)': 'rgba(26, 115, 232, 0.1)', # Fill Blue
    'rgba(245, 158, 11, 0.1)': 'rgba(251, 188, 4, 0.1)', # Fill Yellow
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
        print(f"Updated colors to GA4 in {filepath}")
