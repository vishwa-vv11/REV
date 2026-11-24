"""
AutoDiagnose: Interactive Streamlit Web Dashboard (Phase 7)
Provides an end-to-end interface for automotive troubleshooting,
with hybrid search controls, evidence inspection, and PDF manual ingestion.
"""
import streamlit as st
import json
import time
from pathlib import Path
import sys

# Ensure project root is in sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import config
from retrieval.vector_search import VectorRetriever
from retrieval.bm25_search import BM25Retriever
from retrieval.hybrid_search import HybridRetriever
from generation.answer_generator import AutoDiagnoseGenerator
from generation.context_builder import ContextBuilder
from ingestion.document_loader import DocumentLoader
from ingestion.chunking import AutomotiveChunker, Chunk

# Page Configuration
st.set_page_config(
    page_title="AutoDiagnose | Automotive Diagnostic Intelligence",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .metric-badge {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        border-radius: 0.375rem;
        font-weight: 600;
        font-size: 0.85rem;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .badge-diy { background-color: #D1FAE5; color: #065F46; }
    .badge-pro { background-color: #FEE2E2; color: #991B1B; }
    .badge-code { background-color: #DBEAFE; color: #1E40AF; }
    .badge-verified { background-color: #E0E7FF; color: #3730A3; }
    .evidence-box {
        background-color: #F9FAFB;
        border: 1px solid #E5E7EB;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_rag_engine():
    """Initializes and caches the hybrid RAG components."""
    v_retriever = VectorRetriever()
    h_retriever = HybridRetriever(vector_retriever=v_retriever)
    generator = AutoDiagnoseGenerator(retriever=h_retriever)
    chunker = AutomotiveChunker()
    loader = DocumentLoader()
    return v_retriever, h_retriever, generator, chunker, loader

v_retriever, h_retriever, generator, chunker, loader = load_rag_engine()

# --- Sidebar Controls ---
st.sidebar.image("https://img.icons8.com/color/96/car-service.png", width=70)
st.sidebar.title("Diagnostic Settings")

# 1. Retrieval Mode
retrieval_mode = st.sidebar.radio(
    "Retrieval Engine Mode",
    ["Hybrid Search (Vector + BM25 + RRF)", "Pure Semantic Vector", "Pure Lexical BM25"],
    index=0,
    help="Hybrid combines semantic symptom matching with exact alphanumeric DTC lookup."
)

# 2. Filters
st.sidebar.subheader("Metadata Filters")
category_filter = st.sidebar.selectbox(
    "System Category",
    ["All Categories", "Powertrain", "Chassis", "Network"],
    index=0
)

oem_filter = st.sidebar.selectbox(
    "Vehicle Application",
    ["All Makes (Generic & OEM)", "Ford", "Lincoln", "Generic Only"],
    index=0
)

# 3. Parameters
top_k = st.sidebar.slider("Top Evidence Results (K)", min_value=1, max_value=8, value=3)
use_parent_expansion = st.sidebar.checkbox("Small-to-Big Context Expansion", value=True, help="Injects full parent diagnostic article into context.")

# 4. Ollama Local LLM Configuration
st.sidebar.markdown("---")
st.sidebar.subheader("🦙 Local LLM (Ollama)")

ollama_online = generator.check_ollama_status()
if ollama_online:
    available_models = generator.get_available_models()
    if not available_models:
        available_models = [config.DEFAULT_LLM_MODEL, "llama3.2:1b", "qwen2.5:3b", "mistral"]
    st.sidebar.success("🟢 Ollama Daemon Active")
    selected_model = st.sidebar.selectbox("Active LLM Model", available_models, index=0)
else:
    st.sidebar.warning("⚪ Ollama Offline")
    st.sidebar.caption("Start Ollama (`ollama serve` or open Ollama app) to enable generative synthesis.")
    selected_model = config.DEFAULT_LLM_MODEL

llm_temp = st.sidebar.slider("LLM Temperature", min_value=0.0, max_value=0.7, value=config.TEMPERATURE, step=0.05, help="Lower = strict factual adherence; Higher = conversational flexibility.")

# 5. OEM PDF Manual Uploader
st.sidebar.markdown("---")
st.sidebar.subheader("📄 Upload OEM Service Manual")
uploaded_pdf = st.sidebar.file_uploader("Upload PDF Manual (fitz)", type=["pdf"])
if uploaded_pdf is not None:
    temp_path = config.RAW_DATA_DIR / uploaded_pdf.name
    if not temp_path.exists():
        with open(temp_path, "wb") as f:
            f.write(uploaded_pdf.getbuffer())
        st.sidebar.success(f"Saved {uploaded_pdf.name}. Ready for manual extraction.")

# --- Main Application Header ---
st.markdown('<div class="main-header">🏎️ REV: Engine & Vehicle Diagnostic Intelligence</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">RAG for Engine & Vehicle Diagnostics (ChromaDB + Okapi BM25 + Ollama Llama-3.2)</div>', unsafe_allow_html=True)

# Sample Query Quick Buttons
st.markdown("**Quick Diagnostic Queries:**")
col1, col2, col3, col4 = st.columns(4)
query_input = ""

if col1.button("🔥 P0301 Cylinder 1 Misfire"):
    query_input = "P0301 cylinder 1 misfire engine shaking at idle"
if col2.button("🛑 C0031 Wheel Speed Sensor"):
    query_input = "C0031 left front wheel speed sensor circuit open"
if col3.button("💨 P0171 Lean Fuel Mixture"):
    query_input = "P0171 system too lean bank 1 vacuum leak"
if col4.button("🚀 Negative Test (P9999)"):
    query_input = "What causes diagnostic code P9999 on a warp drive?"

# Main Search Input
user_query = st.text_input(
    "Enter Diagnostic Trouble Code (DTC), vehicle symptoms, or repair inquiry:",
    value=query_input if query_input else "",
    placeholder="e.g. My car displays code P0301 and engine stumbles at idle. What should I check?"
)

# Build search filters dict
search_filters = {}
if category_filter != "All Categories":
    search_filters["system_category"] = category_filter
if oem_filter == "Ford":
    search_filters["oem_make"] = "Ford"
elif oem_filter == "Lincoln":
    search_filters["oem_make"] = "Lincoln"
elif oem_filter == "Generic Only":
    search_filters["is_oem_specific"] = False

if st.button("🔍 Run Diagnostic Analysis", type="primary") or user_query:
    if not user_query.strip():
        st.warning("Please enter a trouble code or vehicle symptom to begin troubleshooting.")
    else:
        with st.spinner("Analyzing diagnostic trouble codes and cross-referencing technical records..."):
            t0 = time.perf_counter()
            filters = search_filters if search_filters else None

            # Execute RAG Pipeline
            response_data = generator.generate_response(
                query=user_query,
                use_parent_context=use_parent_expansion,
                top_k=top_k,
                filters=filters,
                model_name=selected_model,
                temperature=llm_temp
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000

        hits = response_data.get("retrieved_hits", [])
        verification = response_data.get("verification", {})
        evidence_sufficient = verification.get("evidence_sufficient", True)

        # Tabs Layout
        tab_diagnosis, tab_inspector, tab_eval = st.tabs(["📋 Diagnostic Guidance", "🔬 Retrieval Inspector", "📊 Benchmark & Metrics"])

        with tab_diagnosis:
            if verification.get("is_security_violation"):
                st.error("🚨 **Security Alert: Adversarial Prompt Injection / Malicious Request Blocked**")
                st.markdown(response_data["response"])
            elif not evidence_sufficient or not hits:
                st.warning("⚠️ **No valid data found: Insufficient Technical Documentation**")
                st.markdown(response_data["response"])
            else:
                st.markdown(f"**Execution Latency:** `{elapsed_ms:.1f} ms` | **Retrieved Records:** `{len(hits)}`")

                # Status Badges
                badge_html = []
                if response_data.get("ollama_active"):
                    badge_html.append(f'<span class="metric-badge" style="background:#0f3460;color:#00adb5;border:1px solid #00adb5;">🦙 Ollama: {response_data.get("model_name")}</span>')
                else:
                    badge_html.append('<span class="metric-badge" style="background:#222831;color:#aaa;border:1px solid #444;">📋 Deterministic Mode</span>')

                if hits:
                    top_meta = hits[0].get("metadata", {})
                    dtc = top_meta.get("dtc_code")
                    if dtc:
                        badge_html.append(f'<span class="metric-badge badge-code">DTC: {dtc}</span>')
                    diff = top_meta.get("difficulty_level")
                    if diff:
                        c_class = "badge-diy" if "DIY" in diff else "badge-pro"
                        badge_html.append(f'<span class="metric-badge {c_class}">{diff}</span>')

                if verification.get("overall_valid"):
                    badge_html.append('<span class="metric-badge badge-verified">🛡️ 100% Grounded Claim Audit</span>')

                if badge_html:
                    st.markdown("".join(badge_html), unsafe_allow_html=True)

                st.markdown("---")
                st.markdown(response_data["response"])

        with tab_inspector:
            st.subheader("Retrieval Engine Inspection & Ranking Audit")
            if not hits:
                st.info("ℹ️ **No valid data found:** Zero technical records in the knowledge base matched this trouble code or condition.")
            elif not evidence_sufficient:
                st.warning(
                    f"🛡️ **Abstention Guardrail Intercepted This Query**\n\n"
                    f"The candidate records below were returned by raw nearest-neighbor vector/BM25 search, "
                    f"but were **rejected** from being sent to the LLM.\n\n"
                    f"- **Gate Decision:** ❌ Generation Suppressed (Zero Hallucination)\n"
                    f"- **Reason:** `{verification.get('sufficiency_reason', 'Insufficient match')}`"
                )
            else:
                st.caption("Inspect the exact raw evidence chunks and similarity ranks returned by ChromaDB and BM25.")

            for idx, hit in enumerate(hits, 1):
                meta = hit.get("metadata", {})
                score = hit.get("rerank_score") or hit.get("score") or hit.get("rrf_score") or 0.0
                status_badge = " [REJECTED CANDIDATE]" if not evidence_sufficient else ""

                with st.expander(f"Rank {idx}: [{hit['chunk_id']}]{status_badge} — Score: {score:.4f}", expanded=(idx == 1)):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("DTC Trouble Code", meta.get("dtc_code", "N/A"))
                    c2.metric("System Category", meta.get("system_category", "N/A"))
                    c3.metric("Difficulty Level", meta.get("difficulty_level", "N/A"))

                    st.markdown("**Evidence Chunk Text:**")
                    st.code(hit["text"], language="markdown")

                    st.markdown("**Raw Chunk Metadata:**")
                    st.json(meta)

            if response_data.get("context"):
                with st.expander("Constructed LLM Grounding Context"):
                    st.text(response_data["context"])

        with tab_eval:
            st.subheader("Quantitative Evaluation & RAGAS Benchmarks")
            report_file = config.EVALUATION_DATA_DIR / "benchmark_report.md"
            if report_file.exists():
                with open(report_file, "r", encoding="utf-8") as f:
                    st.markdown(f.read())
            else:
                st.info("Run `python evaluation/benchmark.py` to generate the latest evaluation report.")
