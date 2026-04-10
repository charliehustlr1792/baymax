import chromadb
from sentence_transformers import SentenceTransformer
from functools import lru_cache

CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "echomind_techniques"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

_model = None
_collection = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def retrieve_exemplars(
    query: str,
    scratchpad: str,
    n_results: int = 3,
) -> str:
    try:
        collection = get_collection()

        if collection.count() == 0:
            return "No exemplars available."

        model = get_model()

        combined_query = f"{query}\n\n{scratchpad[:300]}"
        query_embedding = model.encode(combined_query).tolist()

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results, collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        if not results["documents"] or not results["documents"][0]:
            return "No relevant exemplars found."

        formatted = []
        for i, (doc, meta, dist) in enumerate(zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )):
            relevance = 1 - dist
            if relevance < 0.2:
                continue
            tag = meta.get("tag", "general")
            formatted.append(f"[Technique: {tag}]\n{doc}")

        if not formatted:
            return "No sufficiently relevant exemplars found."

        return "\n\n---\n\n".join(formatted)

    except Exception as e:
        print(f"RAG retrieval error: {e}")
        return "Exemplar retrieval unavailable."