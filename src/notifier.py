"""
Notification Dispatcher
Extensible notification system — add any channel you want.
Currently supports: console, email (via SMTP), Telegram, Slack, webhook.

Channel is selected automatically from environment variables:
  TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID  → Telegram
  EMAIL_USERNAME + EMAIL_PASSWORD        → Email (Gmail)
  SLACK_BOT_TOKEN + SLACK_CHANNEL       → Slack
Set whichever secrets you want in GitHub → both/all fire if multiple are set.
"""

import json
import os
import smtplib
from abc import ABC, abstractmethod
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from detector import DetectionResult

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------

class Notifier(ABC):
    """Base class for all notification channels."""

    @abstractmethod
    def send(self, result: DetectionResult) -> bool:
        """Send a notification. Returns True on success."""
        pass

    def format_message(self, result: DetectionResult) -> dict:
        """Format the detection result into title + body."""
        title = f"🎉 웹툰 완결: {result.title_name}"
        body_lines = [
            f"「{result.title_name}」 has reached its final episode!",
            f"",
            f"📊 Total Episodes: {result.total_episodes}",
            f"📝 Final Episode: #{result.latest_ep_no} - {result.latest_ep_title}",
            f"🔗 Read it: {result.webtoon_url}",
            f"",
            f"Detection confidence: {result.confidence} ({len(result.signals)} signals)",
        ]
        if result.signals:
            body_lines.append("")
            body_lines.append("Signals detected:")
            for sig in result.signals:
                body_lines.append(f"  • {sig}")
        return {"title": title, "body": "\n".join(body_lines)}


# ---------------------------------------------------------------------------
# Console (for testing / logging)
# ---------------------------------------------------------------------------

class ConsoleNotifier(Notifier):
    def send(self, result: DetectionResult) -> bool:
        msg = self.format_message(result)
        print(f"\n{'='*60}")
        print(f"🔔 NOTIFICATION: {msg['title']}")
        print(f"{'='*60}")
        print(msg["body"])
        print(f"{'='*60}\n")
        return True


# ---------------------------------------------------------------------------
# Webhook (Discord, Slack incoming webhook, custom server, etc.)
# ---------------------------------------------------------------------------

class WebhookNotifier(Notifier):
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send(self, result: DetectionResult) -> bool:
        if not HAS_REQUESTS:
            print("Error: 'requests' library needed for webhook notifications")
            return False
        msg = self.format_message(result)
        payload = {
            "text": f"*{msg['title']}*\n{msg['body']}",         # Slack format
            "content": f"**{msg['title']}**\n{msg['body']}",     # Discord format
        }
        try:
            resp = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            return resp.status_code < 300
        except Exception as e:
            print(f"Webhook error: {e}")
            return False


# ---------------------------------------------------------------------------
# Email (SMTP)
# ---------------------------------------------------------------------------

class EmailNotifier(Notifier):
    def __init__(
        self,
        smtp_host: str = "smtp.gmail.com",
        smtp_port: int = 587,
        sender_email: str = "",
        sender_password: str = "",   # For Gmail, use an App Password
        recipient_email: str = "",
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.recipient_email = recipient_email

    def send(self, result: DetectionResult) -> bool:
        msg_data = self.format_message(result)
        msg = MIMEMultipart()
        msg["From"] = self.sender_email
        msg["To"] = self.recipient_email
        msg["Subject"] = msg_data["title"]
        msg.attach(MIMEText(msg_data["body"], "plain", "utf-8"))
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"Email error: {e}")
            return False


# ---------------------------------------------------------------------------
# Slack (via Bot Token API — more flexible than webhooks)
# ---------------------------------------------------------------------------

class SlackNotifier(Notifier):
    def __init__(self, bot_token: str, channel: str):
        self.bot_token = bot_token
        self.channel = channel

    def send(self, result: DetectionResult) -> bool:
        if not HAS_REQUESTS:
            print("Error: 'requests' library needed for Slack notifications")
            return False
        msg = self.format_message(result)
        try:
            resp = requests.post(
                "https://slack.com/api/chat.postMessage",
                headers={
                    "Authorization": f"Bearer {self.bot_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "channel": self.channel,
                    "text": f"*{msg['title']}*\n{msg['body']}",
                },
                timeout=10,
            )
            data = resp.json()
            return data.get("ok", False)
        except Exception as e:
            print(f"Slack error: {e}")
            return False


# ---------------------------------------------------------------------------
# Dispatcher — sends to all configured channels
# ---------------------------------------------------------------------------

class NotificationDispatcher:
    def __init__(self):
        self.notifiers: list[Notifier] = []

    def add(self, notifier: Notifier):
        self.notifiers.append(notifier)

    def notify(self, result: DetectionResult) -> dict:
        """Send notification to all channels. Returns {channel_name: success}."""
        outcomes = {}
        for notifier in self.notifiers:
            name = type(notifier).__name__
            try:
                success = notifier.send(result)
                outcomes[name] = success
            except Exception as e:
                outcomes[name] = False
                print(f"Error in {name}: {e}")
        return outcomes


# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------

class TelegramNotifier(Notifier):
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id

    def send(self, result: DetectionResult) -> bool:
        if not HAS_REQUESTS:
            print("Error: 'requests' library needed for Telegram notifications")
            return False
        msg = self.format_message(result)
        text = f"*{msg['title']}*\n\n{msg['body']}"
        try:
            resp = requests.post(
                f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": "Markdown",
                },
                timeout=10,
            )
            data = resp.json()
            if not data.get("ok"):
                print(f"Telegram error: {data.get('description')}")
            return data.get("ok", False)
        except Exception as e:
            print(f"Telegram error: {e}")
            return False


# ---------------------------------------------------------------------------
# Factory — build dispatcher from environment variables
# ---------------------------------------------------------------------------

def build_dispatcher_from_env() -> NotificationDispatcher:
    """
    Auto-detect which notifiers to use based on environment variables.
    Set the corresponding GitHub Secrets and the right channel fires.

      Telegram : TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID
      Email    : EMAIL_USERNAME + EMAIL_PASSWORD + NOTIFY_EMAIL (optional, defaults to sender)
      Slack    : SLACK_BOT_TOKEN + SLACK_CHANNEL
    """
    dispatcher = NotificationDispatcher()

    telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    telegram_chat  = os.environ.get("TELEGRAM_CHAT_ID")
    if telegram_token and telegram_chat:
        dispatcher.add(TelegramNotifier(bot_token=telegram_token, chat_id=telegram_chat))
        print("Notifier: Telegram enabled")

    email_user = os.environ.get("EMAIL_USERNAME")
    email_pass = os.environ.get("EMAIL_PASSWORD")
    if email_user and email_pass:
        recipient = os.environ.get("NOTIFY_EMAIL", email_user)
        dispatcher.add(EmailNotifier(
            sender_email=email_user,
            sender_password=email_pass,
            recipient_email=recipient,
        ))
        print(f"Notifier: Email enabled → {recipient}")

    slack_token   = os.environ.get("SLACK_BOT_TOKEN")
    slack_channel = os.environ.get("SLACK_CHANNEL", "#general")
    if slack_token:
        dispatcher.add(SlackNotifier(bot_token=slack_token, channel=slack_channel))
        print(f"Notifier: Slack enabled → {slack_channel}")

    # Always log to console
    dispatcher.add(ConsoleNotifier())

    if len(dispatcher.notifiers) == 1:
        print("Notifier: No secrets configured — console only")

    return dispatcher
