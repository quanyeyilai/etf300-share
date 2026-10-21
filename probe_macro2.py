"""确认两融/国债字段含义，并探测股息率与开户数来源。"""
import json
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"


def get(url, referer="https://data.eastmoney.com/"):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": referer})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", "ignore")


def dc(report, page_size=3, sort="DIM_DATE"):
    return "https://datacenter-web.eastmoney.com/api/data/v1/get?" + urllib.parse.urlencode({
        "reportName": report, "columns": "ALL", "source": "WEB", "client": "WEB",
        "pageNumber": 1, "pageSize": page_size, "sortColumns": sort, "sortTypes": -1})


print("---- 两融字段")
d = json.loads(get(dc("RPTA_RZRQ_LSHJ")))
print(json.dumps(d["result"]["data"][0], ensure_ascii=False, indent=1))

print("---- 国债字段（2021 年对比）")
d = json.loads(get("https://datacenter-web.eastmoney.com/api/data/v1/get?" + urllib.parse.urlencode({
    "reportName": "RPTA_WEB_TREASURYYIELD", "columns": "ALL", "source": "WEB", "client": "WEB",
    "pageNumber": 1, "pageSize": 2, "sortColumns": "SOLAR_DATE", "sortTypes": 1})))
print(json.dumps(d["result"]["data"][0], ensure_ascii=False, indent=1))

print("---- 中证指数尝试")
for u in [
    "https://www.csindex.com.cn/csindex-home/index/indexBasicInfo/getIndexBasicInfo?indexCode=000300",
    "https://www.csindex.com.cn/csindex-home/perf/index-perf?indexCode=000300",
    "https://www.csindex.com.cn/csindex-home/indexInfo/index-basic-info?indexCode=000300",
    "https://www.csindex.com.cn/csindex-home/index/indexTrend/getIndexTrend?indexCode=000300&startDate=20240101&endDate=20241231",
]:
    try:
        t = get(u, "https://www.csindex.com.cn/")
        print("OK", u[:70], t[:160].replace("\n", " "))
    except Exception as e:
        print("FAIL", u[:70], e)

print("---- 开户/投资者数尝试")
for rep in ["RPT_ECONOMY_ACCOUNT", "RPT_ECONOMY_INVESTOR", "RPTA_WEB_INVESTOR", "RPT_ECONOMY_STOCK_ACCOUNT"]:
    try:
        t = get(dc(rep, 2))
        print(rep, "->", t[:200].replace("\n", " "))
    except Exception as e:
        print(rep, "FAIL", e)
