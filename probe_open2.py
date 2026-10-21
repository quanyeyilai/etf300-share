"""查看全国股票交易统计表接口（可能含新增开户数）。"""
import json
import re
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"


def get(url, referer="https://data.eastmoney.com/"):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": referer})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", "ignore")


t = get("https://data.eastmoney.com/cjsj/gpjytj.html")
print("page len", len(t))
print("reports:", sorted(set(re.findall(r"RPT_[A-Z_]+", t)))[:20])
print("js files:", sorted(set(re.findall(r"/([a-zA-Z0-9_\-/]+\.js)", t)))[:15])

# 尝试常见报表名
for rep in ["RPT_ECONOMY_STOCK_TRADE", "RPTA_WEB_STOCK_TRADE", "RPT_ECONOMY_STOCKSTAT",
            "RPT_ECONOMY_TRADE_STAT", "RPT_STOCK_TRADE"]:
    url = "https://datacenter-web.eastmoney.com/api/data/v1/get?" + urllib.parse.urlencode({
        "reportName": rep, "columns": "ALL", "source": "WEB", "client": "WEB",
        "pageNumber": 1, "pageSize": 3, "sortColumns": "REPORT_DATE", "sortTypes": -1})
    try:
        r = get(url)
        print(rep, "->", r[:200].replace("\n", " "))
    except Exception as e:
        print(rep, "FAIL", e)
