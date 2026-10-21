"""板块估值榜：A 股 / 行业主题指数的估值指标与历史序列。

数据源
------
1. 蛋卷基金指数估值
   - 列表：GET https://danjuanfunds.com/djapi/index_eva/dj
     返回各指数当前的 PE、PB、ROE、股息率，以及 PE/PB 的历史百分位
   - 历史：GET https://danjuanfunds.com/djapi/index_eva/{pe|pb|roe}_history/{code}?day=all
2. 腾讯财经日线（仅 SH/SZ 指数）：板块价格走势

输出
----
docs/data/sector.js  ->  window.ETF_SECTOR = {...}
"""

import concurrent.futures as cf
import datetime as dt
import json
import os
import sys
import time
import urllib.request

DJ = "https://danjuanfunds.com"
QQ = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DATA = os.path.join(BASE_DIR, "docs", "data")
OUT = os.path.join(WEB_DATA, "sector.js")

TYPE_NAME = {"1": "宽基", "2": "策略·红利", "3": "行业主题"}
HIST_KEY = {"pe": "index_eva_pe_growths", "pb": "index_eva_pb_growths",
            "roe": "index_eva_roe_growths"}


def log(msg):
    print("[%s] %s" % (dt.datetime.now().strftime("%H:%M:%S"), msg), flush=True)


def _get(url, referer=DJ + "/", retries=4, timeout=30):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": referer,
                                                       "Accept": "application/json, text/plain, */*"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "ignore")
        except Exception as exc:
            last = exc
            time.sleep(1.2 * (i + 1))
    raise RuntimeError("请求失败 %s -> %s" % (url, last))


def region_of(code, name):
    if code.startswith("HK"):
        return "港股"
    if code.startswith("CSI"):
        return "中概"
    if code.startswith(("SH", "SZ")):
        return "A股"
    return "其他"


def eva_list():
    """蛋卷指数估值列表：当前 PE/PB/ROE/股息率 + 历史百分位。"""
    body = json.loads(_get(DJ + "/djapi/index_eva/dj"))
    items = body.get("data", {}).get("items", [])
    rows = []
    for it in items:
        code = it["index_code"]
        rows.append({
            "code": code,
            "name": it["name"],
            "type": it.get("ttype", "3"),
            "typeName": TYPE_NAME.get(it.get("ttype", "3"), "其他"),
            "region": region_of(code, it["name"]),
            "pe": round(it.get("pe") or 0, 3),
            "pb": round(it.get("pb") or 0, 3),
            "roe": round((it.get("roe") or 0) * 100, 2),
            "div": round((it.get("yeild") or 0) * 100, 2),
            "pePct": it.get("pe_percentile"),
            "pbPct": it.get("pb_percentile"),
            "date": it.get("date"),
            "eva": {"low": "低估", "mid": "适中", "high": "高估"}.get(it.get("eva_type"), "-"),
        })
    return rows


def history(code, kind):
    """历史估值序列 -> [(YYYY-MM-DD, value)]。"""
    try:
        body = json.loads(_get("%s/djapi/index_eva/%s_history/%s?day=all" % (DJ, kind, code),
                               retries=2, timeout=25))
    except Exception:
        return []
    arr = body.get("data", {}).get(HIST_KEY.get(kind, ""), []) or []
    out = []
    for it in arr:
        ts, v = it.get("ts"), it.get(kind)
        if not ts or v is None:
            continue
        d = dt.datetime.fromtimestamp(ts / 1000, dt.timezone.utc).strftime("%Y-%m-%d")
        out.append((d, round(float(v), 4)))
    return out


def monthly(series):
    """按自然月保留最后一个点。"""
    d = {}
    for date, v in series:
        d[date[:7]] = (date, v)
    return d


def kline(code, years=3):
    """腾讯日线 -> [(YYYY-MM-DD, close)]，失败返回空。"""
    if not code.startswith(("SH", "SZ")):
        return []
    tc = code.lower()
    end = dt.date.today()
    start = end - dt.timedelta(days=365 * years)
    n = 365 * years + 10
    url = "%s?param=%s,day,%s,%s,%d,qfq" % (QQ, tc, start.strftime("%Y-%m-%d"),
                                            end.strftime("%Y-%m-%d"), n)
    try:
        body = json.loads(_get(url, referer="https://gu.qq.com/", retries=2, timeout=25))
    except Exception:
        return []
    node = (body.get("data") or {}).get(tc) or {}
    arr = node.get("qfqday") or node.get("day") or []
    out = []
    for r in arr:
        try:
            out.append((r[0], round(float(r[2]), 4)))
        except (IndexError, ValueError):
            continue
    return out


def weekly(series):
    """每周保留最后一个点。"""
    d = {}
    for date, v in series:
        key = dt.datetime.strptime(date, "%Y-%m-%d").strftime("%G-W%V")
        d[key] = (date, v)
    return d


def _load_detail(code):
    pe_d = monthly(history(code, "pe"))
    pb_d = monthly(history(code, "pb"))
    roe_d = monthly(history(code, "roe"))
    months = sorted(set(pe_d) | set(pb_d) | set(roe_d))
    dates, pes, pbs, roes = [], [], [], []
    last = {"pe": None, "pb": None, "roe": None}
    for m in months:
        dates.append(m)
        for tag, arr in (("pe", pe_d), ("pb", pb_d), ("roe", roe_d)):
            if m in arr:
                last[tag] = arr[m][1]
        pes.append(last["pe"])
        pbs.append(last["pb"])
        roes.append(round(last["roe"] * 100, 2) if last["roe"] is not None else None)
    kx = weekly(kline(code))
    kdates = [v[0] for k, v in sorted(kx.items())]
    kclose = [v[1] for k, v in sorted(kx.items())]
    return code, {"dates": dates, "pe": pes, "pb": pbs, "roe": roes}, {"dates": kdates, "close": kclose}


def data_date(rows):
    """估值数据日期（蛋卷只给 MM-DD，补上年份）。"""
    for r in rows:
        d = r.get("date")
        if d:
            return "%d-%s" % (dt.date.today().year, d)
    return dt.date.today().strftime("%Y-%m-%d")


def build(workers=8):
    rows = eva_list()
    log("板块估值列表：%d 个指数" % len(rows))
    hist, kmap = {}, {}
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(_load_detail, r["code"]): r["code"] for r in rows}
        done = 0
        for f in cf.as_completed(futures):
            code = futures[f]
            try:
                code, h, k = f.result()
                hist[code] = h
                kmap[code] = k
            except Exception as exc:
                log("  %s 详情抓取失败：%s" % (code, exc))
            done += 1
            if done % 10 == 0:
                log("  已处理 %d/%d" % (done, len(rows)))

    def rank_key(r):
        pe_zero = (not r["pe"]) or r["pe"] <= 0
        pct = r["pePct"] if (r["pePct"] is not None and not pe_zero) else r["pbPct"]
        return (pct if pct is not None else 1,)

    sectors = [r for r in rows if r["type"] == "3"]
    sectors.sort(key=rank_key)
    a_shares = [r for r in sectors if r["region"] == "A股"]
    a_shares.sort(key=rank_key)
    # 默认榜单＝A 股行业主题（页面可切换到“全市场”）
    top = [r["code"] for r in (a_shares or sectors)[:10]]

    payload = {
        "meta": {
            "updatedAt": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "date": data_date(rows),
            "source": "蛋卷基金指数估值 / 腾讯财经日线",
            "count": len(rows),
            "note": "PE、PB 分位为蛋卷基于近 10 年数据的历史百分位；走势为近 3 年周频收盘",
        },
        "list": rows,
        "hist": hist,
        "kline": kmap,
        "top": top,
    }
    os.makedirs(WEB_DATA, exist_ok=True)
    txt = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("window.ETF_SECTOR = " + txt + ";\n")
    log("完成：%s（%.0f KB）" % (OUT, len(txt.encode("utf-8")) / 1024))
    return payload


if __name__ == "__main__":
    try:
        p = build()
        codes = p["top"]
        names = {r["code"]: r for r in p["list"]}
        log("估值最低 Top10（行业主题，按 PE 历史分位）")
        for c in codes:
            r = names[c]
            log("  %-10s %-12s PE=%-7s PB=%-6s ROE=%5s%% 股息=%5s%% PE分位=%-5s PB分位=%-5s %s"
                % (r["code"], r["name"], r["pe"] or "亏损", r["pb"], r["roe"], r["div"],
                   r["pePct"], r["pbPct"], r["eva"]))
    except Exception as exc:
        log("失败：%s" % exc)
        sys.exit(1)
