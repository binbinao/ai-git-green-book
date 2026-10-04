#!/usr/bin/env bash
# 出版级 PDF 构建管线：manuscript/ -> output/git-concept-map-full.pdf
#
# 用法：build/build.sh
#
# 七个步骤，每一步对应 REVIEW-v3-typeset-qa.md 里的一类问题；
# 第 6 步是复验闸门（qa_report.py 23 项 + 字体嵌入），任一不过则以非 0 退出。
set -uo pipefail
cd "$(dirname "$0")/.."

echo '[1/7] 重组书稿 manuscript/ -> build/book.md'
build/.venv/bin/python build/assemble.py >/dev/null

# --wrap=none 是关键：pandoc 默认把段落硬折到 ~72 列，折行在 Typst 里等价于
# 插入一个空格，于是「——」「；」这类禁则字符前面多出一个可断行点，折行后
# 就会落到行首（P2-17 的行首破折号就是这么来的）。
echo '[2/7] pandoc 转 Typst（markdown-smart, wrap=none）'
pandoc build/book.md -f markdown-smart -t typst --wrap=none -o build/book-body.typ

echo '[3/7] 后处理（表格列宽 / 章扉解析 / 行首行末禁则 / emoji 清理）'
build/.venv/bin/python build/postprocess.py

echo '[4/7] Typst 编译'
typst compile build/book-final.typ output/git-concept-map-full.pdf \
  --font-path ~/Library/Fonts --font-path /System/Library/Fonts

echo '[5/7] 配帖补页 + 版本行写回（finalize.py）'
build/.venv/bin/python build/finalize.py

echo '[6/7] 复验闸门'
QA=0
build/.venv/bin/python build/qa_report.py || QA=1
build/.venv/bin/python build/qa_fonts.py | tail -1 || QA=1

echo '[7/7] 完成。'
ls -la output/git-concept-map-full.pdf
if [ "$QA" -ne 0 ]; then
  echo '!! 复验未全部通过，见上面的 FAIL 行。' >&2
fi
exit "$QA"
