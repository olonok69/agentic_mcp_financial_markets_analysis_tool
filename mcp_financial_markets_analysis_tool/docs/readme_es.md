# Financial Analysis MCP Server

Un servidor completo de Model Context Protocol (MCP) que proporciona herramientas avanzadas de análisis técnico para mercados financieros. Este servidor se integra con Claude Desktop para entregar análisis sofisticados de estrategias de trading, backtesting de rendimiento y capacidades de escaneo de mercado.

## 🚀 Características

### Estrategias de Trading Principales
- **Bollinger Z-Score Analysis** - Estrategia de mean reversion usando Z-scores estadísticos
- **Bollinger-Fibonacci Strategy** - Análisis de support/resistance combinando Bollinger Bands con Fibonacci retracements
- **MACD-Donchian Combined** - Estrategia de momentum y breakout usando MACD y Donchian channels
- **Connors RSI + Z-Score** - Momentum de corto plazo con análisis de mean reversion
- **Dual Moving Average** - Estrategia de trend-following con crossovers de EMA

### Capacidades de Análisis
- **Performance Backtesting** - Comparar returns de estrategias vs buy-and-hold
- **Market Scanner** - Analizar múltiples acciones simultáneamente
- **Risk Assessment** - Análisis de volatility, Sharpe ratios y drawdown
- **Signal Generation** - Recomendaciones de buy/sell/hold en tiempo real
- **Comprehensive Reporting** - Reportes detallados en markdown con razonamiento

### Cobertura de Mercado
- Análisis de acciones individuales
- Escaneo de portfolios multi-stock
- Análisis específico por sectores (Banking, Technology, Clean Energy/EV)
- Ranking y comparación de performance

## 📋 Requisitos Previos

- **Python 3.11+** con package manager `uv`
- **Claude Desktop** con soporte MCP
- **Anthropic API Key** (para integración con Claude)
- **Conexión a internet** (para datos de mercado en tiempo real vía Yahoo Finance)

## 🛠️ Instalación

### 1. Clonar y Configurar Proyecto
```bash
# Crear directorio del proyecto
mkdir financial-mcp-server
cd financial-mcp-server

# Inicializar con uv
uv init .

# Instalar dependencias principales
uv add mcp fastmcp yfinance pandas numpy anthropic python-dotenv

# Instalar dependencias adicionales de análisis
uv add python-docx docx2pdf scipy scikit-learn
```

### 2. Estructura del Proyecto
```
financial-mcp-server/
├── server/
│   ├── main.py                     # Punto de entrada principal del servidor MCP
│   ├── strategies/                 # Módulos de estrategias de trading
│   │   ├── __init__.py
│   │   ├── bollinger_zscore.py     # Z-Score mean reversion
│   │   ├── bollinger_fibonacci.py  # Estrategia Bollinger-Fibonacci
│   │   ├── macd_donchian.py       # MACD-Donchian momentum
│   │   ├── connors_zscore.py      # Análisis Connors RSI
│   │   ├── dual_moving_average.py # Estrategia EMA crossover
│   │   ├── performance_tools.py   # Herramientas de comparación de performance
│   │   ├── comprehensive_analysis.py # Análisis multi-estrategia
│   │   └── unified_market_scanner.py # Herramientas de escaneo de mercado
│   └── utils/
│       ├── __init__.py
│       └── yahoo_finance_tools.py  # Utilidades de datos de mercado
├── .env                           # Variables de entorno
├── .gitignore                     # Archivo Git ignore
└── README.md                      # Este archivo
```

### 3. Configuración de Entorno
Crear un archivo `.env`:
```bash
# No requerido para este servidor, pero útil para extensiones
ANTHROPIC_API_KEY=tu_anthropic_api_key_aqui
```

Crear `.gitignore`:
```gitignore
# Archivos generados por Python
__pycache__/
*.py[oc]
build/
dist/
wheels/
*.egg-info

# Entornos virtuales
.venv
.env
.lock
```

### 4. Configuración de Claude Desktop

Agregar a tu archivo de configuración MCP de Claude Desktop:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "financial-analysis": {
      "command": "uv",
      "args": ["run", "python", "server/main.py"],
      "cwd": "/ruta/a/tu/financial-mcp-server"
    }
  }
}
```

## 🎯 Ejemplos de Uso

### Análisis de Acción Individual

```
Analizar TSLA usando las 5 estrategias técnicas con comparación de performance durante un período de 1 año
```

### Escaneo de Mercado

```
Usar market scanner con símbolos "AAPL, MSFT, GOOGL, META, NVDA" con período "1y" y output_format "detailed"
```

### Análisis Sectorial

```
Escanear estas acciones bancarias: JPM, BAC, WFC, C, GS, MS, USB, PNC, TFC, COF
```

### Análisis Específico por Estrategia

```
Para Tesla:
- Calcular Bollinger Z-Score con período de 20 días
- Analizar estrategia MACD-Donchian con período de 1 año
- Comparar performance de dual moving average usando EMA 50/200
```

## 📊 Herramientas Disponibles

### Herramientas de Análisis Principal

| Herramienta | Descripción | Parámetros |
|-------------|-------------|------------|
| `calculate_bollinger_z_score` | Análisis de mean reversion Z-Score | `symbol`, `period` |
| `calculate_bollinger_fibonacci_score` | Estrategia Bollinger-Fibonacci | `symbol`, `period`, `window` |
| `calculate_combined_score_macd_donchian` | MACD-Donchian momentum | `symbol`, `period`, `window` |
| `calculate_combined_connors_zscore_tool` | Connors RSI + Z-Score | `symbol`, `period`, `weights` |
| `analyze_dual_ma_strategy` | Moving average crossovers | `symbol`, `period`, `ma_type` |

### Herramientas de Análisis de Performance

| Herramienta | Descripción | Parámetros |
|-------------|-------------|------------|
| `analyze_bollinger_zscore_performance` | Backtest estrategia Z-Score | `symbol`, `period`, `window` |
| `analyze_bollinger_fibonacci_performance` | Backtest Bollinger-Fibonacci | `symbol`, `period`, `window` |
| `analyze_macd_donchian_performance` | Backtest MACD-Donchian | `symbol`, `period`, `fast/slow` |
| `analyze_connors_zscore_performance` | Backtest estrategia Connors RSI | `symbol`, `period`, `weights` |

### Herramientas de Escaneo de Mercado

| Herramienta | Descripción | Parámetros |
|-------------|-------------|------------|
| `market_scanner` | Análisis unificado de mercado | `symbols`, `period`, `output_format` |
| `comprehensive_strategy_analysis` | Comparación multi-estrategia | `symbol`, `period` |

## 📈 Reportes de Ejemplo

### Análisis de Acción Individual
El servidor genera reportes comprensivos como este [ejemplo de análisis de Tesla](reports_Example/tesla_technical_analysis.md):

- **Executive Summary** con recomendación general
- **Individual Strategy Analysis** con scores y signals
- **Performance Comparison** vs buy-and-hold
- **Current Signal Status** con niveles de confianza
- **Risk Assessment** y position sizing

### Análisis Sectorial
Reportes sectoriales detallados como este [análisis del Sector Bancario](reports_Example/banking_sector_comprehensive_analysis.md):

- **Performance Summary Table** con todas las acciones
- **Strategy Effectiveness Rankings**
- **Individual Stock Breakdowns**
- **Risk Management Framework**
- **Final Investment Recommendations**

### Análisis Multi-Sectorial
Reportes comprensivos de mercado como este [análisis Multi-Sectorial](reports_Example/multi_sector_analysis_report.md):

- **Cross-Sector Performance Overview**
- **Priority Investment Recommendations**
- **Portfolio Construction Framework**
- **Market Outlook & Strategic Themes**

## 🔧 Arquitectura Técnica

### Integración MCP
Este servidor usa el framework **FastMCP** para integración perfecta con Claude Desktop:

```python
from mcp.server.fastmcp import FastMCP

# Inicializar servidor MCP
mcp = FastMCP("finance tools", "1.0.0")

# Registrar herramientas de estrategias
register_bollinger_fibonacci_tools(mcp)
register_macd_donchian_tools(mcp)
# ... otras estrategias

if __name__ == "__main__":
    mcp.run(transport='stdio')
```

### Implementación de Estrategias
Cada estrategia sigue un patrón consistente:

1. **Data Acquisition** - Integración con Yahoo Finance API
2. **Indicator Calculation** - Cálculos de análisis técnico
3. **Signal Generation** - Recomendaciones de buy/sell/hold
4. **Performance Backtesting** - Validación histórica de estrategias
5. **Report Generation** - Salida estructurada en markdown

### Cálculo de Performance
El servidor implementa métricas comprensivas de performance:

```python
def calculate_strategy_performance_metrics(signals_data, signal_column):
    # Calcular returns, volatility, Sharpe ratios
    # Generar win rates y análisis de drawdown
    # Comparar vs baseline de buy-and-hold
    return performance_metrics
```

## ⚙️ Opciones de Configuración

### Períodos de Tiempo
- **Períodos válidos:** `1d`, `5d`, `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `10y`, `ytd`, `max`

### Parámetros de Estrategias
- **Bollinger Bands:** Window (default: 20), Standard deviations (default: 2)
- **MACD:** Fast period (12), Slow period (26), Signal period (9)
- **Moving Averages:** Short period (50), Long period (200), Type (SMA/EMA)
- **Z-Score:** Window para cálculo de mean/std (default: 20)

### Formatos de Salida
- **detailed:** Análisis completo con todas las métricas
- **summary:** Resumen condensado con hallazgos clave
- **executive:** Resumen de alto nivel para tomadores de decisiones

## 🚨 Disclaimers de Riesgo

⚠️ **Importante:** Esta herramienta es solo para propósitos educativos e informativos.

- **No es Asesoría Financiera:** Todo análisis debe ser verificado independientemente
- **Performance Pasado:** No garantiza resultados futuros
- **Riesgo de Mercado:** Todo trading involucra riesgo sustancial de pérdidas
- **Limitaciones de Estrategias:** El análisis técnico tiene limitaciones inherentes
- **Precisión de Datos:** Los datos de mercado son proporcionados por Yahoo Finance

## 🔍 Solución de Problemas

### Problemas Comunes

**Problemas de Conexión:**
- Verificar rutas de scripts del servidor en configuración de Claude Desktop
- Comprobar que entornos de Python/uv estén configurados correctamente
- Asegurar que todas las dependencias estén instaladas

**Problemas de Performance:**
- Las primeras respuestas pueden tomar 30+ segundos (normal para descarga de datos)
- Las respuestas subsiguientes son típicamente más rápidas
- Considerar usar períodos de tiempo más cortos para análisis más rápido

**Problemas de Datos:**
- Verificar que los símbolos ticker sean correctos y se negocien activamente
- Comprobar conectividad a internet para acceso a Yahoo Finance
- Algunas herramientas requieren períodos mínimos de datos (ej. MA de 200 días necesita 200+ días)

### Modo Debug
Habilitar logging detallado modificando el servidor:

```python
import sys
print(f"Analyzing {symbol}...", file=sys.stderr)
```

## 🤝 Contribuciones

### Agregar Nuevas Estrategias
1. Crear nuevo módulo de estrategia en `server/strategies/`
2. Implementar función de análisis principal
3. Agregar capacidad de performance backtesting
4. Registrar con servidor MCP principal
5. Agregar documentación comprensiva

### Extender Análisis
- Agregar nuevos indicadores técnicos
- Implementar métricas adicionales de riesgo
- Crear herramientas de análisis específicas por sector
- Mejorar formatos de reportes

## 📚 Recursos Adicionales

### Model Context Protocol (MCP)
- [Documentación Oficial de MCP](https://modelcontextprotocol.io/)
- [Conceptos y Arquitectura de MCP](https://modelcontextprotocol.io/docs/concepts/)
- [Framework FastMCP](https://github.com/jlowin/fastmcp)

### Recursos de Análisis Técnico
- **Bollinger Bands:** Canales estadísticos de precio para análisis de volatility
- **MACD:** Moving Average Convergence Divergence para momentum
- **Fibonacci Retracements:** Support/resistance basado en ratios matemáticos
- **Connors RSI:** Indicador de mean reversion de corto plazo
- **Donchian Channels:** Análisis de breakout usando rangos de precio

### Datos de Mercado
- **Yahoo Finance:** Datos de mercado históricos y en tiempo real gratuitos
- **Cobertura de Datos:** Acciones globales, índices, divisas, commodities
- **Limitaciones de API:** Rate limits y restricciones de disponibilidad de datos

## 📄 Licencia

Este proyecto se proporciona para propósitos educativos. Por favor revisar y cumplir con:
- Términos de Servicio de Yahoo Finance para uso de datos de mercado
- Términos de Servicio de Anthropic para uso de Claude API
- Regulaciones locales respecto a herramientas de análisis financiero

---

**Construido con:** Python, FastMCP, Yahoo Finance API, Claude Desktop
**Autor:** Financial Analysis MCP Server
**Versión:** 1.0.0