import os
from pathlib import Path
from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

load_dotenv()

EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
COLLECTION_NAME  = "finrag_10k"
DB_PATH          = "chroma_db"

# Load once at module level — stays in memory across calls
print("[VectorStore] Loading embedding model...")
_embedder = SentenceTransformer(EMBED_MODEL_NAME)
print("[VectorStore] Model ready.")


def get_collection():
    """Get or create the persistent ChromaDB collection."""
    chroma_client = chromadb.PersistentClient(
        path=DB_PATH,
        settings=Settings(anonymized_telemetry=False)
    )
    collection = chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )
    return collection


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of texts using the local SentenceTransformer model.
    Batches automatically — no API limits to worry about.
    """
    print(f"  [Embed] Embedding {len(texts)} texts locally...")
    embeddings = _embedder.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True,
    )
    return embeddings.tolist()


def ingest_chunks(chunks: list[dict]):
    """
    Embed and store chunks into ChromaDB.
    Idempotent — skips chunks already stored.
    """
    collection = get_collection()

    ids = [
        f"{c['metadata']['ticker']}_{c['metadata']['year']}_{c['metadata']['chunk_index']}"
        for c in chunks
    ]

    # Check which IDs already exist
    existing     = collection.get(ids=ids, include=[])["ids"]
    existing_set = set(existing)

    new_chunks = [c for c, id_ in zip(chunks, ids) if id_ not in existing_set]
    new_ids    = [id_ for id_ in ids if id_ not in existing_set]

    if not new_chunks:
        print("[VectorStore] All chunks already ingested. Skipping.")
        return

    print(f"[VectorStore] Embedding {len(new_chunks)} new chunks...")
    texts      = [c["text"] for c in new_chunks]
    embeddings = embed_texts(texts)

    metadatas = [{k: str(v) for k, v in c["metadata"].items()} for c in new_chunks]

    collection.add(
        ids=new_ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    print(f"[VectorStore] Stored {len(new_chunks)} chunks. "
          f"Collection total: {collection.count()}")


def query_store(
    query: str,
    ticker: str  = None,
    year: str    = None,
    section: str = None,
    top_k: int   = 5,
) -> list[dict]:
    """
    Semantic search with optional metadata filters.
    Returns top_k most relevant chunks.
    """
    collection = get_collection()

    # Embed the query with the same local model
    query_embedding = _embedder.encode([query], convert_to_numpy=True).tolist()

    # Build ChromaDB where clause
    filters = {}
    if ticker:
        filters["ticker"] = ticker.upper()
    if year:
        filters["year"] = str(year)
    if section:
        filters["section"] = section

    if len(filters) > 1:
        where_clause = {"$and": [{k: {"$eq": v}} for k, v in filters.items()]}
    elif len(filters) == 1:
        k, v = next(iter(filters.items()))
        where_clause = {k: {"$eq": v}}
    else:
        where_clause = None

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        where=where_clause,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "text":       doc,
            "metadata":   meta,
            "similarity": round(1 - dist, 4),
        })

    return chunks


def list_ingested_tickers() -> list[str]:
    """Return all tickers currently in the vector store."""
    collection = get_collection()
    if collection.count() == 0:
        return []
    all_meta = collection.get(include=["metadatas"])["metadatas"]
    return sorted(set(m["ticker"] for m in all_meta))


def delete_ticker(ticker: str):
    """Remove all chunks for a given ticker."""
    collection = get_collection()
    collection.delete(where={"ticker": {"$eq": ticker.upper()}})
    print(f"[VectorStore] Deleted all chunks for {ticker}.")