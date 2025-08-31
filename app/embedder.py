from sentence_transformers import SentenceTransformer


class EmbeddingGenerator:
    def __init__(self):
        # Using a lightweight model
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def generate(self, text: str) -> list[float]:
        embedding = self.model.encode(text)
        return embedding.tolist()


embedder = EmbeddingGenerator()
