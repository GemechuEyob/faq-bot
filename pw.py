from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import os
from sentence_transformers import SentenceTransformer
from itertools import islice
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

load_dotenv()


def scrape_url(url: str):
    start_time = time.time()
    with sync_playwright() as p:
        browser = p.chromium.launch()  # TODO: might need to use a diff library to get the html. this is taking too long sometimes
        page = browser.new_page()
        page.goto(url, timeout=100000)
        html_content = page.content()

        with open("pw_content.html", "w") as fp:
            fp.write(html_content)

        soup = BeautifulSoup(html_content, "lxml")
        for tag in soup(["script", "style"]):
            tag.decompose()

        # Get text and clean whitespace
        text = (
            soup.get_text()
        )  # Note!! totally ignored tables. who know what else it might ignore
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = " ".join(chunk for chunk in chunks if chunk)
        with open("bs4_clean1.txt", "w") as fp:
            fp.write(text)

        # chunk data into pieces of paragraphs
        def chunk_list(iterable, chunk_size):
            it = iter(iterable)
            while True:
                chunk = list(islice(it, chunk_size))
                if not chunk:
                    break
                yield chunk

        chunks = ["".join(chunk) for chunk in chunk_list(text, 145)]
        with open("chunks.txt", "w") as fp:
            fp.write(str(chunks))

        # get embeddings
        model = SentenceTransformer("all-MiniLM-L6-v2")
        embeddings = {}
        for i, chunk in enumerate(chunks):
            embeddings[f"chunk_{i}"] = model.encode(chunk)

        with open("embeddings.txt", "w") as fp:
            fp.write(str(embeddings))

        # store in vector db
        pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
        pc.create_index(
            name="faq",
            dimension=384,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        idx = pc.Index("faq")
        for id, embedding in embeddings.items():
            idx.upsert(vectors=[{"id": id, "values": embedding}])

        browser.close()

    print(f"Took {time.time() - start_time} seconds")


if __name__ == "__main__":
    scrape_url("https://avatar.fandom.com/wiki/Avatar:_The_Last_Airbender")
