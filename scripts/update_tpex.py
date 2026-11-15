#!/usr/bin/env python3
"""Fetch the official TPEx daily close OpenAPI and store the raw JSON array."""
import json
import sys
import time
import urllib.request
from pathlib import Path
URL = "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes"
OUT = Path("data/tpex_daily.json")
def main():
    headers = {
        "Accept": "application/json,text/plain,*/*",
        "User-Agent": "Mozilla/5.0 (compatible; NEXUS-MARKET-DATA/2.3)",
        "Referer": "https://www.tpex.org.tw/",
    }
    last_error = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(URL, headers=headers)
            with urllib.request.urlopen(req, timeout=45) as response:
                raw = response.read()
            data = json.loads(raw.decode("utf-8-sig"))
            if not isinstance(data, list) or len(data) < 50:
                raise ValueError("官方回應不是有效行情陣列")
            first = data[0]
            if not isinstance(first, dict):
                raise ValueError("官方資料列不是 JSON 物件")
            keys = set(first.keys())
            if not any(k in keys for k in (
                "SecuritiesCompanyCode",
                "Code",
                "證券代號",
                "代號"
            )):
                raise ValueError("官方資料缺少證券代號欄位")
            OUT.parent.mkdir(parents=True, exist_ok=True)
            OUT.write_text(
                json.dumps(data, ensure_ascii=False, separators=(",", ":")),
                encoding="utf-8"
            )
            print(f"成功：取得 {len(data)} 筆 TPEx 官方行情")
            print(f"檔案位置：{OUT}")
            return
        except Exception as exc:
            last_error = exc
            print(f"第 {attempt + 1} 次失敗：{exc}", file=sys.stderr)
            time.sleep(5 * (attempt + 1))
    raise SystemExit(f"TPEx 官方行情抓取失敗：{last_error}")
if __name__ == "__main__":
    main()
