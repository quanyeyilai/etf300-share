"""探测蛋卷指数估值接口（沪深300 股息率）与开户数据。"""
import json
import urllib.request

UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"


def get(url, referer="https://danjuanfunds.com/"):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": referer})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", "ignore")


for u in [
    "https://danjuanfunds.com/djapi/index_eva/detail/SH000300",
    "https://danjuanfunds.com/djapi/index_eva/pe_history/SH000300?day=all",
    "https://danjuanfunds.com/djapi/index_eva/pb_history/SH000300?day=all",
]:
    try:
        t = get(u)
        print("OK", u, len(t))
        print(t[:400])
    except Exception as e:
        print("FAIL", u, e)
