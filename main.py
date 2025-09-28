import requests
from bs4 import BeautifulSoup

urls = {
    "Pokemon Center TCG": "https://www.pokemoncenter.com/category/tcg",
    "Costco Item 1": "https://www.costco.ca/.product.4000387559.html",
    "Costco Item 2": "https://www.costco.ca/.product.4000368515.html"
}

def check_site(name, url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"{name}: Error {response.status_code}")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(" ", strip=True).lower()

        # Check for different scenarios
        if "out of stock" in text:
            print(f"{name}: ❌ Out of stock")
        elif "you are in line" in text or "virtual queue" in text:
            print(f"{name}: ⚠️ Virtual queue detected")
        elif "captcha" in text or "verify you are human" in text:
            print(f"{name}: 🚧 Captcha/security check detected")
        else:
            print(f"{name}: ✅ Might be in stock!")

    except Exception as e:
        print(f"{name}: Error {e}")

for name, url in urls.items():
    check_site(name, url)
