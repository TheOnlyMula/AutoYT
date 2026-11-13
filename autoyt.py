import os, sys
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

import argparse

from gtts import gTTS

ATOM = {"atom": "http://www.w3.org/2005/Atom"}
HEADERS = {"User-Agent": "autoyt/1.0"}

def parse_feed(xml):
    entry = ET.fromstring(xml).find("atom:entry", ATOM)
    if entry is None:
        return None

    content = BeautifulSoup(entry.findtext("atom:content", "", ATOM), "html.parser")
    body = content.find("div", class_ = "md")
    text = "\n\n".join(p.get_text() for p in body.find_all("p")) if body else ""

    return {
        "title": entry.findtext("atom:title", "", ATOM),
        "link": entry.find("atom:link", ATOM).get("href"),
        "text": text,
    }

def fetch_feed(subreddit):
    feed_url = f"https://www.reddit.com/r/{subreddit}/top/.rss"
    params = {"t": "day", "limit": 1}
    response = requests.get(feed_url, params = params, headers = HEADERS, timeout = 15)
    response.raise_for_status()
    return response.content

def gtts(text): 
    tts = gTTS(text = text, lang = "en", slow = False)
    tts.save("tts.mp3")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--test', action = 'store_true', help = "Whether or not the extract will use the test destination.")
    parser.add_argument('-sr', '--subreddit', type = str, help = "The subreddit to extract from.", default = "AmItheAsshole")
    args = parser.parse_args() 

    if args.test:
        with open("test/feed.xml", "rb") as f:
            data = f.read()
    else:
        data = fetch_feed(args.subreddit, args.num_post)
    post = parse_feed(data)

    if post is None:
        print("No posts found")
        return

    print(f"Post:\n{post["title"]} \nBody:\n{post["text"]}")
    gtts(f"{post["title"]} {post["text"]}")

if __name__ == '__main__':
    main()
