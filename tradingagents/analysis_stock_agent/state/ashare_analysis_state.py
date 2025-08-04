"""
A股分析状态管理

定义A股分析过程中的状态结构，基于LangGraph的TypedDict模式
"""

from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime


class AShareAnalysisState(TypedDict):
    """A股分析状态定义"""
    
    # 基本输入信息
    ticker: str                    # 股票代码（如：000001, 002027等）
    analysis_date: str            # 分析日期 (YYYY-MM-DD)
    company_info: Dict[str, Any]  # 公司基本信息
    
    # Agent分析结果
    financial_analysis: Optional[Dict[str, Any]]    # 财务分析结果
    industry_analysis: Optional[Dict[str, Any]]     # 行业分析结果  
    valuation_analysis: Optional[Dict[str, Any]]    # 估值分析结果
    integration_report: Optional[str]               # 整合报告
    
    # 执行状态追踪
    current_agent: Optional[str]                    # 当前执行的Agent
    completed_agents: List[str]                     # 已完成的Agent列表
    error_messages: List[str]                       # 错误信息收集
    
    # 数据缓存
    raw_financial_data: Optional[Dict[str, Any]]    # 原始财务数据
    industry_data: Optional[Dict[str, Any]]         # 行业数据
    peer_companies: Optional[List[str]]             # 同行业公司列表
    
    # 分析配置
    analysis_depth: str                             # 分析深度：basic/standard/comprehensive
    enable_cache: bool                              # 是否启用缓存
    data_sources: List[str]                         # 数据源列表
    
    # 时间追踪
    start_time: Optional[datetime]                  # 分析开始时间
    agent_timings: Dict[str, float]                 # 各Agent执行时间
    
    # 最终输出
    investment_recommendation: Optional[str]         # 投资建议（买入/持有/卖出）
    target_price_range: Optional[Dict[str, float]]  # 目标价位区间
    confidence_score: Optional[float]               # 置信度评分 (0-1)
    risk_factors: Optional[List[str]]               # 风险因素列表


class FinancialMetrics(TypedDict):
    """财务指标数据结构"""
    
    # 盈利能力指标
    roe: Optional[float]                    # 净资产收益率
    roa: Optional[float]                    # 总资产收益率  
    net_profit_margin: Optional[float]      # 净利润率
    gross_profit_margin: Optional[float]    # 毛利润率
    
    # 成长性指标
    revenue_growth: Optional[float]         # 营收增长率
    net_income_growth: Optional[float]      # 净利润增长率
    revenue_cagr_3y: Optional[float]        # 3年营收复合增长率
    
    # 财务健康指标
    current_ratio: Optional[float]          # 流动比率
    debt_to_equity: Optional[float]         # 负债权益比
    debt_ratio: Optional[float]             # 资产负债率
    
    # 现金流指标
    operating_cash_flow: Optional[float]    # 经营现金流
    free_cash_flow: Optional[float]         # 自由现金流
    cash_flow_ratio: Optional[float]        # 现金流量比率
    
    # 股东回报指标
    dividend_yield: Optional[float]         # 股息率
    dividend_payout_ratio: Optional[float]  # 分红率
    consecutive_dividend_years: Optional[int] # 连续分红年数


class IndustryComparison(TypedDict):
    """行业对比数据结构"""
    
    # 行业基本信息
    industry_code: str                      # 行业代码
    industry_name: str                      # 行业名称
    industry_stage: str                     # 行业发展阶段
    
    # 行业平均指标
    industry_avg_roe: Optional[float]       # 行业平均ROE
    industry_avg_pe: Optional[float]        # 行业平均PE
    industry_avg_growth: Optional[float]    # 行业平均增长率
    
    # 排名信息
    roe_ranking: Optional[int]              # ROE行业排名
    revenue_ranking: Optional[int]          # 营收行业排名
    market_cap_ranking: Optional[int]       # 市值行业排名
    
    # 竞争对手信息
    top_competitors: List[Dict[str, Any]]   # 头部竞争对手
    competitive_advantages: List[str]       # 竞争优势
    competitive_risks: List[str]            # 竞争风险


class ValuationMetrics(TypedDict):
    """估值指标数据结构"""
    
    # 基本估值指标
    pe_ratio: Optional[float]               # 市盈率
    pb_ratio: Optional[float]               # 市净率
    ps_ratio: Optional[float]               # 市销率
    peg_ratio: Optional[float]              # PEG比率
    
    # 相对估值
    pe_percentile: Optional[float]          # PE历史分位数
    pb_percentile: Optional[float]          # PB历史分位数
    industry_pe_premium: Optional[float]    # 行业PE溢价率
    
    # 目标价测算
    target_price_pe: Optional[float]        # 基于PE的目标价
    target_price_pb: Optional[float]        # 基于PB的目标价
    target_price_dcf: Optional[float]       # DCF目标价
    
    # 股权结构分析
    ownership_concentration: Optional[float] # 股权集中度
    institutional_ownership: Optional[float] # 机构持股比例
    recent_ownership_changes: List[Dict[str, Any]] # 近期股权变动