# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TradingAgents-CN is a Chinese-enhanced multi-agent AI trading framework based on TradingAgents. It provides comprehensive stock analysis for A-shares, Hong Kong stocks, and US stocks using multiple LLM providers and specialized analysis agents.

## Development Commands

### Package Management
```bash
# Install project and dependencies
pip install -e .

# Alternative using uv (faster)
uv pip install -e .

# Install from requirements (deprecated - use pyproject.toml)
pip install -r requirements.txt
```

### Running the Application

#### Web Interface (Primary)
```bash
# Recommended method
python start_web.py

# Alternative methods
python web/run_web.py
streamlit run web/app.py
```

#### CLI Interface
```bash
# Interactive CLI
python -m cli.main

# Direct analysis
python main.py
```

#### Docker Deployment
```bash
# Build and start all services
docker-compose up -d --build

# Start without building
docker-compose up -d

# Smart start scripts (auto-detects changes)
# Windows:
powershell -ExecutionPolicy Bypass -File scripts\smart_start.ps1
# Linux/Mac:
./scripts/smart_start.sh

# View logs
docker-compose logs -f web
```

### Testing and Development
```bash
# Run tests
python tests/test_analysis.py
python tests/integration/test_dashscope_integration.py

# Configuration check
python scripts/validation/check_system_status.py

# Database initialization
python scripts/setup/init_database.py

# Cache cleanup
python scripts/maintenance/cleanup_cache.py --days 7
```

### Useful Scripts
```bash
# Check API configurations
python scripts/check_api_config.py

# Test data sources
python tests/test_data_sources_comprehensive.py

# Debug specific stocks
python tests/test_601127_final.py  # For A-shares
python tests/test_hk_simple.py    # For HK stocks
```

## Architecture Overview

### Core Components

1. **Multi-Agent System (`tradingagents/agents/`)**:
   - **Analysts**: Market, fundamentals, news, social media analysts
   - **Researchers**: Bull/bear researchers for debate-based analysis
   - **Trader**: Final decision maker
   - **Managers**: Research and risk managers

2. **Data Layer (`tradingagents/dataflows/`)**:
   - **Data Sources**: Tushare, AkShare, FinnHub, Yahoo Finance
   - **Cache Management**: Multi-layer caching (Redis, MongoDB, file)
   - **APIs**: Unified interfaces for different data providers

3. **LLM Integration (`tradingagents/llm_adapters/`)**:
   - **Multiple Providers**: DashScope (Alibaba), DeepSeek, Google AI, OpenAI
   - **Adapters**: Unified interface for different LLM APIs
   - **Cost Optimization**: Token tracking and intelligent model selection

4. **Graph Orchestration (`tradingagents/graph/`)**:
   - **Trading Graph**: Main orchestration using LangGraph
   - **Conditional Logic**: Dynamic workflow based on analysis requirements
   - **Signal Processing**: Agent communication and result aggregation

### Key Files

- `tradingagents/graph/trading_graph.py`: Main orchestration class
- `tradingagents/default_config.py`: Default configuration settings
- `web/app.py`: Streamlit web interface
- `cli/main.py`: Command-line interface
- `main.py`: Simple analysis entry point

### Configuration Management

Configuration is handled through multiple layers:
1. Environment variables (`.env` file)
2. Configuration classes (`tradingagents/config/`)
3. Runtime parameters passed to `TradingAgentsGraph`

Key configuration areas:
- **LLM Provider**: `llm_provider` (dashscope, google, openai, deepseek)
- **Models**: `deep_think_llm`, `quick_think_llm`
- **Data Sources**: Tushare, AkShare, FinnHub API keys
- **Databases**: MongoDB, Redis connection settings
- **Analysis Depth**: Research levels 1-5, debate rounds

### Data Flow

1. **Input**: Stock symbol + analysis date
2. **Data Collection**: Multi-source data aggregation with intelligent fallback
3. **Agent Analysis**: Parallel execution of selected analysts
4. **Research Phase**: Bull/bear researcher debate
5. **Risk Assessment**: Multi-dimensional risk evaluation
6. **Final Decision**: Trader agent synthesizes all inputs
7. **Output**: Structured investment recommendation with confidence scores

### Chinese Market Specialization

- **A-Share Support**: Complete integration with Chinese stock exchanges
- **Data Sources**: Tushare (professional), AkShare (comprehensive), TDX (real-time)
- **Chinese LLMs**: DashScope (Alibaba Qwen), DeepSeek integration
- **Localization**: Chinese interface, market-specific analysis patterns
- **News Analysis**: Chinese financial news processing and sentiment analysis

### Testing Strategy

Tests are organized by functionality:
- `tests/integration/`: Full workflow tests
- `tests/test_*_integration.py`: Component integration tests
- `tests/test_*_debug.py`: Debug and troubleshooting tests
- `tests/quick_*.py`: Fast validation tests

### Common Development Patterns

1. **Adding New Analysts**: Extend base analyst classes in `tradingagents/agents/analysts/`
2. **Data Source Integration**: Implement interfaces in `tradingagents/dataflows/`
3. **LLM Provider Addition**: Create adapters in `tradingagents/llm_adapters/`
4. **Configuration Extension**: Modify `default_config.py` and environment handling

### Important Notes

- The project uses a deprecation notice in `requirements.txt` - prefer `pip install -e .`
- Web interface runs on port 8501 by default
- Docker deployment includes MongoDB (27017), Redis (6379), and management UIs
- Logging is centralized through `tradingagents/utils/logging_manager.py`
- Memory/ChromaDB has Windows 10 compatibility issues - use fallback configs
- Cost tracking is built-in for all LLM providers with detailed token usage reports

### Troubleshooting

Common issues and solutions:
- **Module import errors**: Ensure `pip install -e .` has been run
- **Windows 10 ChromaDB issues**: Set `MEMORY_ENABLED=false` in `.env`
- **API rate limits**: Use data directory configuration to cache results
- **Docker port conflicts**: Modify docker-compose.yml port mappings
- **Missing dependencies**: Run dependency check scripts in `scripts/validation/`