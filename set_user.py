"""管理看板登录账号。

账号保存在 data/users.txt（该文件不会上传 GitHub），每行一个：

    账号 密码

用法：
    python set_user.py                 查看现有账号
    python set_user.py 账号 密码        新增账号，或修改已有账号的密码
    python set_user.py --del 账号       删除账号

改完账号后重新生成页面：
    python build_single.py
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
USERS = os.path.join(BASE, "data", "users.txt")


def load():
    rows = []
    if not os.path.exists(USERS):
        return rows
    for line in open(USERS, encoding="utf-8").read().splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        parts = s.split()
        if len(parts) >= 2:
            rows.append((parts[0], " ".join(parts[1:])))
    return rows


def save(rows):
    os.makedirs(os.path.dirname(USERS), exist_ok=True)
    lines = ["# 看板登录账号，格式：账号 密码（每行一个）",
             "# 本文件仅存于本地，不会上传 GitHub", ""]
    lines += ["%s %s" % (u, p) for u, p in rows]
    with open(USERS, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    args = sys.argv[1:]
    rows = load()

    if not args:
        if not rows:
            print("还没有账号。新建一个：python set_user.py 账号 密码")
        else:
            print("现有 %d 个账号：" % len(rows))
            for u, _ in rows:
                print("  - " + u)
        return 0

    if args[0] == "--del":
        if len(args) < 2:
            print("用法：python set_user.py --del 账号")
            return 1
        name = args[1]
        left = [r for r in rows if r[0] != name]
        if len(left) == len(rows):
            print("账号不存在：" + name)
            return 1
        save(left)
        print("已删除账号：" + name)
        return 0

    if len(args) < 2:
        print("用法：python set_user.py 账号 密码")
        return 1

    user, pwd = args[0], " ".join(args[1:])
    names = [r[0] for r in rows]
    if user in names:
        rows = [(u, pwd if u == user else p) for u, p in rows]
        print("已修改密码：" + user)
    else:
        rows.append((user, pwd))
        print("已新增账号：" + user)
    save(rows)
    print("请运行 python build_single.py 重新生成页面")
    return 0


if __name__ == "__main__":
    sys.exit(main())
