import json
import os
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from rag.scraper import build_corpus

CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "echomind_techniques"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def get_chroma_client():
    return chromadb.PersistentClient(path=CHROMA_PATH)


def get_or_create_collection(client):
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def build_index(force_rebuild: bool = False):
    client = get_chroma_client()
    collection = get_or_create_collection(client)

    existing_count = collection.count()
    if existing_count > 0 and not force_rebuild:
        print(f"Index already exists with {existing_count} items. Skipping rebuild.")
        print("Run with force_rebuild=True to rebuild.")
        return

    if force_rebuild and existing_count > 0:
        client.delete_collection(COLLECTION_NAME)
        collection = get_or_create_collection(client)
        print("Deleted existing index for rebuild.")

    print(f"Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)

    corpus = build_corpus()

    if not corpus:
        print("Corpus is empty — nothing to index.")
        return

    texts = [item["text"] for item in corpus]
    tags = [item.get("tag", "general") for item in corpus]
    sources = [item.get("source", "unknown") for item in corpus]

    print(f"Embedding {len(texts)} items...")
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)

    ids = [f"item_{i}" for i in range(len(texts))]
    metadatas = [
        {"tag": tags[i], "source": sources[i]}
        for i in range(len(texts))
    ]

    batch_size = 100
    for i in range(0, len(texts), batch_size):
        batch_end = min(i + batch_size, len(texts))
        collection.add(
            ids=ids[i:batch_end],
            embeddings=embeddings[i:batch_end].tolist(),
            documents=texts[i:batch_end],
            metadatas=metadatas[i:batch_end],
        )
        print(f"Indexed {batch_end}/{len(texts)} items")

    print(f"Index built successfully. Total items: {collection.count()}")


if __name__ == "__main__":
    build_index(force_rebuild=True)