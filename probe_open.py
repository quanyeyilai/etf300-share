"""查找 A 股新增开户数数据源。"""
import json
import re
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"


def get(url, referer="https://data.eastmoney.com/"):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": referer})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", "ignore")


print("---- 东财 cjsj 页面 reportName")
try:
    t = get("https://data.eastmoney.com/cjsj/")
    names = sorted(set(re.findall(r"RPT_ECONOMY_[A-Z_]+", t)))
    print("len", len(t), "names", names[:40])
    anchors = re.findall(r'href="(/cjsj/[a-z_]+\.html)"[^>]*>([^<]{2,18})<', t)
    for a in anchors[:40]:
        print(a)
except Exception as e:
    print("fail", e)

print("---- 猜测开户报表")
for rep in ["RPT_ECONOMY_NEWACCOUNT", "RPT_ECONOMY_ACCOUNT_NUM", "RPT_ECONOMY_INVESTOR_NUM",
            "RPT_ECONOMY_STOCK_ACCOUNT", "RPT_ECONOMY_OPEN_ACCOUNT"]:
    url = "https://datacenter-web.eastmoney.com/api/data/v1/get?" + urllib.parse.urlencode({
        "reportName": rep, "columns": "ALL", "source": "WEB", "client": "WEB", "pageNumber": 1, "pageSize": 2})
    try:
        r = get(url)
        ok = '"result":null' not in r
        print(rep, "->", "OK" if ok else "no-report", r[:120].replace("\n", " "))
        if ok:
            print(json.dumps(json.loads(r)["result"]["data"], ensure_ascii=False)[:300])
    except Exception as e:
        print(rep, "FAIL", e)
