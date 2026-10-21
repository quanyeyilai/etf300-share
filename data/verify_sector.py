"""线上验证板块估值榜是否已部署。"""

import json
import time
import urllib.request

UA = {"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"}
BASE = "https://quanyeyilai.github.io/etf300-share/"


def fetch(path):
    u = BASE + path + "?t=%d" % int(time.time())
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40).read().decode("utf-8", "ignore")


for i in range(8):
    try:
        html = fetch("")
        sec = fetch("data/sector.js")
        d = json.loads(sec[sec.find("=") + 1:].rstrip().rstrip(";"))
        top = d.get("top") or []
        names = {r["code"]: r["name"] for r in d.get("list", [])}
        ok = ("板块估值榜" in html) and len(top) == 10
        print("try", i, "index", len(html), "sector KB", len(sec) // 1024,
              "top10", [names.get(c, c) for c in top][:4], "OK", ok)
        if ok:
            break
    except Exception as exc:
        print("try", i, "fail", exc)
    time.sleep(40)
