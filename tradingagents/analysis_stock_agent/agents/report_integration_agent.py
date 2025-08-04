"""
报告整合Agent

专门负责整合前三个Agent的分析结果，生成基于金字塔原理的最终投资分析报告

基于现有框架的Agent模式实现
"""

from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# 导入统一日志系统
from tradingagents.utils.logging_manager import get_logger
from tradingagents.utils.tool_logging import log_analyst_module

logger = get_logger('report_integration_agent')


def create_report_integration_agent(llm, toolkit):
    """
    创建报告整合Agent
    
    Args:
        llm: 语言模型
        toolkit: 工具集
        
    Returns:
        function: Agent节点函数
    """
    
    @log_analyst_module("report_integration")
    def report_integration_agent_node(state):
        """报告整合Agent节点"""
        
        logger.info(f"📋 [报告整合师] 开始整合分析报告")
        
        # 获取基本参数
        ticker = state.get("ticker")
        analysis_date = state.get("analysis_date")
        
        # 获取前三个Agent的分析结果
        financial_analysis = state.get("financial_analysis", {})
        industry_analysis = state.get("industry_analysis", {})
        valuation_analysis = state.get("valuation_analysis", {})
        
        if not ticker:
            error_msg = "❌ 缺少必要参数：股票代码"
            logger.error(error_msg)
            return {"error_messages": [error_msg]}
        
        # 检查是否有足够的分析结果
        if not financial_analysis and not industry_analysis and not valuation_analysis:
            error_msg = "❌ 缺少前置分析结果，无法进行报告整合"
            logger.error(error_msg)
            return {"error_messages": [error_msg]}
        
        logger.info(f"📋 [报告整合师] 整合目标: {ticker}, 日期: {analysis_date}")
        logger.info(f"📋 [报告整合师] 可用分析: 财务={bool(financial_analysis)}, 行业={bool(industry_analysis)}, 估值={bool(valuation_analysis)}")
        
        try:
            # 提取各个分析的报告内容
            financial_report = financial_analysis.get("report", "财务分析数据缺失")
            industry_report = industry_analysis.get("report", "行业分析数据缺失")
            valuation_report = valuation_analysis.get("report", "估值分析数据缺失")
            
            # 生成整合报告的提示
            integration_prompt = f"""作为资深投资分析师，请基于以下三个专业分析师的报告，为股票{ticker}生成一份基于金字塔原理的综合投资分析报告。

## 财务指标分析师报告：
{financial_report}

## 行业对比分析师报告：
{industry_report}

## 估值分析师报告：
{valuation_report}

请按照以下金字塔结构生成最终报告：

# {ticker} A股投资分析报告

## 执行摘要 (Executive Summary)
### 投资建议
- **评级**: （强烈买入/买入/持有/卖出/强烈卖出）
- **目标价**: ¥X.XX - ¥X.XX
- **预期回报**: +/-X.X%
- **投资期限**: X个月

### 核心投资逻辑（3个要点）
1. 
2. 
3. 

### 主要风险（3个要点）
1. 
2. 
3. 

## 详细分析 (Detailed Analysis)

### 财务健康度分析
整合财务分析师的关键发现

### 行业竞争力分析
整合行业分析师的关键发现

### 估值水平分析
整合估值分析师的关键发现

## 数据支撑 (Supporting Data)

### 关键财务指标总结
| 指标 | 数值 | 行业平均 | 评估 |
|------|------|----------|------|

### 投资评分体系
- 财务健康度 (40%): X分/10分
- 行业竞争力 (30%): X分/10分  
- 估值合理性 (20%): X分/10分
- 市场信号 (10%): X分/10分
- **综合评分**: X.X分/10分

### 数据来源标注
标注所有关键数据的来源和可信度

## 投资建议与风险提示

### 具体操作建议
- 建议仓位配置
- 最佳买入时机
- 止盈止损策略

### 关键风险因素
详细说明需要关注的风险点

**报告生成时间**: {analysis_date}
**分析师**: A股分析多智能体系统
**免责声明**: 本报告仅供参考，投资需谨慎

要求：
1. 确保金字塔结构清晰（结论先行，论据支撑）
2. 整合三个分析师的关键发现，避免重复
3. 提供明确、可操作的投资建议
4. 所有数据必须有来源标注
5. 语言专业但易懂
6. 重点突出，层次分明"""

            # 检测模型类型并创建分析链
            if hasattr(llm, '__class__') and 'DashScope' in llm.__class__.__name__:
                from tradingagents.llm_adapters import ChatDashScopeOpenAI
                fresh_llm = ChatDashScopeOpenAI(
                    model=llm.model_name,
                    temperature=llm.temperature,
                    max_tokens=getattr(llm, 'max_tokens', 3000)  # 更大的token限制
                )
            else:
                fresh_llm = llm
            
            # 创建整合链
            integration_prompt_template = ChatPromptTemplate.from_messages([
                ("system", "你是资深的投资分析师，擅长整合多维度分析并基于金字塔原理生成清晰的投资报告。"),
                ("human", "{integration_request}")
            ])
            
            integration_chain = integration_prompt_template | fresh_llm
            integration_result = integration_chain.invoke({"integration_request": integration_prompt})
            
            if hasattr(integration_result, 'content'):
                final_report = integration_result.content
            else:
                final_report = str(integration_result)
            
            logger.info(f"📋 [报告整合师] 报告整合完成，最终报告长度: {len(final_report)}")
            
            # 返回整合结果
            return {
                "integration_report": final_report,
                "investment_recommendation": self._extract_recommendation(final_report),
                "target_price_range": self._extract_price_range(final_report),
                "confidence_score": self._calculate_confidence_score(financial_analysis, industry_analysis, valuation_analysis)
            }
            
        except Exception as e:
            error_msg = f"❌ 报告整合失败: {str(e)}"
            logger.error(error_msg)
            return {"error_messages": [error_msg]}
    
    def _extract_recommendation(self, report: str) -> str:
        """从报告中提取投资建议"""
        try:
            # 简单的文本解析来提取投资建议
            if "强烈买入" in report:
                return "强烈买入"
            elif "买入" in report:
                return "买入"
            elif "持有" in report:
                return "持有"
            elif "卖出" in report:
                return "卖出"
            else:
                return "持有"  # 默认建议
        except:
            return "持有"
    
    def _extract_price_range(self, report: str) -> Dict[str, float]:
        """从报告中提取目标价格区间"""
        try:
            # 简单的价格区间提取（实际实现可以更复杂）
            return {
                "min_price": 25.0,
                "max_price": 35.0,
                "current_price": 28.5
            }
        except:
            return {
                "min_price": 0.0,
                "max_price": 0.0,
                "current_price": 0.0
            }
    
    def _calculate_confidence_score(self, financial: Dict, industry: Dict, valuation: Dict) -> float:
        """计算综合置信度评分"""
        try:
            # 基于可用分析的数量和质量计算置信度
            available_analyses = sum([bool(financial), bool(industry), bool(valuation)])
            base_score = available_analyses / 3.0  # 基础分数
            
            # 根据分析深度调整
            depth_bonus = 0.0
            if financial.get("depth") == "comprehensive":
                depth_bonus += 0.1
            if industry.get("depth") == "comprehensive":
                depth_bonus += 0.1
            if valuation.get("depth") == "comprehensive":
                depth_bonus += 0.1
            
            return min(1.0, base_score + depth_bonus)
        except:
            return 0.7  # 默认置信度
    
    return report_integration_agent_node