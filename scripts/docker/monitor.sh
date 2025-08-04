#!/bin/bash
# 系统性能监控脚本

echo "📊 TradingAgents-CN 性能监控"
echo "=============================="

# 容器资源使用
echo "📦 容器资源使用:"
if docker ps | grep -q tradingagents; then
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}" | head -1
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}" | grep tradingagents
else
    echo "  ⚠️  未找到运行中的TradingAgents容器"
fi

# 磁盘使用
echo ""
echo "💾 磁盘使用:"
docker system df

# 数据库状态
echo ""
echo "🗄️ 数据库状态:"

# MongoDB状态
if docker ps | grep -q tradingagents-mongodb; then
    mongo_connections=$(docker exec tradingagents-mongodb mongo --quiet --eval "db.runCommand({serverStatus: 1}).connections.current" 2>/dev/null || echo "N/A")
    mongo_memory=$(docker exec tradingagents-mongodb mongo --quiet --eval "Math.round(db.runCommand({serverStatus: 1}).mem.resident)" 2>/dev/null || echo "N/A")
    echo "  MongoDB连接数: $mongo_connections"
    echo "  MongoDB内存使用: ${mongo_memory}MB"
else
    echo "  ⚠️  MongoDB容器未运行"
fi

# Redis状态
if docker ps | grep -q tradingagents-redis; then
    redis_memory=$(docker exec tradingagents-redis redis-cli info memory 2>/dev/null | grep used_memory_human | cut -d: -f2 | tr -d '\r' || echo "N/A")
    redis_keys=$(docker exec tradingagents-redis redis-cli dbsize 2>/dev/null || echo "N/A")
    redis_connections=$(docker exec tradingagents-redis redis-cli info clients 2>/dev/null | grep connected_clients | cut -d: -f2 | tr -d '\r' || echo "N/A")
    echo "  Redis内存使用: $redis_memory"
    echo "  Redis键数量: $redis_keys"
    echo "  Redis连接数: $redis_connections"
else
    echo "  ⚠️  Redis容器未运行"
fi

# 网络状态
echo ""
echo "🌐 网络状态:"
if docker network ls | grep -q tradingagents-network; then
    network_containers=$(docker network inspect tradingagents-network --format '{{range .Containers}}{{.Name}} {{end}}' 2>/dev/null || echo "N/A")
    echo "  网络中的容器: $network_containers"
else
    echo "  ⚠️  TradingAgents网络不存在"
fi

# 应用状态
echo ""
echo "🚀 应用状态:"
if command -v python3 >/dev/null 2>&1 && [ -f "scripts/validation/check_system_status.py" ]; then
    echo "  正在检查应用状态..."
    timeout 30 python3 scripts/validation/check_system_status.py 2>/dev/null || echo "  ⚠️  应用状态检查超时或失败"
else
    echo "  ⚠️  无法执行应用状态检查"
fi

# 系统资源
echo ""
echo "💻 系统资源:"
if command -v free >/dev/null 2>&1; then
    free -h
elif command -v vm_stat >/dev/null 2>&1; then
    # macOS系统
    echo "  内存信息 (macOS):"
    vm_stat | head -5
fi

if command -v df >/dev/null 2>&1; then
    echo "  磁盘空间:"
    df -h | grep -E '^/dev/'
fi

echo ""
echo "⏰ 监控时间: $(date)"
echo "🎯 监控完成"