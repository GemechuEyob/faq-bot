from app.db import ScrapedData
from app.embedder import embedder
from sqlalchemy.orm import Session
import numpy as np


def search_similar_content(text: str, limit: int, threshold: float, db: Session):
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
                            "content": item.content,
                            "similarity": float(similarity),
                        }
                    )

    similarity_results.sort(key=lambda x: x["similarity"], reverse=True)
    result_list = similarity_results[:limit]

    return result_list
