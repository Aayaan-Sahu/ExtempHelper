import requests
from readability import Document
from bs4 import BeautifulSoup

import os
import google.generativeai as genai
from google.generativeai.generative_models import GenerativeModel
from langchain_google_genai import HarmCategory, HarmBlockThreshold
from sentence_transformers import SentenceTransformer

import numpy as np
import pickle


def get_index():
    index = []

    try:
        with open("index.bin", "rb") as handler:
            index = pickle.load(handler)
    except FileNotFoundError:
        print("File not found, starting from blank")
        index = []

    return index


def get_reader_mode_content(url):
    response = requests.get(url)
    doc = Document(response.text)
    return doc.summary()


def parse_cleaned_content(content):
    soup = BeautifulSoup(content, 'html.parser')
    return soup.get_text()


# Gets website content
def final_scrape(url):
    cleaned_content = get_reader_mode_content(url)
    cleaned_text = parse_cleaned_content(cleaned_content)
    return cleaned_text


def get_prompt(prompt_file):
    with open(prompt_file, "r") as pf:
        prompt = pf.read()
    return prompt


def setup_models():
    safety = {
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE
    }

    os.environ["GOOGLE_API_KEY"] = "AIzaSyDzZIv7MuD1dfsy4kiAhxe1lIg64KJh_n4"
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

    model = genai.GenerativeModel("gemini-pro", safety_settings=safety)
    embd_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    # prompt = "Below is some text taken from \"[TITLE]\". Your job is to summarize it in a paragraph. \n\n[CONTENT]."
    prompt = get_prompt("summary-prompt.txt")

    return model, embd_model, prompt


def cosine(x):
    if (np.linalg.norm(x[0]) != 0 and np.linalg.norm(x[1]) != 0):
        return np.dot(x[0], x[1]) / (np.linalg.norm(x[0]) * np.linalg.norm(x[1]))
    else:
        return 0


class Url:
    def __init__(self, title, url, date_time):
        self.title = title
        self.url = url
        self.date_time = date_time


def generate_information(
        index,
        prompt: str,
        model: GenerativeModel,
        embd_model: SentenceTransformer,
        url: Url):
    content = final_scrape(url.url)
    summary = model.generate_content(prompt.replace(
        "[TITLE]", url.title).replace("[CONTENT]", content))
    vector = embd_model.encode(url.title + " " + content + " " + summary.text)

    index.append({
        "title": url.title,
        "url": url.url,
        "datetime": url.date_time,
        "content": content,
        "summary": summary.text,
        "vector": vector,
    })


def search(search_term: str, index, embd_model: SentenceTransformer):
    search_vector = embd_model.encode(search_term).flatten()
    scores = {
        i: cosine((entry["vector"], search_vector))
        for i, entry in enumerate(index)
    }

    scores = []
    for i, vector in enumerate(index):
        scores.append([cosine((vector["vector"], search_vector)), i])
    scores = sorted(scores, key=lambda x: x[0], reverse=True)

    results = []

    for i in scores:
        j = index[i[1]].copy()
        j.pop("vector")
        results.append(j)

    return results
