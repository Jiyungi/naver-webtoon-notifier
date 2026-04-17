# Naver Webtoon Completion Notifier

[English README](./README.md)

네이버 웹툰을 내 GitHub 저장소에서 추적하고, 완결되면 텔레그램으로 알림을 받는 템플릿입니다.

이 저장소는 중앙 서비스가 아닙니다. 각자 자기 저장소로 복사해서 쓰는 구조입니다.

## 이 저장소가 하는 일

설정을 끝내면, 이 저장소는:

- GitHub Pages 에서 웹툰 선택 화면을 보여주고
- 선택한 작품을 `watchlist.json` 에 저장하고
- GitHub Actions 로 주기적으로 상태를 확인하고
- 추적 중인 웹툰이 완결되면 텔레그램 메시지를 보냅니다

## 동작 흐름

```text
GitHub Pages
  -> 웹툰 선택
  -> GitHub issue 생성

Process Subscription Request
  -> watchlist.json 갱신

Check Webtoon Completions
  -> 추적 작품 상태 확인
  -> 상태 갱신
  -> 텔레그램 알림 전송
```

## 설정 방법

### 1. 저장소 복사

둘 중 하나를 선택하세요.

- `Use this template`
- 또는 `Fork`

### 2. 텔레그램 시크릿 추가

복사한 저장소의 GitHub secrets 에 아래 두 값을 넣습니다.

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

### 3. 워크플로 활성화

Actions 탭에서 아래 두 워크플로를 활성화합니다.

- `Check Webtoon Completions`
- `Process Subscription Request`

### 4. GitHub Pages 켜기

`Settings -> Pages` 에서:

- Source: `Deploy from a branch`
- Branch: `main`
- Folder: `/docs`

페이지 주소는 보통 다음 형태입니다.

`https://<your-name>.github.io/<your-repo>/`

### 5. 카탈로그 초기화

`Check Webtoon Completions` 를 한 번 수동 실행하세요.

이 첫 실행이 끝나야:

- `docs/catalog.json`
- `docs/tracked.json`

파일이 실제 데이터로 채워지고, 웹에서도 목록이 보입니다.

## 웹에서 사용하는 방법

GitHub Pages 화면에서:

1. 요일별로 보거나 제목으로 검색합니다.
2. 웹툰을 하나 이상 선택합니다.
3. `추가하기` 를 눌러 추적 목록에 넣습니다.
4. 생성된 GitHub issue 를 제출합니다.
5. `Process Subscription Request` 가 `watchlist.json` 을 갱신합니다.

제거할 때는:

1. `내 워치리스트` 로 이동합니다.
2. 작품을 하나 이상 선택합니다.
3. `제거하기` 를 누릅니다.
4. 생성된 issue 를 제출합니다.

## 텔레그램 메시지는 언제 오나

텔레그램은 “추가 확인용”이 아니라 “완결 알림용”입니다.

즉 텔레그램 메시지는:

- 추적 중인 웹툰이 실제로 완결됐을 때
- 또는 테스트 알림을 실행했을 때

만 옵니다.

웹에서 작품을 추가했다고 바로 텔레그램 메시지가 오지는 않습니다.

## 선택 사항: 로컬 CLI

로컬 명령으로도 관리하고 싶다면:

```bash
git clone https://github.com/YOUR_USERNAME/naver-webtoon-notifier.git
cd naver-webtoon-notifier
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python src/manage.py browse mon
python src/manage.py search "마음의소리"
python src/manage.py add 822557
python src/manage.py remove 822557
python src/manage.py list
python src/manage.py check
```

## 주요 파일

```text
src/
├── catalog.py
├── export_catalog.py
├── process_subscription_issue.py
├── manage.py
├── naver_api.py
├── detector.py
├── notifier.py
├── check.py
└── watchlist.py

docs/
├── index.html
├── app.js
├── styles.css
├── catalog.json
└── tracked.json
```

## 참고

- `catalog.json` 은 GitHub Actions 가 생성합니다
- `tracked.json` 은 현재 추적 중인 `title_id` 목록입니다
- 전체 구조는 비용을 거의 들이지 않고 각자 쓰기 좋게 만들어져 있습니다
