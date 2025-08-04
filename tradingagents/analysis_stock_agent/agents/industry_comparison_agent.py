"""
行业对比分析Agent

专门负责A股公司的行业对比分析，包括：
1. 行业历史业绩增长分析
2. 行业盈利能力对比分析
3. 与行业头部企业竞争力对比

基于现有框架的Agent模式实现
"""

from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# 导入统一日志系统
from tradingagents.utils.logging_manager import get_logger
from tradingagents.utils.tool_logging import log_analyst_module

logger = get_logger('industry_comparison_agent')


def create_industry_comparison_agent(llm, toolkit):
    """
    创建行业对比分析Agent
    
    Args:
        llm: 语言模型
        toolkit: 工具集
        
    Returns:
        function: Agent节点函数
    """
    
    @log_analyst_module("industry_comparison")
    def industry_comparison_agent_node(state):
        """行业对比分析Agent节点"""
        
        logger.info(f"🏭 [行业对比分析师] 开始分析")
        
        # 获取基本参数
        ticker = state.get("ticker")
        analysis_date = state.get("analysis_date")
        analysis_depth = state.get("analysis_depth", "standard")
        
        if not ticker:
            error_msg = "❌ 缺少必要参数：股票代码"
            logger.error(error_msg)
            return {"error_messages": [error_msg]}
        
        logger.info(f"🏭 [行业对比分析师] 分析目标: {ticker}, 日期: {analysis_date}, 深度: {analysis_depth}")
        
        try:
            # 获取A股数据工具
            from tradingagents.analysis_stock_agent.tools import AShareDataTools
            ashare_tools = AShareDataTools(toolkit.config)
            
            # 强制获取行业对比数据
            industry_data = ashare_tools.get_ashare_industry_comparison(ticker)
            
            # 生成行业对比分析报告
            analysis_prompt = f"""基于以下真实行业对比数据，对{ticker}进行专业的行业对比分析：

{industry_data}

请按照以下结构提供详细分析：

## 行业对比分析报告

### 执行摘要
- 行业地位评级：（领先/优秀/一般/落后）
- 竞争优势：
- 竞争劣势：
- 行业前景：

### 行业增长趋势分析
基于真实数据分析行业整体增长趋势和公司在其中的位置

### 盈利能力行业对比
基于真实数据对比毛利率、净利率、ROE等关键指标

### 与头部企业对比
与行业前3名企业的详细对比分析

### 竞争优势评估
识别公司相对于行业平均和头部企业的竞争优势

### 行业风险评估
分析行业整体风险和公司特定风险

要求：
- 所有分析必须基于提供的真实数据
- 提供具体的行业排名和对比数值
- 给出明确的行业地位评价
- 识别具体的竞争优势和劣势"""

            # 检测模型类型并创建分析链
            if hasattr(llm, '__class__') and 'DashScope' in llm.__class__.__name__:
                from tradingagents.llm_adapters import ChatDashScopeOpenAI
                fresh_llm = ChatDashScopeOpenAI(
                    model=llm.model_name,
                    temperature=llm.temperature,
                    max_tokens=getattr(llm, 'max_tokens', 2000)
                )
            else:
                fresh_llm = llm
            
            # 创建分析链
            analysis_prompt_template = ChatPromptTemplate.from_messages([
                ("system", "你是专业的行业分析师，基于提供的真实行业数据进行对比分析。"),
                ("human", "{analysis_request}")
            ])
            
            analysis_chain = analysis_prompt_template | fresh_llm
            analysis_result = analysis_chain.invoke({"analysis_request": analysis_prompt})
            
            if hasattr(analysis_result, 'content'):
                report = analysis_result.content
            else:
                report = str(analysis_result)
            
            logger.info(f"🏭 [行业对比分析师] 行业分析完成，报告长度: {len(report)}")
            
            # 返回分析结果
            return {
                "industry_analysis": {
                    "report": report,
                    "raw_data": industry_data,
                    "analysis_date": analysis_date,
                    "depth": analysis_depth
                }
            }
            
        except Exception as e:
            error_msg = f"❌ 行业对比分析失败: {str(e)}"
            logger.error(error_msg)
            return {"error_messages": [error_msg]}
    
    return industry_comparison_agent_node