"""
AI 종목 분석 - 주가 데이터 수집
해외: yfinance / 국내: pykrx
"""

import json
import os
from datetime import datetime, timedelta

import pytz
import yfinance as yf
from pykrx import stock

from stock_config import STOCKS

KST = pytz.timezone("Asia/Seoul")
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def fetch_overseas(stocks):
    """yfinance로 해외 종목 데이터 수집"""
    tickers = [s["ticker"] for s in stocks if s["market"] == "overseas"]
    if not tickers:
        return {}

    result = {}
    try:
        data = yf.download(tickers, period="5d", group_by="ticker", progress=False)

        for ticker in tickers:
            try:
                if len(tickers) == 1:
                    df = data
                else:
                    df = data[ticker]

                df = df.dropna()
                if len(df) < 2:
                    continue

                close = float(df["Close"].iloc[-1])
                prev_close = float(df["Close"].iloc[-2])
                change_pct = ((close - prev_close) / prev_close) * 100
                volume = int(df["Volume"].iloc[-1])

                info = yf.Ticker(ticker).info
                market_cap = info.get("marketCap", 0)
                if market_cap >= 1_000_000_000_000:
                    market_cap_str = f"${market_cap / 1_000_000_000_000:.2f}T"
                elif market_cap >= 1_000_000_000:
                    market_cap_str = f"${market_cap / 1_000_000_000:.1f}B"
                else:
                    market_cap_str = f"${market_cap / 1_000_000:.0f}M"

                result[ticker] = {
                    "price": round(close, 2),
                    "change_pct": round(change_pct, 2),
                    "volume": volume,
                    "market_cap": market_cap_str,
                }
            except Exception as e:
                print(f"[WARN] {ticker} 데이터 처리 실패: {e}")
                result[ticker] = {
                    "price": 0,
                    "change_pct": 0,
                    "volume": 0,
                    "market_cap": "N/A",
                }
    except Exception as e:
        print(f"[ERROR] yfinance 다운로드 실패: {e}")

    return result


def get_recent_trading_date():
    """최근 거래일 반환 (주말/공휴일 고려)"""
    today = datetime.now(KST).date()
    for i in range(7):
        date = today - timedelta(days=i)
        date_str = date.strftime("%Y%m%d")
        try:
            df = stock.get_market_ohlcv(date_str, date_str, "005930")
            if len(df) > 0:
                return date_str
        except Exception:
            continue
    return today.strftime("%Y%m%d")


def fetch_domestic(stocks):
    """pykrx로 국내 종목 데이터 수집"""
    tickers = [s["ticker"] for s in stocks if s["market"] == "domestic"]
    if not tickers:
        return {}

    result = {}
    try:
        end_date = get_recent_trading_date()
        start_dt = datetime.strptime(end_date, "%Y%m%d") - timedelta(days=10)
        start_date = start_dt.strftime("%Y%m%d")

        for ticker in tickers:
            try:
                df = stock.get_market_ohlcv(start_date, end_date, ticker)
                df = df[df["거래량"] > 0]

                if len(df) < 2:
                    continue

                close = int(df["종가"].iloc[-1])
                prev_close = int(df["종가"].iloc[-2])
                change_pct = ((close - prev_close) / prev_close) * 100
                volume = int(df["거래량"].iloc[-1])

                cap_df = stock.get_market_cap(end_date, end_date, ticker)
                if len(cap_df) > 0:
                    market_cap = int(cap_df["시가총액"].iloc[0])
                    if market_cap >= 1_000_000_000_000:
                        market_cap_str = f"₩{market_cap / 1_000_000_000_000:.1f}조"
                    elif market_cap >= 100_000_000:
                        market_cap_str = f"₩{market_cap / 100_000_000:.0f}억"
                    else:
                        market_cap_str = "N/A"
                else:
                    market_cap_str = "N/A"

                result[ticker] = {
                    "price": close,
                    "change_pct": round(change_pct, 2),
                    "volume": volume,
                    "market_cap": market_cap_str,
                }
            except Exception as e:
                print(f"[WARN] {ticker} 데이터 처리 실패: {e}")
                result[ticker] = {
                    "price": 0,
                    "change_pct": 0,
                    "volume": 0,
                    "market_cap": "N/A",
                }
    except Exception as e:
        print(f"[ERROR] pykrx 데이터 수집 실패: {e}")

    return result


def main():
    print("주가 데이터 수집 시작...")
    now = datetime.now(KST)

    overseas_data = fetch_overseas(STOCKS)
    print(f"해외 종목 {len(overseas_data)}개 수집 완료")

    domestic_data = fetch_domestic(STOCKS)
    print(f"국내 종목 {len(domestic_data)}개 수집 완료")

    output = []
    for s in STOCKS:
        entry = dict(s)
        ticker = s["ticker"]

        if s["market"] == "overseas" and ticker in overseas_data:
            entry.update(overseas_data[ticker])
        elif s["market"] == "domestic" and ticker in domestic_data:
            entry.update(domestic_data[ticker])
        else:
            entry.update({"price": 0, "change_pct": 0, "volume": 0, "market_cap": "N/A"})

        entry["last_updated"] = now.strftime("%Y-%m-%d %H:%M KST")
        output.append(entry)

    os.makedirs(DATA_DIR, exist_ok=True)
    output_path = os.path.join(DATA_DIR, "stocks.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"저장 완료: {output_path}")
    print(f"총 {len(output)}개 종목 데이터 업데이트")


if __name__ == "__main__":
    main()
