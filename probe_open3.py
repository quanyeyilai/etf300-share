"""读取 gpjytj.js，寻找全国股票交易统计接口（含新增开户数则使用）。"""
import re
import urllib.request

UA = {"User-Agent": "Mozilla/5.0", "Referer": "https://data.eastmoney.com/"}
url = "https://data.eastmoney.com/newstatic/js/cjsj/gpjytj.js"
t = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read().decode("utf-8", "ignore")
print("len", len(t))
print("reports", sorted(set(re.findall(r"RPT[A-Z_]+", t))))
print("urls", sorted(set(re.findall(r"/api/[a-zA-Z0-9_/\-]+", t)))[:10])
idx = t.find("reportName")
print(t[max(0, idx - 400):idx + 600] if idx > 0 else t[:600])
