"""探测交易结算资金（银证转账）接口，作为散户资金/开户的替代指标。"""
import re
import urllib.request

UA = {"User-Agent": "Mozilla/5.0", "Referer": "https://data.eastmoney.com/"}
url = "https://data.eastmoney.com/newstatic/js/cjsj/banktransfer.js"
t = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read().decode("utf-8", "ignore")
print("len", len(t))
print("reports", sorted(set(re.findall(r"RPT[A-Z_]+", t))))
i = t.find("columns")
print(t[max(0, i - 500):i + 500])
