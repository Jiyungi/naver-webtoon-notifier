"""
Notification Dispatcher
Extensible notification system — add any channel you want.
Currently supports: console, webhook, email (via SMTP), Slack.
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
# Factory — build dispatcher from config file
# ---------------------------------------------------------------------------

def build_dispatcher_from_config(config_path: str = None) -> NotificationDispatcher:
    """
    Build a dispatcher from a JSON config file.
    Config format:
    {
      "notifications": [
        {"type": "console"},
        {"type": "webhook", "url": "https://hooks.slack.com/..."},
        {"type": "email", "smtp_host": "...", "smtp_port": 587,
         "sender_email": "...", "sender_password": "...", "recipient_email": "..."},
        {"type": "slack", "bot_token": "xoxb-...", "channel": "#webtoon-alerts"}
      ]
    }
    """
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), "config.json")

    dispatcher = NotificationDispatcher()

    if not os.path.exists(config_path):
        # Default to console only
        dispatcher.add(ConsoleNotifier())
        return dispatcher

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    for entry in config.get("notifications", []):
        ntype = entry.get("type", "").lower()
        if ntype == "console":
            dispatcher.add(ConsoleNotifier())
        elif ntype == "webhook":
            dispatcher.add(WebhookNotifier(webhook_url=entry["url"]))
        elif ntype == "email":
            dispatcher.add(EmailNotifier(
                smtp_host=entry.get("smtp_host", "smtp.gmail.com"),
                smtp_port=entry.get("smtp_port", 587),
                sender_email=entry.get("sender_email", ""),
                sender_password=entry.get("sender_password", ""),
                recipient_email=entry.get("recipient_email", ""),
            ))
        elif ntype == "slack":
            dispatcher.add(SlackNotifier(
                bot_token=entry.get("bot_token", ""),
                channel=entry.get("channel", "#general"),
            ))
        else:
            print(f"Unknown notification type: {ntype}")

    # Always include console as fallback
    if not any(isinstance(n, ConsoleNotifier) for n in dispatcher.notifiers):
        dispatcher.add(ConsoleNotifier())

    return dispatcher
