# Naver Webtoon Completion Notifier

[English README](./README.md)

자기 GitHub 저장소와 자기 텔레그램으로 바로 쓸 수 있는 네이버 웹툰 완결 알림 템플릿입니다.

이 저장소는 중앙 서버형 서비스가 아닙니다. 각 사용자가 자기 저장소에서:

- GitHub Pages 로 웹툰 목록을 보고
- 자기 저장소에 감시 대상을 등록하거나 제거하고
- 자기 GitHub Actions 로 주기 체크를 돌리고
- 자기 텔레그램으로 알림을 받는 방식입니다

## 어떤 경우에 맞나

이 구조는 이런 상황에 맞습니다.

- 비용을 거의 0원으로 유지하고 싶을 때
- 별도 서버를 운영하고 싶지 않을 때
- 각 사용자가 자기 워치리스트만 관리하면 충분할 때

이 구조는 이런 상황엔 안 맞습니다.

- 여러 사용자를 한 저장소에서 중앙 관리하려는 경우
- 로그인, DB, 계정 시스템이 있는 멀티유저 SaaS 를 만들려는 경우
- 관리자 기능이나 abuse 대응이 필요한 경우

## 동작 흐름

```text
내 GitHub Pages
    │
    ├─ 비주얼 카탈로그 / 검색 / 요일 필터
    ├─ 작품 선택
    └─ GitHub issue 생성

내 Process Subscription Request
    │
    └─ watchlist.json 갱신

내 Check Webtoon Completions
    │
    ├─ 네이버 웹툰 상태 확인
    ├─ 완결 신호 감지
    ├─ watchlist.json 상태 갱신
    └─ 텔레그램 알림 전송
```

## 빠른 시작

### 1. 내 저장소 만들기

둘 중 하나를 선택하세요.

- `Use this template`
- 또는 `Fork`

그다음 복사된 저장소에서 아래 설정을 진행합니다.

### 2. 텔레그램 시크릿 추가

GitHub repository secrets:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

### 3. 워크플로 활성화

Actions 탭에서 아래 워크플로를 활성화합니다.

- `Check Webtoon Completions`
- `Process Subscription Request`

### 4. GitHub Pages 켜기

`Settings -> Pages` 에서:

- Source: `Deploy from a branch`
- Branch: `main`
- Folder: `/docs`

배포 후 페이지 주소는 보통 다음 형태입니다.

`https://<your-name>.github.io/<your-repo>/`

### 5. 카탈로그 초기화

`Check Webtoon Completions` 를 한 번 수동 실행하세요.

이 첫 실행이 끝나야:

- `docs/catalog.json`
- `docs/tracked.json`

파일이 실제 데이터로 채워지고, 비주얼 페이지에도 목록이 뜹니다.

### 6. 웹에서 작품 관리

GitHub Pages 화면에서:

1. 요일별로 보거나 제목으로 검색합니다.
2. 작품을 하나 이상 선택합니다.
3. `추가하기` 또는 `제거하기` 를 누릅니다.
4. 생성된 GitHub issue 를 제출합니다.
5. `Process Subscription Request` 가 `watchlist.json` 을 갱신합니다.
6. `내 워치리스트` 필터로 현재 추적 중인 작품만 따로 볼 수 있습니다.

## 선택 사항: 로컬 CLI

로컬에서도 관리하고 싶다면:

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

## 워크플로

[check-webtoons.yml](/Users/jiyunkim/Desktop/courses/naver-webtoon-notifier/.github/workflows/check-webtoons.yml:1)

- 매일 `13:30 UTC` 실행
- `watchlist.json` 의 active 항목 검사
- 새 완결이면 텔레그램 전송
- `docs/catalog.json`, `docs/tracked.json` 갱신

[process-subscription-request.yml](/Users/jiyunkim/Desktop/courses/naver-webtoon-notifier/.github/workflows/process-subscription-request.yml:1)

- `subscription-request` issue 감지
- 선택된 `titleId` 와 요청 타입 파싱
- `watchlist.json` 에 추가 또는 제거
- 결과 코멘트를 남기고 issue 종료

## 프로젝트 구조

```text
src/
├── catalog.py                    # 카탈로그 + 썸네일 수집
├── export_catalog.py             # docs/catalog.json 생성
├── process_subscription_issue.py # add/remove issue 처리
├── manage.py                     # 로컬 CLI
├── naver_api.py                  # 작품 상태 / 회차 정보 조회
├── detector.py                   # 완결 감지 로직
├── notifier.py                   # Telegram / email / Slack notifier
├── check.py                      # daily checker entrypoint
└── watchlist.py                  # watchlist.json persistence

docs/
├── index.html
├── app.js
├── styles.css
├── catalog.json
└── tracked.json
```

## 참고

- `catalog.json` 은 GitHub Actions 가 생성합니다.
- `tracked.json` 은 현재 추적 중인 `title_id` 목록입니다.
- 비주얼 선택 화면은 GitHub Pages 에서만 동작합니다.
- 이 템플릿은 저비용 self-serve 사용에 맞춰져 있습니다.
