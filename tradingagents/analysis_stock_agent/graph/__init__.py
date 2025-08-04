"""
A股分析LangGraph工作流

基于LangGraph构建的A股分析多智能体工作流，编排四个专业Agent的执行：
1. FinancialMetricsAgent - 财务指标分析
2. IndustryComparisonAgent - 行业对比分析  
3. ValuationAnalysisAgent - 估值分析
4. ReportIntegrationAgent - 报告整合

支持并行执行前三个Agent，然后由第四个Agent进行整合
"""

from typing import Dict, Any, List
from datetime import datetime

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage

# 导入Agent状态
from tradingagents.analysis_stock_agent.state import AShareAnalysisState

# 导入Agent创建函数
from tradingagents.analysis_stock_agent.agents import (
    create_financial_metrics_agent,
    create_industry_comparison_agent,
    create_valuation_analysis_agent,
    create_report_integration_agent
)

# 导入统一日志系统
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('ashare_analysis_graph')


class AShareAnalysisGraph:
    """A股分析LangGraph工作流"""
    
    def __init__(self, llm, toolkit, config: Dict[str, Any] = None):
        """
        初始化A股分析图
        
        Args:
            llm: 语言模型
            toolkit: 工具集
            config: 配置字典
        """
        self.llm = llm
        self.toolkit = toolkit
        self.config = config or {}
        
        # 创建Agent节点
        self.financial_agent = create_financial_metrics_agent(llm, toolkit)
        self.industry_agent = create_industry_comparison_agent(llm, toolkit)
        self.valuation_agent = create_valuation_analysis_agent(llm, toolkit)
        self.integration_agent = create_report_integration_agent(llm, toolkit)
        
        # 构建图
        self.graph = self._build_graph()
        
        logger.info(f"🔧 [A股分析图] 初始化完成")
    
    def _build_graph(self) -> StateGraph:
        """构建LangGraph工作流图"""
        
        # 创建状态图
        graph = StateGraph(AShareAnalysisState)
        
        # 添加节点
        graph.add_node("financial_metrics", self.financial_agent)
        graph.add_node("industry_comparison", self.industry_agent)
        graph.add_node("valuation_analysis", self.valuation_agent)
        graph.add_node("report_integration", self.integration_agent)
        
        # 添加边：并行执行前三个分析，然后整合
        graph.add_edge(START, "financial_metrics")
        graph.add_edge(START, "industry_comparison")
        graph.add_edge(START, "valuation_analysis")
        
        # 所有分析完成后进行报告整合
        graph.add_edge("financial_metrics", "report_integration")
        graph.add_edge("industry_comparison", "report_integration")
        graph.add_edge("valuation_analysis", "report_integration")
        
        # 整合完成后结束
        graph.add_edge("report_integration", END)
        
        # 编译图
        compiled_graph = graph.compile()
        
        logger.info(f"🔧 [A股分析图] 工作流图构建完成")
        return compiled_graph
    
    def analyze_stock(
        self, 
        ticker: str, 
        analysis_date: str = None,
        analysis_depth: str = "standard",
        enable_cache: bool = True
    ) -> Dict[str, Any]:
        """
        分析A股股票
        
        Args:
            ticker: 股票代码
            analysis_date: 分析日期
            analysis_depth: 分析深度 (basic/standard/comprehensive)
            enable_cache: 是否启用缓存
            
        Returns:
            Dict: 分析结果
        """
        
        if not analysis_date:
            analysis_date = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"📈 [A股分析图] 开始分析股票: {ticker}")
        logger.info(f"📈 [A股分析图] 分析参数: 日期={analysis_date}, 深度={analysis_depth}, 缓存={enable_cache}")
        
        try:
            # 创建初始状态
            initial_state = {
                "ticker": ticker,
                "analysis_date": analysis_date,
                "analysis_depth": analysis_depth,
                "enable_cache": enable_cache,
                "data_sources": self.config.get("data_sources", ["tushare", "akshare"]),
                "messages": [HumanMessage(content=f"请分析A股股票 {ticker}")],
                "completed_agents": [],
                "error_messages": [],
                "start_time": datetime.now(),
                "agent_timings": {}
            }
            
            # 执行工作流
            logger.info(f"📈 [A股分析图] 开始执行多智能体工作流...")
            result = self.graph.invoke(initial_state)
            
            # 处理结果
            logger.info(f"📈 [A股分析图] 工作流执行完成")
            self._log_execution_summary(result)
            
            return result
            
        except Exception as e:
            error_msg = f"❌ A股分析执行失败: {str(e)}"
            logger.error(error_msg)
            return {
                "ticker": ticker,
                "analysis_date": analysis_date,
                "error_messages": [error_msg],
                "success": False
            }
    
    def _log_execution_summary(self, result: Dict[str, Any]):
        """记录执行摘要"""
        try:
            ticker = result.get("ticker", "未知")
            
            # 检查各Agent的执行结果
            financial_success = bool(result.get("financial_analysis"))
            industry_success = bool(result.get("industry_analysis"))
            valuation_success = bool(result.get("valuation_analysis"))
            integration_success = bool(result.get("integration_report"))
            
            # 记录摘要
            logger.info(f"📊 [执行摘要] 股票: {ticker}")
            logger.info(f"📊 [执行摘要] 财务分析: {'✅' if financial_success else '❌'}")
            logger.info(f"📊 [执行摘要] 行业分析: {'✅' if industry_success else '❌'}")
            logger.info(f"📊 [执行摘要] 估值分析: {'✅' if valuation_success else '❌'}")
            logger.info(f"📊 [执行摘要] 报告整合: {'✅' if integration_success else '❌'}")
            
            # 记录错误信息
            error_messages = result.get("error_messages", [])
            if error_messages:
                logger.warning(f"⚠️ [执行摘要] 发现 {len(error_messages)} 个错误")
                for i, error in enumerate(error_messages[:3]):  # 只显示前3个错误
                    logger.warning(f"⚠️ [执行摘要] 错误 {i+1}: {error}")
            
            # 记录投资建议
            investment_recommendation = result.get("investment_recommendation")
            if investment_recommendation:
                logger.info(f"💡 [执行摘要] 投资建议: {investment_recommendation}")
            
            # 记录执行时间
            start_time = result.get("start_time")
            if start_time:
                duration = (datetime.now() - start_time).total_seconds()
                logger.info(f"⏱️ [执行摘要] 总执行时间: {duration:.1f}秒")
                
        except Exception as e:
            logger.error(f"❌ 记录执行摘要失败: {e}")
    
    def get_analysis_status(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """获取分析状态摘要"""
        try:
            return {
                "ticker": result.get("ticker", "未知"),
                "analysis_date": result.get("analysis_date", "未知"),
                "completed_agents": result.get("completed_agents", []),
                "error_count": len(result.get("error_messages", [])),
                "has_financial_analysis": bool(result.get("financial_analysis")),
                "has_industry_analysis": bool(result.get("industry_analysis")),
                "has_valuation_analysis": bool(result.get("valuation_analysis")),
                "has_integration_report": bool(result.get("integration_report")),
                "investment_recommendation": result.get("investment_recommendation"),
                "confidence_score": result.get("confidence_score", 0.0),
                "success": bool(result.get("integration_report")) and len(result.get("error_messages", [])) == 0
            }
        except Exception as e:
            logger.error(f"❌ 获取分析状态失败: {e}")
            return {
                "ticker": "错误", 
                "success": False,
                "error": str(e)
            }


def create_ashare_analysis_graph(llm, toolkit, config: Dict[str, Any] = None) -> AShareAnalysisGraph:
    """
    创建A股分析图的工厂函数
    
    Args:
        llm: 语言模型
        toolkit: 工具集
        config: 配置字典
        
    Returns:
        AShareAnalysisGraph: A股分析图实例
    """
    return AShareAnalysisGraph(llm, toolkit, config)