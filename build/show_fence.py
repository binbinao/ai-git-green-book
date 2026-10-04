#!/usr/bin/env python3
"""读指定文件第 idx 个围栏。"""
import re, sys
f, idx = sys.argv[1], int(sys.argv[2])
t = open(f, encoding='utf-8').read()
blocks = list(re.finditer(r'^```[\w-]*\n(.*?)^```', t, re.M | re.S))
print(blocks[idx].group(1))
