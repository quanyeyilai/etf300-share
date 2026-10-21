"""探测沪深300估值（股息率）与开户数来源。"""
import json
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"


def get(url, referer="https://www.csindex.com.cn/"):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": referer,
                                               "Accept": "application/json, text/plain, */*"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", "ignore")


print("---- 中证 index-perf 全年")
try:
    t = get("https://www.csindex.com.cn/csindex-home/perf/index-perf?indexCode=000300&startDate=2026-01-01&endDate=2026-10-21")
    print(t[:600])
except Exception as e:
    print("fail", e)

print("---- 中证 其他估值接口")
for u in [
    "https://www.csindex.com.cn/csindex-home/index/indexValuation?indexCode=000300",
    "https://www.csindex.com.cn/csindex-home/indices/index-valuation?indexCode=000300",
    "https://www.csindex.com.cn/csindex-home/indexInfo/indexValuation?indexCode=000300",
    "https://www.csindex.com.cn/csindex-home/index/indexBasicInfo/getIndexBasicInfo?indexCode=000300&lang=zh_CN",
]:
    try:
        t = get(u)
        print("OK", u[-45:], t[:200].replace("\n", " "))
    except Exception as e:
        print("FAIL", u[-45:], e)

print("---- 东财单股行情是否含股息率（510300 附近试探字段）")
p = {"secids": "1.600519,1.601318", "fields": "f9,f23,f114,f133,f134,f135,f136,f137,f138,f139,f140,f141,f142"}
try:
    t = get("https://push2.eastmoney.com/api/qt/ulist.np/get?" + urllib.parse.urlencode(p), "https://quote.eastmoney.com/")
    print(t[:400])
except Exception as e:
    print("fail", e)

print("---- 中登/其他开户数据")
for u in ["https://www.chinaclear.cn/cms-web/articleList.do?type=statistics",
          "https://www.chinaclear.cn/zdjs/editor_file/2026/statistics/index.html"]:
    try:
        t = get(u, "https://www.chinaclear.cn/")
        print("OK", u[-50:], len(t), t[:150].replace("\n", " "))
    except Exception as e:
        print("FAIL", u[-50:], e)
