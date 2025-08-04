#!/usr/bin/env python3
"""
A股分析配置验证脚本

用于验证A股分析配置系统的完整性和正确性
"""

import sys
import os
import traceback
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_basic_imports():
    """测试基础模块导入"""
    print("🔍 测试基础模块导入...")
    try:
        # 测试默认配置导入
        from tradingagents.default_config import DEFAULT_CONFIG
        print("   ✅ 默认配置导入成功")
        
        # 检查A股分析配置是否存在
        if "ashare_analysis" in DEFAULT_CONFIG:
            print("   ✅ 默认配置包含A股分析配置")
        else:
            print("   ❌ 默认配置缺少A股分析配置")
            return False
        
        # 测试A股分析配置导入
        from tradingagents.config.ashare_analysis_config import (
            AShareAnalysisConfig,
            AShareAgentConfig, 
            AShareDataSourceConfig,
            AShareAnalysisConfigManager,
            get_ashare_analysis_config,
            validate_ashare_config
        )
        print("   ✅ A股分析配置模块导入成功")
        
        # 测试配置管理器统一导入
        from tradingagents.config import (
            ashare_config_manager,
            get_ashare_analysis_config,
            validate_ashare_config
        )
        print("   ✅ 配置管理器统一导入成功")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 导入失败: {e}")
        traceback.print_exc()
        return False

def test_config_loading():
    """测试配置加载"""
    print("\n🔍 测试配置加载...")
    try:
        from tradingagents.config import get_ashare_analysis_config
        
        config = get_ashare_analysis_config()
        print("   ✅ A股分析配置加载成功")
        
        # 检查配置基本属性
        if hasattr(config, 'enabled'):
            print(f"   ✅ 配置状态: {'启用' if config.enabled else '禁用'}")
        else:
            print("   ❌ 配置缺少enabled属性")
            return False
        
        if hasattr(config, 'agents') and config.agents:
            print(f"   ✅ Agent配置数量: {len(config.agents)}")
        else:
            print("   ❌ 配置缺少agents属性")
            return False
        
        if hasattr(config, 'data_sources') and config.data_sources:
            print(f"   ✅ 数据源配置数量: {len(config.data_sources)}")
        else:
            print("   ❌ 配置缺少data_sources属性")
            return False
            
        return True
        
    except Exception as e:
        print(f"   ❌ 配置加载失败: {e}")
        traceback.print_exc()
        return False

def test_config_validation():
    """测试配置验证"""
    print("\n🔍 测试配置验证...")
    try:
        from tradingagents.config import validate_ashare_config
        
        validation_result = validate_ashare_config()
        print("   ✅ 配置验证执行成功")
        
        # 检查验证结果
        if validation_result.get('config_valid'):
            print("   ✅ 配置验证通过")
        else:
            print("   ⚠️ 配置验证发现问题")
        
        # 显示详细信息
        print(f"   📊 启用Agent数: {validation_result.get('enabled_agents_count', 0)}")
        print(f"   📊 启用数据源数: {validation_result.get('enabled_sources_count', 0)}")
        print(f"   📊 主要数据源: {validation_result.get('primary_data_source', '未配置')}")
        print(f"   📊 成本限制: ¥{validation_result.get('estimated_cost_per_analysis', 0)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 配置验证失败: {e}")
        traceback.print_exc()
        return False

def test_agent_configs():
    """测试Agent配置"""
    print("\n🔍 测试Agent配置...")
    try:
        from tradingagents.config import get_ashare_analysis_config, ashare_config_manager
        
        config = get_ashare_analysis_config()
        enabled_agents = ashare_config_manager.get_enabled_agents(config)
        
        print(f"   ✅ 启用的Agent数量: {len(enabled_agents)}")
        
        expected_agents = ["financial_metrics", "industry_comparison", "valuation_analysis", "report_integration"]
        for expected_agent in expected_agents:
            agent_config = ashare_config_manager.get_agent_config(config, expected_agent)
            if agent_config:
                print(f"   ✅ {expected_agent}: 已配置 (max_tokens={agent_config.max_tokens})")
            else:
                print(f"   ❌ {expected_agent}: 未配置或未启用")
        
        return len(enabled_agents) > 0
        
    except Exception as e:
        print(f"   ❌ Agent配置测试失败: {e}")
        traceback.print_exc()
        return False

def test_data_source_configs():
    """测试数据源配置"""
    print("\n🔍 测试数据源配置...")
    try:
        from tradingagents.config import get_ashare_analysis_config, ashare_config_manager
        
        config = get_ashare_analysis_config()
        enabled_sources = ashare_config_manager.get_enabled_data_sources(config)
        primary_source = ashare_config_manager.get_primary_data_source(config)
        fallback_sources = ashare_config_manager.get_fallback_data_sources(config)
        
        print(f"   ✅ 启用的数据源数量: {len(enabled_sources)}")
        print(f"   ✅ 主要数据源: {primary_source.source_name if primary_source else '未配置'}")
        print(f"   ✅ 备用数据源数量: {len(fallback_sources)}")
        
        # 检查具体数据源
        for source in enabled_sources:
            print(f"   📊 {source.source_name}: 优先级={source.priority}, 启用={source.enabled}")
        
        return len(enabled_sources) > 0
        
    except Exception as e:
        print(f"   ❌ 数据源配置测试失败: {e}")
        traceback.print_exc()
        return False

def test_environment_variables():
    """测试环境变量配置"""
    print("\n🔍 测试环境变量配置...")
    try:
        from tradingagents.config import ashare_config_manager
        
        env_summary = ashare_config_manager.get_env_config_summary()
        
        print("   📊 环境变量摘要:")
        for key, value in env_summary.items():
            status = "✅" if value not in ["false", False, "", None] else "⚠️"
            print(f"      {key}: {status} {value}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 环境变量测试失败: {e}")
        traceback.print_exc()
        return False

def test_cost_calculation():
    """测试成本计算"""
    print("\n🔍 测试成本计算...")
    try:
        from tradingagents.config import get_ashare_analysis_config, ashare_config_manager
        
        config = get_ashare_analysis_config()
        
        # 测试成本估算
        test_tokens = [1000, 2000, 5000, 10000]
        for tokens in test_tokens:
            estimated_cost = ashare_config_manager.calculate_estimated_cost(config, tokens)
            within_limit = ashare_config_manager.is_cost_within_limit(config, estimated_cost)
            print(f"   📊 {tokens} tokens: ¥{estimated_cost:.4f} {'✅' if within_limit else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 成本计算测试失败: {e}")
        traceback.print_exc()
        return False

def test_cache_config():
    """测试缓存配置"""
    print("\n🔍 测试缓存配置...")
    try:
        from tradingagents.config import get_ashare_analysis_config, ashare_config_manager
        
        config = get_ashare_analysis_config()
        cache_config = ashare_config_manager.get_cache_config(config)
        
        print(f"   ✅ 缓存配置获取成功")
        for key, value in cache_config.items():
            status = "✅" if value else "❌"
            print(f"      {key}: {status} {value}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 缓存配置测试失败: {e}")
        traceback.print_exc()
        return False

def test_default_config_integration():
    """测试默认配置集成"""
    print("\n🔍 测试默认配置集成...")
    try:
        from tradingagents.default_config import DEFAULT_CONFIG
        
        ashare_config = DEFAULT_CONFIG.get("ashare_analysis")
        if not ashare_config:
            print("   ❌ 默认配置中未找到A股分析配置")
            return False
        
        print("   ✅ 默认配置中包含A股分析配置")
        
        # 检查关键配置项
        required_keys = ["enabled", "data_sources", "agents"]
        for key in required_keys:
            if key in ashare_config:
                print(f"   ✅ 包含配置项: {key}")
            else:
                print(f"   ❌ 缺少配置项: {key}")
                return False
        
        # 检查数据源配置
        data_sources = ashare_config.get("data_sources", {})
        if "tushare" in data_sources and "akshare" in data_sources:
            print("   ✅ 包含Tushare和AkShare数据源配置")
        else:
            print("   ❌ 数据源配置不完整")
            return False
        
        # 检查Agent配置
        agents = ashare_config.get("agents", {})
        expected_agents = ["financial_metrics", "industry_comparison", "valuation_analysis", "report_integration"]
        for agent in expected_agents:
            if agent in agents:
                print(f"   ✅ 包含Agent配置: {agent}")
            else:
                print(f"   ❌ 缺少Agent配置: {agent}")
                return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ 默认配置集成测试失败: {e}")
        traceback.print_exc()
        return False

def run_comprehensive_test():
    """运行综合测试"""
    print("🚀 A股分析配置系统综合测试")
    print("=" * 60)
    
    test_functions = [
        ("基础模块导入", test_basic_imports),
        ("配置加载", test_config_loading),
        ("配置验证", test_config_validation),
        ("Agent配置", test_agent_configs),
        ("数据源配置", test_data_source_configs),
        ("环境变量配置", test_environment_variables),
        ("成本计算", test_cost_calculation),
        ("缓存配置", test_cache_config),
        ("默认配置集成", test_default_config_integration)
    ]
    
    results = []
    for test_name, test_function in test_functions:
        try:
            result = test_function()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} 测试遇到异常: {e}")
            results.append((test_name, False))
    
    # 总结结果
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    
    passed = 0
    failed = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n🎯 总体结果: {passed}/{len(results)} 测试通过")
    
    if failed == 0:
        print("🎉 所有测试通过！A股分析配置系统工作正常")
        return True
    else:
        print(f"⚠️ {failed} 个测试失败，请检查配置")
        return False

def main():
    """主函数"""
    try:
        success = run_comprehensive_test()
        
        print("\n" + "=" * 60)
        print("💡 后续步骤建议:")
        print("   1. 如果测试通过，可以继续集成到TradingAgentsGraph")
        print("   2. 如果有配置问题，请检查环境变量设置")
        print("   3. 可以运行 diagnose_ashare_config() 获取详细诊断")
        print("   4. 确保.env文件包含必要的A股分析配置")
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)