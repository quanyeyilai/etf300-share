"""每日速报：把「估值最低 10 个板块 + 恐惧贪婪指数」推送到微信。

支持的微信通道（任配一个环境变量即可，都配则全部发送）
------------------------------------------------------
1. PushPlus（微信公众号，免费、推荐）
   PUSHPLUS_TOKEN=你的 token
   可选 PUSHPLUS_TOPIC=群组编码（一对多推送时填）
2. Server酱（微信服务号）
   SERVERCHAN_KEY=你的 SendKey（SCT 开头）
3. 企业微信机器人
   WECOM_WEBHOOK=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxx

用法
----
python notify.py            正式推送
python notify.py --dry-run  只打印内容，不发送
python notify.py --n 5      Top N 板块（默认 10）
"""

import datetime as dt
import hashlib
import json
import os
import sys
import urllib.parse
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
SECTOR = os.path.join(BASE, "docs", "data", "sector.js")
MACRO = os.path.join(BASE, "docs", "data", "macro.js")
LAST = os.path.join(BASE, "data", "notify_last.json")
# 上一日榜单代码：仅本地保存（不入库），云端靠 Actions 缓存
CODES = os.path.join(BASE, "data", "notify_codes.txt")
SITE = "https://quanyeyilai.github.io/etf300-share/"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"


def log(m):
    print("[%s] %s" % (dt.datetime.now().strftime("%H:%M:%S"), m), flush=True)


def load_js(path):
    t = open(path, encoding="utf-8").read()
    return json.loads(t[t.find("=") + 1:].rstrip().rstrip(";"))


def last_of(arr):
    for v in reversed(arr or []):
        if v is not None:
            return v
    return None


def prev_of(arr):
    seen = False
    for v in reversed(arr or []):
        if v is None:
            continue
        if seen:
            return v
        seen = True
    return None


def top_sectors(sec, n, a_only=True):
    rows = sec["list"]
    if a_only:
        rows = [r for r in rows if r["region"] == "A股" and r["type"] == "3"]

    def key(r):
        if r.get("pe") and r["pe"] > 0 and r.get("pePct") is not None:
            return r["pePct"]
        return r["pbPct"] if r.get("pbPct") is not None else 1
    rows = sorted(rows, key=key)
    return rows[:n]


def pct(v):
    return "-" if v is None else "%.1f%%" % (v * 100)


def build_content(top_n=10):
    sec = load_js(SECTOR)
    mac = load_js(MACRO) if os.path.exists(MACRO) else {}
    date = sec["meta"].get("date") or sec["meta"]["updatedAt"][:10]

    rows = top_sectors(sec, top_n)
    lines = ["**【ETF 看板 · 每日速报】**", date, ""]

    # 市场情绪
    em, fng = mac.get("emotion") or [], mac.get("fng") or []
    ev, fv = last_of(em), last_of(fng)
    ep, fp = prev_of(em), prev_of(fng)
    if fv is not None:
        label = "极度恐惧" if fv < 20 else "恐惧" if fv < 40 else "中性" if fv < 60 else \
                "贪婪" if fv < 80 else "极度贪婪"
        d = "" if fp is None else "（较昨日 %+.1f）" % (fv - fp)
        lines += ["**恐惧贪婪指数 %.1f · %s**%s" % (fv, label, d), ""]
    if ev is not None:
        d = "" if ep is None else "（较昨日 %+.1f）" % (ev - ep)
        lines.append("情绪温度 %.1f%s" % (ev, d))
    bal = last_of(mac.get("margin", {}).get("balance"))
    ratio = last_of(mac.get("margin", {}).get("ratio"))
    if bal:
        lines.append("两融余额 %.2f 万亿%s" % (bal / 10000,
                     "" if ratio is None else " · 占流通市值 %.2f%%" % ratio))
    lines.append("")

    # 榜单
    lines.append("**估值最低 %d 个板块**（A股行业主题，按 PE 历史分位）" % len(rows))
    for i, r in enumerate(rows, 1):
        pe = "亏损" if not r["pe"] or r["pe"] <= 0 else "%.2f" % r["pe"]
        lines.append("%d. **%s**  PE %s（%s）  PB %.2f（%s）  ROE %.1f%%  股息 %.2f%%"
                     % (i, r["name"], pe, pct(r["pePct"]), r["pb"], pct(r["pbPct"]),
                        r["roe"], r["div"]))
    lines.append("")

    # 与上次对比
    now_codes = [r["code"] for r in rows]
    names = {r["code"]: r["name"] for r in sec["list"]}
    changes = ""
    old_codes = []
    if os.path.exists(CODES):
        try:
            old_codes = [x.strip() for x in open(CODES, encoding="utf-8").read().splitlines() if x.strip()]
        except Exception:
            old_codes = []
    else:
        old = {}
        if os.path.exists(LAST):
            try:
                old = json.load(open(LAST, encoding="utf-8"))
            except Exception:
                old = {}
        old_codes = old.get("codes") or []
    if old_codes:
        new_in = [c for c in now_codes if c not in old_codes]
        out = [c for c in old_codes if c not in now_codes]
        if new_in or out:
            lines.append("**榜单变化**")
            for c in new_in:
                lines.append("· 新进：%s" % names.get(c, c))
            for c in out:
                lines.append("· 跌出：%s" % names.get(c, c))
        else:
            lines.append("**榜单变化**：前 %d 名与上一交易日一致" % len(rows))
        lines.append("")

    lines.append("完整榜单与图表：" + SITE)
    content = "\n".join(lines)

    rec = {"codes": now_codes, "date": date, "fng": fv, "emotion": ev}
    fp = fingerprint(rec)
    # 入库的标记里只保留日期与指纹，不含榜单代码和指标
    json.dump({"date": date, "hash": fp}, open(LAST, "w", encoding="utf-8"), ensure_ascii=False)
    try:
        open(CODES, "w", encoding="utf-8").write("\n".join(now_codes))
    except Exception:
        pass
    # 网页上只放「日期 + 指纹」，不含榜单代码与任何指标
    try:
        json.dump({"date": date, "hash": fp},
                  open(os.path.join(BASE, "docs", "data", "notify_last.json"),
                       "w", encoding="utf-8"), ensure_ascii=False)
    except Exception:
        pass
    return content, date, len(rows), fp


def fingerprint(rec):
    """当日内容指纹，仅用于本地/云端去重，不泄露榜单与指标。"""
    raw = json.dumps({"c": rec.get("codes"), "f": rec.get("fng"), "e": rec.get("emotion")},
                     ensure_ascii=False, sort_keys=True)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()[:8]


def pushed_online(date, fp=None):
    """网页上是否已记录今天的推送（云端推送过的标志）。"""
    try:
        req = urllib.request.Request(SITE + "data/notify_last.json", headers={"User-Agent": UA})
        j = json.loads(urllib.request.urlopen(req, timeout=12).read().decode("utf-8", "ignore"))
        if j.get("date") != date:
            return False
        return (not fp) or (not j.get("hash")) or (j.get("hash") == fp)
    except Exception:
        return False


# ---------------- 各通道发送 ----------------
def _post(url, data, form=False, headers=None, timeout=20):
    if form:
        body = urllib.parse.urlencode(data).encode("utf-8")
        hd = {"Content-Type": "application/x-www-form-urlencoded"}
    else:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        hd = {"Content-Type": "application/json"}
    if headers:
        hd.update(headers)
    req = urllib.request.Request(url, data=body, headers=hd)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")


def send_pushplus(title, content):
    token = os.environ.get("PUSHPLUS_TOKEN")
    if not token:
        return None
    data = {"token": token, "title": title, "content": content, "template": "markdown"}
    topic = os.environ.get("PUSHPLUS_TOPIC")
    if topic:
        data["topic"] = topic
    return _post("https://www.pushplus.plus/send", data)


def send_serverchan(title, content):
    key = os.environ.get("SERVERCHAN_KEY")
    if not key:
        return None
    return _post("https://sctapi.ftqq.com/%s.send" % key,
                 {"title": title, "desp": content}, form=True)


def send_wecom(title, content):
    hook = os.environ.get("WECOM_WEBHOOK")
    if not hook:
        return None
    return _post(hook, {"msgtype": "markdown",
                        "markdown": {"content": content}})


def load_config():
    """从 data/notify_config.json 读取配置（该文件不入库，避免泄露 token）。"""
    path = os.path.join(BASE, "data", "notify_config.json")
    if not os.path.exists(path):
        return
    try:
        cfg = json.load(open(path, encoding="utf-8"))
    except Exception as exc:
        log("配置文件读取失败：%s" % exc)
        return
    for k in ("PUSHPLUS_TOKEN", "PUSHPLUS_TOPIC", "SERVERCHAN_KEY", "WECOM_WEBHOOK"):
        if cfg.get(k) and not os.environ.get(k):
            os.environ[k] = str(cfg[k])


def main():
    load_config()
    dry = "--dry-run" in sys.argv
    n = 10
    if "--n" in sys.argv:
        try:
            n = int(sys.argv[sys.argv.index("--n") + 1])
        except (IndexError, ValueError):
            pass

    force = "--force" in sys.argv
    content, date, rows, fp = build_content(n)
    title = "%s 板块估值榜 Top%d" % (date, rows)

    # 云端（GitHub Actions）已经推过当天的内容时，本地不再重复推
    if not force and not dry and pushed_online(date, fp):
        log("云端今日（%s）已推送，跳过本地重复推送" % date)
        return 0

    if dry:
        print("-" * 60)
        print("标题：" + title)
        print("-" * 60)
        print(content)
        print("-" * 60)
        log("dry-run：未发送")
        return 0

    results = []
    for name, fn in (("PushPlus", send_pushplus), ("Server酱", send_serverchan),
                     ("企业微信", send_wecom)):
        try:
            r = fn(title, content)
            if r is None:
                log("%s：未配置，跳过" % name)
            else:
                log("%s：已发送 -> %s" % (name, r[:120]))
                results.append(name)
        except Exception as exc:
            log("%s：发送失败 %s" % (name, exc))

    if not results:
        log("没有任何通道配置成功，请检查环境变量 "
            "PUSHPLUS_TOKEN / SERVERCHAN_KEY / WECOM_WEBHOOK")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
