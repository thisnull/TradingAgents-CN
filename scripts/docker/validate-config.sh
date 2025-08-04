#!/bin/bash
# 配置验证脚本

echo "🔍 验证Docker环境配置..."

# 检查必需的环境变量
required_vars=(
    "DASHSCOPE_API_KEY"
    "FINNHUB_API_KEY"
)

# 可选但推荐的环境变量
optional_vars=(
    "TUSHARE_TOKEN"
    "DEEPSEEK_API_KEY"
    "GOOGLE_API_KEY"
    "OPENAI_API_KEY"
)

echo "📋 检查必需的环境变量..."
missing_required=0
for var in "${required_vars[@]}"; do
    value=$(env | grep "^$var=" | cut -d'=' -f2)
    if [ -z "$value" ] || [ "$value" = "your_${var,,}_here" ]; then
        echo "  ❌ 缺少必需的环境变量: $var"
        missing_required=1
    else
        echo "  ✅ $var 已配置"
    fi
done

echo ""
echo "📋 检查可选的环境变量..."
for var in "${optional_vars[@]}"; do
    value=$(env | grep "^$var=" | cut -d'=' -f2)
    if [ -z "$value" ] || [ "$value" = "your_${var,,}_here" ]; then
        echo "  ⚠️  可选变量未配置: $var"
    else
        echo "  ✅ $var 已配置"
    fi
done

# 检查Docker环境
echo ""
echo "🐳 检查Docker环境..."
if ! command -v docker >/dev/null 2>&1; then
    echo "  ❌ Docker未安装"
    exit 1
else
    echo "  ✅ Docker已安装: $(docker --version)"
fi

if ! command -v docker-compose >/dev/null 2>&1; then
    echo "  ❌ Docker Compose未安装"
    exit 1
else
    echo "  ✅ Docker Compose已安装: $(docker-compose --version)"
fi

# 检查Docker服务状态
if ! docker info >/dev/null 2>&1; then
    echo "  ❌ Docker服务未运行"
    exit 1
else
    echo "  ✅ Docker服务运行正常"
fi

# 检查端口占用
echo ""
echo "🌐 检查端口占用..."
ports_to_check=("8501" "27017" "6379" "8081")

for port in "${ports_to_check[@]}"; do
    if command -v netstat >/dev/null 2>&1; then
        if netstat -tln 2>/dev/null | grep -q ":$port "; then
            echo "  ⚠️  端口 $port 已被占用"
        else
            echo "  ✅ 端口 $port 可用"
        fi
    else
        # 使用ss命令作为替代
        if ss -tln 2>/dev/null | grep -q ":$port "; then
            echo "  ⚠️  端口 $port 已被占用"
        else
            echo "  ✅ 端口 $port 可用"
        fi
    fi
done

# 检查磁盘空间
echo ""
echo "💾 检查磁盘空间..."
available_space=$(df . | tail -1 | awk '{print $4}')
if [ "$available_space" -lt 2097152 ]; then  # 2GB in KB
    echo "  ⚠️  磁盘空间不足 (建议至少2GB)"
else
    echo "  ✅ 磁盘空间充足"
fi

if [ $missing_required -eq 1 ]; then
    echo ""
    echo "❌ 配置验证失败：缺少必需的环境变量"
    echo "💡 请在.env文件中配置所有必需的API密钥"
    exit 1
fi

echo ""
echo "✅ 配置验证完成"