import httpx, asyncio
from bs4 import BeautifulSoup
from trafilatura import fetch_url, extract
import trafilatura
import re, html
from markdownify import markdownify


def normalize_text(text):
    text = html.unescape(text)  # &nbsp; → space
    text = re.sub(r"\s+", " ", text)  # collapse whitespace
    return text.strip()


def extract_text_blocks(soup):
    # Extract meaningful blocks
    texts = []
    for elem in soup.find_all(["h1", "h2", "h3", "p", "li", "table", "pre"]):
        txt = elem.get_text(" ", strip=True)
        if txt and len(txt.split()) > 3:  # skip short junk
            texts.append(txt)
    return texts


def clean_html(raw_html):
    soup = BeautifulSoup(raw_html, "lxml")

    # Remove scripts, styles, meta
    for tag in soup(
        [
            "script",
            "style",
            "noscript",
            "iframe",
            "header",
            "footer",
            "form",
            "nav",
            "svg",
            "img",
        ]
    ):
        tag.decompose()

    return soup


def parse_html(raw_html, url=None):
    # Use trafilatura first
    extracted = trafilatura.extract(raw_html, url=url, favor_precision=True)
    if extracted:
        return normalize_text(extracted)

    # Fallback: manual cleaning
    soup = clean_html(raw_html)
    texts = extract_text_blocks(soup)
    return "\n\n".join(normalize_text(t) for t in texts)


async def main():
    # TODO (2025-08-26) Implement ingestion + chunking + embeddings (pgvector)
    # ingest the source given
    # sample_url = "https://avatar.fandom.com/wiki/Avatar:_The_Last_Airbender"
    # async with httpx.AsyncClient() as client:
    #     r = await client.get(sample_url)
    #     sample_html = r.text

    # # clean the source data
    # soup = BeautifulSoup(sample_html, "lxml")
    # for tag in soup(
    #     [
    #         "script",
    #         "style",
    #         "noscript",
    #         "iframe",
    #         "header",
    #         "footer",
    #         "form",
    #         "nav",
    #         "svg",
    #         "img",
    #     ]
    # ):
    #     tag.decompose()

    # with open("cleaned_html.html", "w") as fp:
    #     fp.write(str(soup))

    # parsed_text = trafilatura.extract(str(soup), url=sample_url, favor_precision=True)
    # print(parsed_text)

    raw_html = fetch_url("https://avatar.fandom.com/wiki/Avatar:_The_Last_Airbender")
    parsed_text = parse_html(raw_html)

    # output main content and comments as plain text
    # parsed_text = extract(downloaded)
    # parsed_text = html.unescape(parsed_text)
    # parsed_text = re.sub(r"\s+", " ", parsed_text)
    # parsed_text = markdownify(parsed_text, heading_style="ATX")
    with open("cleaned_html.text", "w") as fp:
        fp.write(parsed_text)

    # segement the cleaned data into chuncks

    # embed the segmented data
    # store in a vector DB
    # take user's query
    # embed the query
    # use both embeddings to do knn search in vectory DB
    # optional re-ranker (cross-encoder) to improve top-k quality
    # dedupe by source/section.
    # create a grounded prompt using top contexts from vector db + instructions + tooling (e.g., citation enclosure)
    # run LLM → return answer + cited sources (URLs, titles, snippet line numbers if available)

    # Guardrails
    # refusal policy for questions clearly outside knowledge base (“I don’t have that info” + suggestions).
    # PII redaction (if user content accepted), profanity filter, prompt injection checks.

    # Feedback
    # thumbs up/down + free-text feedback; store query, retrieved docs, answer, latency, and user feedback for continuous improvement.
    # offline eval set (50–100 Q/A pairs) + answer-faithfulness and context-recall metrics.

    # TODO (2025-08-26) Deployment
    # backend: FastAPI (python) or Node.js.
    # hosting: Docker → Fly.io/Render/Vercel serverless (for API) + Vercel/Netlify for UI.
    # Postgres for metadata/tenants; vector DB (Weaviate, Pinecone, Qdrant, or pgvector for small scale)
    # CI/CD: GitHub Actions.


if __name__ == "__main__":
    asyncio.run(main())
