"""宏观与资金面指标抓取。

指标：
1. 两融余额（沪深两市合计）、融资余额、两融余额占 A 股流通市值比
2. 中国 10 年期 / 2 年期国债收益率
3. 沪深300 股息率（蛋卷当前真实值 + 按 PE 反推的历史近似值）
4. 全市场成交额（上证综指 + 深证综指）、沪深300 指数点位
"""

import datetime as dt
import json
import time
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
DC = "https://datacenter-web.eastmoney.com/api/data/v1/get"


def _get(url, referer, retries=6):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": referer,
                                                      "Accept": "application/json, text/plain, */*"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "ignore")
        except Exception as exc:
            last = exc
            time.sleep(2.0 * (i + 1))
    raise RuntimeError("请求失败 %s -> %s" % (url, last))


def _dc_all(report, date_field, start, extra=None, page_size=500):
    """分页取东财数据中心整张表。"""
    rows, page = [], 1
    while True:
        p = {"reportName": report, "columns": "ALL", "source": "WEB", "client": "WEB",
             "pageNumber": page, "pageSize": page_size,
             "sortColumns": date_field, "sortTypes": 1,
             "filter": "(%s>='%s')" % (date_field, start)}
        if extra:
            p.update(extra)
        url = DC + "?" + urllib.parse.urlencode(p)
        data = json.loads(_get(url, "https://data.eastmoney.com/"))
        block = data.get("result") or {}
        chunk = block.get("data") or []
        rows.extend(chunk)
        if len(chunk) < page_size or page >= (block.get("pages") or 1):
            break
        page += 1
        time.sleep(0.3)
    return rows


def fetch_margin(start="2021-01-01"):
    """两融：{date: {balance: 两融余额亿元, fin: 融资余额亿元, ratio: 占流通市值%}}"""
    out = {}
    for r in _dc_all("RPTA_RZRQ_LSHJ", "DIM_DATE", start):
        d = str(r.get("DIM_DATE", ""))[:10]
        if not d:
            continue
        def num(k, scale=1e8):
            v = r.get(k)
            try:
                return round(float(v) / scale, 4)
            except (TypeError, ValueError):
                return None
        out[d] = {"balance": num("RZRQYE"), "fin": num("RZYE"),
                  "ratio": round(float(r["RZYEZB"]), 4) if r.get("RZYEZB") else None}
    return out


def fetch_bond(start="2021-01-01"):
    """国债收益率：{date: {y10, y2}}（单位 %）"""
    out = {}
    for r in _dc_all("RPTA_WEB_TREASURYYIELD", "SOLAR_DATE", start):
        d = str(r.get("SOLAR_DATE", ""))[:10]
        if not d:
            continue
        y10, y2 = r.get("EMM00166466"), r.get("EMM00588704")
        out[d] = {"y10": float(y10) if y10 is not None else None,
                  "y2": float(y2) if y2 is not None else None}
    return out


def fetch_index_dividend(code="SH000300"):
    """沪深300 股息率：真实当前值 + 按 PE 反推的历史序列。

    返回 (current, {date: yield%})
    """
    detail = json.loads(_get("https://danjuanfunds.com/djapi/index_eva/detail/%s" % code,
                             "https://danjuanfunds.com/"))["data"]
    cur_yield, cur_pe = detail.get("yeild"), detail.get("pe")
    hist = json.loads(_get("https://danjuanfunds.com/djapi/index_eva/pe_history/%s?day=all" % code,
                           "https://danjuanfunds.com/"))["data"]["index_eva_pe_growths"]
    series = {}
    if cur_yield and cur_pe:
        for item in hist:
            ts, pe = item.get("ts"), item.get("pe")
            if not ts or not pe:
                continue
            d = dt.datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d")
            series[d] = round(cur_yield * cur_pe / pe * 100, 4)   # % 单位
    current = {"date": dt.datetime.fromtimestamp(detail["ts"] / 1000).strftime("%Y-%m-%d"),
               "divYield": round(cur_yield * 100, 4) if cur_yield else None,
               "pe": cur_pe, "pb": detail.get("pb")}
    return current, series


def fetch_index_kline(code, secid):
    """指数日线：{date: {close, amount(亿元)}}"""
    p = {"secid": secid, "fields1": "f1,f2,f3", "fields2": "f51,f53,f57",
         "klt": "101", "fqt": "0", "beg": "20210101", "end": "20500101", "lmt": "10000"}
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?" + urllib.parse.urlencode(p)
    data = json.loads(_get(url, "https://quote.eastmoney.com/"))
    out = {}
    for line in (data.get("data") or {}).get("klines") or []:
        parts = line.split(",")
        if len(parts) < 3:
            continue
        try:
            out[parts[0]] = {"close": float(parts[1]), "amount": round(float(parts[2]) / 1e8, 4)}
        except ValueError:
            continue
    return out


def fetch_market(start="2021-01-01"):
    """全市场成交额与沪深300 点位。

    :return: {date: {amount: 沪深两市成交额亿元, hs300: 沪深300 收盘}}
    """
    sh = fetch_index_kline("000001", "1.000001")     # 上证综指（沪市全部）
    time.sleep(2)
    sz = fetch_index_kline("399106", "0.399106")     # 深证综指（深市全部）
    time.sleep(2)
    hs = fetch_index_kline("000300", "1.000300")     # 沪深300
    out = {}
    for d in set(sh) | set(sz) | set(hs):
        if d < start:
            continue
        amt = (sh.get(d, {}).get("amount") or 0) + (sz.get(d, {}).get("amount") or 0)
        out[d] = {"amount": round(amt, 4) if amt else None,
                  "hs300": hs.get(d, {}).get("close")}
    return out
