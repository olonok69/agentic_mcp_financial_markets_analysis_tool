"""
Streamlit UI for the LLM-powered MCP Stock Analyzer.

NEW: Agent Type Selection
- ToolCallingAgent (original): JSON-based tool calls
- CodeAgent (new): Python code-based, efficient loops

All analysis features use AI to interpret data and generate professional reports:
- Technical Analysis: 4 trading strategies on a single stock
- Market Scanner: Compare multiple stocks, rank opportunities  
- Fundamental Analysis: Financial statements interpretation
- Multi-Sector Analysis: Cross-sector comparison
- Combined Analysis: Technical + Fundamental together
"""
from __future__ import annotations

import os
from typing import Any, Dict

import requests
import streamlit as st

# Configuration
API_BASE_URL = os.getenv("STOCK_ANALYZER_API_URL", "http://localhost:8000")
DEFAULT_PERIOD = os.getenv("DEFAULT_ANALYSIS_PERIOD", "1y")
DEFAULT_SCANNER_SYMBOLS = os.getenv("DEFAULT_SCANNER_SYMBOLS", "AAPL,MSFT,GOOGL,AMZN")
DEFAULT_MODEL_ID = os.getenv("SMOLAGENT_MODEL_ID", "gpt-4o")
DEFAULT_MODEL_PROVIDER = os.getenv("SMOLAGENT_MODEL_PROVIDER", "litellm")
DEFAULT_AGENT_TYPE = os.getenv("SMOLAGENT_AGENT_TYPE", "tool_calling")

# Default sectors for multi-sector analysis
DEFAULT_SECTORS = {
    "Banking": "JPM,BAC,WFC,C,GS,MS,USB,PNC,TFC,COF",
    "Technology": "AAPL,MSFT,GOOGL,META,NVDA,AMD,CRM,ORCL,ADBE,INTC",
    "Clean Energy": "TSLA,NIO,RIVN,LCID,PLUG,SEDG,NEE,ICLN,ENPH",
}

# Page configuration
st.set_page_config(
    page_title="MCP Stock Analyzer",
    page_icon="📊",
    layout="wide",
)

# Custom CSS for better styling
st.markdown("""
<style>
    .stAlert {
        margin-top: 1rem;
    }
    .report-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .agent-badge {
        display: inline-block;
        padding: 0.2rem 0.5rem;
        border-radius: 0.3rem;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .agent-tool-calling {
        background-color: #e3f2fd;
        color: #1565c0;
    }
    .agent-code-agent {
        background-color: #fff3e0;
        color: #ef6c00;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# Session State Initialization
# =============================================================================

if "messages" not in st.session_state:
    st.session_state.messages = []
if "api_url" not in st.session_state:
    st.session_state.api_url = API_BASE_URL
if "model_id" not in st.session_state:
    st.session_state.model_id = DEFAULT_MODEL_ID
if "model_provider" not in st.session_state:
    st.session_state.model_provider = DEFAULT_MODEL_PROVIDER
if "openai_api_key" not in st.session_state:
    st.session_state.openai_api_key = os.getenv("OPENAI_API_KEY", "")
# NEW: Agent type state
if "agent_type" not in st.session_state:
    st.session_state.agent_type = DEFAULT_AGENT_TYPE
if "executor_type" not in st.session_state:
    st.session_state.executor_type = "local"


# =============================================================================
# Helper Functions
# =============================================================================

def call_api(endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Call the FastAPI backend and return the response."""
    url = f"{st.session_state.api_url.rstrip('/')}{endpoint}"
    
    # Add model settings if configured
    if st.session_state.model_id:
        payload["model_id"] = st.session_state.model_id
    if st.session_state.model_provider:
        payload["model_provider"] = st.session_state.model_provider
    if st.session_state.openai_api_key:
        payload["openai_api_key"] = st.session_state.openai_api_key
    
    # NEW: Add agent type settings
    payload["agent_type"] = st.session_state.agent_type
    if st.session_state.agent_type == "code_agent":
        payload["executor_type"] = st.session_state.executor_type
    
    # Longer timeout for multi-sector analysis (20 minutes)
    timeout = 1200 if "/multisector" in endpoint else 600
    
    try:
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        raise RuntimeError("Request timed out. Try with fewer stocks or check the server.")
    except requests.exceptions.ConnectionError:
        raise RuntimeError(f"Cannot connect to API at {url}. Is the server running?")
    except requests.HTTPError as exc:
        detail = response.text if response else str(exc)
        raise RuntimeError(f"API Error ({response.status_code}): {detail}")


def add_to_history(title: str, report: str, analysis_type: str, duration: float = 0, agent_type: str = ""):
    """Add analysis result to session history."""
    st.session_state.messages.append({
        "title": title,
        "report": report,
        "type": analysis_type,
        "duration": duration,
        "agent_type": agent_type,
    })


def get_agent_badge(agent_type: str) -> str:
    """Return HTML badge for agent type."""
    if agent_type == "code_agent":
        return '<span class="agent-badge agent-code-agent">🐍 CodeAgent</span>'
    else:
        return '<span class="agent-badge agent-tool-calling">🔧 ToolCalling</span>'


# =============================================================================
# Main App
# =============================================================================

st.title("📊 MCP Stock Analyzer")
st.markdown("*AI-powered financial analysis using smolagents + MCP tools*")

# Sidebar - Settings
with st.sidebar:
    st.header("⚙️ Settings")
    
    st.session_state.api_url = st.text_input(
        "API URL",
        value=st.session_state.api_url,
        help="FastAPI backend URL",
    )
    
    # NEW: Agent Type Selection (prominent position)
    st.subheader("🤖 Agent Type")
    
    agent_options = {
        "tool_calling": "🔧 ToolCallingAgent (Original)",
        "code_agent": "🐍 CodeAgent (New - Faster)",
    }
    
    selected_agent = st.radio(
        "Select Agent Type",
        options=list(agent_options.keys()),
        format_func=lambda x: agent_options[x],
        index=0 if st.session_state.agent_type == "tool_calling" else 1,
        help="CodeAgent writes Python code to call tools - more efficient for multi-stock analysis",
    )
    st.session_state.agent_type = selected_agent
    
    # Show agent comparison
    if selected_agent == "tool_calling":
        st.info("""
        **ToolCallingAgent**
        - JSON-based tool calls
        - One tool call per LLM round
        - More LLM calls needed
        - ✅ Safe (no code execution)
        """)
    else:
        st.success("""
        **CodeAgent**
        - Python code-based
        - Can use loops & variables
        - Fewer LLM calls needed
        - ⚡ Faster for multi-stock
        """)
        
        # Executor type for CodeAgent
        st.session_state.executor_type = st.selectbox(
            "Code Executor",
            ["local", "e2b", "docker"],
            index=0,
            help="local=development, e2b/docker=production (sandboxed)",
        )
        
        if st.session_state.executor_type == "local":
            st.warning("⚠️ Local executor runs code in your environment. Use e2b/docker for production.")
    
    st.divider()
    
    with st.expander("🧠 Model Settings", expanded=False):
        st.session_state.model_id = st.text_input(
            "Model ID",
            value=st.session_state.model_id,
            help="e.g., gpt-4o-mini, gpt-4o, gpt-4-turbo",
        )
        
        st.session_state.model_provider = st.selectbox(
            "Provider",
            ["litellm", "inference"],
            index=0 if st.session_state.model_provider == "litellm" else 1,
            help="litellm = OpenAI, inference = HuggingFace",
        )
        
        st.session_state.openai_api_key = st.text_input(
            "OpenAI API Key",
            value=st.session_state.openai_api_key,
            type="password",
            help="Override the server's API key",
        )
    
    st.divider()
    
    st.markdown("""
    ### How It Works
    
    All analysis uses **AI** to:
    1. 🔧 Call MCP finance tools
    2. 📊 Get raw financial data
    3. 🤖 Interpret & synthesize results
    4. 📝 Generate professional reports
    
    **Requirements:**
    - FastAPI backend running
    - OpenAI API key configured
    """)
    
    # Show current agent type prominently
    st.divider()
    st.markdown(f"**Current Agent:** {agent_options[st.session_state.agent_type]}")

# Main content - Tabs for different analysis types
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Technical Analysis",
    "🔍 Market Scanner", 
    "💰 Fundamental Analysis",
    "🌐 Multi-Sector Analysis",
    "🔄 Combined Analysis",
])

# =============================================================================
# Tab 1: Technical Analysis
# =============================================================================

with tab1:
    st.subheader("📈 Technical Analysis")
    st.markdown("""
    Analyze a single stock using **4 trading strategies**:
    - Bollinger Bands & Fibonacci Retracement
    - MACD-Donchian Combined
    - Connors RSI & Z-Score
    - Dual Moving Average (50/200 EMA)
    
    The AI will call each strategy tool, extract metrics, and synthesize a comprehensive report.
    """)
    
    # Show agent type indicator
    st.markdown(f"Using: {get_agent_badge(st.session_state.agent_type)}", unsafe_allow_html=True)
    
    with st.form("technical-form"):
        col1, col2 = st.columns([2, 1])
        with col1:
            tech_symbol = st.text_input(
                "Ticker Symbol",
                value="AAPL",
                placeholder="e.g., AAPL, MSFT, TSLA",
            )
        with col2:
            tech_period = st.selectbox(
                "Period",
                ["1y", "6mo", "3mo", "2y", "5y"],
                index=0,
            )
        
        tech_submit = st.form_submit_button(
            "🚀 Run Technical Analysis",
            use_container_width=True,
        )
        
        if tech_submit:
            if not tech_symbol.strip():
                st.error("Please enter a ticker symbol")
            else:
                agent_label = "CodeAgent" if st.session_state.agent_type == "code_agent" else "ToolCallingAgent"
                with st.spinner(f"🤖 {agent_label} is analyzing {tech_symbol.upper()}... This may take 30-60 seconds."):
                    try:
                        response = call_api("/technical", {
                            "symbol": tech_symbol,
                            "period": tech_period,
                        })
                        
                        report = response.get("report", "No report generated")
                        duration = response.get("duration_seconds", 0)
                        used_agent = response.get("agent_type", st.session_state.agent_type)
                        
                        add_to_history(
                            f"📈 Technical: {tech_symbol.upper()}",
                            report,
                            "technical",
                            duration,
                            used_agent,
                        )
                        
                        st.success(f"✅ Analysis completed in {duration:.1f}s using {used_agent}")
                        st.markdown(report)
                        
                    except Exception as exc:
                        st.error(f"❌ Analysis failed: {exc}")

# =============================================================================
# Tab 2: Market Scanner
# =============================================================================

with tab2:
    st.subheader("🔍 Market Scanner")
    st.markdown("""
    Compare **multiple stocks** and identify the best opportunities.
    
    The AI will:
    - Call 4 strategy tools for **each stock**
    - Rank stocks by technical performance
    - Identify BUY/HOLD/AVOID recommendations
    - Suggest portfolio allocation
    """)
    
    # Show agent recommendation
    st.markdown(f"Using: {get_agent_badge(st.session_state.agent_type)}", unsafe_allow_html=True)
    
    if st.session_state.agent_type == "tool_calling":
        st.info("💡 **Tip:** Switch to CodeAgent in sidebar for faster multi-stock analysis!")
    else:
        st.success("⚡ CodeAgent will use efficient loops for faster scanning!")
    
    with st.form("scanner-form"):
        scanner_symbols = st.text_input(
            "Ticker Symbols (comma-separated)",
            value=DEFAULT_SCANNER_SYMBOLS,
            placeholder="e.g., AAPL,MSFT,GOOGL,AMZN",
        )
        
        col1, col2 = st.columns(2)
        with col1:
            scanner_period = st.selectbox(
                "Period",
                ["1y", "6mo", "3mo", "2y"],
                index=0,
                key="scanner_period",
            )
        with col2:
            # Count symbols for user info
            symbol_count = len([s for s in scanner_symbols.split(",") if s.strip()])
            st.metric("Stocks to Analyze", symbol_count)
        
        scanner_submit = st.form_submit_button(
            "🔍 Run Market Scanner",
            use_container_width=True,
        )
        
        if scanner_submit:
            if not scanner_symbols.strip():
                st.error("Please enter at least one ticker symbol")
            else:
                agent_label = "CodeAgent" if st.session_state.agent_type == "code_agent" else "ToolCallingAgent"
                with st.spinner(f"🤖 {agent_label} is scanning {symbol_count} stocks... This may take several minutes."):
                    try:
                        response = call_api("/scanner", {
                            "symbols": scanner_symbols,
                            "period": scanner_period,
                        })
                        
                        report = response.get("report", "No report generated")
                        duration = response.get("duration_seconds", 0)
                        used_agent = response.get("agent_type", st.session_state.agent_type)
                        
                        add_to_history(
                            f"🔍 Scanner: {scanner_symbols.upper()[:30]}...",
                            report,
                            "scanner",
                            duration,
                            used_agent,
                        )
                        
                        st.success(f"✅ Scanner completed in {duration:.1f}s using {used_agent}")
                        st.markdown(report)
                        
                    except Exception as exc:
                        st.error(f"❌ Scanner failed: {exc}")

# =============================================================================
# Tab 3: Fundamental Analysis
# =============================================================================

with tab3:
    st.subheader("💰 Fundamental Analysis")
    st.markdown("""
    Analyze a company's **financial statements** and generate an investment thesis.
    
    The AI will interpret:
    - Income Statement (Revenue, Net Income, Margins)
    - Balance Sheet (Assets, Liabilities, Equity)
    - Cash Flow (Operating, Investing, Financing)
    
    And provide: Strengths, Risks, Valuation perspective, and a BUY/HOLD/SELL recommendation.
    """)
    
    st.markdown(f"Using: {get_agent_badge(st.session_state.agent_type)}", unsafe_allow_html=True)
    
    with st.form("fundamental-form"):
        col1, col2 = st.columns([2, 1])
        with col1:
            fund_symbol = st.text_input(
                "Ticker Symbol",
                value="AAPL",
                placeholder="e.g., AAPL, MSFT, GOOGL",
                key="fund_symbol",
            )
        with col2:
            fund_period = st.selectbox(
                "Period",
                ["3y", "5y", "1y"],
                index=0,
                key="fund_period",
                help="Years of financial data to analyze",
            )
        
        fund_submit = st.form_submit_button(
            "💰 Run Fundamental Analysis",
            use_container_width=True,
        )
        
        if fund_submit:
            if not fund_symbol.strip():
                st.error("Please enter a ticker symbol")
            else:
                agent_label = "CodeAgent" if st.session_state.agent_type == "code_agent" else "ToolCallingAgent"
                with st.spinner(f"🤖 {agent_label} is analyzing {fund_symbol.upper()} financials... This may take 30-45 seconds."):
                    try:
                        response = call_api("/fundamental", {
                            "symbol": fund_symbol,
                            "period": fund_period,
                        })
                        
                        report = response.get("report", "No report generated")
                        duration = response.get("duration_seconds", 0)
                        used_agent = response.get("agent_type", st.session_state.agent_type)
                        
                        add_to_history(
                            f"💰 Fundamental: {fund_symbol.upper()}",
                            report,
                            "fundamental",
                            duration,
                            used_agent,
                        )
                        
                        st.success(f"✅ Fundamental analysis completed in {duration:.1f}s using {used_agent}")
                        st.markdown(report)
                        
                    except Exception as exc:
                        st.error(f"❌ Analysis failed: {exc}")

# =============================================================================
# Tab 4: Multi-Sector Analysis
# =============================================================================

with tab4:
    st.subheader("🌐 Multi-Sector Analysis")
    st.markdown("""
    Compare stocks **across multiple sectors** to find the best opportunities.
    
    The AI will:
    - Analyze ALL stocks in EACH sector
    - Compare performance across sectors
    - Identify top picks from the entire universe
    - Suggest portfolio allocation by sector
    """)
    
    # Show agent recommendation (strong recommendation for CodeAgent)
    st.markdown(f"Using: {get_agent_badge(st.session_state.agent_type)}", unsafe_allow_html=True)
    
    if st.session_state.agent_type == "tool_calling":
        st.warning("⚠️ **Strongly recommend CodeAgent** for multi-sector! Switch in sidebar for 3-5x faster analysis.")
    else:
        st.success("⚡ CodeAgent will use nested loops for efficient multi-sector analysis!")
    
    # Initialize sector configuration in session state
    if "sector_configs" not in st.session_state:
        st.session_state.sector_configs = [
            {"name": name, "symbols": symbols}
            for name, symbols in DEFAULT_SECTORS.items()
        ]
    
    st.markdown("### Configure Sectors")
    st.caption("Add, edit, or remove sectors. Each sector should have a name and comma-separated symbols.")
    
    # Display current sectors with editable fields
    sectors_to_remove = []
    
    for i, sector in enumerate(st.session_state.sector_configs):
        col1, col2, col3 = st.columns([2, 6, 1])
        with col1:
            new_name = st.text_input(
                "Sector Name",
                value=sector["name"],
                key=f"sector_name_{i}",
                label_visibility="collapsed",
                placeholder="Sector name",
            )
            st.session_state.sector_configs[i]["name"] = new_name
        with col2:
            new_symbols = st.text_input(
                "Symbols",
                value=sector["symbols"],
                key=f"sector_symbols_{i}",
                label_visibility="collapsed",
                placeholder="Comma-separated symbols",
            )
            st.session_state.sector_configs[i]["symbols"] = new_symbols
        with col3:
            if st.button("🗑️", key=f"remove_sector_{i}", help="Remove this sector"):
                sectors_to_remove.append(i)
    
    # Remove marked sectors
    for i in sorted(sectors_to_remove, reverse=True):
        st.session_state.sector_configs.pop(i)
    
    # Add new sector button
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("➕ Add Sector"):
            st.session_state.sector_configs.append({
                "name": f"Sector {len(st.session_state.sector_configs) + 1}",
                "symbols": "",
            })
            st.rerun()
    with col2:
        if st.button("🔄 Reset to Defaults"):
            st.session_state.sector_configs = [
                {"name": name, "symbols": symbols}
                for name, symbols in DEFAULT_SECTORS.items()
            ]
            st.rerun()
    
    st.divider()
    
    # Period selection and run button
    col1, col2 = st.columns([1, 2])
    with col1:
        multi_period = st.selectbox(
            "Period",
            ["1y", "6mo", "2y", "3mo"],
            index=0,
            key="multi_period",
        )
    with col2:
        # Calculate total stocks
        total_stocks = sum(
            len([s for s in sector["symbols"].split(",") if s.strip()])
            for sector in st.session_state.sector_configs
            if sector["symbols"].strip()
        )
        st.metric(
            "Total Stocks to Analyze",
            total_stocks,
            help="Each stock requires 4 tool calls",
        )
    
    # Validate and run
    valid_sectors = [
        s for s in st.session_state.sector_configs
        if s["name"].strip() and s["symbols"].strip()
    ]
    
    if st.button(
        "🌐 Run Multi-Sector Analysis",
        use_container_width=True,
        disabled=len(valid_sectors) == 0,
    ):
        if len(valid_sectors) == 0:
            st.error("Please configure at least one sector with symbols")
        else:
            # Build request payload
            sectors_payload = [
                {"name": s["name"], "symbols": s["symbols"]}
                for s in valid_sectors
            ]
            
            sector_names = ", ".join(s["name"] for s in valid_sectors)
            agent_label = "CodeAgent" if st.session_state.agent_type == "code_agent" else "ToolCallingAgent"
            
            with st.spinner(f"🤖 {agent_label} is analyzing {len(valid_sectors)} sectors ({total_stocks} stocks)... This may take 5-15 minutes."):
                try:
                    response = call_api("/multisector", {
                        "sectors": sectors_payload,
                        "period": multi_period,
                    })
                    
                    report = response.get("report", "No report generated")
                    duration = response.get("duration_seconds", 0)
                    used_agent = response.get("agent_type", st.session_state.agent_type)
                    
                    add_to_history(
                        f"🌐 Multi-Sector: {sector_names}",
                        report,
                        "multi_sector",
                        duration,
                        used_agent,
                    )
                    
                    st.success(f"✅ Multi-sector analysis completed in {duration:.1f}s using {used_agent}")
                    st.markdown(report)
                    
                except Exception as exc:
                    st.error(f"❌ Analysis failed: {exc}")

# =============================================================================
# Tab 5: Combined Technical + Fundamental Analysis
# =============================================================================

with tab5:
    st.subheader("🔄 Combined Technical + Fundamental Analysis")
    st.markdown("""
    The most comprehensive analysis combining **both approaches**:
    
    **Fundamental Analysis** tells you **"WHAT to buy"**
    - Company financial health and profitability
    - Balance sheet strength and debt levels
    - Cash flow and intrinsic value
    
    **Technical Analysis** tells you **"WHEN to buy"**
    - Price trends and momentum
    - Entry/exit timing signals
    - Support and resistance levels
    
    **Combined Benefits:**
    - 🎯 When FA + TA **align** → High conviction opportunity
    - ⚠️ When they **diverge** → Caution, deeper analysis needed
    - 📊 360-degree investment view for better decisions
    """)
    
    st.markdown(f"Using: {get_agent_badge(st.session_state.agent_type)}", unsafe_allow_html=True)
    
    st.info("""
    💡 **Research shows** that combining fundamental and technical analysis leads to better 
    investment returns than using either method alone. This approach helps identify quality 
    companies (fundamentals) AND optimal entry points (technicals).
    """)
    
    with st.form("combined-form"):
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            combined_symbol = st.text_input(
                "Ticker Symbol",
                value="AAPL",
                placeholder="e.g., AAPL, MSFT, GOOGL",
                key="combined_symbol",
            )
        with col2:
            combined_tech_period = st.selectbox(
                "Technical Period",
                ["1y", "6mo", "2y", "3mo"],
                index=0,
                key="combined_tech_period",
                help="Period for technical analysis (price trends)",
            )
        with col3:
            combined_fund_period = st.selectbox(
                "Fundamental Period",
                ["3y", "5y", "1y"],
                index=0,
                key="combined_fund_period",
                help="Period for fundamental data (financials)",
            )
        
        combined_submit = st.form_submit_button(
            "🔄 Run Combined Analysis",
            use_container_width=True,
        )
        
        if combined_submit:
            if not combined_symbol.strip():
                st.error("Please enter a ticker symbol")
            else:
                agent_label = "CodeAgent" if st.session_state.agent_type == "code_agent" else "ToolCallingAgent"
                with st.spinner(f"🤖 {agent_label} is analyzing {combined_symbol.upper()} (Technical + Fundamental)... This may take 1-2 minutes."):
                    try:
                        response = call_api("/combined", {
                            "symbol": combined_symbol,
                            "technical_period": combined_tech_period,
                            "fundamental_period": combined_fund_period,
                        })
                        
                        report = response.get("report", "No report generated")
                        duration = response.get("duration_seconds", 0)
                        used_agent = response.get("agent_type", st.session_state.agent_type)
                        
                        add_to_history(
                            f"🔄 Combined: {combined_symbol.upper()}",
                            report,
                            "combined",
                            duration,
                            used_agent,
                        )
                        
                        st.success(f"✅ Combined analysis completed in {duration:.1f}s using {used_agent}")
                        st.markdown(report)
                        
                    except Exception as exc:
                        st.error(f"❌ Analysis failed: {exc}")

# =============================================================================
# Analysis History
# =============================================================================

st.divider()
st.subheader("📜 Analysis History")

if not st.session_state.messages:
    st.info("Run an analysis to see results here. Reports are stored during your session.")
else:
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    
    for idx, entry in enumerate(reversed(st.session_state.messages), 1):
        title = entry["title"]
        duration = entry.get("duration", 0)
        agent_used = entry.get("agent_type", "unknown")
        
        # Create title with agent badge
        agent_emoji = "🐍" if agent_used == "code_agent" else "🔧"
        
        with st.expander(f"{idx}. {title} ({duration:.1f}s) {agent_emoji}", expanded=(idx == 1)):
            st.caption(f"Agent: {agent_used}")
            st.markdown(entry["report"])

# =============================================================================
# Footer
# =============================================================================

st.divider()
st.caption(f"""
**MCP Stock Analyzer** v2.3.0 • Powered by smolagents + LiteLLM + MCP Finance Tools  
Current Agent: **{st.session_state.agent_type}** | Model: **{st.session_state.model_id}**  
*This tool is for educational purposes only. Not financial advice.*
""")