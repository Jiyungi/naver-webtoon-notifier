# Naver Webtoon Completion Notifier

포크해서 자기 GitHub 저장소와 자기 텔레그램으로 바로 쓸 수 있는 네이버 웹툰 완결 알림 템플릿입니다.

이 저장소는 중앙 서버형 서비스가 아닙니다. 각 사용자가 자기 저장소에서:

- GitHub Pages 로 웹툰 목록을 보고
- 자기 저장소에 감시 대상을 등록하고
- 자기 GitHub Actions 로 주기 체크를 돌리고
- 자기 텔레그램으로 알림을 받는 방식입니다

## Why This Shape

이 구조는 이런 상황에 맞습니다.

- 아직 작은 프로젝트라 운영 서버를 두고 싶지 않을 때
- 비용을 거의 0원으로 유지하고 싶을 때
- 각 사용자가 자기 텔레그램 알림만 받으면 충분할 때

이 구조는 이런 상황엔 안 맞습니다.

- 여러 사용자를 한 저장소에서 중앙 관리하려는 경우
- 로그인/계정/DB 가 있는 멀티유저 SaaS 를 만들려는 경우
- abuse 대응, 관리자 대시보드, 사용자별 권한 관리가 필요한 경우

## Flow

```text
Your GitHub Pages
    │
    ├─ 카드형 목록 / 검색 / 요일 필터
    ├─ 작품 선택
    └─ GitHub issue 생성

Your Process Subscription Request
    │
    └─ watchlist.json 에 자동 추가

Your Check Webtoon Completions
    │
    ├─ Naver Webtoon API 상태 확인
    ├─ 완결 신호 감지
    ├─ watchlist.json 상태 갱신
    └─ Telegram notification
```

## Quick Start

### 1. Create your own copy

둘 중 하나를 선택하세요.

- `Use this template`
- 또는 `Fork`

그다음 자기 저장소에서 아래 설정을 진행합니다.

### 2. Add Telegram secrets

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

배포 후 `https://<your-name>.github.io/<your-repo>/` 형태의 페이지가 생깁니다.

### 5. Initialize catalog data

Actions 에서 `Check Webtoon Completions` 를 한 번 수동 실행하세요.

이 단계가 끝나야:

- `docs/catalog.json`
- `docs/tracked.json`

이 실제 데이터로 채워지고, Pages 카드 목록이 정상 표시됩니다.

### 6. Pick webtoons visually

정적 페이지에서:

1. 검색하거나 요일별로 작품을 둘러봅니다.
2. 카드 클릭으로 작품을 선택합니다.
3. `Track Selected` 를 누릅니다.
4. 열리는 GitHub issue 화면을 그대로 제출합니다.
5. 자기 저장소의 `Process Subscription Request` 액션이 `watchlist.json` 에 자동 반영합니다.
6. Pages 에서 `내 워치리스트` 버튼을 누르면 현재 추적 중인 작품만 따로 볼 수 있습니다.

## Optional Local CLI

로컬에서 직접 관리하고 싶으면 CLI 도 그대로 쓸 수 있습니다.

```bash
git clone https://github.com/YOUR_USERNAME/naver-webtoon-notifier.git
cd naver-webtoon-notifier
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python src/manage.py add 822557
python src/manage.py browse mon
python src/manage.py search "마음의소리"
python src/manage.py list
python src/manage.py remove 822557
python src/manage.py check
```

## Workflows

[check-webtoons.yml](/Users/jiyunkim/Desktop/courses/naver-webtoon-notifier/.github/workflows/check-webtoons.yml:1)

- 매일 `13:30 UTC`
- `watchlist.json` 의 active 항목 검사
- 새 완결이면 텔레그램 전송
- `docs/catalog.json`, `docs/tracked.json` 도 함께 갱신

[process-subscription-request.yml](/Users/jiyunkim/Desktop/courses/naver-webtoon-notifier/.github/workflows/process-subscription-request.yml:1)

- `subscription-request` issue 를 감지
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
- `tracked.json` 은 현재 워치리스트의 `title_id` 목록입니다.
- visual picker 는 서버 없이 GitHub Pages 에서 동작합니다.
- 현재 구조는 비용 0원에 가깝게 유지하면서, self-serve template 으로 배포하기 좋은 형태입니다.
