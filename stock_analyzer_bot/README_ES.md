# 🤖 Stock Analyzer Bot

Capa de orquestación de IA impulsada por Smolagents que conecta LLMs a herramientas de análisis financiero MCP. Este módulo soporta **dos arquitecturas de agentes**: ToolCallingAgent (basado en JSON) y CodeAgent (basado en código Python).

---

## 📋 Tabla de Contenidos

- [Descripción General](#descripción-general)
- [Tipos de Agentes](#tipos-de-agentes)
- [Arquitectura](#arquitectura)
- [Referencia de Módulos](#referencia-de-módulos)
- [Endpoints de API](#endpoints-de-api)
- [Ejemplos de Uso](#ejemplos-de-uso)
- [Configuración](#configuración)
- [Solución de Problemas](#solución-de-problemas)

---

## Descripción General

El Stock Analyzer Bot es la **capa de orquestación de IA** que:

1. Recibe solicitudes de análisis desde la API
2. Usa un LLM (OpenAI/HuggingFace) para decidir qué herramientas llamar
3. Ejecuta herramientas MCP vía la conexión del cliente
4. Sintetiza resultados en informes markdown profesionales

### Características Clave

- **Soporte Dual de Agentes**: ToolCallingAgent O CodeAgent
- **5 Tipos de Análisis**: Técnico, Escáner, Fundamental, Multi-Sector, Combinado
- **Integración MCP**: Conexión perfecta a herramientas financieras
- **Agnóstico de LLM**: Funciona con OpenAI, HuggingFace y más

---

## Tipos de Agentes

### 🔧 ToolCallingAgent (`main.py`)

La implementación original usando llamadas de herramientas basadas en JSON.

**Cómo Funciona:**
```
Usuario: "Analiza AAPL"
     ↓
LLM: {"tool": "bollinger_fibonacci_analysis", "args": {"symbol": "AAPL"}}
     ↓
Ejecutar herramienta → Retornar resultado
     ↓
LLM: {"tool": "macd_donchian_analysis", "args": {"symbol": "AAPL"}}
     ↓
Ejecutar herramienta → Retornar resultado
     ↓
... (repetir para cada herramienta)
     ↓
LLM: Sintetizar todos los resultados → Generar informe
```

**Características:**
- Una llamada de herramienta por ronda LLM
- Ejecución secuencial
- Simple y predecible
- Sin riesgos de ejecución de código

### 🐍 CodeAgent (`main_codeagent.py`)

La implementación avanzada donde el LLM escribe código Python.

**Cómo Funciona:**
```
Usuario: "Analiza AAPL, MSFT, GOOGL"
     ↓
LLM genera código Python:
┌──────────────────────────────────────────────────┐
│ results = {}                                      │
│ for stock in ["AAPL", "MSFT", "GOOGL"]:          │
│     results[stock] = {                            │
│         "bb": bollinger_fibonacci_analysis(stock),│
│         "macd": macd_donchian_analysis(stock),   │
│     }                                             │
│                                                   │
│ # Clasificar por rendimiento                      │
│ ranked = sorted(results.items(), key=...)        │
│ final_answer(generate_report(ranked))            │
└──────────────────────────────────────────────────┘
     ↓
Ejecutor Python ejecuta código → Llama todas las herramientas
     ↓
Retornar informe final
```

**Características:**
- Múltiples herramientas en una ronda LLM
- Basado en loops para multi-acción
- Puede almacenar variables y calcular
- Requiere sandbox de ejecución de código

### Tabla Comparativa

| Característica | ToolCallingAgent | CodeAgent |
|----------------|-----------------|-----------|
| Llamadas de herramienta por ronda | 1 | Muchas (vía loops) |
| Eficiencia multi-acción | ⚠️ Lento | ✅ Rápido |
| Almacenamiento de variables | ❌ No | ✅ Sí |
| Depuración | ✅ Fácil | ⚠️ Más difícil |
| Seguridad | ✅ Seguro | ⚠️ Necesita sandbox |
| Requisitos LLM | Cualquier LLM | Bueno en Python |

---

## Arquitectura

### Diagrama de Flujo de Datos

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         STOCK ANALYZER BOT                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐                                                        │
│  │   api.py    │  ← Endpoints FastAPI                                   │
│  │             │    Recibe solicitudes, selecciona tipo de agente       │
│  └──────┬──────┘                                                        │
│         │                                                               │
│         ▼                                                               │
│  ┌──────────────────────────────────────────────────┐                   │
│  │              SELECCIÓN DE AGENTE                 │                   │
│  │  ┌──────────────────┐  ┌──────────────────────┐  │                   │
│  │  │     main.py      │  │  main_codeagent.py   │  │                   │
│  │  │ ToolCallingAgent │  │     CodeAgent        │  │                   │
│  │  │   (Basado JSON)  │  │  (Código Python)     │  │                   │
│  │  └────────┬─────────┘  └──────────┬───────────┘  │                   │
│  └───────────┼───────────────────────┼──────────────┘                   │
│              │                       │                                  │
│              └───────────┬───────────┘                                  │
│                          ▼                                              │
│  ┌─────────────────────────────────────────────────┐                    │
│  │               tools.py                          │                    │
│  │    Funciones decoradas con @tool                │                    │
│  │    bollinger_fibonacci_analysis()               │                    │
│  │    macd_donchian_analysis()                     │                    │
│  │    connors_zscore_analysis()                    │                    │
│  │    dual_moving_average_analysis()               │                    │
│  │    fundamental_analysis_report()                │                    │
│  └──────────────────────┬──────────────────────────┘                    │
│                         │                                               │
│                         ▼                                               │
│  ┌─────────────────────────────────────────────────┐                    │
│  │            mcp_client.py                        │                    │
│  │    MCPFinanceSession                            │                    │
│  │    - Gestiona conexión al servidor MCP          │                    │
│  │    - Envía llamadas de herramientas vía stdio   │                    │
│  └──────────────────────┬──────────────────────────┘                    │
│                         │ stdio                                         │
└─────────────────────────┼───────────────────────────────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │    MCP SERVER         │
              │   (server/main.py)    │
              │   Herramientas        │
              │   Financieras         │
              └───────────────────────┘
```

### Estructura de Archivos

```
stock_analyzer_bot/
├── __init__.py              # Inicialización del paquete
├── main.py                  # Implementación ToolCallingAgent
├── main_codeagent.py        # Implementación CodeAgent (NUEVO)
├── api.py                   # Endpoints REST de FastAPI
├── tools.py                 # Wrappers @tool de Smolagents
├── mcp_client.py            # Gestor de conexión al servidor MCP
└── README.md                # Este archivo
```

### Flujo de Datos

```
Solicitud del Usuario
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. Endpoint FastAPI recibe la solicitud                     │
│    - Valida entrada (símbolo, período, etc.)                │
│    - Selecciona tipo de agente (tool_calling o code_agent)  │
│    - Llama la función run_*_analysis() apropiada            │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Función de Análisis (main.py o main_codeagent.py)        │
│    - Construye modelo LLM (OpenAI/HuggingFace)              │
│    - Crea agente (ToolCallingAgent O CodeAgent)             │
│    - Formatea prompt con parámetros del usuario             │
│    - Ejecuta agent.run(prompt)                              │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Smolagents Agent (ToolCallingAgent O CodeAgent)          │
│    - LLM lee el prompt y decide qué herramientas llamar     │
│    - ToolCallingAgent: Una herramienta por turno LLM        │
│    - CodeAgent: Múltiples herramientas vía código Python    │
│    - Para cada llamada de herramienta:                      │
│      a. Agente genera nombre de herramienta + parámetros    │
│      b. Wrapper de herramienta (tools.py) se invoca         │
│      c. Wrapper llama al cliente MCP                        │
│      d. Cliente MCP envía solicitud al servidor MCP         │
│      e. Servidor ejecuta herramienta, retorna datos         │
│      f. Datos retornados al agente                          │
│    - Agente sintetiza todos los resultados                  │
│    - Agente genera informe markdown final                   │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Respuesta                                                │
│    - Informe markdown retornado a FastAPI                   │
│    - FastAPI envuelve en respuesta JSON                     │
│    - Streamlit muestra informe formateado                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Referencia de Módulos

### 1. `main.py` - ToolCallingAgent

**Implementación basada en JSON para entornos productivos estables**

#### Función Principal
```python
async def run_stock_analysis(ticker: str, llm_provider: str = "openai")
```

**Parámetros:**
- `ticker`: Símbolo del ticker (ej: "AAPL", "MSFT")
- `llm_provider`: Proveedor LLM ("openai" o "huggingface")

**Características:**
- ✅ **Una herramienta por turno**: Llamadas de herramientas controladas paso a paso
- ✅ **Depuración determinista**: Salida JSON predecible
- ✅ **Manejo robusto de errores**: Menor riesgo de fallos en tiempo de ejecución
- ⚠️ **Velocidad moderada**: Múltiples llamadas LLM para análisis complejos

**Caso de Uso Ideal:**
```python
# Mejor para análisis de un solo ticker
result = await run_stock_analysis("AAPL", "openai")
```

---

### 2. `main_codeagent.py` - CodeAgent

**Implementación basada en código Python para análisis de alto rendimiento**

#### Función Principal
```python
async def run_stock_analysis_with_code_agent(
    ticker: str, 
    llm_provider: str = "openai",
    executor: str = "local"
)
```

**Parámetros:**
- `ticker`: Símbolo del ticker (ej: "AAPL", "MSFT")
- `llm_provider`: Proveedor LLM ("openai" o "huggingface")
- `executor`: Tipo de executor
  - `"local"`: Ejecución directa de Python (desarrollo)
  - `"e2b"`: E2B sandbox en la nube (producción)
  - `"docker"`: Contenedor Docker (producción autohospedada)

**Características:**
- 🚀 **Múltiples herramientas por turno**: Ejecuta 3-5 herramientas en bucles
- 🚀 **2-3x más rápido**: Mejoras del 50-66% en análisis multi-ticker
- ⚠️ **Sandbox obligatorio en producción**: Requiere e2b o Docker para seguridad
- ⚠️ **Depuración compleja**: Rastreo de código Python generado dinámicamente

**Caso de Uso Ideal:**
```python
# Mejor para análisis de múltiples tickers o complejo
# Desarrollo
result = await run_stock_analysis_with_code_agent("AAPL", "openai", "local")

# Producción (E2B)
result = await run_stock_analysis_with_code_agent("AAPL", "openai", "e2b")

# Producción (Docker)
result = await run_stock_analysis_with_code_agent("AAPL", "openai", "docker")
```

---

### 3. `api.py` - Endpoints FastAPI

### Flujo de Ejecución de Herramientas

Cuando el agente decide llamar una herramienta:

```
Decisión del Agente: "Necesito llamar bollinger_fibonacci_analysis para AAPL"
          │
          ▼
    ┌─────────────────────────────────────────────┐
    │ @tool                                       │
    │ def bollinger_fibonacci_analysis(symbol):   │
    │     return _call_finance_tool(              │
    │         "analyze_bollinger_fibonacci_...",  │
    │         {"symbol": symbol, "period": "1y"}  │
    │     )                                       │
    └─────────────────────────────────────────────┘
          │
          ▼
    ┌─────────────────────────────────────────────┐
    │ _call_finance_tool()                        │
    │     session = get_session()                 │
    │     return session.call_tool(name, params)  │
    └─────────────────────────────────────────────┘
          │
          ▼
    ┌─────────────────────────────────────────────┐
    │ MCPFinanceSession.call_tool()               │
    │     # Envía JSON-RPC al servidor MCP        │
    │     # vía transporte stdio                  │
    └─────────────────────────────────────────────┘
          │
          ▼
    ┌─────────────────────────────────────────────┐
    │ Servidor MCP (server/main.py)               │
    │     # Ejecuta cálculo de estrategia         │
    │     # Retorna datos de rendimiento          │
    └─────────────────────────────────────────────┘
          │
          ▼
    Los datos fluyen de vuelta al agente
```

---

## Instalación

### Prerrequisitos

- Python 3.10+
- Servidor MCP (carpeta `server/` en la raíz del proyecto)
- Clave API de OpenAI (o token de HuggingFace)

### Dependencias

```bash
pip install smolagents fastapi uvicorn streamlit requests python-dotenv mcp
```

### Inicio Rápido

```bash
# 1. Iniciar el backend FastAPI
uvicorn stock_analyzer_bot.api:app --reload --port 8000

# 2. (Opcional) Iniciar frontend Streamlit
streamlit run streamlit_app.py

# 3. (Opcional) Ejecutar análisis CLI
python -m stock_analyzer_bot.main AAPL --period 1y
```

---

## Configuración

### Variables de Entorno

Crear un archivo `.env` en la raíz del proyecto:

```bash
# Configuración LLM
OPENAI_API_KEY=sk-tu-clave-openai-aqui
OPENAI_BASE_URL=                      # Opcional: para endpoints personalizados
HF_TOKEN=hf_tu-token-huggingface      # Para modelos HuggingFace

# Configuración de Agente (NUEVO)
SMOLAGENT_AGENT_TYPE=tool_calling     # "tool_calling" o "code_agent"
SMOLAGENT_EXECUTOR=local              # Para CodeAgent: "local" | "e2b" | "docker"

# Valores Predeterminados del Modelo
SMOLAGENT_MODEL_ID=gpt-4.1            # Modelo predeterminado
SMOLAGENT_MODEL_PROVIDER=litellm       # litellm o inference
SMOLAGENT_MAX_STEPS=25                 # Máx iteraciones del agente

# Configuración de Executor de CodeAgent
E2B_API_KEY=e2b_tu-clave-api          # Necesario para executor="e2b"
DOCKER_IMAGE=python:3.11-slim         # Necesario para executor="docker"

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
