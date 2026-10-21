"""抓取 4 只沪深300ETF 每日份额，写入本地数据文件并生成网页所需数据。

用法：
    python update.py                # 增量更新到最新交易日
    python update.py --days 365     # 回填最近 365 个自然日（首次使用推荐）
    python update.py --rebuild --days 365   # 清空重抓
"""

import argparse
import csv
import datetime as dt
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetcher  # noqa: E402

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
WEB_DATA = os.path.join(BASE_DIR, "docs", "data")
CSV_PATH = os.path.join(DATA_DIR, "etf_shares.csv")

# 关注的基金：代码 -> (交易所, 展示名)
FUNDS = {
    "510300": ("SSE", "华泰柏瑞沪深300ETF"),
    "510310": ("SSE", "易方达沪深300ETF"),
    "510330": ("SSE", "华夏沪深300ETF"),
    "159919": ("SZSE", "嘉实沪深300ETF"),
}
SSE_CODES = [c for c, v in FUNDS.items() if v[0] == "SSE"]
SZSE_CODES = [c for c, v in FUNDS.items() if v[0] == "SZSE"]

SSE_WORKERS = 6
SZSE_CHUNK_DAYS = 170  # 深交所单次查询最长约 6 个月


def log(msg):
    print("[%s] %s" % (dt.datetime.now().strftime("%H:%M:%S"), msg), flush=True)


def load_rows():
    rows = {}
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, "r", encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                try:
                    rows[(r["date"], r["code"])] = {
                        "date": r["date"],
                        "code": r["code"],
                        "name": r.get("name", ""),
                        "share": float(r["share"]),
                    }
                except (KeyError, ValueError):
                    continue
    return rows


def save_rows(rows):
    os.makedirs(DATA_DIR, exist_ok=True)
    data = sorted(rows.values(), key=lambda x: (x["date"], x["code"]))
    with open(CSV_PATH, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "code", "name", "share"])
        for r in data:
            w.writerow([r["date"], r["code"], r["name"], "%.2f" % r["share"]])
    return data


def workdays(start, end):
    out = []
    d = start
    while d <= end:
        if d.weekday() < 5:
            out.append(d.strftime("%Y-%m-%d"))
        d += dt.timedelta(days=1)
    return out


def fetch_sse_range(dates):
    """并发抓取上交所多个日期，返回新增行列表。"""
    found = []
    if not dates:
        return found

    def one(d):
        try:
            return d, fetcher.fetch_sse(d)
        except Exception as exc:
            return d, {"__error__": str(exc)}

    done = 0
    with ThreadPoolExecutor(SSE_WORKERS) as ex:
        for d, res in ex.map(one, dates):
            done += 1
            if "__error__" in res:
                log("  上交所 %s 抓取失败：%s" % (d, res["__error__"]))
                continue
            hit = {c: res[c] for c in SSE_CODES if c in res}
            if hit:
                for c, v in hit.items():
                    found.append({"date": d, "code": c, "name": v["name"], "share": v["share"]})
            if done % 20 == 0 or done == len(dates):
                log("  上交所进度 %d/%d" % (done, len(dates)))
    return found


def fetch_szse_range(start, end):
    """分段抓取深交所区间数据，返回新增行列表。"""
    found = []
    if not SZSE_CODES:
        return found
    s = dt.datetime.strptime(start, "%Y-%m-%d").date()
    e = dt.datetime.strptime(end, "%Y-%m-%d").date()
    chunks = []
    while s <= e:
        c_end = min(s + dt.timedelta(days=SZSE_CHUNK_DAYS), e)
        chunks.append((s.strftime("%Y-%m-%d"), c_end.strftime("%Y-%m-%d")))
        s = c_end + dt.timedelta(days=1)
    for code in SZSE_CODES:
        for cs, ce in chunks:
            try:
                rows = fetcher.fetch_szse(code, cs, ce)
            except Exception as exc:
                log("  深交所 %s %s~%s 抓取失败：%s" % (code, cs, ce, exc))
                continue
            for r in rows:
                if r["code"] == code:
                    found.append({"date": r["date"], "code": code,
                                  "name": r["name"] or FUNDS[code][1], "share": r["share"]})
            log("  深交所 %s %s~%s 获取 %d 条" % (code, cs, ce, len(rows)))
    return found


def build_web_data(rows):
    dates = sorted({r["date"] for r in rows})
    series = {}
    meta_funds = []
    for code, (ex, display) in FUNDS.items():
        by_date = {r["date"]: r["share"] for r in rows if r["code"] == code}
        series[code] = [by_date.get(d) for d in dates]
        raw_name = next((r["name"] for r in rows if r["code"] == code and r["name"]), "")
        meta_funds.append({"code": code, "name": display, "rawName": raw_name, "exchange": ex})
        meta_funds[-1]["latest"] = by_date.get(dates[-1]) if dates else None
    totals = []
    for i, d in enumerate(dates):
        vals = [series[c][i] for c in FUNDS if series[c][i] is not None]
        totals.append(round(sum(vals), 2) if vals else None)
    payload = {
        "meta": {
            "updatedAt": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "latestDate": dates[-1] if dates else "",
            "startDate": dates[0] if dates else "",
            "count": len(dates),
            "unit": "万份",
        },
        "funds": meta_funds,
        "dates": dates,
        "series": series,
        "totals": totals,
    }
    os.makedirs(WEB_DATA, exist_ok=True)
    with open(os.path.join(WEB_DATA, "data.js"), "w", encoding="utf-8") as f:
        f.write("window.ETF_DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n")
    with open(os.path.join(WEB_DATA, "data.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    return payload


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=None, help="抓取最近 N 个自然日（默认：从已有数据最后日期增量到今天，首次默认 365）")
    ap.add_argument("--rebuild", action="store_true", help="清空已有数据重新抓取")
    ap.add_argument("--only", choices=["sse", "szse"], help="只抓取指定交易所")
    args = ap.parse_args()

    rows = {} if args.rebuild else load_rows()
    today = dt.date.today()
    if args.days:
        start = today - dt.timedelta(days=args.days)
    elif rows:
        last = max(r["date"] for r in rows.values())
        start = dt.datetime.strptime(last, "%Y-%m-%d").date()  # 含最后一天，便于覆盖修正
    else:
        start = today - dt.timedelta(days=365)

    if start > today:
        start = today
    log("抓取区间：%s ~ %s（%s）" % (start, today, "重建" if args.rebuild else "增量"))

    added = []
    if args.only != "szse":
        dates = workdays(start, today)
        log("上交所待抓工作日 %d 天" % len(dates))
        added += fetch_sse_range(dates)
    if args.only != "sse":
        log("深交所按区间抓取 %s" % ",".join(SZSE_CODES))
        added += fetch_szse_range(start.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"))

    for r in added:
        if r["share"] and r["share"] > 0:
            rows[(r["date"], r["code"])] = r
    log("新增/更新记录 %d 条，累计 %d 条" % (len(added), len(rows)))

    data = save_rows(rows)
    payload = build_web_data(data)
    log("最新数据日期：%s（共 %d 个交易日，%d 条记录）"
        % (payload["meta"]["latestDate"], payload["meta"]["count"], len(data)))
    log("完成：%s" % os.path.join(WEB_DATA, "data.js"))


if __name__ == "__main__":
    main()
