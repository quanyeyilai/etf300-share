"""沪深交易所 ETF 份额（规模）数据抓取。

数据源：
- 上交所 ETF 规模：https://query.sse.com.cn/commonQuery.do
  sqlId = COMMON_SSE_ZQPZ_ETFZL_XXPL_ETFGM_SEARCH_L，字段 TOT_VOL 单位：万份
- 深交所 基金规模：https://www.szse.cn/api/report/ShowReport/data
  CATALOGID = scsj_fund_jjgm，字段 current_size 单位：万份

仅使用 Python 标准库，无需安装第三方依赖。
"""

import json
import random
import time
import urllib.error
import urllib.parse
import urllib.request

SSE_URL = "https://query.sse.com.cn/commonQuery.do"
SZSE_URL = "https://www.szse.cn/api/report/ShowReport/data"
SSE_SQLID = "COMMON_SSE_ZQPZ_ETFZL_XXPL_ETFGM_SEARCH_L"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"


class FetchError(Exception):
    pass


def _http_get(url, referer, retries=3, timeout=30, sleep=1.5):
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": UA,
                "Referer": referer,
                "Accept": "application/json, text/javascript, */*; q=0.01",
            })
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", "ignore")
        except Exception as exc:  # 网络抖动 / 交易所限流
            last = exc
            time.sleep(sleep * (attempt + 1) + random.random())
    raise FetchError("请求失败: %s -> %s" % (url, last))


def _strip_jsonp(text):
    t = text.strip()
    if t.startswith("("):
        t = t[1:-1]
    i = t.find("(")
    if i > 0 and i < 30 and t.endswith(")"):
        t = t[i + 1:-1]
    return t.strip()


def fetch_sse(date_str):
    """抓取上交所某日全部 ETF 规模。

    :param date_str: YYYY-MM-DD，非交易日返回空 dict
    :return: {code: {"name": 简称, "share": 万份}}
    """
    params = {
        "isPagination": "true",
        "pageHelp.pageSize": "3000",
        "pageHelp.pageNo": "1",
        "pageHelp.beginPage": "1",
        "pageHelp.cacheSize": "1",
        "pageHelp.endPage": "1",
        "sqlId": SSE_SQLID,
        "STAT_DATE": date_str,
    }
    url = SSE_URL + "?" + urllib.parse.urlencode(params)
    raw = _http_get(url, "https://www.sse.com.cn/market/funddata/volumn/etfvolumn/")
    data = json.loads(_strip_jsonp(raw))
    rows = data.get("result") or data.get("pageHelp", {}).get("data") or []
    out = {}
    for row in rows:
        code = str(row.get("SEC_CODE", "")).strip()
        vol = row.get("TOT_VOL")
        if not code or vol in (None, ""):
            continue
        try:
            out[code] = {
                "name": str(row.get("SEC_NAME", "")).strip(),
                "share": float(str(vol).replace(",", "")),
            }
        except ValueError:
            continue
    return out


def fetch_szse(code, start_date, end_date, max_pages=60):
    """抓取深交所单只 ETF 在日期区间内的规模（接口每页 20 条，自动翻页）。

    :return: [{"date": YYYY-MM-DD, "code": code, "name": 简称, "share": 万份}]
    """
    out = []
    page = 1
    while page <= max_pages:
        params = {
            "SHOWTYPE": "JSON",
            "CATALOGID": "scsj_fund_jjgm",
            "jjlb": "ETF",
            "txtDm": code,
            "txtStart": start_date,
            "txtEnd": end_date,
            "PAGENO": str(page),
            "random": "%.15f" % random.random(),
        }
        url = SZSE_URL + "?" + urllib.parse.urlencode(params)
        raw = _http_get(url, "https://www.szse.cn/market/fund/volume/etf/index.html")
        data = json.loads(raw)
        block = data[0] if isinstance(data, list) and data else {}
        meta = block.get("metadata", {}) or {}
        rows = block.get("data") or []
        for row in rows:
            d = str(row.get("size_date", "")).strip()[:10]
            vol = row.get("current_size")
            if not d or vol in (None, ""):
                continue
            try:
                out.append({
                    "date": d,
                    "code": str(row.get("fund_code", code)).strip(),
                    "name": str(row.get("security_short_name", "")).strip(),
                    "share": float(str(vol).replace(",", "")),
                })
            except ValueError:
                continue
        try:
            pagecount = int(meta.get("pagecount") or 1)
        except ValueError:
            pagecount = 1
        if page >= pagecount or not rows:
            break
        page += 1
        time.sleep(0.2)
    return out
