import sys
import os

# 將 main_project 的根目錄路徑添加到模組搜尋路徑中
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from python.common_utils import *

x = 'path/ttt.py'
print(get_basename(x))
