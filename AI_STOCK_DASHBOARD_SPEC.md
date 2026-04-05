# AI 종목 분석 대시보드 프로젝트 스펙

## 프로젝트 개요
매일 아침 AI 관련 국내/해외 주식 데이터를 자동 수집하여, GitHub Pages 대시보드에 업데이트하고, Telegram으로 요약 알림 + Mini App 버튼을 보내는 시스템.

## 아키텍처
```
GitHub Actions (매일 KST 08:00) 
  → scripts/fetch_data.py (주가 수집 → data/stocks.json 생성)
  → docs/index.html이 stocks.json을 읽어서 대시보드 렌더링
  → GitHub Pages에 자동 배포
  → scripts/send_telegram.py (텍스트 요약 + WebApp 버튼 전송)
```

## 디렉토리 구조
```
ai-stock-dashboard/
├── .github/
│   └── workflows/
│       └── daily-update.yml       # 매일 KST 08:00 실행
├── scripts/
│   ├── fetch_data.py              # yfinance + pykrx로 주가 수집
│   ├── send_telegram.py           # Telegram 알림 발송
│   └── stock_config.py            # 종목 리스트 & 분석 점수 설정
├── docs/                          # GitHub Pages 소스
│   └── index.html                 # 인터랙티브 대시보드 (단일 파일)
├── data/
│   └── stocks.json                # 매일 업데이트되는 주가 데이터
├── requirements.txt
└── README.md
```

## 1. stock_config.py - 종목 설정 & 점수

아래 종목들의 정적 분석 데이터(투자 점수, 리스크, 장단점)를 딕셔너리로 관리.
주가/등락률 등 동적 데이터는 fetch_data.py에서 매일 업데이트.

### 해외 종목 (8개)
| 티커 | 이름 | 카테고리 | 단기(1달) | 중기(1년) | 장기(10년) | 리스크 |
|------|------|----------|-----------|-----------|-----------|--------|
| NVDA | NVIDIA | AI 인프라 (GPU) | 3 | 5 | 4 | 3 |
| AVGO | Broadcom | AI 인프라 (커스텀칩) | 4 | 4 | 4 | 3 |
| AMD | AMD | AI 인프라 (GPU/CPU) | 3 | 4 | 4 | 3 |
| MSFT | Microsoft | AI 플랫폼 (클라우드) | 3 | 4 | 5 | 4 |
| META | Meta Platforms | AI 응용 (광고) | 3 | 4 | 4 | 3 |
| PLTR | Palantir | AI 소프트웨어 | 2 | 3 | 3 | 2 |
| TSM | TSMC | AI 인프라 (파운드리) | 3 | 4 | 5 | 2 |
| MU | Micron | AI 인프라 (메모리) | 4 | 4 | 3 | 2 |

### 국내 종목 (6개)
| 티커 | 이름 | 카테고리 | 단기(1달) | 중기(1년) | 장기(10년) | 리스크 |
|------|------|----------|-----------|-----------|-----------|--------|
| 000660 | SK하이닉스 | AI 인프라 (HBM) | 3 | 5 | 4 | 3 |
| 005930 | 삼성전자 | AI 인프라 (메모리) | 4 | 5 | 4 | 3 |
| 035420 | 네이버 | AI 응용 (플랫폼) | 2 | 3 | 3 | 3 |
| 017670 | SK텔레콤 | AI 응용 (통신) | 2 | 3 | 3 | 4 |
| 328130 | 루닛 | AI 응용 (의료AI) | 2 | 3 | 4 | 2 |
| 403870 | HPSP | AI 인프라 (반도체장비) | 3 | 4 | 4 | 2 |

### 각 종목별 포함 데이터
```python
{
    "ticker": "NVDA",
    "name": "NVIDIA",
    "market": "overseas",  # "overseas" 또는 "domestic"
    "category": "AI 인프라 (GPU)",
    "description": "AI GPU 시장 절대 지배자...",
    "scores": {"short": 3, "mid": 5, "long": 4},
    "risk_score": 3,
    "pros": ["GPU 시장 90%+ 점유율", ...],
    "cons": ["커스텀 ASIC 경쟁 심화", ...],
    "risk_factors": ["커스텀칩 경쟁으로 점유율 하락", ...],
    # 아래는 fetch_data.py에서 매일 업데이트
    "price": 0,
    "change_pct": 0,
    "volume": 0,
    "market_cap": "",
    "last_updated": ""
}
```

## 2. fetch_data.py - 데이터 수집

### 해외 종목: yfinance 사용
```python
import yfinance as yf

tickers = ["NVDA", "AVGO", "AMD", "MSFT", "META", "PLTR", "TSM", "MU"]
data = yf.download(tickers, period="5d")
# 최신 종가, 전일 대비 등락률, 거래량, 시가총액 추출
```

### 국내 종목: pykrx 사용
```python
from pykrx import stock

tickers = ["000660", "005930", "035420", "017670", "328130", "403870"]
# 오늘 날짜 기준 최근 5 거래일 데이터 조회
# 종가, 등락률, 거래량 추출
```

### 출력: data/stocks.json
stock_config.py의 정적 데이터 + 동적 주가 데이터를 합쳐서 JSON으로 저장.
docs/index.html에서 fetch하여 렌더링.

## 3. docs/index.html - 인터랙티브 대시보드

**단일 HTML 파일** (GitHub Pages 배포용). 아래 기능 포함:

### UI 요구사항
- 다크 테마 (배경: #0c1120 계열)
- 탭: 해외 종목 / 국내 종목 전환
- 카드형 레이아웃, 각 종목별:
  - 티커, 이름, 카테고리 표시
  - 현재가, 등락률 (양수=초록, 음수=빨강)
  - 단기/중기/장기 투자점수 + 리스크점수 (1~5 바 차트)
  - 클릭하면 펼쳐지는 상세 영역: 장점, 단점, 리스크 요인
- 정렬: 기본 / 장기점수순 / 단기점수순 / 리스크 낮은순 / 등락률순
- 상단 요약: 평균 점수, 마지막 업데이트 시간
- 하단 투자 관점 요약 섹션
- 반응형 (모바일 최적화 필수 - Telegram Mini App에서 열림)
- 투자 유의사항 경고 표시

### 데이터 로딩
```javascript
// GitHub Pages에서 상대 경로로 JSON 로드
fetch('./data/stocks.json')
  .then(r => r.json())
  .then(data => renderDashboard(data));
```

### 폰트
- 한글: Pretendard (CDN)
- 숫자/코드: JetBrains Mono (Google Fonts)

### 점수 표시 기준
- 투자점수: 5점(매우 유망) ~ 1점(매우 약함)
- 리스크점수: 1점(리스크 매우 높음) ~ 5점(리스크 매우 낮음)
- 색상: 1~2=빨강, 3=노랑, 4~5=초록

## 4. send_telegram.py - 텔레그램 알림

### 환경변수
- `TELEGRAM_BOT_TOKEN`: 봇 토큰
- `TELEGRAM_CHAT_ID`: 발송 대상 채팅 ID
- `DASHBOARD_URL`: GitHub Pages URL (예: https://username.github.io/ai-stock-dashboard/)

### 발송 메시지 포맷
```
📊 AI 종목 일일 리포트 (2026.04.05 KST)

🇺🇸 해외 주요 종목
NVDA  $120.50 ▲2.1%  단기3 중기5 장기4 리스크3
AVGO  $185.30 ▼0.8%  단기4 중기4 장기4 리스크3
AMD   $115.20 ▲1.5%  단기3 중기4 장기4 리스크3
MSFT  $385.00 ▲0.3%  단기3 중기4 장기5 리스크4
META  $520.10 ▼1.2%  단기3 중기4 장기4 리스크3
PLTR  $85.60  ▲3.5%  단기2 중기3 장기3 리스크2
TSM   $175.40 ▲0.9%  단기3 중기4 장기5 리스크2
MU    $110.80 ▼0.5%  단기4 중기4 장기3 리스크2

🇰🇷 국내 주요 종목
SK하이닉스  ₩922,000 ▲1.5%  단기3 중기5 장기4 리스크3
삼성전자    ₩179,700 ▼0.2%  단기4 중기5 장기4 리스크3
네이버      ₩230,500 ▲0.8%  단기2 중기3 장기3 리스크3
SK텔레콤    ₩65,300  ▲0.1%  단기2 중기3 장기3 리스크4
루닛        ₩85,200  ▲2.3%  단기2 중기3 장기4 리스크2
HPSP        ₩52,100  ▼1.1%  단기3 중기4 장기4 리스크2

⚠️ 본 분석은 참고용이며 투자 추천이 아닙니다.
```

### Telegram WebApp 버튼
```python
import requests

def send_with_webapp_button(token, chat_id, message, dashboard_url):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "reply_markup": {
            "inline_keyboard": [[
                {
                    "text": "📊 상세 대시보드 열기",
                    "web_app": {"url": dashboard_url}
                }
            ]]
        }
    }
    requests.post(url, json=payload)
```

## 5. GitHub Actions Workflow

### .github/workflows/daily-update.yml
```yaml
name: Daily AI Stock Update

on:
  schedule:
    - cron: '0 23 * * 0-4'  # UTC 23:00 = KST 08:00 (월~금)
  workflow_dispatch:  # 수동 실행 가능

jobs:
  update:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pages: write
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Fetch stock data
        run: python scripts/fetch_data.py

      - name: Copy data to docs
        run: cp -r data docs/

      - name: Commit and push
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add data/ docs/
          git diff --staged --quiet || git commit -m "📊 Daily stock data update $(date +'%Y-%m-%d')"
          git push

      - name: Send Telegram notification
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          DASHBOARD_URL: ${{ secrets.DASHBOARD_URL }}
        run: python scripts/send_telegram.py
```

## 6. requirements.txt
```
yfinance>=0.2.36
pykrx>=1.0.45
requests>=2.31.0
pytz>=2024.1
```

## 7. 셋업 가이드 (README.md에 포함)

### 사전 준비
1. **Telegram Bot 생성**: @BotFather → /newbot → 토큰 저장
2. **Chat ID 확인**: 봇에 메시지 보낸 후 `https://api.telegram.org/bot{TOKEN}/getUpdates`에서 chat_id 확인
3. **GitHub Repo 생성**: `ai-stock-dashboard` 이름으로 생성
4. **GitHub Pages 설정**: Settings → Pages → Source: Deploy from branch → Branch: main, /docs
5. **GitHub Secrets 설정**:
   - `TELEGRAM_BOT_TOKEN`: 봇 토큰
   - `TELEGRAM_CHAT_ID`: 채팅 ID
   - `DASHBOARD_URL`: `https://{username}.github.io/ai-stock-dashboard/`

### 로컬 테스트
```bash
pip install -r requirements.txt
python scripts/fetch_data.py          # data/stocks.json 생성 확인
python scripts/send_telegram.py       # 텔레그램 수신 확인
# docs/index.html을 브라우저에서 열어서 대시보드 확인
```

## 구현 시 주의사항

1. **pykrx 날짜 처리**: 주말/공휴일에는 최근 거래일 데이터를 가져와야 함
2. **yfinance 에러 핸들링**: 마켓 종료 전이면 전일 종가 사용
3. **GitHub Pages 경로**: docs/index.html에서 data/stocks.json을 상대경로로 로드
4. **Telegram Mini App**: HTTPS 필수 (GitHub Pages는 기본 HTTPS)
5. **시간대**: 모든 시간 KST 기준으로 표시
6. **모바일 반응형**: Telegram Mini App에서 열리므로 모바일 뷰 최적화 필수
7. **등락률 색상**: 양수는 초록(#22c55e), 음수는 빨강(#ef4444)
8. **data 폴더를 docs 안에 복사**: GitHub Actions에서 `cp -r data docs/` 실행

## Claude Code 실행 명령어

프로젝트 디렉토리에서 아래 순서로 진행:

```bash
# 1. 프로젝트 초기화
mkdir ai-stock-dashboard && cd ai-stock-dashboard
git init

# 2. Claude Code에 이 스펙 전달 후 구현 요청
# "이 스펙대로 전체 프로젝트를 구현해줘"

# 3. 로컬 테스트
pip install -r requirements.txt
python scripts/fetch_data.py
# 브라우저에서 docs/index.html 열기

# 4. GitHub 배포
git remote add origin https://github.com/{username}/ai-stock-dashboard.git
git add .
git commit -m "🚀 Initial commit"
git push -u origin main

# 5. GitHub Settings에서 Pages 활성화 + Secrets 설정
```
