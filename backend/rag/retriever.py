import chromadb
from sentence_transformers import SentenceTransformer
from functools import lru_cache

CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "echomind_techniques"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_model():
    return SentenceTransformer(EMBEDDING_MODEL)


@lru_cache(maxsize=1)
def get_collection():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def retrieve_exemplars(
    query: str,
    scratchpad: str,
    n_results: int = 3,
) -> str:
    """
    Build a semantic query from the user message + scratchpad signal,
    retrieve the top-n matching technique exemplars,
    and format them for injection into the generation prompt.
    """
    collection = get_collection()

    if collection.count() == 0:
        return "No exemplars available. Run rag/embedder.py first."

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