"""探测宏观/资金面指标数据源。"""
import json
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"


def get(url, referer="https://data.eastmoney.com/"):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": referer})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", "ignore")


CASES = []

# 1) 两融余额（沪深两市合计，日频）
CASES.append(("两融", "https://datacenter-web.eastmoney.com/api/data/v1/get?" + urllib.parse.urlencode({
    "reportName": "RPTA_RZRQ_LSHJ", "columns": "ALL", "source": "WEB", "client": "WEB",
    "pageNumber": 1, "pageSize": 5, "sortColumns": "DIM_DATE", "sortTypes": -1})))

# 2) 中国 10 年期国债收益率
CASES.append(("国债", "https://datacenter-web.eastmoney.com/api/data/v1/get?" + urllib.parse.urlencode({
    "reportName": "RPTA_WEB_TREASURYYIELD", "columns": "ALL", "source": "WEB", "client": "WEB",
    "pageNumber": 1, "pageSize": 5, "sortColumns": "SOLAR_DATE", "sortTypes": -1})))

# 3) 中证指数（沪深300）估值/股息率
CASES.append(("中证300", "https://www.csindex.com.cn/csindex-home/index/indexTrend/getIndexTrend?indexCode=000300"))
CASES.append(("中证估值", "https://www.csindex.com.cn/csindex-home/index/indexBasicInfo/getIndexBasicInfo?indexCode=000300"))

# 4) 全市场成交额与涨跌家数（情绪代理）
CASES.append(("全市场", "https://push2.eastmoney.com/api/qt/ulist.np/get?" + urllib.parse.urlencode({
    "secids": "1.000001,0.399001,1.000300", "fields": "f1,f2,f3,f4,f6,f12,f14"})))

# 5) 乐咕：沪深300 股息率
CASES.append(("乐咕", "https://legulegu.com/api/stock-data/index-basic-pe?indexCode=000300&token=325843825a2a2b1e8d72d1b5a9c0b0a2"))

for name, url in CASES:
    try:
        t = get(url)
        print("=== %s OK len=%d" % (name, len(t)))
        print(t[:300].replace("\n", " "))
    except Exception as e:
        print("=== %s FAIL %s" % (name, e))
