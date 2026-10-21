"""启动局域网服务，供同一 WiFi 下的手机/平板访问看板。

用法：python serve.py [端口]
"""

import functools
import http.server
import os
import socket
import socketserver
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(BASE, "docs")


def lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("223.5.5.5", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=WEB)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("", port), handler) as httpd:
        ip = lan_ip()
        print("=" * 56)
        print(" ETF 300 share dashboard / 沪深300ETF份额看板")
        print("=" * 56)
        print(" 本机访问：   http://127.0.0.1:%d" % port)
        print(" 手机访问：   http://%s:%d" % (ip, port))
        print(" （手机需与电脑连接同一个 WiFi）")
        print(" 停止服务：   按 Ctrl+C")
        print("=" * 56)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n已停止")


if __name__ == "__main__":
    main()
