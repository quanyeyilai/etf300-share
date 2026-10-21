"""批量生成看板登录账号（写入 data/users.txt，保留已有 admin）。"""

import os
import secrets
import string

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(BASE, "data", "users.txt")

# 去掉容易看错的字符：0 O 1 l I
CHARS = "".join(c for c in string.ascii_letters + string.digits if c not in "0O1lI")


def main():
    lines = [
        "# 看板登录账号，格式：账号 密码（每行一个，密码可含空格）",
        "# 本文件仅存于本地，不会上传 GitHub",
        "# 修改后请运行：python build_single.py",
        "",
        "admin etf300",
    ]
    made = []
    for i in range(1, 21):
        user = "etf%02d" % i
        pwd = "".join(secrets.choice(CHARS) for _ in range(12))
        lines.append("%s %s" % (user, pwd))
        made.append((user, pwd))
    open(PATH, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    for u, p in made:
        print(u, p)


if __name__ == "__main__":
    main()
