"""行情与净值数据抓取（东方财富公开接口）。

- 日线行情：收盘价、成交额、涨跌幅、换手率
- 基金单位净值：用于计算折溢价率与净流入金额
"""

import datetime as dt
import json
import random
import re
import time
import urllib.parse
import urllib.request

KLINE_URL = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
NAV_URL = "https://fund.eastmoney.com/pingzhongdata/%s.js"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"


def _get(url, referer, retries=3):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": referer})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "ignore")
        except Exception as exc:
            last = exc
            time.sleep(1.5 * (i + 1) + random.random())
    raise RuntimeError("请求失败 %s -> %s" % (url, last))


def secid(code):
    """沪市 1.xxxxxx，深市 0.xxxxxx"""
    return ("1." if code.startswith(("5", "6", "9", "11")) else "0.") + code


def fetch_kline(code, start="20210101", end="20500101"):
    """日线：返回 {date: {"close": 元, "amount": 元, "pct": %, "turnover": %}}"""
    params = {
        "secid": secid(code),
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f53,f57,f59,f61",
        "klt": "101",          # 日线
        "fqt": "0",            # 不复权：需与单位净值直接比较计算折溢价
        "beg": start,
        "end": end,
        "lmt": "10000",
    }
    url = KLINE_URL + "?" + urllib.parse.urlencode(params)
    raw = _get(url, "https://quote.eastmoney.com/")
    data = json.loads(raw)
    out = {}
    for line in (data.get("data") or {}).get("klines") or []:
        parts = line.split(",")
        if len(parts) < 5:
            continue
        d, close, amount, pct, turn = parts[0], parts[1], parts[2], parts[3], parts[4]
        try:
            out[d] = {
                "close": float(close),
                "amount": float(amount),
                "pct": float(pct),
                "turnover": float(turn),
            }
        except ValueError:
            continue
    return out


def fetch_nav(code):
    """单位净值序列：返回 {date: nav}"""
    raw = _get(NAV_URL % code, "https://fund.eastmoney.com/")
    m = re.search(r"var\s+Data_netWorthTrend\s*=\s*(\[.*?\]);", raw, re.S)
    if not m:
        return {}
    try:
        arr = json.loads(m.group(1))
    except ValueError:
        return {}
    out = {}
    for item in arr:
        ts = item.get("x")
        y = item.get("y")
        if not ts or y in (None, ""):
            continue
        try:
            d = dt.datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d")
            out[d] = float(y)
        except (ValueError, OSError):
            continue
    return out
