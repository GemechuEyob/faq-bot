def main():
    # ingest the source given
    source_doc = "1_the_jungle_book.txt"
    # clean the source data
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

    # Deployment
    # backend: FastAPI (python) or Node.js.
    # hosting: Docker → Fly.io/Render/Vercel serverless (for API) + Vercel/Netlify for UI.
    # Postgres for metadata/tenants; vector DB (Weaviate, Pinecone, Qdrant, or pgvector for small scale)
    # CI/CD: GitHub Actions.


if __name__ == "__main__":
    main()
