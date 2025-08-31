import logging
from datetime import datetime, timezone
from typing import List

import numpy as np
from fastapi import Depends, FastAPI, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .db import ScrapedData, get_db
from .embedder import embedder
from .scraper import scrape_url

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.DEBUG,
)
app = FastAPI()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class SimilaritySearch(BaseModel):
    text: str
    limit: int = 5
    threshold: float = 0.7


class ScrapeRequest(BaseModel):
    urls: List[str]


@app.post("/v1/scrape")
def trigger_scrape(request: ScrapeRequest, db: Session = Depends(get_db)):
    results = []
    for url in request.urls:
        success = scrape_url(url=url, db=db)
        results.append({"url": url, "success": success})
    return JSONResponse(content=results)


@app.get("/v1/data/{data_id}")
def get_scrapped_data_by_id(data_id: int):
    pass


@app.get("/v1/search")
def search_similar_content(
    text: str = Query(..., description="Text to search for similar content"),
    limit: int = Query(5, description="Number of similar items to return"),
    threshold: float = Query(0.7, description="Minimum similarity score"),
    db: Session = Depends(get_db),
):
    try:
        search_embedding = embedder.generate(text)
        all_data = db.query(ScrapedData).all()

        similarity_results = []
        for item in all_data:
            if item.embedding is not None:
                item_embedding = np.array(item.embedding)
                search_embedding_np = np.array(search_embedding)

                item_norm = np.linalg.norm(item_embedding)
                search_norm = np.linalg.norm(search_embedding_np)

                if item_norm > 0 and search_norm > 0:
                    # Calculate cosine similarity with the dot product between item_embedding and search_embedding_np
                    similarity = np.dot(item_embedding, search_embedding_np) / (
                        item_norm * search_norm
                    )

                    if similarity > threshold:
                        similarity_results.append(
                            {
                                "id": item.id,
                                "url": item.url,
                                "content": item.content[:200] + "...",
                                "similarity": float(similarity),
                            }
                        )

        similarity_results.sort(key=lambda x: x["similarity"], reverse=True)
        result_list = similarity_results[:limit]

        return result_list

    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return JSONResponse(
            status_code=500, content={"detail": "An error occured during search."}
        )


@app.get("/v1/health")
async def health_check():
    return JSONResponse(
        content={
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


# uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
