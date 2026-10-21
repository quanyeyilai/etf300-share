"""把看板打包成单个 HTML 文件（加密数据 + ECharts 全部内联）。

生成的文件可直接发送到手机（微信 / 邮件 / 网盘）离线打开；
打开时需要输入账号密码解密，没有密码看不到任何数据。

用法：python build_single.py
"""

import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(BASE, "docs")
SRC = os.path.join(WEB, "index.html")
BUNDLE = os.path.join(WEB, "data", "bundle.js")
ECHARTS = os.path.join(WEB, "vendor", "echarts.min.js")
OUT = os.path.join(BASE, "沪深300ETF份额看板.html")

# 数据与依赖：缺哪一个就移除对应引用，保证单文件仍能打开
TAGS = [
    ('<script src="./data/bundle.js"></script>', BUNDLE),
    ('<script src="./vendor/echarts.min.js"></script>', ECHARTS),
]


def protect():
    """先把明文数据加密成 bundle.js（需要 data/users.txt 或环境变量 ETF_USERS）。"""
    try:
        r = subprocess.run(["node", os.path.join(BASE, "protect.js")],
                           capture_output=True, text=True)
    except FileNotFoundError:
        print("未找到 node，无法加密数据。请安装 Node.js 后重试。")
        return False
    if r.stdout and r.stdout.strip():
        print(r.stdout.strip())
    if r.returncode != 0:
        if r.stderr and r.stderr.strip():
            print(r.stderr.strip())
        return False
    return True


def main():
    if not os.path.exists(os.path.join(WEB, "data", "data.js")):
        print("未找到数据文件，请先运行 update.py")
        return 1
    if not protect():
        return 1
    html = open(SRC, encoding="utf-8").read()
    for tag, path in TAGS:
        if tag not in html:
            continue
        if not os.path.exists(path):
            html = html.replace(tag, "")
            print("缺少文件，已跳过：" + os.path.basename(path))
            continue
        inner = open(path, encoding="utf-8").read()
        html = html.replace(tag, "<script>\n" + inner + "\n</script>")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    size = os.path.getsize(OUT) / 1024.0
    print("已生成：%s（%.0f KB）" % (OUT, size))
    print("发送到手机后，用浏览器打开，输入账号密码即可查看。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
