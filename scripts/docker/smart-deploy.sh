#!/bin/bash
# A股分析系统智能部署脚本

set -e

echo "🚀 TradingAgents-CN A股分析系统部署"
echo "====================================="

# 参数解析
ENVIRONMENT=${1:-production}
REBUILD=${2:-auto}
PROFILE=${3:-default}

echo "📋 部署参数:"
echo "  环境: $ENVIRONMENT"
echo "  重建: $REBUILD"
echo "  配置文件: $PROFILE"

# 环境配置
case $ENVIRONMENT in
    "development")
        COMPOSE_FILE="docker-compose.yml"
        ENV_FILE=".env.development"
        ;;
    "testing")
        COMPOSE_FILE="docker-compose.yml"
        ENV_FILE=".env.testing"
        ;;
    "production")
        COMPOSE_FILE="docker-compose.yml"
        ENV_FILE=".env"
        ;;
    *)
        echo "❌ 未知环境: $ENVIRONMENT"
        exit 1
        ;;
esac

# 检查配置文件
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ 配置文件不存在: $ENV_FILE"
    echo "💡 请基于.env.example创建配置文件"
    exit 1
fi

# 加载环境配置
export $(cat $ENV_FILE | grep -v '^#' | xargs)

# 配置验证
echo "🔍 验证配置..."
if [ -f "scripts/docker/validate-config.sh" ]; then
    bash scripts/docker/validate-config.sh
else
    echo "⚠️ 配置验证脚本不存在，跳过验证"
fi

# 构建决策
if [ "$REBUILD" = "auto" ]; then
    if docker images | grep -q "tradingagents-cn"; then
        if git diff --quiet HEAD~1 HEAD -- . ':!*.md' ':!docs/' 2>/dev/null; then
            echo "📦 代码无变化，跳过构建"
            BUILD_FLAG=""
        else
            echo "🔄 检测到代码变化，重新构建"
            BUILD_FLAG="--build"
        fi
    else
        echo "🏗️ 首次部署，构建镜像"
        BUILD_FLAG="--build"
    fi
elif [ "$REBUILD" = "force" ]; then
    echo "🔄 强制重新构建"
    BUILD_FLAG="--build --no-cache"
else
    echo "📦 跳过构建"
    BUILD_FLAG=""
fi

# 部署服务
echo "🚀 启动服务..."
if [ "$PROFILE" = "analysis-worker" ]; then
    docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE up -d $BUILD_FLAG --profile analysis-worker
elif [ "$PROFILE" = "management" ]; then
    docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE up -d $BUILD_FLAG --profile management
else
    docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE up -d $BUILD_FLAG
fi

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 30

# 健康检查
echo "🔍 健康检查..."
if [ -f "scripts/docker/health-check.sh" ]; then
    bash scripts/docker/health-check.sh
else
    # 简单健康检查
    docker-compose ps
fi

echo "✅ 部署完成!"
echo ""
echo "🌐 访问地址:"
echo "  Web应用: http://localhost:8501"
echo "  Redis管理: http://localhost:8081"
if [ "$PROFILE" = "management" ]; then
    echo "  MongoDB管理: http://localhost:8082"
fi
echo ""
echo "📊 查看日志:"
echo "  docker-compose logs -f web"
echo "  docker-compose logs -f mongodb"
echo "  docker-compose logs -f redis"
echo ""
echo "🛠️ 管理命令:"
echo "  重启服务: docker-compose restart"
echo "  停止服务: docker-compose down"
echo "  查看状态: docker-compose ps"