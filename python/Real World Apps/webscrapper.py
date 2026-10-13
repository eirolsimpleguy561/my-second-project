import csv
import requests
from bs4 import BeautifulSoup

URL = "https://example.com/articles"
OUTPUT_FILE = "articles.csv"


def scrape_articles(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching page: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    articles = []

    for item in soup.select("article h2 a"):
        title = item.get_text(strip=True)
        link = item.get("href")
        articles.append({"title": title, "link": link})

    return articles


def save_to_csv(articles, filename):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "link"])
        writer.writeheader()
        writer.writerows(articles)
    print(f"Saved {len(articles)} articles to {filename}")


if __name__ == "__main__":
    data = scrape_articles(URL)
    if data:
        save_to_csv(data, OUTPUT_FILE)
    else:
        print("No articles found.")
