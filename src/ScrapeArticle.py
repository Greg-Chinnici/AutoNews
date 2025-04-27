import os
import shutil
import sqlite3
import requests
from bs4 import BeautifulSoup
import spacy


# Load spaCy's English model
nlp = spacy.load("en_core_web_sm")

DATABASE_PATH = "database/autonews.db"
OUTPUT_DIR = "scraped_articles"
LIMIT = 5


def fetch_top_article_by_topics(source_filter, topics, min_matches):
    """Fetches the top article for a specific source based on the most topic matches using NLP."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT title, link, topics FROM articles
            WHERE link LIKE ?
        """, (f"%{source_filter}%",))
        results = cursor.fetchall()
        conn.close()

        # Preprocess input topics: lowercase and lemmatize
        input_topics = set()
        for topic in topics:
            doc = nlp(topic)
            for token in doc:
                input_topics.add(token.lemma_.lower())

        top_article = None
        max_matches = 0

        for title, link, article_topics in results:
            if not article_topics:
                continue

            split_topics = [t.strip() for t in article_topics.split(",")]

            article_tokens = set()
            for topic_phrase in split_topics:
                doc = nlp(topic_phrase)
                for token in doc:
                    article_tokens.add(token.lemma_.lower())

            matches = len(input_topics.intersection(article_tokens))

            if matches >= min_matches:
                if matches > max_matches:
                    max_matches = matches
                    top_article = {"title": title, "link": link}

        if top_article:
            print(f"Selected article for source '{source_filter}': {top_article['title']} with {max_matches} matches.")
        else:
            print(f"No relevant articles found for source '{source_filter}'.")

        return top_article
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None


def scrape_article(title, link, skip_words):
    """Scrapes the article content from the given link, skipping unwanted titles."""
    try:
        if any(word in title for word in skip_words):
            print(f"Skipping article due to title containing skip words: {title}\n")
            return None

        response = requests.get(link)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        paragraphs = soup.find_all("p")
        content = "\n".join([p.get_text() for p in paragraphs if p.get_text()])

        print(f"Scraped content from: {link}\n")
        return content, link
    except Exception as e:
        print(f"Error scraping {link}: {e}")
        return None
    

def process_articles_for_sources(sources, topics, output_dir, min_matches):
    """Processes one article per source based on topic matches and aggregates them into a single file."""
    # Generate the output file name based on topics
    file_name = "_".join(topics) + ".txt"
    output_file = os.path.join(output_dir, file_name)

    aggregated_content = []

    for source, skip_words in sources.items():
        print(f"Processing articles for source: {source}")

        # Fetch the top article for the current source
        article = fetch_top_article_by_topics(source_filter=source, topics=topics, min_matches=min_matches)
        if not article:
            print(f"No articles found for source: {source}")
            continue

        print(f"Scraping: {article['title']}")
        result = scrape_article(article["title"], article["link"], skip_words)
        if result:  # Only proceed if scrape_article returns valid content
            content, link = result
            aggregated_content.append(f"Source: {source}\nTitle: {article['title']}\nLink: {link}\n\n{content}\n{'-'*80}")

    with open(output_file, 'w', encoding='utf-8') as file:
        file.write('\n\n'.join(aggregated_content))

    print(f"Aggregated content written to {output_file}")


if __name__ == "__main__":

    # Define sources and their respective skip words
    sources = {
        "nbcnews": ["Video", "Watch"],
        "cnbc": ["Video", "Watch"],
        "abcnews": ["Video", "Watch"],
        "cbsnews": ["Watch CBS", "Daily Report"],
        "politico": ["Video", "Watch"],
        "bbc": ["Video", "Watch"]
    }

    # hardcoded topics for testing
    #topics = ["Trump", "Zelensky", "Ukraine", "Russia", "NATO"]
    topics = ["Giuffre", "Epstein", "Maxwell"]

    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    process_articles_for_sources(sources, topics, OUTPUT_DIR, min_matches=2)
