"""
AI 종목 분석 - 텔레그램 알림 발송
텍스트 요약 + WebApp 버튼 전송
"""

import json
import os
from datetime import datetime

import pytz
import requests

KST = pytz.timezone("Asia/Seoul")
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def format_price(price, market):
    """시장별 가격 포맷"""
    if market == "overseas":
        return f"${price:,.2f}"
    else:
        return f"₩{price:,}"


def format_change(change_pct):
    """등락률 포맷"""
    arrow = "▲" if change_pct >= 0 else "▼"
    return f"{arrow}{abs(change_pct):.1f}%"


def build_message(stocks):
    """텔레그램 메시지 생성"""
    now = datetime.now(KST)
    date_str = now.strftime("%Y.%m.%d")

    lines = [f"📊 AI 종목 일일 리포트 ({date_str} KST)", ""]

    overseas = [s for s in stocks if s["market"] == "overseas"]
    domestic = [s for s in stocks if s["market"] == "domestic"]

    if overseas:
        lines.append("🇺🇸 해외 주요 종목")
        for s in overseas:
            price_str = format_price(s.get("price", 0), "overseas")
            change_str = format_change(s.get("change_pct", 0))
            scores = s.get("scores", {})
            risk = s.get("risk_score", 0)
            name = s["ticker"]
            lines.append(
                f"{name:<5} {price_str:>10} {change_str:>7}  "
                f"단기{scores.get('short', 0)} 중기{scores.get('mid', 0)} "
                f"장기{scores.get('long', 0)} 리스크{risk}"
            )
        lines.append("")

    if domestic:
        lines.append("🇰🇷 국내 주요 종목")
        for s in domestic:
            price_str = format_price(s.get("price", 0), "domestic")
            change_str = format_change(s.get("change_pct", 0))
            scores = s.get("scores", {})
            risk = s.get("risk_score", 0)
            name = s["name"]
            lines.append(
                f"{name:<8} {price_str:>12} {change_str:>7}  "
                f"단기{scores.get('short', 0)} 중기{scores.get('mid', 0)} "
                f"장기{scores.get('long', 0)} 리스크{risk}"
            )
        lines.append("")

    lines.append("⚠️ 본 분석은 참고용이며 투자 추천이 아닙니다.")

    return "\n".join(lines)


def send_with_webapp_button(token, chat_id, message, dashboard_url):
    """텔레그램 WebApp 버튼과 함께 메시지 전송"""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "reply_markup": {
            "inline_keyboard": [
                [
                    {
                        "text": "📊 상세 대시보드 열기",
                        "web_app": {"url": dashboard_url},
                    }
                ]
            ]
        },
    }
    response = requests.post(url, json=payload)
    return response.json()


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    dashboard_url = os.environ.get("DASHBOARD_URL")

    if not all([token, chat_id, dashboard_url]):
        print("[ERROR] 환경변수 설정 필요: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, DASHBOARD_URL")
        return

    stocks_path = os.path.join(DATA_DIR, "stocks.json")
    if not os.path.exists(stocks_path):
        print(f"[ERROR] 데이터 파일 없음: {stocks_path}")
        return

    with open(stocks_path, "r", encoding="utf-8") as f:
        stocks = json.load(f)

    message = build_message(stocks)
    print("=== 발송 메시지 ===")
    print(message)
    print("==================")

    result = send_with_webapp_button(token, chat_id, message, dashboard_url)

    if result.get("ok"):
        print("텔레그램 발송 성공!")
    else:
        print(f"텔레그램 발송 실패: {result}")


if __name__ == "__main__":
    main()
