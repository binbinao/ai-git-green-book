#!/usr/bin/env python3
import re
from pathlib import Path
p = Path('build/book-final.typ')
body = p.read_text()
# 消除 "图 N -slug" 形式中的 " -" 残留
body = re.sub(r'图 (\d+) -([a-z])', r'图 \1 \2', body)
p.write_text(body)
print('done')
