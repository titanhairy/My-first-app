import time
import threading
import requests
from bs4 import BeautifulSoup
from flask import Flask
from datetime import datetime
import pytz
import os

app = Flask(__name__)

status_message = "Starting up..."  # latest status
history = []  # rotating log of last 5 statuses
last_alert = None  # track last alert sent

URL = "https://www.pokemoncenter.com/category/tcg"
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")  # set in Render → Environment


def log_status(message):
    """Keep a rotating log of last 5 statuses"""
    global history, status_message
    status_message = message
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {message}"
    history.append(entry)
    if len(history) > 5:
        history.pop(0)  # keep only last 5


def send_discord(message):
    """Send message to Discord webhook with @here alert"""
    if not DISCORD_WEBHOOK:
        return
    try:
        payload = {"content": f"@here {message}"}
        requests.post(DISCORD_WEBHOOK, json=payload, timeout=10)
    except Exception as e:
        print(f"Discord error: {e}")


def check_site():
    global last_alert
    try:
        response = requests.get(URL, timeout=10)
        if response.status_code != 200:
            log_status(f"Error {response.status_code}")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(" ", strip=True).lower()

        if "out of stock" in text:
            msg = "❌ Out of stock"
            log_status(msg)
            # no discord alert for this
        elif "you are in line" in text or "virtual queue" in text:
            msg = "⚠️ Virtual queue detected"
            log_status(msg)
            if last_alert != msg:
                send_discord(f"Pokemon Center TCG update: {msg}")
                last_alert = msg
        elif "captcha" in text or "verify you are human" in text:
            msg = "🚧 Captcha/security check detected"
            log_status(msg)
            if last_alert != msg:
                send_discord(f"Pokemon Center TCG update: {msg}")
                last_alert = msg
        else:
            msg = "✅ Might be in stock!"
            log_status(msg)
            if last_alert != msg:
                send_discord(f"Pokemon Center TCG update: {msg}")
                last_alert = msg

    except Exception as e:
        log_status(f"Error: {e}")


def loop_checker():
    tz = pytz.timezone("America/Los_Angeles")  # PST/PDT timezone
    last_reset_date = None

    while True:
        now = datetime.now(tz)

        # daily reset at 7am PST
        if now.hour == 7 and (last_reset_date != now.date()):
            log_status("🔄 Daily reset — waiting for next check")
            last_reset_date = now.date()
            # reset alert tracking so you get notified again on changes
            global last_alert
            last_alert = None

        # Monday–Friday, 7am–3pm PST
        if now.weekday() < 5 and 7 <= now.hour < 15:
            check_site()
        else:
            log_status("⏸️ Paused (outside working hours)")

        time.sleep(300)  # check every 5 minutes


@app.route("/")
def home():
    logs_html = "<br>".join(history)
    return f"""
    <h1>Pokemon Center Stock Checker</h1>
    <p><b>Current:</b> {status_message}</p>
    <h3>History (last 5):</h3>
    <p>{logs_html}</p>
    """


if __name__ == "__main__":
    t = threading.Thread(target=loop_checker)
    t.daemon = True
    t.start()
    app.run(host="0.0.0.0", port=10000)

send_discord("🚀 Bot just went live on Render and is connected!")
