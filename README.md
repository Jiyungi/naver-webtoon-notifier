# Naver Webtoon Completion Notifier

Get notified when your ongoing Naver Webtoon series posts its final episode.

Runs daily via **GitHub Actions** (free) — no server, no API keys, no cost.

## How It Works

```
GitHub Actions (daily cron)
    │
    ▼
Naver Webtoon Public API ──→ "finished": true?
    │                              │
    │  Also checks episode         │
    │  titles for: 최종화,          │
    │  마지막화, 완결, etc.         │
    │                              │
    ▼                              ▼
watchlist.json updated      Email notification sent
(committed back to repo)    (only on new completions)
```

### Detection Signals

| Signal | Source | Reliability |
|--------|--------|-------------|
| `finished: true` | Naver API | Very High — official flag |
| `publishDescription` contains "완결" | Naver API | Very High |
| Episode title keywords (최종화, 마지막화, 완결, etc.) | Episode list | Medium-High |

The system uses **multiple signals** because not every webtoon labels its final episode the same way. Some say `마지막화`, some just use a number. The API `finished` flag is the primary detector.

## Setup (5 minutes)

### 1. Fork or clone this repo

```bash
git clone https://github.com/YOUR_USERNAME/naver-webtoon-notifier.git
cd naver-webtoon-notifier
```

### 2. Add your webtoons

```bash
# By title ID (from the URL: comic.naver.com/webtoon/list?titleId=822557)
python src/manage.py add 822557

# By URL
python src/manage.py add "https://comic.naver.com/webtoon/list?titleId=822557"

# See your watchlist
python src/manage.py list

# Remove one
python src/manage.py remove 822557
```

Or just edit `watchlist.json` directly.

### 3. Set up email notifications

You need a Gmail account to send notification emails. Create an **App Password** (not your regular password):

1. Go to [Google App Passwords](https://myaccount.google.com/apppasswords)
2. Create a new app password (name it "Webtoon Notifier")
3. Copy the 16-character password

Then add these **GitHub Secrets** (Settings → Secrets and variables → Actions):

| Secret | Value |
|--------|-------|
| `EMAIL_USERNAME` | Your Gmail address (e.g. `you@gmail.com`) |
| `EMAIL_PASSWORD` | The 16-char App Password from step 2 |
| `NOTIFY_EMAIL` | Where to receive notifications (can be any email) |

### 4. Enable GitHub Actions

Go to the **Actions** tab in your repo and enable workflows. The check runs daily at:
- **10:00 PM KST** / **7:00 PM IST** / **1:30 PM UTC**

You can also trigger it manually from the Actions tab ("Run workflow" button).

### 5. Push and done

```bash
git add .
git commit -m "Initial setup"
git push
```

## Managing Your Watchlist

### Add a new webtoon
```bash
python src/manage.py add 822557
git add watchlist.json
git commit -m "Add new webtoon"
git push
```

### Remove a webtoon
```bash
python src/manage.py remove 822557
git add watchlist.json
git commit -m "Remove webtoon"
git push
```

### Check status manually
```bash
# Check all watched webtoons
python src/manage.py check

# Check a specific webtoon (doesn't need to be in watchlist)
python src/manage.py status 822557
```

## Notification-Free Option

If you don't want email, you can skip the secrets and just check the GitHub Actions logs — they show the status of every webtoon on each run.

Alternatively, swap email for **Discord** or **Slack** by editing `.github/workflows/check-webtoons.yml`.

## Project Structure

```
naver-webtoon-notifier/
├── .github/workflows/
│   └── check-webtoons.yml    ← GitHub Actions daily cron
├── src/
│   ├── naver_api.py           ← Naver Webtoon API client
│   ├── watchlist.py           ← Watchlist persistence
│   ├── detector.py            ← Multi-signal completion detection
│   ├── notifier.py            ← Notification channels (extensible)
│   ├── check.py               ← GitHub Actions entry point
│   └── manage.py              ← CLI for managing watchlist
├── watchlist.json             ← Your tracked webtoons (committed to repo)
├── requirements.txt
└── README.md
```

## Cost

**$0.** GitHub Actions free tier gives 2,000 minutes/month. Each run takes ~10 seconds. Even checking 50 webtoons daily would use <1% of the free quota.
