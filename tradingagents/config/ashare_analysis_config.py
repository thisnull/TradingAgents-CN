#!/usr/bin/env python3
"""
A股分析配置管理

专门处理A股分析多智能体系统的配置，包括：
1. A股分析Agent配置
2. 数据源配置(Tushare/AkShare)
3. 分析深度和资源限制配置
4. 缓存和性能配置
"""

import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

# 导入统一日志系统
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('ashare_analysis_config')


@dataclass
class AShareAgentConfig:
    """A股分析Agent配置"""
    agent_name: str  # Agent名称
    enabled: bool = True  # 是否启用
    analysis_depth: str = "standard"  # 分析深度: basic/standard/comprehensive
    max_tokens: int = 2000  # 最大token限制
    temperature: float = 0.7  # 生成温度
    timeout_seconds: int = 300  # 超时时间
    retry_count: int = 3  # 重试次数
    parallel_execution: bool = True  # 是否支持并行执行


@dataclass
class AShareDataSourceConfig:
    """A股数据源配置"""
    source_name: str  # 数据源名称 (tushare/akshare)
    enabled: bool = True  # 是否启用
    api_key: str = ""  # API密钥
    priority: int = 1  # 优先级 (1-10, 数字越小优先级越高)
    rate_limit_per_second: int = 10  # 每秒请求限制
    cache_ttl_hours: int = 24  # 缓存TTL小时数
    fallback_enabled: bool = True  # 是否支持作为备用数据源


@dataclass
class AShareAnalysisConfig:
    """A股分析配置"""
    # 基础配置
    enabled: bool = True
    default_analysis_depth: str = "standard"  # basic/standard/comprehensive
    max_concurrent_analyses: int = 3  # 最大并发分析数
    
    # Agent配置
    agents: List[AShareAgentConfig] = None
    
    # 数据源配置
    data_sources: List[AShareDataSourceConfig] = None
    
    # 资源限制配置
    max_tokens_per_analysis: int = 8000  # 每次分析最大token数
    max_analysis_time_minutes: int = 10  # 最大分析时间
    cost_limit_per_analysis_cny: float = 5.0  # 每次分析成本限制(人民币)
    
    # 缓存配置
    cache_enabled: bool = True
    cache_redis_enabled: bool = True
    cache_mongodb_enabled: bool = True
    cache_file_enabled: bool = True
    
    # 报告配置
    report_format: str = "markdown"  # markdown/json/html
    include_raw_data: bool = False  # 是否包含原始数据
    pyramid_structure: bool = True  # 是否使用金字塔结构
    
    # 调试配置
    debug_mode: bool = False
    log_level: str = "INFO"
    save_intermediate_results: bool = False


class AShareAnalysisConfigManager:
    """A股分析配置管理器"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "ashare_analysis.json")
        
        # 加载环境变量
        self._load_env_variables()
        
        # 初始化默认配置
        self._init_default_config()
    
    def _load_env_variables(self):
        """加载环境变量"""
        # 尝试加载.env文件
        try:
            load_dotenv()
        except ImportError:
            pass
    
    def _init_default_config(self) -> AShareAnalysisConfig:
        """初始化默认A股分析配置"""
        
        # 默认Agent配置
        default_agents = [
            AShareAgentConfig(
                agent_name="financial_metrics",
                enabled=True,
                analysis_depth="standard",
                max_tokens=2000,
                temperature=0.7,
                timeout_seconds=300
            ),
            AShareAgentConfig(
                agent_name="industry_comparison", 
                enabled=True,
                analysis_depth="standard",
                max_tokens=2000,
                temperature=0.7,
                timeout_seconds=300
            ),
            AShareAgentConfig(
                agent_name="valuation_analysis",
                enabled=True,
                analysis_depth="standard", 
                max_tokens=2000,
                temperature=0.7,
                timeout_seconds=300
            ),
            AShareAgentConfig(
                agent_name="report_integration",
                enabled=True,
                analysis_depth="comprehensive",
                max_tokens=3000,
                temperature=0.7,
                timeout_seconds=600,
                parallel_execution=False  # 报告整合不能并行
            )
        ]
        
        # 默认数据源配置
        default_data_sources = [
            AShareDataSourceConfig(
                source_name="tushare",
                enabled=self._parse_bool_env("TUSHARE_ENABLED", False),
                api_key=os.getenv("TUSHARE_TOKEN", ""),
                priority=1,
                rate_limit_per_second=10,
                cache_ttl_hours=24,
                fallback_enabled=True
            ),
            AShareDataSourceConfig(
                source_name="akshare",
                enabled=self._parse_bool_env("AKSHARE_ENABLED", True),
                api_key="",  # AkShare不需要API密钥
                priority=2,
                rate_limit_per_second=20,
                cache_ttl_hours=12,
                fallback_enabled=True
            )
        ]
        
        # 基础配置
        config = AShareAnalysisConfig(
            enabled=self._parse_bool_env("ASHARE_ANALYSIS_ENABLED", True),
            default_analysis_depth=os.getenv("ASHARE_DEFAULT_DEPTH", "standard"),
            max_concurrent_analyses=int(os.getenv("ASHARE_MAX_CONCURRENT", "3")),
            agents=default_agents,
            data_sources=default_data_sources,
            max_tokens_per_analysis=int(os.getenv("ASHARE_MAX_TOKENS", "8000")),
            max_analysis_time_minutes=int(os.getenv("ASHARE_MAX_TIME_MINUTES", "10")),
            cost_limit_per_analysis_cny=float(os.getenv("ASHARE_COST_LIMIT_CNY", "5.0")),
            cache_enabled=self._parse_bool_env("ASHARE_CACHE_ENABLED", True),
            cache_redis_enabled=self._parse_bool_env("ASHARE_REDIS_CACHE", True),
            cache_mongodb_enabled=self._parse_bool_env("ASHARE_MONGODB_CACHE", True),
            cache_file_enabled=self._parse_bool_env("ASHARE_FILE_CACHE", True),
            report_format=os.getenv("ASHARE_REPORT_FORMAT", "markdown"),
            include_raw_data=self._parse_bool_env("ASHARE_INCLUDE_RAW_DATA", False),
            pyramid_structure=self._parse_bool_env("ASHARE_PYRAMID_STRUCTURE", True),
            debug_mode=self._parse_bool_env("ASHARE_DEBUG_MODE", False),
            log_level=os.getenv("ASHARE_LOG_LEVEL", "INFO"),
            save_intermediate_results=self._parse_bool_env("ASHARE_SAVE_INTERMEDIATE", False)
        )
        
        return config
    
    def _parse_bool_env(self, env_name: str, default: bool) -> bool:
        """解析布尔环境变量"""
        value = os.getenv(env_name, "").lower()
        if value in ("true", "1", "yes", "on"):
            return True
        elif value in ("false", "0", "no", "off"):
            return False
        else:
            return default
    
    def load_config(self) -> AShareAnalysisConfig:
        """加载A股分析配置"""
        try:
            # 首先获取默认配置
            config = self._init_default_config()
            
            # 如果存在配置文件，则合并配置
            if os.path.exists(self.config_file):
                import json
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    # 这里可以添加配置合并逻辑
                    logger.info(f"✅ 加载A股分析配置文件: {self.config_file}")
            
            # 验证配置
            self._validate_config(config)
            
            logger.info(f"✅ A股分析配置加载完成")
            return config
            
        except Exception as e:
            logger.error(f"❌ 加载A股分析配置失败: {e}")
            # 返回默认配置
            return self._init_default_config()
    
    def save_config(self, config: AShareAnalysisConfig):
        """保存A股分析配置"""
        try:
            import json
            
            # 确保配置目录存在
            os.makedirs(self.config_dir, exist_ok=True)
            
            # 转换为字典
            config_dict = asdict(config)
            
            # 保存到文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ A股分析配置已保存: {self.config_file}")
            
        except Exception as e:
            logger.error(f"❌ 保存A股分析配置失败: {e}")
    
    def _validate_config(self, config: AShareAnalysisConfig):
        """验证配置有效性"""
        issues = []
        
        # 检查基础配置
        if config.max_concurrent_analyses <= 0:
            issues.append("max_concurrent_analyses 必须大于0")
        
        if config.max_tokens_per_analysis <= 0:
            issues.append("max_tokens_per_analysis 必须大于0")
        
        if config.cost_limit_per_analysis_cny <= 0:
            issues.append("cost_limit_per_analysis_cny 必须大于0")
        
        # 检查Agent配置
        if not config.agents:
            issues.append("至少需要配置一个Agent")
        else:
            enabled_agents = [agent for agent in config.agents if agent.enabled]
            if not enabled_agents:
                issues.append("至少需要启用一个Agent")
        
        # 检查数据源配置
        if not config.data_sources:
            issues.append("至少需要配置一个数据源")
        else:
            enabled_sources = [source for source in config.data_sources if source.enabled]
            if not enabled_sources:
                issues.append("至少需要启用一个数据源")
        
        # 检查分析深度设置
        valid_depths = ["basic", "standard", "comprehensive"]
        if config.default_analysis_depth not in valid_depths:
            issues.append(f"default_analysis_depth 必须是 {valid_depths} 之一")
        
        # 报告验证结果
        if issues:
            logger.warning(f"⚠️ A股分析配置验证发现问题:")
            for issue in issues:
                logger.warning(f"   - {issue}")
        else:
            logger.info(f"✅ A股分析配置验证通过")
    
    def get_enabled_agents(self, config: AShareAnalysisConfig) -> List[AShareAgentConfig]:
        """获取启用的Agent配置"""
        return [agent for agent in config.agents if agent.enabled]
    
    def get_enabled_data_sources(self, config: AShareAnalysisConfig) -> List[AShareDataSourceConfig]:
        """获取启用的数据源配置"""
        sources = [source for source in config.data_sources if source.enabled]
        # 按优先级排序
        return sorted(sources, key=lambda x: x.priority)
    
    def get_primary_data_source(self, config: AShareAnalysisConfig) -> Optional[AShareDataSourceConfig]:
        """获取主要数据源"""
        enabled_sources = self.get_enabled_data_sources(config)
        if enabled_sources:
            return enabled_sources[0]  # 优先级最高的
        return None
    
    def get_fallback_data_sources(self, config: AShareAnalysisConfig) -> List[AShareDataSourceConfig]:
        """获取备用数据源"""
        enabled_sources = self.get_enabled_data_sources(config)
        return [source for source in enabled_sources[1:] if source.fallback_enabled]
    
    def get_agent_config(self, config: AShareAnalysisConfig, agent_name: str) -> Optional[AShareAgentConfig]:
        """根据名称获取Agent配置"""
        for agent in config.agents:
            if agent.agent_name == agent_name and agent.enabled:
                return agent
        return None
    
    def calculate_estimated_cost(self, config: AShareAnalysisConfig, estimated_tokens: int) -> float:
        """计算预估成本(基于配置的成本限制)"""
        if estimated_tokens <= 0:
            return 0.0
        
        # 基于token数量和配置的成本限制进行估算
        token_ratio = estimated_tokens / config.max_tokens_per_analysis
        estimated_cost = config.cost_limit_per_analysis_cny * token_ratio
        
        return min(estimated_cost, config.cost_limit_per_analysis_cny)
    
    def is_cost_within_limit(self, config: AShareAnalysisConfig, estimated_cost: float) -> bool:
        """检查成本是否在限制范围内"""
        return estimated_cost <= config.cost_limit_per_analysis_cny
    
    def get_cache_config(self, config: AShareAnalysisConfig) -> Dict[str, Any]:
        """获取缓存配置"""
        return {
            "enabled": config.cache_enabled,
            "redis_enabled": config.cache_redis_enabled,
            "mongodb_enabled": config.cache_mongodb_enabled,
            "file_enabled": config.cache_file_enabled,
            "default_ttl_hours": 24 if config.data_sources else 12
        }
    
    def get_env_config_summary(self) -> Dict[str, Any]:
        """获取环境变量配置摘要"""
        return {
            "ashare_analysis_enabled": os.getenv("ASHARE_ANALYSIS_ENABLED", "true"),
            "tushare_enabled": os.getenv("TUSHARE_ENABLED", "false"),
            "tushare_token_set": bool(os.getenv("TUSHARE_TOKEN")),
            "akshare_enabled": os.getenv("AKSHARE_ENABLED", "true"),
            "default_analysis_depth": os.getenv("ASHARE_DEFAULT_DEPTH", "standard"),
            "max_concurrent_analyses": os.getenv("ASHARE_MAX_CONCURRENT", "3"),
            "cost_limit_cny": os.getenv("ASHARE_COST_LIMIT_CNY", "5.0"),
            "debug_mode": os.getenv("ASHARE_DEBUG_MODE", "false")
        }


# 全局配置管理器实例
ashare_config_manager = AShareAnalysisConfigManager()


def get_ashare_analysis_config() -> AShareAnalysisConfig:
    """获取A股分析配置"""
    return ashare_config_manager.load_config()


def validate_ashare_config() -> Dict[str, Any]:
    """验证A股分析配置"""
    config = get_ashare_analysis_config()
    enabled_agents = ashare_config_manager.get_enabled_agents(config)
    enabled_sources = ashare_config_manager.get_enabled_data_sources(config)
    primary_source = ashare_config_manager.get_primary_data_source(config)
    
    return {
        "config_valid": len(enabled_agents) > 0 and len(enabled_sources) > 0,
        "enabled_agents_count": len(enabled_agents),
        "enabled_agents": [agent.agent_name for agent in enabled_agents],
        "enabled_sources_count": len(enabled_sources),
        "enabled_sources": [source.source_name for source in enabled_sources],
        "primary_data_source": primary_source.source_name if primary_source else None,
        "estimated_cost_per_analysis": config.cost_limit_per_analysis_cny,
        "max_concurrent_analyses": config.max_concurrent_analyses,
        "cache_enabled": config.cache_enabled,
        "debug_mode": config.debug_mode,
        "env_summary": ashare_config_manager.get_env_config_summary()
    }


def diagnose_ashare_config():
    """诊断A股分析配置问题"""
    print("🔍 A股分析配置诊断")
    print("=" * 60)
    
    validation = validate_ashare_config()
    
    # 显示配置状态
    print(f"\n📊 配置状态:")
    print(f"   配置有效: {'✅' if validation['config_valid'] else '❌'}")
    print(f"   启用Agent数: {validation['enabled_agents_count']}")
    print(f"   启用数据源数: {validation['enabled_sources_count']}")
    print(f"   主要数据源: {validation['primary_data_source'] or '未配置'}")
    print(f"   预估成本限制: ¥{validation['estimated_cost_per_analysis']}")
    print(f"   最大并发数: {validation['max_concurrent_analyses']}")
    
    # 显示Agent详情
    print(f"\n🤖 启用的Agent:")
    for agent_name in validation['enabled_agents']:
        print(f"   ✅ {agent_name}")
    
    # 显示数据源详情
    print(f"\n📊 启用的数据源:")
    for source_name in validation['enabled_sources']:
        print(f"   ✅ {source_name}")
    
    # 显示环境变量
    print(f"\n🔍 环境变量配置:")
    env_summary = validation['env_summary']
    for key, value in env_summary.items():
        status = "✅" if value not in ["false", False, "", None] else "❌"
        print(f"   {key}: {status} {value}")
    
    # 建议
    if not validation['config_valid']:
        print(f"\n💡 修复建议:")
        if validation['enabled_agents_count'] == 0:
            print(f"   - 至少启用一个分析Agent")
        if validation['enabled_sources_count'] == 0:
            print(f"   - 至少启用一个数据源(推荐启用AkShare)")
        if not validation['primary_data_source']:
            print(f"   - 配置有效的主要数据源")


if __name__ == "__main__":
    diagnose_ashare_config()