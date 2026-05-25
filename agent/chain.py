import os
from groq import Groq
from dotenv import load_dotenv
from agent.prompt import FINANCE_SYSTEM_PROMPT
from agent.retriever import retrieve, format_context

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def ask(query: str, chat_history: list[dict] = None) -> dict:
    """
    Main FinRAG entry point.
    Retrieves context via local embeddings, answers via Groq Llama.
    """
    chunks = retrieve(query)

    if not chunks:
        return {
            "answer": "I couldn't find relevant information in the knowledge base. "
                      "Try ingesting more filings with `python ingest.py TICKER`.",
            "sources": [],
            "chunks_used": 0,
        }

    context = format_context(chunks)

    messages = [{"role": "system", "content": FINANCE_SYSTEM_PROMPT}]

    if chat_history:
        messages.extend(chat_history[-6:])

    messages.append({
        "role": "user",
        "content": f"Context from SEC filings:\n\n{context}\n\nQuestion: {query}"
    })

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.1,
        max_tokens=1000,
    )

    answer = response.choices[0].message.content

    sources = list({
        f"{c['metadata']['ticker']} 10-K {c['metadata']['year']}"
        for c in chunks
    })

    return {
        "answer": answer,
        "sources": sorted(sources),
        "chunks_used": len(chunks),
        "chunks": chunks,
    }