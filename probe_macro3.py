"""确认 10Y 国债字段、指数股息率与开户数接口。"""
import json
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"


def get(url, referer="https://data.eastmoney.com/"):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": referer})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", "ignore")


def dc(report, extra=None):
    p = {"reportName": report, "columns": "ALL", "source": "WEB", "client": "WEB", "pageNumber": 1, "pageSize": 3}
    if extra:
        p.update(extra)
    return "https://datacenter-web.eastmoney.com/api/data/v1/get?" + urllib.parse.urlencode(p)


print("---- 国债 2024-01-02 各字段")
u = dc("RPTA_WEB_TREASURYYIELD", {"sortColumns": "SOLAR_DATE", "sortTypes": -1,
                                 "filter": '(SOLAR_DATE=\'2024-01-02\')'})
try:
    d = json.loads(get(u))
    print(json.dumps(d["result"]["data"], ensure_ascii=False))
except Exception as e:
    print("fail", e)

print("---- 中证 index-perf 带日期")
for u in [
    "https://www.csindex.com.cn/csindex-home/perf/index-perf?indexCode=000300&startDate=2026-10-01&endDate=2026-10-21",
    "https://www.csindex.com.cn/csindex-home/perf/get-index-perf?indexCode=000300",
    "https://www.csindex.com.cn/csindex-home/indexInfo/index-basic-info?indexCode=000300",
]:
    try:
        t = get(u, "https://www.csindex.com.cn/")
        print("OK", u[-60:], t[:180].replace("\n", " "))
    except Exception as e:
        print("FAIL", u[-60:], e)

print("---- 东财指数估值 reportName")
for rep in ["RPT_INDEX_TSVAL", "RPT_VALUEINDEX_DET", "RPT_INDEXVALUE", "RPT_INDEX_VALUATION"]:
    try:
        t = get(dc(rep))
        print(rep, "->", t[:220].replace("\n", " "))
    except Exception as e:
        print(rep, "FAIL", e)

print("---- 开户/投资者 reportName")
for rep in ["RPT_ECONOMY_ACCOUNT", "RPT_ECONOMY_INVESTOR", "RPTA_WEB_INVESTOR", "RPT_ECONOMY_STOCK"]:
    try:
        t = get(dc(rep))
        print(rep, "->", t[:220].replace("\n", " "))
    except Exception as e:
        print(rep, "FAIL", e)

print("---- 全市场成交额（含深证综指）")
p = {"secids": "1.000001,0.399106", "fields": "f2,f3,f6,f12,f14"}
t = get("https://push2.eastmoney.com/api/qt/ulist.np/get?" + urllib.parse.urlencode(p), "https://quote.eastmoney.com/")
print(t[:400])
