"""
A股分析多智能体系统

这个模块实现了专门针对A股市场的多智能体分析系统，包含四个核心分析Agent：
1. FinancialMetricsAgent - 财务指标分析
2. IndustryComparisonAgent - 行业对比分析  
3. ValuationAnalysisAgent - 估值分析
4. ReportIntegrationAgent - 报告整合

基于TradingAgents-CN框架构建，支持：
- 基于LangGraph的Agent协作
- 多数据源集成（Tushare、AkShare）
- 多层缓存优化
- 金字塔原理报告结构
"""

from .agents.financial_metrics_agent import create_financial_metrics_agent
from .agents.industry_comparison_agent import create_industry_comparison_agent
from .agents.valuation_analysis_agent import create_valuation_analysis_agent
from .agents.report_integration_agent import create_report_integration_agent

from .tools.ashare_data_tools import AShareDataTools
from .state.ashare_analysis_state import AShareAnalysisState
from .graph.ashare_analysis_graph import AShareAnalysisGraph

__version__ = "1.0.0"

__all__ = [
    # Agents
    "create_financial_metrics_agent",
    "create_industry_comparison_agent", 
    "create_valuation_analysis_agent",
    "create_report_integration_agent",
    
    # Tools
    "AShareDataTools",
    
    # State Management
    "AShareAnalysisState",
    
    # Graph
    "AShareAnalysisGraph",
]