import tiktoken
from ingestion.parser import clean_filing_text


CHUNK_SIZE = 800      # tokens
CHUNK_OVERLAP = 100   # tokens


def count_tokens(text: str, model: str = "text-embedding-3-small") -> int:
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


def split_into_chunks(text: str) -> list[str]:
    """Split text into overlapping chunks by token count."""
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)
    
    chunks = []
    start = 0
    
    while start < len(tokens):
        end = min(start + CHUNK_SIZE, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = enc.decode(chunk_tokens)
        chunks.append(chunk_text)
        
        if end == len(tokens):
            break
        start += CHUNK_SIZE - CHUNK_OVERLAP
    
    return chunks


def detect_section(text: str) -> str:
    """Heuristically detect which section of the 10-K this chunk belongs to."""
    text_lower = text.lower()
    
    if any(k in text_lower for k in ["risk factor", "risk associated", "we may not"]):
        return "risk_factors"
    if any(k in text_lower for k in ["revenue", "net income", "operating income", "gross profit", "earnings per share"]):
        return "financials"
    if any(k in text_lower for k in ["management's discussion", "md&a", "results of operations"]):
        return "mda"
    if any(k in text_lower for k in ["business overview", "our products", "our services", "we design"]):
        return "business"
    if any(k in text_lower for k in ["forward-looking", "cautionary"]):
        return "forward_looking"
    
    return "general"


def process_filing(filing: dict) -> list[dict]:
    """
    Takes a raw filing dict (from sec_fetcher), cleans and chunks it.
    Returns list of chunk dicts ready to embed.
    """
    clean_text = clean_filing_text(filing["text"])
    chunks = split_into_chunks(clean_text)
    
    processed = []
    for i, chunk in enumerate(chunks):
        processed.append({
            "text": chunk,
            "metadata": {
                "ticker": filing["ticker"],
                "year": filing["year"],
                "filing_date": filing["filing_date"],
                "source": filing["source"],
                "section": detect_section(chunk),
                "chunk_index": i,
                "chunk_total": len(chunks),
            }
        })
    
    print(f"[Chunker] {filing['ticker']} {filing['year']}: {len(chunks)} chunks")
    return processed