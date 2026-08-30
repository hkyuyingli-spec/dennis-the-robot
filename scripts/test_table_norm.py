import sys, os
sys.path.insert(0, os.getcwd())
from nutribot.format_utils import normalize_markdown_tables
s = "Here is some text\n4. Seasonal Adjustments | Season | Focus | |\nSpring | Move Qi | Gentle exercise | |\nMore text"
print('Original:\n'+s)
print('\nNormalized:\n'+normalize_markdown_tables(s))
