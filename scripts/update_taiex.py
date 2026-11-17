#!/usr/bin/env python3
"""Fetch monthly official TWSE TAIEX OHLC history and save a deduplicated JSON mirror."""
import json
import sys
import time
import urllib.request
from datetime import date
from pathlib import Path

BASE = "https://www.twse.com.tw/rwd/zh/TAIEX/MI_5MINS_HIST"
OUT = Path("data/taiex_history.json")
START_YEAR, START_MONTH = 2016, 11

def parse_num(value):
    s = str(value or "").replace(",", "").strip()
    if not s or s in ("--", "---", "-", "－"):
        return None
    try:
        return float(s)
    except ValueError:
        return None

def parse_roc_date(value):
    parts = str(value or "").strip().split("/")
    if len(parts) != 3:
        return None
    try:
        year = int(parts[0]) + 1911
        month = int(parts[1])
        day = int(parts[2])
        return f"{year:04d}-{month:02d}-{day:02d}"
    except (TypeError, ValueError):
        return None

def months():
    today = date.today()
    y, m = START_YEAR, START_MONTH
    while (y, m) <= (today.year, today.month):
        yield y, m
        m += 1
        if m == 13:
            y, m = y + 1, 1

def fetch_month(year, month):
    url = f"{BASE}?date={year:04d}{month:02d}01&response=json"
    headers = {
        "Accept": "application/json,text/plain,*/*",
        "User-Agent": "Mozilla/5.0 (compatible; NEXUS-MARKET-DATA/2.4)",
        "Referer": "https://www.twse.com.tw/",
    }
    last_error = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8-sig"))
            rows = payload.get("data", [])
            result = []
            for row in rows:
                if not isinstance(row, list) or len(row) < 5:
                    continue
                d = parse_roc_date(row[0])
                o, h, l, c = (parse_num(x) for x in row[1:5])
                if d and None not in (o, h, l, c) and c > 0:
                    result.append({
                        "date": d, "open": o, "high": h, "low": l,
                        "close": c, "volume": 0
                    })
            return result
        except Exception as exc:
            last_error = exc
            print(f"{year}-{month:02d} 第 {attempt + 1} 次失敗：{exc}", file=sys.stderr)
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"{year}-{month:02d} 下載失敗：{last_error}")

def main():
    all_rows = {}
    month_list = list(months())
    for index, (year, month) in enumerate(month_list, 1):
        rows = fetch_month(year, month)
        for row in rows:
            all_rows[row["date"]] = row
        print(f"[{index}/{len(month_list)}] {year}-{month:02d}：{len(rows)} 筆")
        # Conservative pacing to reduce the chance of official API throttling.
        if index < len(month_list):
            time.sleep(1.0)

    ordered = [all_rows[k] for k in sorted(all_rows)]
    if len(ordered) < 1000:
        raise SystemExit(f"資料筆數異常，僅取得 {len(ordered)} 筆；不覆寫輸出檔")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(ordered, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"完成：{len(ordered)} 筆；最早 {ordered[0]['date']}；最新 {ordered[-1]['date']}；輸出 {OUT}")

if __name__ == "__main__":
    main()
