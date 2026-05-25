import argparse
from ingestion.sec_fetcher import fetch_10k
from ingestion.chunker import process_filing
from vectorstore.chroma_store import ingest_chunks, list_ingested_tickers

def main():
    parser = argparse.ArgumentParser(description="Ingest 10-K filings into FinRAG")
    parser.add_argument("tickers", nargs="+", help="Ticker symbols e.g. AAPL MSFT GOOGL")
    parser.add_argument("--years", type=int, default=4, help="Number of years to fetch (default 4)")
    args = parser.parse_args()

    for ticker in args.tickers:
        print(f"\n{'='*50}")
        print(f"  Ingesting {ticker.upper()}")
        print(f"{'='*50}")

        filings = fetch_10k(ticker, num_years=args.years)

        all_chunks = []
        for filing in filings:
            chunks = process_filing(filing)
            all_chunks.extend(chunks)

        ingest_chunks(all_chunks)

    print(f"\n✓ Done. Tickers in store: {list_ingested_tickers()}")

if __name__ == "__main__":
    main()