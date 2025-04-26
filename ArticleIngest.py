import feedparser
import requests
import time

from colorama import Fore, Style

LIMIT_PER_FEED = 20
source = ""

'''
Common keys across all entries:
links, published_parsed, id, guidislink, title, title_detail, link, published
'''

with open('rssfeeds.txt', 'r') as file:
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
                print(Fore.GREEN   + f"{entry.link}")
                print(Fore.MAGENTA + f"{entry.published}")

                # if it gets to this point there is enough info to put it into a database
            except AttributeError:
                print(Fore.RED + "Error: Missing attribute in entry.")

