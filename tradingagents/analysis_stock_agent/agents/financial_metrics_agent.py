"""
财务指标分析Agent

专门负责A股公司的财务指标深度分析，包括：
1. 营收与净利润增长分析
2. ROE健康度分析
3. 三大报表健康度分析
4. 股东回报分析

基于现有框架的Agent模式实现
"""

from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# 导入统一日志系统
from tradingagents.utils.logging_manager import get_logger
from tradingagents.utils.tool_logging import log_analyst_module

logger = get_logger('financial_metrics_agent')


def create_financial_metrics_agent(llm, toolkit):
    """
    创建财务指标分析Agent
    
    Args:
        llm: 语言模型
        toolkit: 工具集（包含A股数据工具）
        
    Returns:
        function: Agent节点函数
    """
    
    @log_analyst_module("financial_metrics")
    def financial_metrics_agent_node(state):
        """财务指标分析Agent节点"""
        
        logger.info(f"💰 [财务指标分析师] 开始分析")
        
        # 获取基本参数
        ticker = state.get("ticker")
        analysis_date = state.get("analysis_date")
        analysis_depth = state.get("analysis_depth", "standard")
        
        if not ticker:
            error_msg = "❌ 缺少必要参数：股票代码"
            logger.error(error_msg)
            return {"error_messages": [error_msg]}
        
        logger.info(f"💰 [财务指标分析师] 分析目标: {ticker}, 日期: {analysis_date}, 深度: {analysis_depth}")
        
        # 获取A股数据工具
        from tradingagents.analysis_stock_agent.tools import AShareDataTools
        ashare_tools = AShareDataTools(toolkit.config)
        
        # 选择工具函数
        tools = [ashare_tools.get_ashare_financial_data]
        
        # 构建系统提示
        system_message = f"""你是专业的A股财务指标分析师。

🎯 **核心任务**：
对股票 {ticker} 进行深度财务指标分析，必须基于真实数据。

📊 **分析维度**：
1. **盈利能力分析**
   - 净资产收益率(ROE)：计算最近3年ROE变化趋势
   - 总资产收益率(ROA)：评估资产使用效率
   - 净利润率和毛利润率：分析盈利质量
   - 杜邦分析：ROE = 净利率 × 资产周转率 × 权益乘数

2. **成长性分析**
   - 营收增长率：分析最近3年营收增长趋势
   - 净利润增长率：评估盈利增长的可持续性
   - 复合增长率(CAGR)：计算3年营收和净利润CAGR
   - 增长质量评估：分析增长的稳定性和可持续性

3. **财务健康度分析**
   - 资产负债表健康度：流动比率、负债权益比、资产负债率
   - 现金流量表健康度：经营现金流、自由现金流、现金流量比率
   - 资产质量：应收账款周转率、存货周转率
   - 偿债能力：流动比率、速动比率、利息保障倍数

4. **股东回报分析**
   - 股息率和分红率分析
   - 连续分红年数统计
   - 分红政策稳定性评估
   - 股东回报总体评价

🔧 **操作要求**：
- 立即调用 get_ashare_financial_data 工具获取真实财务数据
- 基于真实数据进行专业分析，不允许假设或编造
- 提供具体的财务指标数值和趋势分析
- 给出明确的财务健康度评级和投资建议

📈 **分析深度**：{analysis_depth}
- basic: 提供核心指标概览
- standard: 包含趋势分析和对比
- comprehensive: 深度分析和预测

现在立即开始调用工具获取数据！"""

        # 创建提示模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="messages"),
        ])
        
        # 创建工具链
        try:
            # 检测阿里百炼模型并创建新实例
            if hasattr(llm, '__class__') and 'DashScope' in llm.__class__.__name__:
                logger.debug(f"💰 [财务指标分析师] 检测到阿里百炼模型，创建新实例")
                from tradingagents.llm_adapters import ChatDashScopeOpenAI
                fresh_llm = ChatDashScopeOpenAI(
                    model=llm.model_name,
                    temperature=llm.temperature,
                    max_tokens=getattr(llm, 'max_tokens', 2000)
                )
            else:
                fresh_llm = llm
            
            chain = prompt | fresh_llm.bind_tools(tools)
            
            logger.info(f"💰 [财务指标分析师] 调用LLM进行财务分析...")
            result = chain.invoke(state["messages"])
            
            # 检查工具调用
            if hasattr(result, 'tool_calls') and len(result.tool_calls) > 0:
                logger.info(f"💰 [财务指标分析师] 检测到工具调用，返回执行结果")
                return {"messages": [result]}
            else:
                # 没有工具调用，强制执行财务数据获取
                logger.info(f"💰 [财务指标分析师] 未检测到工具调用，强制获取财务数据")
                
                try:
                    # 强制调用财务数据获取工具
                    financial_data = ashare_tools.get_ashare_financial_data(ticker, 3)
                    
                    # 基于真实数据生成分析报告
                    analysis_prompt = f"""基于以下真实财务数据，对{ticker}进行专业的财务指标分析：

{financial_data}

请按照以下结构提供详细分析：

## 财务指标分析报告

### 执行摘要
- 财务健康度评级：（优秀/良好/一般/较差）
- 核心优势：
- 主要风险：
- 投资建议：（买入/持有/卖出）

### 盈利能力分析
基于真实ROE、ROA、净利润率数据的深度分析

### 成长性分析  
基于真实营收和净利润增长数据的趋势分析

### 财务健康度分析
基于真实资产负债率、现金流数据的安全性评估

### 股东回报分析
基于真实分红数据的股东回报评价

### 风险提示
基于财务数据识别的潜在风险

要求：
- 所有分析必须基于提供的真实数据
- 提供具体的财务比率和数值
- 给出明确的评级和建议
- 使用专业的财务分析语言"""

                    # 创建分析链
                    analysis_prompt_template = ChatPromptTemplate.from_messages([
                        ("system", "你是专业的财务分析师，基于提供的真实财务数据进行分析。"),
                        ("human", "{analysis_request}")
                    ])
                    
                    analysis_chain = analysis_prompt_template | fresh_llm
                    analysis_result = analysis_chain.invoke({"analysis_request": analysis_prompt})
                    
                    if hasattr(analysis_result, 'content'):
                        report = analysis_result.content
                    else:
                        report = str(analysis_result)
                    
                    logger.info(f"💰 [财务指标分析师] 财务分析完成，报告长度: {len(report)}")
                    
                    # 返回分析结果
                    return {
                        "financial_analysis": {
                            "report": report,
                            "raw_data": financial_data,
                            "analysis_date": analysis_date,
                            "depth": analysis_depth
                        }
                    }
                    
                except Exception as e:
                    error_msg = f"❌ 财务数据获取失败: {str(e)}"
                    logger.error(error_msg)
                    return {"error_messages": [error_msg]}
            
        except Exception as e:
            error_msg = f"❌ 财务指标分析失败: {str(e)}"
            logger.error(error_msg)
            return {"error_messages": [error_msg]}
    
    return financial_metrics_agent_node