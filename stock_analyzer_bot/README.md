# Smolagents Stock Analyzer Bot

This folder hosts a smolagents-based agent that reuses the existing MCP finance tools to run end-to-end technical analysis for a given ticker symbol.

## Prerequisites

- Python 3.10+
- Dependencies from `requirements.txt` (`smolagents`, `mcp`, `yfinance`, etc.)
- A running MCP strategy server (the provided `server/main.py` entry point is used by default)
- Access to a Hugging Face Inference endpoint (set `HF_TOKEN` in your environment or pass `--hf-token`)

The agent relies on the Hugging Face `InferenceClientModel`. You can override the `--model-id` argument if you prefer a different hosted model that supports code-style reasoning.

## Usage

```powershell
# Activate your virtual environment first
python -m stock_analyzer_bot.main AAPL --period 1y --model-id meta-llama/Meta-Llama-3.1-8B-Instruct
```

Key options:

- `--server-script`: Path to the MCP server entry point if you moved it elsewhere.
- `--hf-token`: Explicit Hugging Face API token (defaults to the `HF_TOKEN` environment variable).
- `--max-steps`: Limits smolagents reasoning iterations (default 20).
- `--no-stream`: Disable streaming intermediate reasoning from the agent.
- `--output`: Save the final markdown report to a file.

The agent prompt enforces calling all five MCP strategies that `stock_analyzer.py` relied on:

1. `analyze_bollinger_zscore_performance`
2. `analyze_bollinger_fibonacci_performance`
3. `analyze_macd_donchian_performance`
4. `analyze_connors_zscore_performance`
5. `analyze_dual_ma_strategy`

Each MCP response is fed back to the LLM, which composes a concise markdown report summarizing every strategy, the consensus view, risk metrics, and a final recommendation.

## FastAPI Backend

Expose the agent (plus the comprehensive report and unified market scanner tools) via FastAPI:

```powershell
uvicorn stock_analyzer_bot.api:app --reload --port 8000
```

Endpoints:

- `POST /analyze` &mdash; runs the multi-strategy smolagents workflow.
- `POST /report` &mdash; executes `generate_comprehensive_analysis_report` through MCP.
- `POST /scanner` &mdash; runs the unified market scanner for a basket of tickers.

The same environment variables as the CLI (e.g., `HF_TOKEN`, `OPENAI_API_KEY`) control authentication and defaults. See the Pydantic models in `stock_analyzer_bot/api.py` for payload details.

## Streamlit Frontend

A lightweight Streamlit UI is available at the repo root (`streamlit_app.py`). It offers three actions: full analysis, comprehensive report, and multi-symbol scanner.

```powershell
streamlit run streamlit_app.py
```

Set the API base URL in the sidebar (defaults to `http://localhost:8000`). Each run is added to a session history for quick comparison.

## Troubleshooting

- If you see `MCP server not found`, ensure the repo was not moved and the default `server/main.py` exists, or pass `--server-script` with the new path.
- When calls hang, confirm that `python` can launch the MCP server and that dependencies inside `server/` are installed.
- For authentication errors, double-check that `HF_TOKEN` has model access or use a different model ID/host supported by smolagents.
