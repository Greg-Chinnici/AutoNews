import requests
import time
import os
from datetime import datetime
import json
import re

import sqlite3
import feedparser
from colorama import Fore, Style
import spacy
import spacy.cli
from sentence_transformers import SentenceTransformer

from bs4 import BeautifulSoup


spacy.cli.download("en_core_web_sm")
# Load the spaCy English model
nlp = spacy.load("en_core_web_sm")

model = SentenceTransformer('all-MiniLM-L6-v2')

LIMIT_PER_FEED = 30
source = ""

'''
Common keys across all entries:
links, published_parsed, id, guidislink, title, title_detail, link, published
'''


def create_db():
    try:
        conn = sqlite3.connect('database/autonews.db')
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                link TEXT NOT NULL,
                published_at TEXT,
                topics TEXT,
                embedding TEXT  -- store as JSON string
            )
        ''')

        conn.commit()
        print("Database and 'articles' table created successfully.")
    except sqlite3.Error as e:
        print(f"An error occurred while creating the database: {e}")
    finally:
        if conn:
            conn.close()


def delete_db():
    db_path = 'database/autonews.db'
    if os.path.exists(db_path):
        os.remove(db_path)
        print("Database deleted successfully.")
    else:
        print("No database found to delete.")


# Extracts main topics, grouping proper nouns into named entities using spaCy, and formats them.
def extract_topics(title, max_topics=10):
    try:
        doc = nlp(title)
        topics = []

        for ent in doc.ents:
            if ent.label_ in {"PERSON", "ORG", "GPE"}:
                topics.append(ent.text)

        standalone_nouns = [
            token.lemma_ for token in doc
            if token.pos_ == "NOUN" and not token.is_stop and token.is_alpha and token.text not in topics
        ]

        topics.extend(standalone_nouns)

        formatted_topics = []
        for topic in topics:
            if topic.endswith("'s"):
                topic = topic[:-2]
            if topic not in formatted_topics:
                formatted_topics.append(topic)

        return ', '.join(formatted_topics[:max_topics])
    except Exception as e:
        print(f"Error extracting topics: {e}")
        return None


def insert_article(title, link, time):
    conn = sqlite3.connect('database/autonews.db')
    cursor = conn.cursor()

    formatted_time = convert_time(time)
    topics = extract_topics(title)
    embedding = model.encode(title).tolist()



    cursor.execute('''
        INSERT INTO articles (title, link, published_at, topics, embedding)
        VALUES (?, ?, ?, ?, ?)
    ''', (title, link, formatted_time, topics, json.dumps(embedding)))

    conn.commit()
    conn.close()


# Converts a timestamp string like 'Wed, 16 Apr 2025 21:02:57 +0000' into ISO 8601 format: '2025-04-16 21:02:57'
def convert_time(raw_time_str):
    try:
        dt = datetime.strptime(raw_time_str, "%a, %d %b %Y %H:%M:%S %z")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError as e:
        print(f"Time conversion error: {e}")
        return None
    

def resolve_final_url(google_news_url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(google_news_url, headers=headers, timeout=5)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        # Find the meta refresh tag
        meta = soup.find("meta", attrs={"http-equiv": "refresh"})
        if meta:
            content = meta["content"]
            # Content looks like "0;URL=https://www.reuters.com/article/...."
            real_url = content.split("URL=")[-1]
            return real_url
        else:
            return google_news_url
    except Exception as e:
        print(f"Error resolving final URL from {google_news_url}: {e}")
        return google_news_url


def main():

    delete_db()
    create_db()

    skip_words = ["Video", "Watch", "Daily Report", "24/7", "CBS", "Here Comes the Sun", "Live", "cartoonists on the week in politics"]

    with open('config/rssfeeds.txt', 'r') as file:
        print(Fore.YELLOW + f"Starting to parse RSS feeds at {time.strftime('%Y-%m-%d %H:%M:%S' , time.localtime())}")
        feeds = file.readlines()
        for feed_link in feeds:
            if feed_link.startswith('#') or not feed_link.strip():
                print(Fore.RED + f"Skipping {feed_link} or empty line.")
                print(Style.RESET_ALL)
                continue
                
            req = requests.get(feed_link.strip())
            obj = feedparser.parse(req.text) # already formatted as xml text, so no bs4 needed

            try:
                source = obj['feed']['title']
                print(Fore.WHITE + f"{source}")
            except KeyError:
                source = "?"
                print(Fore.RED + "Error: Feed title not found.")
            
            total_articles = len(obj.entries)
            for index, entry in enumerate(obj.entries):
                print(Style.RESET_ALL)
                if index >= LIMIT_PER_FEED:
                    print(Fore.RED + f"Limit of {LIMIT_PER_FEED} entries reached for {source}.")
                    print(Fore.RED + f"There are {total_articles} entries in total.")
                    print(Style.RESET_ALL)
                    break
            
                print(Fore.BLUE + f"[{source}:{index + 1}/{total_articles}]")
                try:
                    print(Fore.GREEN   + f"{entry.title}")
                    real_link = resolve_final_url(entry.link)
                    print(Fore.GREEN   + f"{real_link}")
                    print(Fore.MAGENTA + f"{entry.published}")

                    # Check for skip words
                    if any(word.lower() in entry.title.lower() for word in skip_words):
                        print(Fore.RED + f"Skipping article due to skip word match: {entry.title}")
                        continue

                    if any(keyword in entry.link.lower() for keyword in ["video", "play", "watch", "livestream", "meet-the-press"]):
                        print(Fore.RED + f"Skipping article due to video link: {entry.link}")
                        continue

                    # if it gets to this point there is enough info to put it into a database
                    insert_article(entry.title, real_link, entry.published)

                except AttributeError:
                    print(Fore.RED + "Error: Missing attribute in entry.")

            print(Style.RESET_ALL)


main()

