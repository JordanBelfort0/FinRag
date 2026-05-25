from ingestion.sec_fetcher import fetch_10k
from ingestion.chunker import process_filing

# Test with Apple, 2 years only (faster)
filings = fetch_10k("AAPL", num_years=2)

all_chunks = []
for filing in filings:
    chunks = process_filing(filing)
    all_chunks.extend(chunks)

print(f"\nTotal chunks: {len(all_chunks)}")
print(f"\nSample chunk:")
print(all_chunks[10]["text"][:300])
print(f"\nMetadata: {all_chunks[10]['metadata']}")