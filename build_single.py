"""把看板打包成单个 HTML 文件（数据 + ECharts 全部内联）。

生成的文件可直接发送到手机（微信/邮件/网盘）离线打开，无需网络与服务器。
用法：python build_single.py
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(BASE, "docs")
SRC = os.path.join(WEB, "index.html")
DATA = os.path.join(WEB, "data", "data.js")
MACRO = os.path.join(WEB, "data", "macro.js")
SECTOR = os.path.join(WEB, "data", "sector.js")
ECHARTS = os.path.join(WEB, "vendor", "echarts.min.js")
OUT = os.path.join(BASE, "沪深300ETF份额看板.html")

# 数据与依赖：缺哪一个就移除对应引用，保证单文件仍能打开
TAGS = [
    ('<script src="./data/data.js"></script>', DATA),
    ('<script src="./data/macro.js"></script>', MACRO),
    ('<script src="./data/sector.js"></script>', SECTOR),
    ('<script src="./vendor/echarts.min.js"></script>', ECHARTS),
]


def main():
    if not os.path.exists(DATA):
        print("未找到数据文件，请先运行 update.py")
        return 1
    html = open(SRC, encoding="utf-8").read()
    for tag, path in TAGS:
        if tag not in html:
            continue
        if not os.path.exists(path):
            html = html.replace(tag, "")
            print("缺少数据文件，已跳过：" + os.path.basename(path))
            continue
        inner = open(path, encoding="utf-8").read()
        html = html.replace(tag, "<script>\n" + inner + "\n</script>")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    size = os.path.getsize(OUT) / 1024.0
    print("已生成：%s（%.0f KB）" % (OUT, size))
    print("发送到手机后，用浏览器打开即可离线查看。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
