import os
import shutil
import sqlite3
import requests
from bs4 import BeautifulSoup


DATABASE_PATH = "database/autonews.db"
OUTPUT_DIR = "scraped_articles"
LIMIT = 5


def fetch_cbs_news_links(limit=LIMIT, offset=0):
    """Fetches CBS News links from the database with a limit and offset."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Query to fetch CBS News links with limit and offset
        cursor.execute("""
            SELECT title, link FROM articles
            WHERE link LIKE '%cbsnews.com%'
            LIMIT ? OFFSET ?
        """, (limit, offset))
        results = cursor.fetchall()
        conn.close()

        return [{"title": row[0], "link": row[1]} for row in results]
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []


def scrape_article(title, link):

    skip_words = ["CBS News", "CBS", "CBSNews", "Watch CBS", "Daily Report", "America Decides"]

    try:
        # Skip articles with "CBS" in the title
        if any(word in title for word in skip_words):
            print(f"Skipping article due to title containing '{skip_words} News': {title}\n")
            return None

        response = requests.get(link)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Attempt to extract the main content of the article
        paragraphs = soup.find_all("p")
        content = "\n".join([p.get_text() for p in paragraphs if p.get_text()])

        print(f"Link: {link}\n")
        print(f"Content: {content}\n")

        return content, link
    except Exception as e:
        print(f"Error scraping {link}: {e}")
        return None


def save_article(title, content, link):
    """Saves the article content to a .txt file."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Create a valid filename from the title
    filename = f"{title[:50].replace(' ', '_').replace('/', '_')}.txt"
    filepath = os.path.join(OUTPUT_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as file:
        file.write(f"Title: {title}\n")
        file.write(f"Link: {link}\n")
        file.write(content)

    print(f"Article saved to {filepath}")


def process_articles():
    valid_articles = []
    offset = 0  # Offset for fetching additional articles if needed

    while len(valid_articles) < LIMIT:
        # Fetch articles with an offset to avoid duplicates
        articles = fetch_cbs_news_links(limit=LIMIT + offset)[offset:]
        if not articles:
            print("No more articles available in the database.")
            break

        for article in articles:
            if len(valid_articles) >= LIMIT:
                break

            print(f"Scraping: {article['title']}")
            result = scrape_article(article["title"], article["link"])
            if result:  # Only proceed if scrape_article returns valid content
                content, link = result
                save_article(article["title"], content, link)
                valid_articles.append(article)

        offset += LIMIT 


if __name__ == "__main__":

    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    process_articles()