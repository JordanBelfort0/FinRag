import re
from vectorstore.chroma_store import query_store


TICKER_PATTERNS = {
    "apple": "AAPL", "aapl": "AAPL",
    "microsoft": "MSFT", "msft": "MSFT",
    "google": "GOOGL", "alphabet": "GOOGL", "googl": "GOOGL",
    "amazon": "AMZN", "amzn": "AMZN",
    "nvidia": "NVDA", "nvda": "NVDA",
    "tesla": "TSLA", "tsla": "TSLA",
    "meta": "META", "facebook": "META",
}


def extract_ticker(query: str) -> str | None:
    """Extract a ticker symbol from a natural language query."""
    q = query.lower()
    for keyword, ticker in TICKER_PATTERNS.items():
        if keyword in q:
            return ticker
    match = re.search(r'\b([A-Z]{2,5})\b', query)
    if match:
        return match.group(1)
    return None


def extract_year(query: str) -> str | None:
    """Extract a 4-digit year from a query."""
    match = re.search(r'\b(20[12]\d)\b', query)
    return match.group(1) if match else None


def extract_section(query: str) -> str | None:
    """Map query keywords to filing sections for targeted retrieval."""
    q = query.lower()
    if any(k in q for k in ["risk", "threat", "challenge", "concern"]):
        return "risk_factors"
    if any(k in q for k in ["revenue", "income", "profit", "margin",
                              "earnings", "eps", "cash", "financial"]):
        return "financials"
    if any(k in q for k in ["management", "discuss", "outlook",
                              "strategy", "results of operation"]):
        return "mda"
    if any(k in q for k in ["business", "product", "service",
                              "segment", "market"]):
        return "business"
    return None


def retrieve(query: str, top_k: int = 5) -> list[dict]:
    """
    Smart retrieval: extracts ticker/year/section from the query
    and applies them as metadata filters.
    Falls back to broader search if filtered search returns nothing.
    """
    ticker  = extract_ticker(query)
    year    = extract_year(query)
    section = extract_section(query)

    print(f"  [Retriever] ticker={ticker} year={year} section={section}")

    results = query_store(
        query=query,
        ticker=ticker,
        year=year,
        section=section,
        top_k=top_k,
    )

    if not results and section:
        print("  [Retriever] No results with section filter, retrying without...")
        results = query_store(query=query, ticker=ticker, year=year, top_k=top_k)

    if not results and year:
        print("  [Retriever] No results with year filter, retrying without...")
        results = query_store(query=query, ticker=ticker, top_k=top_k)

    return results


def format_context(chunks: list[dict]) -> str:
    """Format retrieved chunks into a clean context block for the LLM."""
    if not chunks:
        return "No relevant context found in the knowledge base."

    parts = []
    for i, chunk in enumerate(chunks, 1):
        meta   = chunk["metadata"]
        source = f"{meta['ticker']} 10-K {meta['year']} (section: {meta['section']})"
        parts.append(f"[Context {i} | {source}]\n{chunk['text'].strip()}")

    return "\n\n---\n\n".join(parts)