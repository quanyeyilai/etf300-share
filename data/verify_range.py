"""验证线上页面已包含区间联动代码。"""
import time
import urllib.request

UA = {"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"}
u = "https://quanyeyilai.github.io/etf300-share/?t=%d" % int(time.time())
b = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read().decode("utf-8", "ignore")
print("len", len(b))
for key in ["区间变化(", "区间净流入", "rangeName", "state.range = +b.dataset.n; renderAll()", 'id="gate"']:
    print("%-42s %s" % (key, key in b))
