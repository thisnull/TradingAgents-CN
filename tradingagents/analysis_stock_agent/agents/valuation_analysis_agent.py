"""
估值分析Agent

专门负责A股公司的估值分析，包括：
1. 股权变动异常分析
2. 股东结构分析
3. PEG估值分析

基于现有框架的Agent模式实现
"""

from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# 导入统一日志系统
from tradingagents.utils.logging_manager import get_logger
from tradingagents.utils.tool_logging import log_analyst_module

logger = get_logger('valuation_analysis_agent')


def create_valuation_analysis_agent(llm, toolkit):
    """
    创建估值分析Agent
    
    Args:
        llm: 语言模型
        toolkit: 工具集
        
    Returns:
        function: Agent节点函数
    """
    
    @log_analyst_module("valuation_analysis")
    def valuation_analysis_agent_node(state):
        """估值分析Agent节点"""
        
        logger.info(f"💎 [估值分析师] 开始分析")
        
        # 获取基本参数
        ticker = state.get("ticker")
        analysis_date = state.get("analysis_date")
        analysis_depth = state.get("analysis_depth", "standard")
        
        if not ticker:
            error_msg = "❌ 缺少必要参数：股票代码"
            logger.error(error_msg)
            return {"error_messages": [error_msg]}
        
        logger.info(f"💎 [估值分析师] 分析目标: {ticker}, 日期: {analysis_date}, 深度: {analysis_depth}")
        
        try:
            # 获取A股数据工具
            from tradingagents.analysis_stock_agent.tools import AShareDataTools
            ashare_tools = AShareDataTools(toolkit.config)
            
            # 强制获取估值指标数据
            valuation_data = ashare_tools.get_ashare_valuation_metrics(ticker)
            
            # 生成估值分析报告
            analysis_prompt = f"""基于以下真实估值数据，对{ticker}进行专业的估值分析：

{valuation_data}

请按照以下结构提供详细分析：

## 估值分析报告

### 执行摘要
- 估值水平评级：（严重低估/低估/合理/高估/严重高估）
- 目标价区间：
- 投资评级：（强烈买入/买入/持有/卖出/强烈卖出）
- 预期回报：

### 当前估值水平分析
基于真实PE、PB、PS、PEG数据的估值水平评估

### 相对估值分析
基于历史分位数和行业对比的相对估值分析

### 目标价测算
使用多种估值方法计算目标价区间

### 股权结构分析
分析股权集中度、机构持股比例等结构特征

### 近期股权变动分析
识别异常的股权变动和其对估值的影响

### 估值风险因素
识别可能影响估值的关键风险因素

要求：
- 所有分析必须基于提供的真实数据
- 提供具体的估值指标和目标价
- 给出明确的估值水平判断
- 考虑股权结构对估值的影响"""

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
                ("system", "你是专业的估值分析师，基于提供的真实市场数据进行估值分析。"),
                ("human", "{analysis_request}")
            ])
            
            analysis_chain = analysis_prompt_template | fresh_llm
            analysis_result = analysis_chain.invoke({"analysis_request": analysis_prompt})
            
            if hasattr(analysis_result, 'content'):
                report = analysis_result.content
            else:
                report = str(analysis_result)
            
            logger.info(f"💎 [估值分析师] 估值分析完成，报告长度: {len(report)}")
            
            # 返回分析结果
            return {
                "valuation_analysis": {
                    "report": report,
                    "raw_data": valuation_data,
                    "analysis_date": analysis_date,
                    "depth": analysis_depth
                }
            }
            
        except Exception as e:
            error_msg = f"❌ 估值分析失败: {str(e)}"
            logger.error(error_msg)
            return {"error_messages": [error_msg]}
    
    return valuation_analysis_agent_node