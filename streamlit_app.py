"""Streamlit UI for interacting with the MCP Stock Analyzer FastAPI backend."""
from __future__ import annotations

import os
from typing import Any, Dict

import requests
import streamlit as st

API_BASE_URL = os.getenv("STOCK_ANALYZER_API_URL", "http://localhost:8000")
DEFAULT_PERIOD = os.getenv("DEFAULT_ANALYSIS_PERIOD", "1y")
DEFAULT_SCANNER_SYMBOLS = os.getenv("DEFAULT_SCANNER_SYMBOLS", "AAPL,MSFT,TSLA,AMZN")
DEFAULT_MODEL_ID = os.getenv("SMOLAGENT_MODEL_ID", "gpt-4o-mini")
DEFAULT_MODEL_PROVIDER = os.getenv("SMOLAGENT_MODEL_PROVIDER", "litellm").lower()
DEFAULT_MAX_STEPS = int(os.getenv("SMOLAGENT_MAX_STEPS", "20"))

st.set_page_config(page_title="MCP Stock Analyzer", layout="wide")
st.title("📊 MCP Stock Analyzer Bot")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "model_id" not in st.session_state:
    st.session_state.model_id = DEFAULT_MODEL_ID
if "model_provider" not in st.session_state:
    st.session_state.model_provider = DEFAULT_MODEL_PROVIDER
if "hf_token" not in st.session_state:
    st.session_state.hf_token = os.getenv("HF_TOKEN", "")
if "openai_api_key" not in st.session_state:
    st.session_state.openai_api_key = os.getenv("OPENAI_API_KEY", "")
if "openai_base_url" not in st.session_state:
    st.session_state.openai_base_url = os.getenv("OPENAI_BASE_URL", "")
if "max_steps" not in st.session_state:
    st.session_state.max_steps = DEFAULT_MAX_STEPS
if "api_url" not in st.session_state:
    st.session_state.api_url = API_BASE_URL


def apply_model_settings(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Apply model settings to the API payload (only for Full Strategy Analysis)."""
    if st.session_state.model_id:
        payload["model_id"] = st.session_state.model_id
    if st.session_state.model_provider:
        payload["model_provider"] = st.session_state.model_provider
    if st.session_state.hf_token:
        payload["hf_token"] = st.session_state.hf_token
    if st.session_state.openai_api_key:
        payload["openai_api_key"] = st.session_state.openai_api_key
    if st.session_state.openai_base_url:
        payload["openai_base_url"] = st.session_state.openai_base_url
    if st.session_state.max_steps:
        payload["max_steps"] = st.session_state.max_steps
    return payload


def call_backend(endpoint: str, payload: Dict[str, Any]) -> str:
    """Call the FastAPI backend and return the report."""
    url = f"{st.session_state.api_url.rstrip('/')}{endpoint}"
    response = requests.post(url, json=payload, timeout=300)
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        detail = response.text
        raise RuntimeError(f"{exc.response.status_code} error from API: {detail}") from exc
    data = response.json()
    return data.get("report", "No report returned.")


# Simplified sidebar - only API URL
with st.sidebar:
    st.header("⚙️ Connection")
    st.session_state.api_url = st.text_input("API URL", value=st.session_state.api_url)
    st.caption("Backend: `uvicorn stock_analyzer_bot.api:app --reload`")
    
    st.divider()
    
    # Quick help
    st.markdown("""
    **Quick Start:**
    1. Start the FastAPI backend
    2. Select an analysis type
    3. Enter a ticker symbol
    4. Click the action button
    """)


# Main content area
mode = st.radio(
    "Choose an action",
    (
        "Full Strategy Analysis",
        "Comprehensive Performance Report",
        "Unified Market Scanner",
        "Fundamental Analysis",
    ),
    horizontal=True,
)

st.divider()

# Full Strategy Analysis
if mode == "Full Strategy Analysis":
    st.subheader("🤖 Full Strategy Analysis (AI-Interpreted)")
    st.caption("Uses an AI agent to execute 4 strategy tools and synthesize results.")
    
    with st.form("analysis-form"):
        col1, col2 = st.columns([2, 1])
        with col1:
            symbol = st.text_input("Ticker Symbol", value="AAPL")
        with col2:
            period = st.text_input("Period", value=DEFAULT_PERIOD)
        
        submitted = st.form_submit_button("🚀 Run Analysis", use_container_width=True)
        
        if submitted:
            with st.spinner("Running AI-powered analysis..."):
                try:
                    payload = apply_model_settings({"symbol": symbol, "period": period})
                    report = call_backend("/analyze", payload)
                    st.session_state.messages.append((f"🤖 Full Analysis: {symbol}", report))
                    st.success("Analysis completed!")
                except Exception as exc:
                    st.error(f"Failed to run analysis: {exc}")
    
    # Advanced settings in expander (only shown for Full Strategy Analysis)
    with st.expander("⚙️ Advanced Model Settings", expanded=False):
        st.caption("Configure the AI model used for Full Strategy Analysis")
        
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.model_id = st.text_input(
                "Model ID", 
                value=st.session_state.model_id,
                help="e.g., gpt-4o-mini, gpt-4o, meta-llama/Meta-Llama-3.1-8B-Instruct"
            )
            provider_options = ["litellm", "inference", "auto"]
            try:
                provider_index = provider_options.index(st.session_state.model_provider)
            except ValueError:
                provider_index = 0
            st.session_state.model_provider = st.selectbox(
                "Provider",
                provider_options,
                index=provider_index,
                help="litellm = OpenAI, inference = HuggingFace"
            )
        with col2:
            st.session_state.openai_api_key = st.text_input(
                "OpenAI API Key",
                value=st.session_state.openai_api_key,
                type="password",
                help="Required for litellm provider"
            )
            st.session_state.hf_token = st.text_input(
                "HuggingFace Token",
                value=st.session_state.hf_token,
                type="password",
                help="Required for inference provider"
            )
        
        col3, col4 = st.columns(2)
        with col3:
            st.session_state.openai_base_url = st.text_input(
                "OpenAI Base URL (optional)",
                value=st.session_state.openai_base_url,
                help="For custom OpenAI-compatible endpoints"
            )
        with col4:
            st.session_state.max_steps = st.number_input(
                "Max Steps",
                min_value=1,
                max_value=100,
                value=st.session_state.max_steps,
                help="Maximum reasoning steps for the agent"
            )

# Comprehensive Performance Report
elif mode == "Comprehensive Performance Report":
    st.subheader("📊 Comprehensive Performance Report (Deterministic)")
    st.caption("Direct strategy execution with fixed parameters - no AI interpretation.")
    
    with st.form("report-form"):
        col1, col2 = st.columns([2, 1])
        with col1:
            symbol = st.text_input("Ticker Symbol", value="MSFT")
        with col2:
            period = st.text_input("Period", value=DEFAULT_PERIOD)
        
        submitted = st.form_submit_button("📈 Generate Report", use_container_width=True)
        
        if submitted:
            with st.spinner("Generating comprehensive report..."):
                try:
                    report = call_backend("/report", {"symbol": symbol, "period": period})
                    st.session_state.messages.append((f"📊 Comprehensive Report: {symbol}", report))
                    st.success("Report ready!")
                except Exception as exc:
                    st.error(f"Failed to generate report: {exc}")

# Unified Market Scanner
elif mode == "Unified Market Scanner":
    st.subheader("🔍 Unified Market Scanner")
    st.caption("Scan multiple stocks and rank by technical signals.")
    
    with st.form("scanner-form"):
        symbols = st.text_input("Symbols (comma separated)", value=DEFAULT_SCANNER_SYMBOLS)
        
        col1, col2 = st.columns(2)
        with col1:
            period = st.selectbox("Period", ("1y", "6mo", "3mo", "1mo", "2y", "5y"), index=0)
        with col2:
            output_format = st.selectbox("Output Format", ("detailed", "summary", "executive"), index=0)
        
        submitted = st.form_submit_button("🔍 Run Scanner", use_container_width=True)
        
        if submitted:
            with st.spinner("Scanning market opportunities..."):
                try:
                    report = call_backend(
                        "/scanner",
                        {
                            "symbols": symbols,
                            "period": period,
                            "output_format": output_format,
                        },
                    )
                    st.session_state.messages.append(("🔍 Market Scanner", report))
                    st.success("Scanner completed!")
                except Exception as exc:
                    st.error(f"Failed to run scanner: {exc}")

# Fundamental Analysis
elif mode == "Fundamental Analysis":
    st.subheader("💰 Fundamental Analysis")
    st.caption("Financial statements, ratios, and company fundamentals.")
    
    with st.form("fundamental-form"):
        col1, col2 = st.columns([2, 1])
        with col1:
            symbol = st.text_input("Ticker Symbol", value="MSFT")
        with col2:
            period = st.text_input("Statement Period", value="3y")
        
        submitted = st.form_submit_button("💰 Run Analysis", use_container_width=True)
        
        if submitted:
            with st.spinner("Gathering financial statements and ratios..."):
                try:
                    report = call_backend("/fundamental", {"symbol": symbol, "period": period})
                    st.session_state.messages.append((f"💰 Fundamental Analysis: {symbol}", report))
                    st.success("Fundamental report ready!")
                except Exception as exc:
                    st.error(f"Failed to generate fundamental analysis: {exc}")

st.divider()

# Conversation History
st.subheader("📜 Analysis History")
if not st.session_state.messages:
    st.info("Run an analysis to see results here.")
else:
    # Clear history button
    if st.button("🗑️ Clear History"):
        st.session_state.messages = []
        st.rerun()
    
    for idx, (title, content) in enumerate(reversed(st.session_state.messages), 1):
        with st.expander(f"{idx}. {title}", expanded=(idx == 1)):
            st.markdown(content)