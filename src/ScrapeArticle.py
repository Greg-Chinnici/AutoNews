import os
import shutil
import sqlite3
import requests
from bs4 import BeautifulSoup
import spacy

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import json

from PickTopic import pick_topic 
from GoogleFormsUpdater import createClusters


# Load spaCy's English model
nlp = spacy.load("en_core_web_sm")

model = SentenceTransformer('all-MiniLM-L6-v2')

DATABASE_PATH = "database/autonews.db"
OUTPUT_DIR = "scraped_articles"


def fetch_top_article_by_embeddings(source_filter, selected_topic, threshold=0.5):
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT title, link, embedding FROM articles
            WHERE link LIKE ?
        """, (f"%{source_filter}%",))
        results = cursor.fetchall()
        conn.close()

        if not results:
            print(f"No articles found for source '{source_filter}'.")
            return None

        topic_embedding = model.encode(selected_topic).reshape(1, -1)

        best_article = None
        best_similarity = -1

        for title, link, embedding_json in results:
            if not embedding_json:
                continue

            article_embedding = np.array(json.loads(embedding_json)).reshape(1, -1)
            similarity = cosine_similarity(topic_embedding, article_embedding)[0][0]

            if similarity > best_similarity:
                best_similarity = similarity
                best_article = {"title": title, "link": link}

        if best_article and best_similarity >= threshold:
            print(f"Selected article for source '{source_filter}': {best_article['title']} with similarity {best_similarity:.4f}.")
            return best_article
        else:
            print(f"No relevant articles found for source '{source_filter}' with similarity above threshold {threshold}.")
            return None
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
    

def process_articles_for_sources(sources, topics, output_dir, threshold=0.5):
    """Processes one article per source based on topic matches and aggregates them into a single file."""
    # Generate the output file name based on topics
    file_name = "_".join(topics) + ".txt"
    output_file = os.path.join(output_dir, file_name)

    aggregated_content = []

    for source, skip_words in sources.items():
        print(f"Processing articles for source: {source}")

        article = fetch_top_article_by_embeddings(source_filter=source, selected_topic=topics[0], threshold=threshold)
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
        "apnews": ["Video", "Watch"],
        #"news.google": ["Video", "Watch"],
        "guardian": ["Video", "Watch"],
        "nbcnews": ["Video", "Watch"],
        "cnbc": ["Video", "Watch"],
        "abcnews": ["Video", "Watch"],
        "cbsnews": ["Watch CBS", "Daily Report", "24/7", "CBS", "Here Comes the Sun"],
        "bbc": ["Video", "Watch"],

    }

    topics = createClusters()

    cosine_similarity_threshold = 0.5

    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for selected_topic in topics:
        print(f"Selected Topic: {selected_topic}")
        process_articles_for_sources(sources, [selected_topic], OUTPUT_DIR, threshold=cosine_similarity_threshold)
