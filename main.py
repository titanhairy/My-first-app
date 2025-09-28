import requests
from bs4 import BeautifulSoup
import json
import os

URL = "https://www.pokemoncenter.com/category/tcg"
STATE_FILE = "seen_products.json"

def fetch_products():
    response = requests.get(URL, timeout=10)
    if response.status_code != 200:
        print(f"Error {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(" ", strip=True).lower()

    # Captcha / queue detection
    if "you are in line" in text or "virtual queue" in text:
        print("⚠️ Virtual queue detected")
        return []
    if "captcha" in text or "verify you are human" in text:
        print("🚧 Captcha/security check detected")
        return []

    # Find product blocks
    products = []
    for item in soup.select("li.product-grid__card"):  # selector may need tuning
        title = item.get_text(" ", strip=True)
        link_tag = item.find("a", href=True)
        link = link_tag["href"] if link_tag else None
        products.append({"title": title, "link": link})

    return products

def load_seen():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return []

def save_seen(products):
    with open(STATE_FILE, "w") as f:
        json.dump(products, f, indent=2)

def check_for_changes():
    current = fetch_products()
    if not current:
        return

    seen = load_seen()
    seen_titles = {p["title"] for p in seen}
    current_titles = {p["title"] for p in current}

    # New drops
    new_products = [p for p in current if p["title"] not in seen_titles]
    if new_products:
        print("✨ New products detected:")
        for p in new_products:
            print(f"- {p['title']} ({p['link']})")

    # Restocks (items that were seen but marked as sold out before, then now appear differently)
    # For now we’ll just detect reappearance if something disappeared and came back
    restocks = [p for p in current if p["title"] in seen_titles]
    if restocks:
        print("♻️ Possible restocks detected:")
        for p in restocks:
            print(f"- {p['title']} ({p['link']})")

    save_seen(current)

if __name__ == "__main__":
    check_for_changes()
