# Naver Webtoon Completion Notifier

네이버 웹툰을 카드형 목록에서 고르고, 완결되면 텔레그램으로 알림을 받는 GitHub Actions 기반 서비스입니다.

구조는 단순하게 유지했습니다.

- 시각적인 선택 화면은 `docs/` 정적 페이지
- 실제 감시 상태는 `watchlist.json`
- 선택 요청은 GitHub issue 로 받고, Actions 가 자동 반영
- 완결 체크와 텔레그램 전송은 기존 GitHub Actions 가 처리

## Flow

```text
GitHub Pages
    │
    ├─ 카드형 목록 / 검색 / 요일 필터
    ├─ 작품 선택
    └─ GitHub issue 생성

Process Subscription Request
    │
    └─ watchlist.json 에 자동 추가

Check Webtoon Completions
    │
    ├─ Naver Webtoon API 상태 확인
    ├─ 완결 신호 감지
    ├─ watchlist.json 상태 갱신
    └─ Telegram notification
```

## Setup

### 1. Install

```bash
git clone https://github.com/YOUR_USERNAME/naver-webtoon-notifier.git
cd naver-webtoon-notifier
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Set up Telegram

GitHub repository secrets:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

### 3. Enable workflows

Actions 탭에서 아래 워크플로를 활성화합니다.

- `Check Webtoon Completions`
- `Process Subscription Request`

### 4. Turn on GitHub Pages

Settings → Pages 에서:

- Source: `Deploy from a branch`
- Branch: `main`
- Folder: `/docs`

배포 후 `https://<your-name>.github.io/<repo>/` 형태의 페이지가 생깁니다.

### 5. Pick webtoons visually

정적 페이지에서:

1. 검색하거나 요일별로 작품을 둘러봅니다.
2. 카드 클릭으로 작품을 선택합니다.
3. `Track Selected` 를 누릅니다.
4. 열리는 GitHub issue 화면을 그대로 제출합니다.
5. `Process Subscription Request` 액션이 `watchlist.json` 에 자동 반영합니다.

## Optional Local CLI

로컬에서 직접 관리하고 싶으면 기존 CLI 도 그대로 쓸 수 있습니다.

```bash
python src/manage.py add 822557
python src/manage.py browse mon
python src/manage.py search "마음의소리"
python src/manage.py list
python src/manage.py remove 822557
python src/manage.py check
```

## GitHub Actions

[check-webtoons.yml](/Users/jiyunkim/Desktop/courses/naver-webtoon-notifier/.github/workflows/check-webtoons.yml:1)

- 매일 `13:30 UTC`
- `watchlist.json` 의 active 항목 검사
- 새 완결이면 텔레그램 전송
- `docs/catalog.json`, `docs/tracked.json` 도 함께 갱신

[process-subscription-request.yml](/Users/jiyunkim/Desktop/courses/naver-webtoon-notifier/.github/workflows/process-subscription-request.yml:1)

- `subscription-request` 라벨이 붙은 issue 를 감지
- 선택된 `titleId` 를 파싱
- `watchlist.json` 에 추가
- 결과 코멘트를 남기고 issue 를 닫음

## Project Structure

```text
src/
├── catalog.py                    # 요일별 카탈로그 + 썸네일 수집
├── export_catalog.py             # docs/catalog.json 생성
├── process_subscription_issue.py # visual picker issue 처리
├── manage.py                     # 로컬 CLI
├── naver_api.py                  # 작품 상태 / 회차 정보 조회
├── detector.py                   # 완결 감지 로직
├── notifier.py                   # Telegram / email / Slack notifier
├── check.py                      # daily checker
└── watchlist.py                  # watchlist.json persistence

docs/
├── index.html
├── app.js
├── styles.css
├── catalog.json
└── tracked.json
```

## Notes

- `catalog.json` 은 Actions 가 생성하는 정적 데이터입니다.
- visual picker 는 서버 없이 GitHub Pages 에서 동작합니다.
- 현재 구조는 비용 0원에 가깝게 유지하면서, 입력 UX 만 비주얼하게 바꾼 형태입니다.
