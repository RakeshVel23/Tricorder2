import glob
import os

for f in glob.glob('e:/VSC/Tricorder2/src/ui/*.py'):
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    content = content.replace('template="plotly_dark"', 'template="plotly_white"')
    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)

print("Done")
