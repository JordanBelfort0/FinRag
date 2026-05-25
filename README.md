# 📈 FinRAG — SEC 10-K Intelligence

> Ask natural language questions about public company filings. Every answer is grounded in SEC EDGAR data with source citations — no hallucination.

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square)
![LangChain](https://img.shields.io/badge/LangChain-0.2-green?style=flat-square)
![Groq](https://img.shields.io/badge/Groq-Llama_3.3_70B-orange?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)

---

## What it does

FinRAG lets you query SEC 10-K annual filings using natural language. Ask things like:

- *"What are Apple's main risk factors in 2025?"*
- *"Compare Microsoft and Google's revenue growth from 2023–2025"*
- *"How is Microsoft monetising its AI investments?"*
- *"What did Apple say about supply chain risks?"*

Answers are retrieved directly from the actual filings — not generated from model training data — so every claim is cited and traceable to a specific document and section.

---

## Architecture

SEC EDGAR API
↓
HTML/iXBRL Parser (BeautifulSoup)
↓
Token-aware Chunker (800 tok / 100 overlap) + metadata tagging
↓
Local Embeddings (all-MiniLM-L6-v2)
↓
ChromaDB Vector Store (persistent, cosine similarity)
↑
User Query → embed → retrieve top-5 chunks (+ metadata filters)
↓
Groq Llama 3.3 70B → cited answer
↓
Streamlit UI

---

## Stack

| Layer | Technology |
|---|---|
| Data source | SEC EDGAR API (free, no key needed) |
| Parsing | BeautifulSoup (iXBRL-aware) |
| Embeddings | `all-MiniLM-L6-v2` via sentence-transformers (local, free) |
| Vector store | ChromaDB (persistent on disk) |
| LLM | Groq Llama 3.3 70B (free API) |
| Orchestration | LangChain |
| UI | Streamlit |

---

## Setup

```bash
git clone https://github.com/yourusername/finrag.git
cd finrag
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file:
```env
GROQ_API_KEY=your_groq_key_here
```

Get a free Groq API key at [console.groq.com](https://console.groq.com) — no credit card required.

---

## Usage

**Ingest filings:**
```bash
# Single company
python ingest.py AAPL

# Multiple companies, 3 years each
python ingest.py AAPL MSFT GOOGL --years 3
```

**Run the app:**
```bash
streamlit run app/streamlit_app.py
```

Open `http://localhost:8501` — you'll see the chat interface with your ingested tickers in the sidebar. You can also add new companies directly from the UI.

---

## Project structure

<img width="650" height="385" alt="Screenshot 2026-05-25 at 5 02 01 PM" src="https://github.com/user-attachments/assets/6d8fa512-1800-4093-94c8-c7df16d101ef" />


## Key design decisions

**Why local embeddings?** `all-MiniLM-L6-v2` runs on CPU, costs nothing, and produces strong semantic similarity for financial text. Embedding 600+ chunks takes under 10 seconds on a MacBook.

**Why metadata filtering?** Each chunk is tagged with `ticker`, `year`, and `section` (risk_factors, financials, mda, business). The retriever extracts these from the query and filters before semantic search — dramatically improving precision for questions like *"Apple's risks in 2023"*.

**Why Groq?** Free tier, fast inference (~1s), and Llama 3.3 70B handles multi-document financial reasoning well with a strict system prompt.

---

## Example queries

"What are Apple's main risk factors in 2025?"

"Compare Microsoft and Google revenue in 2024"

"How is Microsoft monetising AI?"

"What did Apple say about the App Store legal challenges?"

"Google's capital expenditure plans?"

"Which company mentioned supply chain risks most prominently?"

---

## Limitations

- Chunk count per filing is modest (~60–100) due to iXBRL stripping — dense financial tables are partially lost
- Retrieval is single-hop; complex multi-step reasoning may require follow-up questions
- ChromaDB is local — not suitable for multi-user cloud deployment without a persistent volume

---

## License

MIT
