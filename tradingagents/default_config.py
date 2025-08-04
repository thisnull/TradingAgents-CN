import os

DEFAULT_CONFIG = {
    "project_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
    "results_dir": os.getenv("TRADINGAGENTS_RESULTS_DIR", "./results"),
    "data_dir": os.path.join(os.path.expanduser("~"), "Documents", "TradingAgents", "data"),
    "data_cache_dir": os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
        "dataflows/data_cache",
    ),
    # LLM settings
    "llm_provider": "openai",
    "deep_think_llm": "o4-mini",
    "quick_think_llm": "gpt-4o-mini",
    "backend_url": "https://api.openai.com/v1",
    # Debate and discussion settings
    "max_debate_rounds": 1,
    "max_risk_discuss_rounds": 1,
    "max_recur_limit": 100,
    # Tool settings
    "online_tools": True,

    # A股分析多智能体系统配置
    "ashare_analysis": {
        "enabled": os.getenv("ASHARE_ANALYSIS_ENABLED", "true").lower() == "true",
        "default_analysis_depth": os.getenv("ASHARE_DEFAULT_DEPTH", "standard"),
        "max_concurrent_analyses": int(os.getenv("ASHARE_MAX_CONCURRENT", "3")),
        "cost_limit_per_analysis_cny": float(os.getenv("ASHARE_COST_LIMIT_CNY", "5.0")),
        "max_tokens_per_analysis": int(os.getenv("ASHARE_MAX_TOKENS", "8000")),
        "cache_enabled": os.getenv("ASHARE_CACHE_ENABLED", "true").lower() == "true",
        "debug_mode": os.getenv("ASHARE_DEBUG_MODE", "false").lower() == "true",
        # 数据源配置
        "data_sources": {
            "tushare": {
                "enabled": os.getenv("TUSHARE_ENABLED", "false").lower() == "true",
                "priority": 1,
                "api_key": os.getenv("TUSHARE_TOKEN", ""),
            },
            "akshare": {
                "enabled": os.getenv("AKSHARE_ENABLED", "true").lower() == "true", 
                "priority": 2,
                "api_key": "",  # AkShare不需要API密钥
            }
        },
        # Agent配置
        "agents": {
            "financial_metrics": {
                "enabled": True,
                "max_tokens": 2000,
                "timeout_seconds": 300
            },
            "industry_comparison": {
                "enabled": True,
                "max_tokens": 2000,
                "timeout_seconds": 300
            },
            "valuation_analysis": {
                "enabled": True,
                "max_tokens": 2000,
                "timeout_seconds": 300
            },
            "report_integration": {
                "enabled": True,
                "max_tokens": 3000,
                "timeout_seconds": 600
            }
        }
    },

    # Note: Database and cache configuration is now managed by .env file and config.database_manager
    # No database/cache settings in default config to avoid configuration conflicts
}
