import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from agent.chain import ask
from vectorstore.chroma_store import list_ingested_tickers, delete_ticker

st.set_page_config(
    page_title="FinRAG — SEC Filing Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        background-color: #0f1117 !important;
        font-family: 'Inter', sans-serif;
        color: #e2e8f0;
    }
    [data-testid="stMainBlockContainer"] {
        background-color: #0f1117 !important;
    }
    #MainMenu, footer, header { visibility: hidden; }
    [data-testid="stDecoration"] { display: none; }

    [data-testid="stSidebar"] {
        background-color: #13151f !important;
        border-right: 1px solid #1e2130 !important;
    }
    [data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }

    [data-testid="stChatMessage"] {
        background: transparent !important;
        border: none !important;
        padding: 4px 0 !important;
    }
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"])
    [data-testid="stChatMessageContent"] {
        background: #1e2130 !important;
        border: 1px solid #2a2f45 !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        color: #e2e8f0 !important;
    }

    [data-testid="stChatInput"] {
        background: #13151f !important;
        border: 1.5px solid #2a2f45 !important;
        border-radius: 12px !important;
        color: #e2e8f0 !important;
    }
    [data-testid="stChatInputTextArea"] {
        color: #e2e8f0 !important;
        background: transparent !important;
    }

    [data-testid="stTextInput"] input {
        background: #1e2130 !important;
        border: 1px solid #2a2f45 !important;
        border-radius: 8px !important;
        color: #e2e8f0 !important;
    }

    .stButton > button {
        background: #1e2130 !important;
        border: 1px solid #2a2f45 !important;
        border-radius: 8px !important;
        color: #c8d0e0 !important;
        font-size: 13px !important;
        transition: all 0.15s !important;
    }
    .stButton > button:hover {
        background: #252b3d !important;
        border-color: #3d4460 !important;
        color: #ffffff !important;
    }
    .stButton > button[kind="primary"] {
        background: #2563eb !important;
        border: none !important;
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: #1d4ed8 !important;
    }

    [data-testid="stMetric"] {
        background: #13151f !important;
        border: 1px solid #1e2130 !important;
        border-radius: 10px !important;
        padding: 12px 16px !important;
    }
    [data-testid="stMetricValue"] { color: #e2e8f0 !important; }
    [data-testid="stMetricLabel"] { color: #7c8399 !important; }

    hr { border-color: #1e2130 !important; }
    [data-testid="stSpinner"] { color: #7c8399 !important; }
    [data-testid="stSlider"] * { color: #e2e8f0 !important; }
    [data-testid="stAlert"] {
        background: #13151f !important;
        border: 1px solid #2a2f45 !important;
        color: #e2e8f0 !important;
    }

    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #0f1117; }
    ::-webkit-scrollbar-thumb { background: #2a2f45; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #3d4460; }
</style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

with st.sidebar:
    st.markdown("""
        <div style='padding:8px 0 20px'>
            <span style='font-size:22px;font-weight:700;color:#e2e8f0'>📈 FinRAG</span><br>
            <span style='font-size:11px;color:#4a5068;letter-spacing:0.08em'>SEC 10-K INTELLIGENCE</span>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div style="font-size:11px;font-weight:600;letter-spacing:0.08em;'
        'text-transform:uppercase;color:#4a5068;margin-bottom:10px">Knowledge base</div>',
        unsafe_allow_html=True
    )

    tickers = list_ingested_tickers()

    if tickers:
        cols_per_row = 2
        rows = [tickers[i:i + cols_per_row] for i in range(0, len(tickers), cols_per_row)]
        for row in rows:
            cols = st.columns(len(row))
            for col, t in zip(cols, row):
                with col:
                    st.markdown(
                        f'<div style="display:inline-flex;align-items:center;gap:6px;'
                        f'background:#1a2035;border:1px solid #2a3a5c;border-radius:20px;'
                        f'padding:4px 12px;font-size:13px;font-weight:500;color:#60a0f0;'
                        f'margin:2px">✦ {t}</div>',
                        unsafe_allow_html=True
                    )
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        col1.metric("Companies", len(tickers))
        col2.metric("Years", "3")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            '<div style="font-size:11px;font-weight:600;letter-spacing:0.08em;'
            'text-transform:uppercase;color:#4a5068;margin-bottom:6px">Remove ticker</div>',
            unsafe_allow_html=True
        )
        remove_cols = st.columns(min(len(tickers), 3))
        for i, t in enumerate(tickers):
            with remove_cols[i % 3]:
                if st.button(f"✕ {t}", key=f"del_{t}"):
                    delete_ticker(t)
                    st.rerun()
    else:
        st.markdown(
            '<div style="background:#13151f;border:1px solid #1e2130;border-radius:8px;'
            'padding:12px;font-size:13px;color:#7c8399;text-align:center">'
            'No filings ingested yet.</div>',
            unsafe_allow_html=True
        )

    st.divider()

    st.markdown(
        '<div style="font-size:11px;font-weight:600;letter-spacing:0.08em;'
        'text-transform:uppercase;color:#4a5068;margin-bottom:10px">Add company</div>',
        unsafe_allow_html=True
    )

    new_ticker = st.text_input(
        "Ticker",
        placeholder="NVDA, TSLA, AMZN...",
        label_visibility="collapsed"
    ).upper().strip()

    new_years = st.select_slider(
        "Filing years",
        options=[1, 2, 3, 4, 5],
        value=3,
        label_visibility="visible"
    )

    if st.button("＋ Ingest filings", type="primary", use_container_width=True):
        if new_ticker:
            with st.spinner(f"Fetching {new_ticker} from SEC EDGAR..."):
                try:
                    sys.argv = ["ingest.py", new_ticker, "--years", str(new_years)]
                    from ingest import main as run_ingest
                    run_ingest()
                    st.success(f"✅ {new_ticker} added.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Enter a ticker symbol first.")

    st.divider()

    st.markdown(
        '<div style="font-size:11px;font-weight:600;letter-spacing:0.08em;'
        'text-transform:uppercase;color:#4a5068;margin-bottom:10px">Sample questions</div>',
        unsafe_allow_html=True
    )

    samples = [
        "What are Apple's main risks in 2025?",
        "Compare MSFT and GOOGL revenue 2024",
        "How is Microsoft monetising AI?",
        "What did Google say about competition?",
        "Apple's capital allocation strategy?",
    ]
    for q in samples:
        if st.button(q, use_container_width=True, key=f"sample_{q}"):
            st.session_state.pending_question = q
            st.rerun()

    st.divider()
    st.markdown(
        '<div style="font-size:11px;color:#4a5068;text-align:center;line-height:1.8">'
        'ChromaDB · all-MiniLM-L6-v2 · Groq Llama 3.3<br>Source: SEC EDGAR</div>',
        unsafe_allow_html=True
    )

if not st.session_state.messages:
    st.markdown("""
        <div style="background:#13151f;border:1px solid #1e2130;border-radius:16px;
                    padding:40px 36px;text-align:center;margin:40px auto;max-width:620px">
            <div style="font-size:40px;margin-bottom:14px">📊</div>
            <div style="font-size:24px;font-weight:700;color:#e2e8f0;margin-bottom:10px">
                Ask anything about SEC filings
            </div>
            <div style="font-size:14px;color:#7c8399;line-height:1.8;margin-bottom:24px">
                FinRAG retrieves answers directly from 10-K annual reports.<br>
                Every response is grounded in source documents — no hallucination.
            </div>
            <div style="display:flex;justify-content:center;gap:8px;flex-wrap:wrap">
                <span style="background:#0d1520;border:1px solid #1e3a5c;border-radius:20px;
                             padding:4px 14px;font-size:12px;color:#60a0f0">AAPL · MSFT · GOOGL</span>
                <span style="background:#0d1520;border:1px solid #1e3a5c;border-radius:20px;
                             padding:4px 14px;font-size:12px;color:#60a0f0">2023 · 2024 · 2025</span>
                <span style="background:#0d1520;border:1px solid #1e3a5c;border-radius:20px;
                             padding:4px 14px;font-size:12px;color:#60a0f0">Risk · Revenue · Strategy</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    for col, icon, title, desc in [
        (c1, "🔍", "Semantic retrieval", "Finds relevant passages by meaning, not just keywords"),
        (c2, "📎", "Source citations",   "Every answer cites the exact filing and section"),
        (c3, "⚡", "Cross-company analysis", "Compare financials and strategy across companies"),
    ]:
        with col:
            st.markdown(f"""
                <div style="background:#13151f;border:1px solid #1e2130;border-radius:12px;
                            padding:22px 20px">
                    <div style="font-size:22px;margin-bottom:10px">{icon}</div>
                    <div style="font-weight:600;color:#e2e8f0;margin-bottom:6px;font-size:14px">{title}</div>
                    <div style="font-size:13px;color:#7c8399;line-height:1.6">{desc}</div>
                </div>
            """, unsafe_allow_html=True)

else:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                st.markdown(
                    f'<div style="background:#13151f;border:1px solid #1e2130;'
                    f'border-left:3px solid #2563eb;border-radius:10px;'
                    f'padding:18px 22px;font-size:15px;line-height:1.8;color:#e2e8f0">'
                    f'{msg["content"]}</div>',
                    unsafe_allow_html=True
                )
                if "sources" in msg and msg["sources"]:
                    pills = "".join(
                        f'<span style="display:inline-block;background:#0d1f12;'
                        f'border:1px solid #1a3a22;border-radius:20px;padding:3px 11px;'
                        f'font-size:12px;color:#4ade80;margin:2px 3px">📄 {s}</span>'
                        for s in msg["sources"]
                    )
                    st.markdown(
                        f'<div style="margin-top:10px;display:flex;align-items:center;'
                        f'flex-wrap:wrap;gap:2px">{pills}'
                        f'<span style="font-size:11px;color:#4a5068;margin-left:6px">'
                        f'{msg["chunks_used"]} chunks retrieved</span></div>',
                        unsafe_allow_html=True
                    )
            else:
                st.markdown(msg["content"])

if st.session_state.pending_question:
    query = st.session_state.pending_question
    st.session_state.pending_question = None
else:
    query = st.chat_input("Ask about any company in the knowledge base...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})

    history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages[:-1]
    ]

    with st.spinner("Retrieving from filings..."):
        result = ask(query, chat_history=history)

    st.session_state.messages.append({
        "role":        "assistant",
        "content":     result["answer"],
        "sources":     result["sources"],
        "chunks_used": result["chunks_used"],
    })
    st.rerun()