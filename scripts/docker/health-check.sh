#!/bin/bash
# 系统健康检查脚本

echo "🔍 系统健康检查"
echo "=================="

# 检查容器状态
echo "📦 检查容器状态..."
containers=("TradingAgents-web" "tradingagents-mongodb" "tradingagents-redis")

for container in "${containers[@]}"; do
    if docker ps --format "table {{.Names}}" | grep -q "$container"; then
        status=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "no-healthcheck")
        if [ "$status" = "healthy" ] || [ "$status" = "no-healthcheck" ]; then
            echo "  ✅ $container: 运行正常"
        else
            echo "  ❌ $container: 状态异常 ($status)"
        fi
    else
        echo "  ❌ $container: 未运行"
    fi
done

# 检查服务端口
echo ""
echo "🌐 检查服务端口..."
ports=("8501:Web应用" "27017:MongoDB" "6379:Redis" "8081:Redis管理")

for port_info in "${ports[@]}"; do
    IFS=':' read -r port name <<< "$port_info"
    if command -v netstat >/dev/null 2>&1; then
        if netstat -tln 2>/dev/null | grep -q ":$port "; then
            echo "  ✅ $name ($port): 端口开放"
        else
            echo "  ❌ $name ($port): 端口关闭"
        fi
    else
        # 使用ss命令作为替代
        if ss -tln 2>/dev/null | grep -q ":$port "; then
            echo "  ✅ $name ($port): 端口开放"
        else
            echo "  ❌ $name ($port): 端口关闭"
        fi
    fi
done

# 检查应用功能
echo ""
echo "🧪 检查应用功能..."

# Web应用健康检查
if curl -s -f http://localhost:8501/_stcore/health > /dev/null 2>&1; then
    echo "  ✅ Web应用: 响应正常"
else
    echo "  ❌ Web应用: 响应异常"
fi

# 数据库连接检查
if docker exec tradingagents-mongodb mongo --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
    echo "  ✅ MongoDB: 连接正常"
else
    echo "  ❌ MongoDB: 连接失败"
fi

# Redis连接检查
if docker exec tradingagents-redis redis-cli ping > /dev/null 2>&1; then
    echo "  ✅ Redis: 连接正常"
else
    echo "  ❌ Redis: 连接失败"
fi

echo ""
echo "🎯 系统状态检查完成"