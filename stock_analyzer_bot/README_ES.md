# 📊 Stock Analyzer Bot

La **capa de orquestación con smolagents** del proyecto MCP Financial Markets Analysis Tool. Este módulo ofrece dos arquitecturas de agente para ejecutar análisis financieros mediante herramientas MCP.

---

## 🎯 Descripción general

El módulo implementa dos tipos de agentes que orquestan las herramientas MCP de finanzas:

| Tipo de agente | Implementación | Herramientas usadas | Ideal para |
|----------------|----------------|---------------------|-------------|
| **ToolCallingAgent** | `main.py` | ALTO NIVEL (1 llamada = informe completo) | Producción, fiabilidad |
| **CodeAgent** | `main_codeagent.py` | BAJO NIVEL (bucles en Python) | Velocidad, transparencia |

Ambos agentes ofrecen las mismas capacidades de análisis, pero difieren en su forma de ejecución.

---

## 📁 Estructura del módulo

```
stock_analyzer_bot/
├── __init__.py              # Inicialización del paquete
├── main.py                  # Implementación ToolCallingAgent
├── main_codeagent.py        # Implementación CodeAgent
├── api.py                   # Endpoints FastAPI con selección de agente
├── tools.py                 # Wrappers de herramientas MCP
├── mcp_client.py            # Gestión de la sesión MCP
└── README.md                # Este archivo
```

---

## 🔧 Categorías de herramientas

### Herramientas de ALTO NIVEL (ToolCallingAgent)

Realizan todo el trabajo en **una llamada MCP**. El servidor MCP maneja toda la lógica interna.

```python
from stock_analyzer_bot.tools import HIGH_LEVEL_TOOLS

# Herramientas disponibles:
# - comprehensive_performance_report: 4 estrategias + informe completo (1 llamada)
# - unified_market_scanner: escáner de múltiples acciones con ranking (1 llamada)
# - fundamental_analysis_report: análisis fundamental (1 llamada)
```

**Uso:**
```python
from stock_analyzer_bot.tools import comprehensive_performance_report

resultado = comprehensive_performance_report("AAPL", "1y")
# Devuelve un informe markdown con las 4 estrategias
```

### Herramientas de BAJO NIVEL (CodeAgent)

Son herramientas **granulares** que CodeAgent combina con código Python.

```python
from stock_analyzer_bot.tools import LOW_LEVEL_TOOLS

# Herramientas disponibles:
# - bollinger_fibonacci_analysis: Estrategia individual
# - macd_donchian_analysis: Estrategia individual
# - connors_zscore_analysis: Estrategia individual
# - dual_moving_average_analysis: Estrategia individual
# - fundamental_analysis_report: Datos financieros para análisis combinado
```

**Uso:**
```python
from stock_analyzer_bot.tools import bollinger_fibonacci_analysis

resultado = bollinger_fibonacci_analysis("AAPL", "1y")
# Retorna JSON con señal, métricas e interpretación
```

---

## 🤖 Implementaciones de agentes

### ToolCallingAgent (`main.py`)

Utiliza herramientas de ALTO NIVEL para análisis sencillos y confiables.

```python
from stock_analyzer_bot.main import (
    run_technical_analysis,
    run_market_scanner,
    run_fundamental_analysis,
    run_multi_sector_analysis,
    run_combined_analysis,
)

# Análisis técnico (1 llamada MCP)
informe = run_technical_analysis("AAPL", period="1y")

# Escáner de mercado (1 llamada MCP)
informe = run_market_scanner("AAPL,MSFT,GOOGL", period="1y")

# Análisis fundamental (1 llamada MCP)
informe = run_fundamental_analysis("MSFT", period="3y")

# Análisis multi-sector (1 llamada por sector)
informe = run_multi_sector_analysis(
    sectors={"Banking": "JPM,BAC,WFC", "Tech": "AAPL,MSFT"},
    period="1y"
)

# Análisis combinado (2 llamadas MCP)
informe = run_combined_analysis(
    "TSLA",
    technical_period="1y",
    fundamental_period="3y"
)
```

**Características:**
- Comportamiento simple y predecible.
- Una llamada de herramienta produce un resultado completo.
- Consumo de tokens reducido.
- Ideal para entornos de producción.

### CodeAgent (`main_codeagent.py`)

Utiliza herramientas de BAJO NIVEL coordinadas mediante código Python.

```python
from stock_analyzer_bot.main_codeagent import (
    run_technical_analysis,
    run_market_scanner,
    run_fundamental_analysis,
    run_multi_sector_analysis,
    run_combined_analysis,
)

# Análisis técnico (4 llamadas a herramientas dentro de un bucle)
informe = run_technical_analysis(
    "AAPL",
    period="1y",
    executor_type="local"
)

# Escáner de mercado (4 * N llamadas con bucles anidados)
informe = run_market_scanner(
    "AAPL,MSFT,GOOGL",
    period="1y",
    executor_type="local"
)
```

**Características:**
- El LLM escribe código Python para llamar herramientas.
- Usa bucles para analizar varias acciones con eficiencia.
- Razonamiento transparente (puedes inspeccionar el código generado).
- 2-3× más rápido en escenarios multi-acción.
- Necesita sandbox en producción.

---

## 📡 Endpoints de API

El módulo `api.py` expone todas las funciones de análisis vía FastAPI.

### Configuración

```python
# Variables de entorno
DEFAULT_MODEL_ID = os.getenv("SMOLAGENT_MODEL_ID", "gpt-4o")
DEFAULT_MODEL_PROVIDER = os.getenv("SMOLAGENT_MODEL_PROVIDER", "litellm")
DEFAULT_AGENT_TYPE = os.getenv("SMOLAGENT_AGENT_TYPE", "tool_calling")
DEFAULT_TEMPERATURE = float(os.getenv("SMOLAGENT_TEMPERATURE", "0.1"))
DEFAULT_MAX_TOKENS = int(os.getenv("SMOLAGENT_MAX_TOKENS", "8192"))
```

### Endpoints

#### Health Check

```http
GET /health
```

**Respuesta:**
```json
{
  "status": "ok",
  "version": "2.3.0",
  "features": ["technical_analysis", "market_scanner", "fundamental_analysis", "multisector", "combined"],
  "agent_types": {
    "tool_calling": true,
    "code_agent": true
  },
  "default_agent_type": "tool_calling"
}
```

#### Análisis técnico

```http
POST /technical
Content-Type: application/json

{
  "symbol": "AAPL",
  "period": "1y",
  "agent_type": "tool_calling",
  "model_id": "gpt-4o",
  "max_steps": 25
}
```

**ToolCallingAgent:** llama a `comprehensive_performance_report` (1 llamada).

**CodeAgent:** ejecuta 4 herramientas individuales con orquestación en código.

#### Escáner de mercado

```http
POST /scanner
Content-Type: application/json

{
  "symbols": "AAPL,MSFT,GOOGL,META,NVDA",
  "period": "1y",
  "agent_type": "code_agent"
}
```

**ToolCallingAgent:** llama a `unified_market_scanner`.

**CodeAgent:** itera por acción y estrategia.

#### Análisis fundamental

```http
POST /fundamental
Content-Type: application/json

{
  "symbol": "MSFT",
  "period": "3y",
  "agent_type": "tool_calling"
}
```

Utiliza `fundamental_analysis_report` con más de 70 alias.

#### Análisis multi-sector

```http
POST /multisector
Content-Type: application/json

{
  "sectors": [
    {"name": "Banking", "symbols": "JPM,BAC,WFC"},
    {"name": "Technology", "symbols": "AAPL,MSFT,GOOGL"}
  ],
  "period": "1y",
  "agent_type": "code_agent"
}
```

**ToolCallingAgent:** llama `unified_market_scanner` por sector.

**CodeAgent:** usa bucles anidados (sector → acción → estrategia).

#### Análisis combinado

```http
POST /combined
Content-Type: application/json

{
  "symbol": "TSLA",
  "technical_period": "1y",
  "fundamental_period": "3y",
  "agent_type": "tool_calling"
}
```

Combina análisis técnico (4 estrategias) y fundamental en una sola tesis.

### Formato de respuesta

```json
{
  "report": "# AAPL Comprehensive Technical Analysis\n...",
  "symbol": "AAPL",
  "analysis_type": "technical",
  "duration_seconds": 35.2,
  "agent_type": "tool_calling",
  "tools_approach": "HIGH-LEVEL tools (comprehensive reports in single MCP calls)"
}
```

---

## ⚙️ Configuración

### Parámetros del agente

```python
# Ajustes de modelo
DEFAULT_MODEL_ID = "gpt-4o"
DEFAULT_MODEL_PROVIDER = "litellm"
DEFAULT_TEMPERATURE = 0.1
DEFAULT_MAX_TOKENS = 8192

# Ajustes del agente
DEFAULT_MAX_STEPS = 25
DEFAULT_EXECUTOR = "local"  # local, e2b o docker
```

### Tipos de ejecutor (solo CodeAgent)

| Tipo | Seguridad | Configuración | Caso de uso |
|------|-----------|---------------|-------------|
| `local` | ⚠️ Baja | Ninguna | Desarrollo |
| `e2b` | ✅ Alta | Cuenta E2B | Producción |
| `docker` | ✅ Alta | Docker instalado | Auto-hospedado |

**Configurar e2b:**
```bash
pip install 'smolagents[e2b]'
setx E2B_API_KEY your-key
```

**Configurar Docker:**
```bash
pip install 'smolagents[docker]'
# Asegúrate de que el demonio de Docker esté activo
```

---

## 📝 Plantillas de prompts

Todos los prompts siguen reglas de formato estrictas:

### Reglas de formato

1. **Moneda:** usar el prefijo "USD" en lugar del símbolo `$`.
2. **Tablas:** evitar el uso de `|` en tablas para minimizar problemas en Streamlit.
3. **Estructura:** cada métrica en su propia línea.
4. **Encabezados:** secciones numeradas y jerárquicas.
5. **Sin cursivas:** evitar `*texto*`.

### Prompt de análisis técnico

```
1. EXECUTIVE SUMMARY
   - Recomendación general (BUY/HOLD/SELL)
   - Nivel de confianza
   - Métricas clave

2. STRATEGY ANALYSIS
   - Bollinger-Fibonacci: señal, métricas, interpretación
   - MACD-Donchian: señal, métricas, interpretación
   - Connors RSI-ZScore: señal, métricas, interpretación
   - Dual Moving Average: señal, métricas, interpretación

3. RISK ASSESSMENT
   - Guía de tamaño de posición
   - Niveles de stop loss

4. FINAL RECOMMENDATION
   - Conclusión accionable
```

### Prompt del escáner de mercado

```
1. MARKET OVERVIEW
   - Total de acciones analizadas
   - Condiciones de mercado

2. RANKED OPPORTUNITIES
   - Ranking con puntuaciones
   - Cinco estrategias por acción:
     * Bollinger Z-Score
     * Bollinger-Fibonacci
     * MACD-Donchian
     * Connors RSI-ZScore
     * Dual Moving Average

3. TOP RECOMMENDATIONS
   - Mejores oportunidades con razonamiento

4. PORTFOLIO ALLOCATION
   - Porcentajes sugeridos
```

---

## 🧪 Ejemplos de uso

### Python - Importación directa

```python
from stock_analyzer_bot.tools import configure_finance_tools, shutdown_finance_tools

# Inicializar conexión MCP
configure_finance_tools()

try:
    # ToolCallingAgent
    from stock_analyzer_bot.main import run_technical_analysis
    report = run_technical_analysis(symbol="AAPL", period="1y")

    # CodeAgent
    from stock_analyzer_bot.main_codeagent import run_market_scanner
    report = run_market_scanner(
        symbols="AAPL,MSFT,GOOGL",
        period="1y",
        executor_type="local"
    )

    print(report)
finally:
    shutdown_finance_tools()
```

### CLI - ToolCallingAgent

```bash
python -m stock_analyzer_bot.main AAPL --mode technical --period 1y
python -m stock_analyzer_bot.main "AAPL,MSFT" --mode scanner
python -m stock_analyzer_bot.main MSFT --mode fundamental
```

### CLI - CodeAgent

```bash
python -m stock_analyzer_bot.main_codeagent AAPL --mode technical --executor local
python -m stock_analyzer_bot.main_codeagent "AAPL,MSFT,GOOGL" --mode scanner
python -m stock_analyzer_bot.main_codeagent TSLA --mode combined
```

### cURL - API

```bash
# Análisis técnico con ToolCallingAgent
curl -X POST "http://localhost:8000/technical" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "agent_type": "tool_calling"}'

# Escáner con CodeAgent
curl -X POST "http://localhost:8000/scanner" \
  -H "Content-Type: application/json" \
  -d '{"symbols": "AAPL,MSFT", "agent_type": "code_agent"}'

# Multi-sector con CodeAgent (recomendado)
curl -X POST "http://localhost:8000/multisector" \
  -H "Content-Type: application/json" \
  -d '{
    "sectors": [
      {"name": "Banking", "symbols": "JPM,BAC,WFC"},
      {"name": "Tech", "symbols": "AAPL,MSFT,GOOGL"}
    ],
    "agent_type": "code_agent"
  }'
```

---

## 📊 Comparativa de rendimiento

### Benchmarks: ToolCallingAgent vs CodeAgent

| Escenario | ToolCallingAgent | CodeAgent (local) | Mejora |
|-----------|-----------------|-------------------|--------|
| Acción única (4 estrategias) | ~45 s | ~40 s | 10% |
| Comparación de 3 acciones | ~180 s | ~90 s | 50% |
| Comparación de 5 acciones | ~300 s | ~100 s | 66% |
| Multi-sector (3 sectores) | ~600 s | ~200 s | 66% |

**Conclusiones:**
- ✅ CodeAgent es 2-3× más rápido consolidando varias acciones.
- ✅ ToolCallingAgent es más estable para análisis simples.
- ⚠️ CodeAgent necesita sandbox (e2b/docker) en producción.

---

## 🛠️ Solución de problemas

### Problemas comunes

| Problema | Causa | Solución |
|----------|-------|----------|
| "CodeAgent not available" | Falta `main_codeagent.py` | Verifica en `stock_analyzer_bot/` |
| "MCP server not found" | Ruta incorrecta | Asegura que `server/main.py` exista |
| "Connection refused" | FastAPI no iniciado | Ejecuta `uvicorn stock_analyzer_bot.api:app --port 8000` |
| "Code execution failed" | Python inválido generado | Usa un modelo distinto (gpt-4o recomendado) |
| "Timeout" | Demasiadas acciones | Reduce la lista o usa CodeAgent |
| "Authentication error" | API key inválida | Revisa `OPENAI_API_KEY` |
| "Import not allowed" | Restricción del sandbox | Añade a `additional_authorized_imports` |
| "Truncated output" | Falta de tokens | Aumenta `max_tokens` a 8192+ |
| "LaTeX formatting" | Uso del símbolo `$` | El código emplea prefijo USD |

### Consejos de depuración

**Activar logging detallado:**
```python
agent = CodeAgent(
    tools=tools,
    model=model,
    verbosity_level=2,
)
```

**Inspeccionar el razonamiento:**
```python
resultado = agent.run(prompt)
print(agent.logs)
```

**Probar la conexión MCP:**
```python
from stock_analyzer_bot.tools import configure_finance_tools
from stock_analyzer_bot.mcp_client import get_session

configure_finance_tools()
session = get_session()
print(f"Sesión activa: {session is not None}")
```

---

## 📚 Documentación relacionada

- [README raíz](../README.md)
- [README del servidor](../server/README.md)
- [Documentación de smolagents](https://huggingface.co/docs/smolagents/index)
- [Secure Code Execution](https://huggingface.co/docs/smolagents/tutorials/secure_code_execution)

---

## 🔄 Cambios recientes

### v2.3.0 – Formato de salida y estabilidad

- Temperatura fijada en 0.1 para salidas más deterministas.
- Formato de moneda: prefijo USD en lugar de símbolo `$`.
- Límite de tokens ampliado a 8192 por defecto.
- Escáner de mercado: restauradas MACD-Donchian y Connors RSI-ZScore.
- Plantillas: resueltos conflictos de formato en cadenas Python.
- Helper `format_agent_result()` para limpiar la salida.

### v2.2.0 – Mejoras de análisis fundamental

- Más de 70 alias para obtener datos con yfinance.
- Matching multinivel: exacto → alias → substring.
- Ratios financieros adicionales en 4 categorías.
- Fallbacks elegantes cuando faltan datos.

### v2.1.0 – Arquitectura dual de agentes

- Añadido CodeAgent para bucles eficientes en Python.
- Ejecutores soportados: local, e2b y docker.
- Separación entre herramientas de ALTO y BAJO nivel.
- Selección de agente vía API por cada petición.

---

<p align="center">
  <i>Stock Analyzer Bot v2.3.0 – Soporte dual con ToolCallingAgent y CodeAgent</i>
</p>

# Valores Predeterminados de Análisis
DEFAULT_ANALYSIS_PERIOD=1y
DEFAULT_SCANNER_SYMBOLS=AAPL,MSFT,GOOGL,AMZN

# Servidor API
STOCK_ANALYZER_API_URL=http://localhost:8000
```

### Configuración de Executor para CodeAgent

#### Opción 1: E2B (Sandbox en la Nube)

```bash
# 1. Registrarse en https://e2b.dev
# 2. Obtener clave API
export E2B_API_KEY=e2b_tu-clave-api

# 3. Configurar agente
export SMOLAGENT_AGENT_TYPE=code_agent
export SMOLAGENT_EXECUTOR=e2b
```

**Ventajas:**
- ✅ Sin configuración de infraestructura
- ✅ Sandbox seguro gestionado
- ✅ Escalado automático

**Desventajas:**
- ⚠️ Costo por uso
- ⚠️ Requiere conectividad a internet

#### Opción 2: Docker (Autohospedado)

```bash
# 1. Instalar Docker
# 2. Construir imagen con dependencias

# Dockerfile
FROM python:3.11-slim
RUN pip install yfinance pandas numpy

# 3. Configurar agente
export SMOLAGENT_AGENT_TYPE=code_agent
export SMOLAGENT_EXECUTOR=docker
export DOCKER_IMAGE=python:3.11-slim
```

**Ventajas:**
- ✅ Sin costos externos
- ✅ Control total sobre el entorno
- ✅ Sin dependencias de internet

**Desventajas:**
- ⚠️ Requiere gestión de infraestructura
- ⚠️ Requiere configuración de Docker

#### Opción 3: Local (Solo Desarrollo)

```bash
export SMOLAGENT_AGENT_TYPE=code_agent
export SMOLAGENT_EXECUTOR=local
```

**⚠️ ADVERTENCIA:** Solo para desarrollo. Ejecuta código generado por LLM sin sandbox.

---

## Uso

### Opción 1: API FastAPI

#### Ejemplo con ToolCallingAgent
```python
import requests

response = requests.post("http://localhost:8000/analyze/stock", json={
    "ticker": "AAPL",
    "llm_provider": "openai",
    "agent_type": "tool_calling"  # Estable, depuración fácil
})

print(response.json()["analysis"])
```

#### Ejemplo con CodeAgent (Desarrollo)
```python
response = requests.post("http://localhost:8000/analyze/stock", json={
    "ticker": "AAPL",
    "llm_provider": "openai",
    "agent_type": "code_agent",
    "executor_type": "local"  # Solo desarrollo
})
```

#### Ejemplo con CodeAgent (Producción - E2B)
```python
response = requests.post("http://localhost:8000/analyze/stock", json={
    "ticker": "AAPL",
    "llm_provider": "openai",
    "agent_type": "code_agent",
    "executor_type": "e2b"  # Sandbox seguro
})
```

### Opción 2: Python Directo

#### ToolCallingAgent
```python
from stock_analyzer_bot.main import run_stock_analysis

result = await run_stock_analysis("AAPL", "openai")
print(result)
```

#### CodeAgent
```python
from stock_analyzer_bot.main_codeagent import run_stock_analysis_with_code_agent

# Desarrollo
result = await run_stock_analysis_with_code_agent("AAPL", "openai", "local")

# Producción
result = await run_stock_analysis_with_code_agent("AAPL", "openai", "e2b")
```

---

## Ejemplos de Salida

### ToolCallingAgent - Análisis de Acción Única
    max_steps: int = 25,
) -> str:  # Retorna informe markdown
```

---

### api.py - Backend FastAPI

API RESTful que expone todas las funciones de análisis.

#### Configuración de la Aplicación

```python
app = FastAPI(
    title="MCP Stock Analyzer API",
    version="2.2.0",
)

# CORS habilitado para acceso del frontend
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)

# Eventos del ciclo de vida
@app.on_event("startup")   # Inicializar conexión MCP
@app.on_event("shutdown")  # Limpiar conexión MCP
```

#### Modelos de Solicitud

```python
class TechnicalAnalysisRequest(BaseModel):
    symbol: str           # Requerido: símbolo ticker
    period: str = "1y"    # Período histórico
    model_id: Optional[str]
    model_provider: Optional[str]
    openai_api_key: Optional[str]
    hf_token: Optional[str]
    max_steps: Optional[int]

class MarketScannerRequest(BaseModel):
    symbols: str          # Separado por comas: "AAPL,MSFT,GOOGL"
    period: str = "1y"
    # ... mismos campos opcionales

class FundamentalAnalysisRequest(BaseModel):
    symbol: str
    period: str = "3y"    # Años de datos financieros
    # ... mismos campos opcionales

class MultiSectorAnalysisRequest(BaseModel):
    sectors: List[SectorConfig]  # [{"name": "Banking", "symbols": "JPM,BAC"}]
    period: str = "1y"
    # ... mismos campos opcionales

class CombinedAnalysisRequest(BaseModel):
    symbol: str
    technical_period: str = "1y"
    fundamental_period: str = "3y"
    # ... mismos campos opcionales
```

#### Modelo de Respuesta

```python
class AnalysisResponse(BaseModel):
    report: str              # Informe de análisis en markdown
    symbol: str              # Símbolo(s) analizados
    analysis_type: str       # "technical", "scanner", etc.
    duration_seconds: float  # Tiempo de procesamiento
```

---

### tools.py - Wrappers de Herramientas Smolagents

Conecta smolagents con el servidor MCP. Cada herramienta es una función decorada que el LLM puede llamar.

#### Categorías de Herramientas

**STRATEGY_TOOLS (4 herramientas para análisis técnico):**
```python
STRATEGY_TOOLS = [
    bollinger_fibonacci_analysis,   # BB + Fibonacci
    macd_donchian_analysis,         # MACD + Donchian
    connors_zscore_analysis,        # Connors RSI + Z-Score
    dual_moving_average_analysis,   # Cruce 50/200 EMA
]
```

**Herramientas Adicionales:**
```python
comprehensive_performance_report  # Informe multi-estrategia determinístico
unified_market_scanner           # Escáner multi-acción
fundamental_analysis_report      # Estados financieros
```

#### Patrón de Definición de Herramientas

```python
from smolagents import tool

@tool
def bollinger_fibonacci_analysis(
    symbol: str,
    period: str = "1y",
    window: int = 20,
    num_std: float = 2.0,
    window_swing_points: int = 10,
) -> str:
    """Ejecuta el análisis de estrategia MCP combinado Bollinger-Fibonacci.
    
    Esta estrategia combina Bandas de Bollinger (reversión a la media) con 
    niveles de retroceso de Fibonacci (soporte/resistencia) para análisis 
    de precios integral.
    
    Args:
        symbol: Ticker a analizar (ej., 'AAPL', 'MSFT').
        period: Período histórico (predeterminado: '1y').
        window: Ventana retrospectiva de Bollinger (predeterminado: 20).
        num_std: Desviaciones estándar para bandas (predeterminado: 2.0).
        window_swing_points: Ventana de detección de puntos swing (predeterminado: 10).
    
    Returns:
        Informe de rendimiento detallado con señales y métricas.
    """
    params = {
        "symbol": _normalize_symbol(symbol),
        "period": period,
        "window": window,
        "num_std": num_std,
        "window_swing_points": window_swing_points,
    }
    return _call_finance_tool("analyze_bollinger_fibonacci_performance", params)
```

#### Funciones Helper Internas

```python
def _normalize_symbol(symbol: str) -> str:
    """Limpia y valida símbolo ticker."""
    cleaned = symbol.strip().upper()
    if not cleaned:
        raise ValueError("Symbol must be a non-empty string")
    return cleaned

def _call_finance_tool(tool_name: str, parameters: Dict) -> str:
    """Llama herramienta del servidor MCP vía sesión."""
    try:
        return get_session().call_tool(tool_name, parameters)
    except Exception as exc:
        logger.exception("Error calling %s", tool_name)
        return f"Error calling {tool_name}: {exc}"
```

---

### mcp_client.py - Conexión al Servidor MCP

Gestiona la conexión de larga duración al servidor financiero MCP.

#### Clase MCPFinanceSession

```python
class MCPFinanceSession:
    """Gestiona una conexión de larga duración al servidor financiero MCP."""
    
    def __init__(self, server_path: Path = None):
        self.server_path = server_path or _DEFAULT_SERVER_PATH
        self._session: Optional[ClientSession] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        
    def start(self):
        """Inicia conexión al servidor MCP en hilo de fondo."""
        # Crea event loop async en hilo separado
        # Establece conexión stdio a server/main.py
        
    def stop(self):
        """Detiene conexión al servidor MCP."""
        
    def call_tool(self, name: str, arguments: Dict) -> str:
        """Llama una herramienta en el servidor MCP sincrónicamente."""
        # Conecta código síncrono a llamadas MCP asíncronas
```

#### Patrón de Conexión

```python
# Ruta predeterminada del servidor (relativa a mcp_client.py)
_DEFAULT_SERVER_PATH = Path(__file__).resolve().parents[1] / "server" / "main.py"

# Parámetros del servidor para transporte stdio
server_params = StdioServerParameters(
    command="python",
    args=[str(self.server_path)]
)

# Conexión vía protocolo MCP
async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        # Sesión lista para llamadas de herramientas
```

#### Funciones a Nivel de Módulo

```python
# Gestión de sesión global
_session: Optional[MCPFinanceSession] = None

def configure_session(server_path: Path = None):
    """Inicializa sesión MCP (llamada al inicio)."""
    global _session
    _session = MCPFinanceSession(server_path)
    _session.start()

def get_session() -> MCPFinanceSession:
    """Obtiene la sesión MCP activa."""
    if _session is None:
        configure_session()
    return _session

def shutdown_session():
    """Detiene la sesión MCP (llamada al cerrar)."""
    global _session
    if _session:
        _session.stop()
        _session = None
```

---

## Endpoints de API

### GET /health

Verificación de salud y lista de características.

**Respuesta:**
```json
{
  "status": "ok",
  "version": "2.2.0",
  "features": [
    "technical_analysis",
    "market_scanner",
    "fundamental_analysis",
    "multi_sector_analysis",
    "combined_analysis"
  ],
  "model": {
    "default_id": "gpt-4.1",
    "default_provider": "litellm"
  }
}
```

---

### POST /technical

Análisis técnico de acción única con 4 estrategias.

**Solicitud:**
```json
{
  "symbol": "AAPL",
  "period": "1y"
}
```

**Qué Sucede:**
1. El agente llama 4 herramientas de estrategia para AAPL
2. Cada herramienta retorna métricas de rendimiento
3. El agente sintetiza en informe

**Respuesta:**
```json
{
  "report": "# Análisis Técnico Completo de AAPL\n...",
  "symbol": "AAPL",
  "analysis_type": "technical",
  "duration_seconds": 45.2
}
```

---

### POST /scanner

Comparación y clasificación multi-acción.

**Solicitud:**
```json
{
  "symbols": "AAPL,MSFT,GOOGL,META,NVDA",
  "period": "1y"
}
```

**Qué Sucede:**
1. El agente llama 4 herramientas de estrategia para CADA acción (20 llamadas totales)
2. Compara rendimiento entre todas las acciones
3. Clasifica e identifica las mejores oportunidades

**Respuesta:**
```json
{
  "report": "# Informe de Análisis Multi-Acción del Mercado\n...",
  "symbol": "AAPL,MSFT,GOOGL,META,NVDA",
  "analysis_type": "scanner",
  "duration_seconds": 180.5
}
```

---

### POST /fundamental

Análisis de estados financieros.

**Solicitud:**
```json
{
  "symbol": "MSFT",
  "period": "3y"
}
```

**Qué Sucede:**
1. El agente llama la herramienta fundamental_analysis_report
2. Obtiene estado de resultados, balance general, flujo de caja
3. Interpreta salud financiera y crea tesis

**Respuesta:**
```json
{
  "report": "# Informe de Análisis Fundamental de MSFT\n...",
  "symbol": "MSFT",
  "analysis_type": "fundamental",
  "duration_seconds": 35.0
}
```

---

### POST /multisector

Análisis comparativo entre sectores.

**Solicitud:**
```json
{
  "sectors": [
    {"name": "Banking", "symbols": "JPM,BAC,WFC,C,GS"},
    {"name": "Technology", "symbols": "AAPL,MSFT,GOOGL,META,NVDA"},
    {"name": "Clean Energy", "symbols": "TSLA,NIO,ENPH,PLUG,NEE"}
  ],
  "period": "1y"
}
```

**Qué Sucede:**
1. El agente procesa cada sector
2. Llama 4 herramientas por acción (60 llamadas totales para 15 acciones)
3. Compara rendimiento ENTRE sectores
4. Identifica mejores oportunidades de todo el universo

**Respuesta:**
```json
{
  "report": "# Informe de Análisis Multi-Sector del Mercado\n...",
  "symbol": "Banking, Technology, Clean Energy",
  "analysis_type": "multi_sector",
  "duration_seconds": 450.0
}
```

---

### POST /combined

Análisis Técnico + Fundamental combinado.

**Solicitud:**
```json
{
  "symbol": "AAPL",
  "technical_period": "1y",
  "fundamental_period": "3y"
}
```

**Qué Sucede:**
1. El agente llama fundamental_analysis_report
2. El agente llama 4 herramientas de estrategia técnica
3. Sintetiza AMBAS perspectivas
4. Determina si las señales se alinean o divergen

**Respuesta:**
```json
{
  "report": "# Análisis de Inversión Combinado de AAPL\n...",
  "symbol": "AAPL",
  "analysis_type": "combined",
  "duration_seconds": 75.0
}
```

---

## Tipos de Análisis

### Tabla Comparativa

| Tipo | Endpoint | Acciones | Herramientas/Acción | Propósito | Tiempo |
|------|----------|----------|---------------------|-----------|--------|
| Técnico | `/technical` | 1 | 4 | Análisis profundo acción única | 30-60s |
| Escáner | `/scanner` | N | 4 | Comparar oportunidades | 2-5min |
| Fundamental | `/fundamental` | 1 | 1 | Salud financiera | 30s |
| Multi-Sector | `/multisector` | N×M | 4 | Comparación entre sectores | 5-15min |
| Combinado | `/combined` | 1 | 5 | Análisis completo | 60-90s |

### Cuándo Usar Cada Uno

| Caso de Uso | Análisis Recomendado |
|-------------|---------------------|
| "¿Debería comprar AAPL?" | Análisis Combinado |
| "¿Cuál es la mejor acción tech?" | Escáner de Mercado |
| "¿Es MSFT financieramente saludable?" | Análisis Fundamental |
| "¿Dónde debería invertir entre sectores?" | Análisis Multi-Sector |
| "¿Qué dicen los gráficos sobre TSLA?" | Análisis Técnico |

---

## Frontend Streamlit

El `streamlit_app.py` proporciona una interfaz web con 5 pestañas:

### Características

- **Pestaña Análisis Técnico**: Acción única, selector de período
- **Pestaña Escáner de Mercado**: Entrada multi-acción, comparación
- **Pestaña Análisis Fundamental**: Análisis de estados financieros
- **Pestaña Multi-Sector**: Sectores configurables con agregar/eliminar
- **Pestaña Análisis Combinado**: Téc + Fundamental juntos

### Estado de Sesión

```python
st.session_state.messages     # Historial de análisis
st.session_state.api_url      # URL del backend
st.session_state.model_id     # Modelo LLM
st.session_state.model_provider  # Proveedor
st.session_state.openai_api_key  # Sobrescritura de clave API
```

### Comunicación API

```python
def call_api(endpoint: str, payload: Dict) -> Dict:
    """Llama backend FastAPI con configuraciones de modelo."""
    # Agrega model_id, model_provider, openai_api_key al payload
    # Timeout: 600s normal, 1200s para multi-sector
    response = requests.post(url, json=payload, timeout=timeout)
    return response.json()
```

---

## Ejemplos de Uso

### Uso CLI

```bash
# Análisis técnico básico
python -m stock_analyzer_bot.main AAPL

# Con período personalizado
python -m stock_analyzer_bot.main TSLA --period 2y

# Con modelo personalizado
python -m stock_analyzer_bot.main MSFT --model-id gpt-4o --model-provider litellm

# Guardar salida a archivo
python -m stock_analyzer_bot.main GOOGL --output report.md
```

### API Python

```python
from stock_analyzer_bot.main import (
    run_technical_analysis,
    run_market_scanner,
    run_fundamental_analysis,
    run_combined_analysis,
)

# Análisis Técnico
report = run_technical_analysis("AAPL", period="1y")
print(report)

# Escáner de Mercado
report = run_market_scanner("AAPL,MSFT,GOOGL", period="1y")
print(report)

# Análisis Fundamental
report = run_fundamental_analysis("MSFT", period="3y")
print(report)

# Análisis Combinado
report = run_combined_analysis("AAPL", technical_period="1y", fundamental_period="3y")
print(report)
```

### REST API

```bash
# Análisis Técnico
curl -X POST "http://localhost:8000/technical" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "period": "1y"}'

# Escáner de Mercado
curl -X POST "http://localhost:8000/scanner" \
  -H "Content-Type: application/json" \
  -d '{"symbols": "AAPL,MSFT,GOOGL", "period": "1y"}'

# Multi-Sector
curl -X POST "http://localhost:8000/multisector" \
  -H "Content-Type: application/json" \
  -d '{
    "sectors": [
      {"name": "Tech", "symbols": "AAPL,MSFT"},
      {"name": "Finance", "symbols": "JPM,BAC"}
    ],
    "period": "1y"
  }'
```

---

## Comparación de Rendimiento

### Benchmarks: ToolCallingAgent vs CodeAgent

| Escenario | ToolCallingAgent | CodeAgent (local) | Mejora |
|-----------|-----------------|-------------------|--------|
| Acción única (4 estrategias) | ~45s | ~40s | 10% |
| Comparación de 3 acciones | ~180s | ~90s | 50% |
| Comparación de 5 acciones | ~300s | ~100s | 66% |
| Análisis multi-sector | ~600s | ~200s | 66% |

**Conclusiones:**
- ✅ CodeAgent es 2-3x más rápido para análisis multi-ticker
- ✅ ToolCallingAgent es más estable para análisis simple
- ⚠️ CodeAgent requiere sandbox (e2b/docker) en producción

---

## Solución de Problemas

### Problemas Comunes

| Problema | Causa | Solución |
|----------|-------|----------|
| "MCP server not found" | Ruta del servidor incorrecta | Verifica que `server/main.py` existe |
| "Connection refused" | FastAPI no está corriendo | Iniciar con `uvicorn` |
| "Timeout" | Demasiadas acciones | Reducir cantidad de acciones o aumentar timeout |
| "Authentication error" | Clave API inválida | Verifica `OPENAI_API_KEY` en `.env` |
| "Agent stopped early" | Máx steps alcanzado | Aumentar parámetro `max_steps` |

### Problemas de ToolCallingAgent

**Error: "Max steps reached"**
```python
# Aumentar límite de pasos en main.py
agent = ToolCallingAgent(
    tools=tools,
    model=model,
    max_steps=50,  # Aumentar desde 25
)
```

**Error: "Tool call failed - Invalid JSON"**
- Verificar que el servidor MCP esté ejecutándose
- Verificar conectividad stdio al servidor MCP
- Verificar formato de parámetros de herramientas en tools.py

### Problemas de CodeAgent

**Error: "Executor type 'local' not allowed in production"**
```bash
# Cambiar a e2b o docker
export SMOLAGENT_EXECUTOR=e2b
export E2B_API_KEY=tu-clave-api
```

**Error: "E2B API key not found"**
```bash
# Configurar clave API de E2B
export E2B_API_KEY=e2b_tu-clave-api
```

**Error: "Docker container failed to start"**
```bash
# Verificar que Docker esté ejecutándose
docker ps

# Construir imagen con dependencias
docker build -t python-finance .
export DOCKER_IMAGE=python-finance
```

**Error: "Code execution timeout"**
```python
# Aumentar timeout en main_codeagent.py
agent = CodeAgent(
    tools=tools,
    model=model,
    max_steps=50,
    timeout=300,  # 5 minutos
)
```

### Modo Debug

```bash
# Habilitar logging de debug
export LOG_LEVEL=DEBUG
uvicorn stock_analyzer_bot.api:app --reload --port 8000
```

---

## Mejores Prácticas

### Cuándo Usar ToolCallingAgent

✅ **Usar para:**
- Análisis de acción única
- Entornos productivos donde se requiere estabilidad
- Cuando la depuración es prioritaria
- Presupuesto limitado de llamadas LLM (uso de GPT-4)

❌ **Evitar para:**
- Comparación de múltiples acciones (lento)
- Análisis multi-sector (muy lento)
- Cuando la velocidad es crítica

### Cuándo Usar CodeAgent

✅ **Usar para:**
- Comparación de múltiples acciones
- Análisis multi-sector
- Cuando la velocidad es prioritaria
- Análisis complejo requiriendo almacenamiento de variables

❌ **Evitar para:**
- Análisis simple de acción única (overhead innecesario)
- Cuando no se puede configurar sandbox (usar solo local en desarrollo)
- Cuando la depuración es prioritaria

### Configuración de Producción

```bash
# Recomendado para producción
export SMOLAGENT_AGENT_TYPE=code_agent
export SMOLAGENT_EXECUTOR=e2b           # O docker
export E2B_API_KEY=tu-clave-api
export OPENAI_API_KEY=tu-clave-openai
export SMOLAGENT_MODEL_ID=gpt-4o-mini  # Más barato
export SMOLAGENT_MAX_STEPS=50
```

---

## Historial de Versiones

| Versión | Cambios |
|---------|---------|
| 1.0.0 | Lanzamiento inicial con análisis técnico |
| 2.0.0 | Agregado Escáner de Mercado, Análisis Fundamental |
| 2.1.0 | Agregado Análisis Multi-Sector |
| 2.2.0 | Agregado Análisis Técnico + Fundamental Combinado |
| 2.3.0 | **Agregado CodeAgent dual-arquitectura con executors** |

---

## Recursos Adicionales

### Documentación

- **README Principal**: [README_ES.md](../README_ES.md) - Guía completa del proyecto
- **Servidor MCP**: [server/README_ES.md](../server/README_ES.md) - Documentación del servidor de herramientas
- **Smolagents**: [Documentación Oficial](https://github.com/huggingface/smolagents)
- **Model Context Protocol**: [Especificación MCP](https://modelcontextprotocol.io/)

### Comparación de Agentes

| Aspecto | ToolCallingAgent | CodeAgent |
|---------|-----------------|-----------|
| **Implementación** | `main.py` | `main_codeagent.py` |
| **Paradigma** | JSON-based | Python code-based |
| **Velocidad** | Moderada | 2-3x más rápido |
| **Debugging** | Fácil | Complejo |
| **Seguridad** | Alto | Requiere sandbox |
| **Producción** | ✅ Listo | ⚠️ Requiere e2b/docker |

---

## Licencia

Este software se proporciona para fines educativos e investigación. Siempre verifica los resultados de análisis y consulta profesionales financieros antes de tomar decisiones de inversión.

---

*Construido con [smolagents](https://github.com/huggingface/smolagents), [FastAPI](https://fastapi.tiangolo.com/) y [MCP](https://modelcontextprotocol.io/)*
