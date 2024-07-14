import time
import pickle
import urllib3
import logging
import certifi
import requests
import pandas as pd
from bs4 import BeautifulSoup
from GoogleNews import GoogleNews
from sentence_transformers import SentenceTransformer
from utils import final_scrape, get_index, setup_models
from google.generativeai.generative_models import GenerativeModel


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1.2 Safari/605.1.15'}
http = urllib3.PoolManager(
    cert_reqs='CERT_REQUIRED',
    ca_certs=certifi.where()
)

model, embd_model, prompt = setup_models()
index = get_index()

googlenews = GoogleNews()
googlenews.enableException(True)
googlenews.set_lang("en")


def generate_information(
        index,
        prompt: str,
        model: GenerativeModel,
        embd_model: SentenceTransformer,
        url: str,
        content: str,
        title: str,
        date_time: str):
    summary = model.generate_content(prompt.replace(
        "[TITLE]", title).replace("[CONTENT]", content))
    vector = embd_model.encode(title + " " + content + " " + summary.text)

    index.append({
        "title": title,
        "url": url,
        "datetime": date_time,
        "content": content,
        "summary": summary.text,
        "vector": vector,
    })


def search_with_term(search_term: str, googlenews: GoogleNews, number_of_articles=100):
    print_it = True
    googlenews.search(search_term)
    articles = []
    seen_titles = []
    page = 1

    while len(articles) < number_of_articles:
        googlenews.getpage(page)
        results = googlenews.result()
        if not results:
            break
        for result in results:
            title = result["title"]
            if title not in seen_titles:
                seen_titles.append(title)
                articles.append(result)
                print("Seen titles:", seen_titles)
            if len(articles) >= number_of_articles:
                break
        # articles.extend(results)
        page += 1

    # ensure correct number of articles
    articles = articles[:number_of_articles]
    # if print_it:
    #     print(articles[0])
    #     print(type(articles[0]["datetime"]))
    #     print_it = False

    # clean up article links
    for article in articles:
        print("Doing:", article["title"])
        article["link"] = article["link"].split("&ved")[0]
        print("String version of datetime:", article["datetime"])
        try:
            article["datetime"] = article["datetime"].strftime("%m.%d.%Y")
        except:
            pass
        print("Converted version:", article["datetime"])
        print("\n\n")

    return articles


articles = search_with_term(search_term="Tajikistan",
                            googlenews=googlenews, number_of_articles=20)

df = pd.DataFrame(articles)
df.to_csv("google_news_articles.csv")

print("=" * 50)
print("SUMMARIES")
print("=" * 50)

x = 1
for article in articles:
    print("Started:", x)
    x += 1
    title = article["title"]
    url = article["link"]
    date_time = article["datetime"]

    # req = requests.get(url, headers=HEADERS)
    try:
        req = http.request("GET", url, headers=HEADERS)
    except urllib3.exceptions.MaxRetryError as e:
        logging.error("Max retries exceeded with URL: %s", url)
        logging.error("Error: %s", e)
        continue
    except urllib3.exceptions.SSLError as e:
        logging.error("SSL error occurred: %s", e)
        logging.error("CA certificates are located at: %s", certifi.where())
        continue
    except Exception as e:
        logging.error("An unexpected error occurred: %s", e)
        continue
    # soup = BeautifulSoup(req.content, features="html.parser")
    soup = BeautifulSoup(req.data, features="html.parser")
    article_content = final_scrape(url)

    if "forbidden" not in article_content.lower():
        generate_information(index, prompt, model, embd_model, url,
                             article_content, title, date_time)
        time.sleep(4)


with open("index.bin", "wb") as handler:
    pickle.dump(index, handler)
