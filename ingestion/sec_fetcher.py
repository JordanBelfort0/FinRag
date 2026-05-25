import os
import requests
from pathlib import Path
import time

HEADERS = {
    "User-Agent": "FinRAG your@email.com",
    "Accept-Encoding": "gzip, deflate",
}


def get_cik(ticker: str) -> str:
    """Convert ticker symbol to SEC CIK number."""
    resp = requests.get(
        "https://www.sec.gov/files/company_tickers.json",
        headers=HEADERS
    )
    resp.raise_for_status()
    data = resp.json()

    ticker_upper = ticker.upper()
    for entry in data.values():
        if entry["ticker"] == ticker_upper:
            return str(entry["cik_str"]).zfill(10)

    raise ValueError(f"Ticker '{ticker}' not found in SEC database.")


def get_10k_filings(cik: str, num_filings: int = 4) -> list[dict]:
    """Fetch metadata for the most recent 10-K filings."""
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()

    filings = data["filings"]["recent"]
    results = []

    for i, form in enumerate(filings["form"]):
        if form == "10-K":
            results.append({
                "accession_number": filings["accessionNumber"][i].replace("-", ""),
                "accession_raw": filings["accessionNumber"][i],
                "filing_date": filings["filingDate"][i],
                "report_date": filings["reportDate"][i],
                "primary_document": filings["primaryDocument"][i],
                "form": form,
            })
        if len(results) >= num_filings:
            break

    return results


def get_full_10k_document(cik: str, accession_number: str) -> str:
    """
    Fetch the full 10-K HTM document from SEC EDGAR.
    Parses index.htm (works for all filings, including recent ones
    that don't have index.json).
    """
    cik_int    = int(cik)
    acc_clean  = accession_number                                          # 000032019325000079
    acc_dashed = f"{acc_clean[:10]}-{acc_clean[10:12]}-{acc_clean[12:]}"  # 0000320193-25-000079

    index_url = (
        f"https://www.sec.gov/Archives/edgar/data/"
        f"{cik_int}/{acc_clean}/{acc_dashed}-index.htm"
    )

    print(f"  [SEC] Index: {index_url}")
    resp = requests.get(index_url, headers=HEADERS)
    resp.raise_for_status()

    # Parse the filing index table to find the main 10-K document
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(resp.text, "lxml")

    best_doc  = None
    best_size = 0

    for row in soup.select("table tr"):
        cols = [td.get_text(strip=True) for td in row.find_all("td")]
        if len(cols) < 5:
            continue

        doc_type = cols[1]   # e.g. "10-K", "EX-4.1"
        raw_name = cols[2]   # e.g. "aapl-20250927.htmiXBRL"
        size_str = cols[4]   # e.g. "1520208"

        # Only grab the primary 10-K, not exhibits
        if doc_type != "10-K":
            continue

        # Clean garbage appended to filename (e.g. "iXBRL", "XBRL")
        name = raw_name.replace("iXBRL", "").replace("XBRL", "").strip()

        try:
            size = int(size_str)
        except ValueError:
            size = 0

        if name.endswith(".htm") and size > best_size:
            best_doc  = name
            best_size = size

    if not best_doc:
        raise ValueError(
            f"Could not find 10-K document in index for "
            f"CIK={cik_int} accession={acc_dashed}"
        )

    doc_url = (
        f"https://www.sec.gov/Archives/edgar/data/"
        f"{cik_int}/{acc_clean}/{best_doc}"
    )

    print(f"  [SEC] Fetching: {best_doc} ({best_size // 1024} KB)")
    time.sleep(0.5)   # be polite to SEC servers
    doc_resp = requests.get(doc_url, headers=HEADERS)
    doc_resp.raise_for_status()
    return doc_resp.text


def fetch_10k(ticker: str, num_years: int = 4, save_dir: str = "data/raw") -> list[dict]:
    """
    Main entry point. Downloads recent 10-K filings for a ticker.
    Returns list of dicts with filing text + metadata.
    """
    print(f"[SEC] Fetching 10-K filings for {ticker}...")
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    cik = get_cik(ticker)
    print(f"[SEC] CIK: {cik}")

    filings = get_10k_filings(cik, num_filings=num_years)
    print(f"[SEC] Found {len(filings)} filings")

    results = []
    for filing in filings:
        year = filing["report_date"][:4]
        save_path = Path(save_dir) / f"{ticker}_{year}_10K.html"

        if save_path.exists():
            print(f"[SEC] Cached: {save_path}")
            text = save_path.read_text(encoding="utf-8")
        else:
            print(f"[SEC] Downloading {ticker} {year} 10-K...")
            text = get_full_10k_document(cik, filing["accession_number"])
            save_path.write_text(text, encoding="utf-8")
            print(f"[SEC] Saved to {save_path}")

        results.append({
            "ticker": ticker,
            "year": year,
            "filing_date": filing["filing_date"],
            "text": text,
            "source": f"{ticker} 10-K {year}",
        })

    return results


if __name__ == "__main__":
    filings = fetch_10k("AAPL", num_years=2)
    for f in filings:
        print(f"  {f['ticker']} {f['year']} — {len(f['text']):,} chars")