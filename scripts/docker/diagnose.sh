#!/bin/bash
# 故障诊断脚本

echo "🔍 TradingAgents-CN 故障诊断"
echo "============================"

# 检查Docker状态
echo "🐳 Docker环境检查:"
if command -v docker >/dev/null 2>&1; then
    echo "  ✅ Docker版本: $(docker --version)"
else
    echo "  ❌ Docker未安装"
    exit 1
fi

if command -v docker-compose >/dev/null 2>&1; then
    echo "  ✅ Docker Compose版本: $(docker-compose --version)"
else
    echo "  ❌ Docker Compose未安装"
    exit 1
fi

if docker info >/dev/null 2>&1; then
    echo "  ✅ Docker服务运行正常"
else
    echo "  ❌ Docker服务未运行"
    exit 1
fi

# Docker系统资源
echo ""
echo "💾 Docker系统资源:"
docker system df

# 检查容器状态
echo ""
echo "📦 容器状态检查:"
if docker-compose ps 2>/dev/null; then
    echo ""
else
    echo "  ❌ 无法获取容器状态，可能docker-compose.yml有问题"
fi

# 检查网络连接
echo "🌐 网络连接检查:"
if docker network ls | grep -q tradingagents; then
    network_info=$(docker network inspect tradingagents-network --format '{{range .Containers}}{{.Name}} {{end}}' 2>/dev/null)
    echo "  ✅ TradingAgents网络存在"
    echo "  📋 网络中的容器: $network_info"
else
    echo "  ❌ TradingAgents网络不存在"
fi

# 检查数据卷
echo ""
echo "💿 数据卷检查:"
volumes=$(docker volume ls | grep tradingagents || echo "")
if [ -n "$volumes" ]; then
    echo "  ✅ 发现TradingAgents数据卷:"
    echo "$volumes" | sed 's/^/    /'
else
    echo "  ⚠️  未发现TradingAgents数据卷"
fi

# 检查最近错误日志
echo ""
echo "📋 最近错误日志 (最近50行):"
if docker-compose logs --tail=50 2>/dev/null | grep -i -E "(error|exception|failed|fatal)" | tail -10; then
    echo ""
else
    echo "  ✅ 未发现明显错误"
fi

# 检查端口占用
echo "🌐 端口占用检查:"
ports=("8501" "27017" "6379" "8081" "8082")
for port in "${ports[@]}"; do
    if command -v netstat >/dev/null 2>&1; then
        port_info=$(netstat -tln 2>/dev/null | grep ":$port " || echo "")
    else
        port_info=$(ss -tln 2>/dev/null | grep ":$port " || echo "")
    fi
    
    if [ -n "$port_info" ]; then
        echo "  🟡 端口 $port 被占用"
    else
        echo "  ✅ 端口 $port 可用"
    fi
done

# 检查资源使用
echo ""
echo "📊 容器资源使用:"
if docker ps | grep -q tradingagents; then
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" | head -1
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" | grep tradingagents
else
    echo "  ⚠️  未找到运行中的TradingAgents容器"
fi

# 检查磁盘空间
echo ""
echo "💾 磁盘空间检查:"
available_space_kb=$(df . | tail -1 | awk '{print $4}')
available_space_gb=$((available_space_kb / 1024 / 1024))
echo "  可用空间: ${available_space_gb}GB"

if [ "$available_space_kb" -lt 1048576 ]; then  # 1GB in KB
    echo "  ⚠️  磁盘空间不足 (少于1GB)"
elif [ "$available_space_kb" -lt 2097152 ]; then  # 2GB in KB
    echo "  🟡 磁盘空间较少 (少于2GB)"
else
    echo "  ✅ 磁盘空间充足"
fi

# 检查配置文件
echo ""
echo "⚙️ 配置文件检查:"
config_files=(".env" "docker-compose.yml" ".env.example")
for file in "${config_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file 存在"
    else
        echo "  ❌ $file 不存在"
    fi
done

# 环境变量检查
echo ""
echo "🔑 关键环境变量检查:"
if [ -f ".env" ]; then
    source .env 2>/dev/null || true
    
    # 检查API密钥
    key_vars=("DASHSCOPE_API_KEY" "FINNHUB_API_KEY" "TUSHARE_TOKEN" "DEEPSEEK_API_KEY")
    for var in "${key_vars[@]}"; do
        value=$(eval echo \$$var)
        if [ -n "$value" ] && [ "$value" != "your_${var,,}_here" ]; then
            echo "  ✅ $var 已配置"
        else
            echo "  ❌ $var 未配置或使用默认值"
        fi
    done
else
    echo "  ❌ .env文件不存在"
fi

# 应用功能检查
echo ""
echo "🧪 应用功能检查:"
if [ -f "scripts/validation/check_system_status.py" ]; then
    echo "  🔍 执行系统状态检查..."
    timeout 30 python3 scripts/validation/check_system_status.py 2>/dev/null || echo "    ⚠️  系统状态检查超时或失败"
else
    echo "  ⚠️  系统状态检查脚本不存在"
fi

# 诊断建议
echo ""
echo "💡 诊断建议:"
echo "1. 如果容器无法启动，检查:"
echo "   - 端口冲突"
echo "   - 配置文件错误"
echo "   - 磁盘空间不足"
echo ""
echo "2. 如果服务异常，尝试:"
echo "   - docker-compose restart"
echo "   - docker-compose down && docker-compose up -d"
echo "   - 查看详细日志: docker-compose logs -f [service_name]"
echo ""
echo "3. 如果数据库连接失败:"
echo "   - 检查MongoDB/Redis容器状态"
echo "   - 验证数据库密码配置"
echo "   - 重启数据库服务"

echo ""
echo "⏰ 诊断时间: $(date)"
echo "🎯 诊断完成"