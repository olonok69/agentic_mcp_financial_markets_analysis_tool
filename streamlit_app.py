"""Streamlit UI for interacting with the MCP Stock Analyzer FastAPI backend."""
from __future__ import annotations

import os
from typing import Any, Dict

import requests
import streamlit as st

API_BASE_URL = os.getenv("STOCK_ANALYZER_API_URL", "http://localhost:8000")
DEFAULT_PERIOD = os.getenv("DEFAULT_ANALYSIS_PERIOD", "1y")
DEFAULT_SCANNER_SYMBOLS = os.getenv("DEFAULT_SCANNER_SYMBOLS", "AAPL,MSFT,TSLA,AMZN")
DEFAULT_MODEL_ID = os.getenv("SMOLAGENT_MODEL_ID", "meta-llama/Meta-Llama-3.1-8B-Instruct")
DEFAULT_MODEL_PROVIDER = os.getenv("SMOLAGENT_MODEL_PROVIDER", "auto").lower()
DEFAULT_MAX_STEPS = int(os.getenv("SMOLAGENT_MAX_STEPS", "20"))

st.set_page_config(page_title="MCP Stock Analyzer", layout="wide")
st.title("📊 MCP Stock Analyzer Bot")

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


def apply_model_settings(payload: Dict[str, Any]) -> Dict[str, Any]:
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
    url = f"{st.session_state.api_url.rstrip('/')}{endpoint}"
    response = requests.post(url, json=payload, timeout=300)
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        detail = response.text
        raise RuntimeError(f"{exc.response.status_code} error from API: {detail}") from exc
    data = response.json()
    return data.get("report", "No report returned.")


with st.sidebar:
    st.header("Settings")
    st.session_state.api_url = st.text_input("API URL", value=API_BASE_URL)
    st.markdown(
        "Start the backend with `uvicorn stock_analyzer_bot.api:app --reload` and point the UI here."
    )
    st.subheader("Model Settings")
    st.session_state.model_id = st.text_input("Model ID", value=st.session_state.model_id)
    provider_options = ["auto", "inference", "litellm"]
    try:
        provider_index = provider_options.index(st.session_state.model_provider)
    except ValueError:
        provider_index = 0
    st.session_state.model_provider = st.selectbox(
        "Model Provider",
        provider_options,
        index=provider_index,
    )
    st.session_state.hf_token = st.text_input(
        "HF Token",
        value=st.session_state.hf_token,
        type="password",
    )
    st.session_state.openai_api_key = st.text_input(
        "OpenAI API Key",
        value=st.session_state.openai_api_key,
        type="password",
    )
    st.session_state.openai_base_url = st.text_input(
        "OpenAI Base URL",
        value=st.session_state.openai_base_url,
    )
    st.session_state.max_steps = st.number_input(
        "Max Steps",
        min_value=1,
        max_value=100,
        value=st.session_state.max_steps,
    )

mode = st.radio(
    "Choose an action",
    (
        "Full Strategy Analysis",
        "Comprehensive Performance Report",
        "Unified Market Scanner",
        "Fundamental Analysis",
    ),
)

if mode == "Full Strategy Analysis":
    with st.form("analysis-form"):
        symbol = st.text_input("Ticker Symbol", value="AAPL")
        period = st.text_input("Historical Period", value=DEFAULT_PERIOD)
        submitted = st.form_submit_button("Run Analysis")
        if submitted:
            with st.spinner("Running smolagents analysis..."):
                try:
                    payload = apply_model_settings(
                        {
                            "symbol": symbol,
                            "period": period,
                        }
                    )
                    report = call_backend("/analyze", payload)
                    st.session_state.messages.append((f"Analyze {symbol}", report))
                    st.success("Analysis completed")
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Failed to run analysis: {exc}")

elif mode == "Comprehensive Performance Report":
    with st.form("report-form"):
        symbol = st.text_input("Ticker Symbol", value="MSFT")
        period = st.text_input("Historical Period", value=DEFAULT_PERIOD)
        submitted = st.form_submit_button("Generate Report")
        if submitted:
            with st.spinner("Requesting comprehensive report..."):
                try:
                    report = call_backend(
                        "/report",
                        {
                            "symbol": symbol,
                            "period": period,
                        },
                    )
                    st.session_state.messages.append((f"Comprehensive report for {symbol}", report))
                    st.success("Report ready")
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Failed to generate report: {exc}")
elif mode == "Unified Market Scanner":
    with st.form("scanner-form"):
        symbols = st.text_input("Symbols (comma separated)", value=DEFAULT_SCANNER_SYMBOLS)
        ma_type = st.selectbox("MA Type", ("SMA", "EMA"))
        col1, col2 = st.columns(2)
        with col1:
            short_period = st.number_input("Short Period", min_value=5, max_value=200, value=50)
        with col2:
            long_period = st.number_input("Long Period", min_value=10, max_value=400, value=200)
        submitted = st.form_submit_button("Run Scanner")
        if submitted:
            with st.spinner("Scanning market opportunities..."):
                try:
                    report = call_backend(
                        "/scanner",
                        {
                            "symbols": symbols,
                            "ma_type": ma_type,
                            "short_period": short_period,
                            "long_period": long_period,
                        },
                    )
                    st.session_state.messages.append(("Market scanner", report))
                    st.success("Scanner completed")
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Failed to run scanner: {exc}")
elif mode == "Fundamental Analysis":
    with st.form("fundamental-form"):
        symbol = st.text_input("Ticker Symbol", value="MSFT")
        period = st.text_input("Statement Period", value="3y")
        submitted = st.form_submit_button("Run Fundamental Analysis")
        if submitted:
            with st.spinner("Gathering financial statements and ratios..."):
                try:
                    report = call_backend(
                        "/fundamental",
                        {
                            "symbol": symbol,
                            "period": period,
                        },
                    )
                    st.session_state.messages.append((f"Fundamental analysis for {symbol}", report))
                    st.success("Fundamental report ready")
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Failed to generate fundamental analysis: {exc}")

st.subheader("Conversation History")
if not st.session_state.messages:
    st.info("Run an action to see responses here.")
else:
    for idx, (title, content) in enumerate(reversed(st.session_state.messages), 1):
        with st.expander(f"{idx}. {title}", expanded=idx == 1):
            st.markdown(content)
