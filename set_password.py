"""修改看板的访问口令。

用法：
    python set_password.py 新口令

会重写 docs/index.html 中的口令摘要，然后执行：
    python build_single.py
    git push
"""

import hashlib
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(BASE, "docs", "index.html")
SALT = "etf300-share"


def fnv1a(s):
    h = 2166136261
    for b in s.encode("utf-8"):
        h ^= b
        h = (h * 16777619) & 0xFFFFFFFF
    return format(h, "08x")


def main():
    if len(sys.argv) < 2:
        print("用法：python set_password.py 新口令")
        return 1
    pwd = sys.argv[1].strip()
    if not pwd:
        print("口令不能为空")
        return 1
    sha = hashlib.sha256((SALT + pwd).encode()).hexdigest()
    fnv = fnv1a(SALT + pwd)

    html = open(PAGE, encoding="utf-8").read()
    pat = re.compile(r'(const AUTH = \{\s*salt: ")[^"]*(",\s*sha: ")[^"]*(",\s*fnv: ")[^"]*(")')
    if not pat.search(html):
        print("未在 index.html 中找到 AUTH 配置")
        return 1
    new = pat.sub(lambda m: m.group(1) + SALT + m.group(2) + sha + m.group(3) + fnv + m.group(4), html, count=1)
    with open(PAGE, "w", encoding="utf-8") as f:
        f.write(new)
    print("口令已更新：%s" % pwd)
    print("下一步：python build_single.py  &&  git add -A && git commit -m 'chore: 更新访问口令' && git push")
    return 0


if __name__ == "__main__":
    sys.exit(main())
