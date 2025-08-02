# A股分析多智能体系统Docker部署指南

## 概述

本文档提供基于TradingAgents-CN项目的A股分析多智能体系统的完整Docker部署方案。系统包含多个分析Agent、多层缓存架构、多LLM支持，并集成了完整的数据源系统。

## 系统架构

### 核心组件
```
┌─────────────────────────────────────────────────────────────┐
│                  TradingAgents-CN Web界面                     │
│                    (端口: 8501)                              │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────────────────┐
│              多智能体分析系统                                 │
│  ┌─────────────────┬─────────────────┬─────────────────┐    │
│  │   财务指标      │   行业对比      │   估值分析      │    │
│  │    Agent       │    Agent       │    Agent       │    │
│  └─────────────────┴─────────────────┴─────────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              报告整合Agent                           │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────────────────┐
│                数据层                                        │
│  ┌─────────────┬─────────────┬─────────────────────────┐    │
│  │   MongoDB   │    Redis    │      文件缓存           │    │
│  │  (27017)    │   (6379)    │                         │    │
│  └─────────────┴─────────────┴─────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │            数据源集成                                │    │
│  │      Tushare + AkShare + FinnHub                    │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────────────────┐
│                LLM层                                         │
│  ┌─────────────┬─────────────┬─────────────────────────┐    │
│  │  DashScope  │  DeepSeek   │     自定义OpenAPI       │    │
│  │  (阿里云)   │  (性价比)   │      本地Ollama         │    │
│  └─────────────┴─────────────┴─────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Docker配置扩展

### 1. 增强的docker-compose.yml

项目已有完善的Docker配置，针对A股分析功能的优化建议：

```yaml
# 在现有docker-compose.yml基础上的优化配置
version: '3.8'

services:
  # 主要Web应用服务 (已配置完善)
  web:
    build: .
    image: tradingagents-cn:latest
    container_name: TradingAgents-web
    ports:
      - "8501:8501"
    volumes:
      - .env:/app/.env
      - ./web:/app/web
      - ./tradingagents:/app/tradingagents
      - ./logs:/app/logs
      - ./config:/app/config
      - ./data:/app/data              # 数据目录持久化
      - ./cache:/app/cache            # 缓存目录持久化
      - ./results:/app/results        # 分析结果持久化
    environment:
      # A股分析特定环境变量
      TRADINGAGENTS_ANALYSIS_STOCK_ENABLED: "true"
      TRADINGAGENTS_DEFAULT_RESEARCH_LEVEL: "3"
      TRADINGAGENTS_MAX_CONCURRENT_ANALYSIS: "3"
      TRADINGAGENTS_CACHE_TTL_HOURS: "24"
      # 资源限制
      TRADINGAGENTS_MAX_MEMORY_MB: "2048"
      TRADINGAGENTS_TOKEN_LIMIT_PER_REQUEST: "50000"
    restart: unless-stopped
    depends_on:
      mongodb:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 15s
      retries: 3
      start_period: 90s
    # 资源限制
    deploy:
      resources:
        limits:
          memory: 3G
          cpus: '2.0'
        reservations:
          memory: 1G
          cpus: '0.5'

  # A股分析专用Worker服务 (可选扩展)
  analysis-worker:
    build: .
    image: tradingagents-cn:latest
    container_name: TradingAgents-analysis-worker
    profiles:
      - analysis-worker
    volumes:
      - .env:/app/.env
      - ./tradingagents:/app/tradingagents
      - ./logs:/app/logs
      - ./data:/app/data
      - ./cache:/app/cache
      - ./results:/app/results
    environment:
      TRADINGAGENTS_WORKER_MODE: "true"
      TRADINGAGENTS_ANALYSIS_STOCK_ENABLED: "true"
      TRADINGAGENTS_MONGODB_URL: mongodb://admin:tradingagents123@mongodb:27017/tradingagents?authSource=admin
      TRADINGAGENTS_REDIS_URL: redis://:tradingagents123@redis:6379
    command: python -m tradingagents.workers.analysis_worker
    restart: unless-stopped
    depends_on:
      - mongodb
      - redis
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'

  # MongoDB (已配置完善，增加索引优化)
  mongodb:
    image: mongo:4.4
    container_name: tradingagents-mongodb
    restart: unless-stopped
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: tradingagents123
      MONGO_INITDB_DATABASE: tradingagents
    volumes:
      - mongodb_data:/data/db
      - ./scripts/mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js:ro
      - ./scripts/mongo-indexes.js:/docker-entrypoint-initdb.d/mongo-indexes.js:ro
    networks:
      - tradingagents-network
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongo localhost:27017/test --quiet
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 60s
    # MongoDB性能优化
    command: mongod --wiredTigerCacheSizeGB 1

  # Redis (已配置完善，增加持久化优化)
  redis:
    image: redis:7-alpine
    container_name: tradingagents-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    command: >
      redis-server 
      --appendonly yes 
      --requirepass tradingagents123
      --maxmemory 512mb
      --maxmemory-policy allkeys-lru
      --save 900 1
      --save 300 10
      --save 60 10000
    volumes:
      - redis_data:/data
    networks:
      - tradingagents-network
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

# 新增数据卷
volumes:
  mongodb_data:
    driver: local
    name: tradingagents_mongodb_data
  redis_data:
    driver: local
    name: tradingagents_redis_data
  analysis_cache:
    driver: local
    name: tradingagents_analysis_cache
  analysis_results:
    driver: local
    name: tradingagents_analysis_results

networks:
  tradingagents-network:
    driver: bridge
    name: tradingagents-network
```

### 2. 增强的Dockerfile

```dockerfile
# 多阶段构建优化的Dockerfile
FROM python:3.10-slim-bookworm as base

# 设置工作目录和基础环境
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 系统依赖安装阶段
FROM base as system-deps

# 使用阿里云镜像源
RUN echo 'deb http://mirrors.aliyun.com/debian/ bookworm main' > /etc/apt/sources.list && \
    echo 'deb-src http://mirrors.aliyun.com/debian/ bookworm main' >> /etc/apt/sources.list && \
    echo 'deb http://mirrors.aliyun.com/debian/ bookworm-updates main' >> /etc/apt/sources.list && \
    echo 'deb-src http://mirrors.aliyun.com/debian/ bookworm-updates main' >> /etc/apt/sources.list && \
    echo 'deb http://mirrors.aliyun.com/debian-security bookworm-security main' >> /etc/apt/sources.list && \
    echo 'deb-src http://mirrors.aliyun.com/debian-security bookworm-security main' >> /etc/apt/sources.list

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    wkhtmltopdf \
    xvfb \
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    fonts-liberation \
    pandoc \
    procps \
    htop \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Python依赖安装阶段
FROM system-deps as python-deps

# 安装uv包管理器
RUN pip install -i https://mirrors.aliyun.com/pypi/simple uv

# 复制依赖文件
COPY requirements.txt pyproject.toml ./

# 多源轮询安装Python依赖
RUN set -e; \
    for src in \
        https://mirrors.aliyun.com/pypi/simple \
        https://pypi.tuna.tsinghua.edu.cn/simple \
        https://pypi.doubanio.com/simple \
        https://pypi.org/simple; do \
      echo "Try installing from $src"; \
      pip install --no-cache-dir -r requirements.txt -i $src && break; \
      echo "Failed at $src, try next"; \
    done

# 应用构建阶段
FROM python-deps as app

# 创建必要目录
RUN mkdir -p /app/data /app/logs /app/cache /app/results /app/config

# 复制应用代码
COPY . .

# 安装项目本身
RUN pip install -e . --no-deps

# 设置启动脚本
RUN echo '#!/bin/bash\nXvfb :99 -screen 0 1024x768x24 -ac +extension GLX &\nexport DISPLAY=:99\nexec "$@"' > /usr/local/bin/start-xvfb.sh \
    && chmod +x /usr/local/bin/start-xvfb.sh

# 健康检查脚本
COPY scripts/docker/healthcheck.sh /usr/local/bin/healthcheck.sh
RUN chmod +x /usr/local/bin/healthcheck.sh

# 创建非root用户
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=15s --start-period=60s --retries=3 \
    CMD /usr/local/bin/healthcheck.sh

EXPOSE 8501

CMD ["/usr/local/bin/start-xvfb.sh", "python", "-m", "streamlit", "run", "web/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
```

## 环境配置管理

### 1. 分环境配置策略

#### 开发环境 (.env.development)
```bash
# 开发环境配置
TRADINGAGENTS_ENV=development
TRADINGAGENTS_LOG_LEVEL=DEBUG
TRADINGAGENTS_ANALYSIS_STOCK_ENABLED=true

# 数据库配置 (本地)
MONGODB_ENABLED=false
REDIS_ENABLED=false
TRADINGAGENTS_CACHE_TYPE=file

# LLM配置 (本地优先)
LLM_PROVIDER=openai
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=llama3.1:8b

# 性能配置 (开发)
TRADINGAGENTS_MAX_CONCURRENT_ANALYSIS=1
TRADINGAGENTS_CACHE_TTL_HOURS=1
```

#### 测试环境 (.env.testing)
```bash
# 测试环境配置
TRADINGAGENTS_ENV=testing
TRADINGAGENTS_LOG_LEVEL=INFO
TRADINGAGENTS_ANALYSIS_STOCK_ENABLED=true

# 数据库配置 (Docker)
MONGODB_ENABLED=true
REDIS_ENABLED=true
MONGODB_HOST=mongodb
REDIS_HOST=redis

# LLM配置 (经济型)
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
DEEPSEEK_ENABLED=true

# 性能配置 (测试)
TRADINGAGENTS_MAX_CONCURRENT_ANALYSIS=2
TRADINGAGENTS_CACHE_TTL_HOURS=6
```

#### 生产环境 (.env.production)
```bash
# 生产环境配置
TRADINGAGENTS_ENV=production
TRADINGAGENTS_LOG_LEVEL=WARNING
TRADINGAGENTS_ANALYSIS_STOCK_ENABLED=true

# 数据库配置 (Docker)
MONGODB_ENABLED=true
REDIS_ENABLED=true
MONGODB_HOST=mongodb
REDIS_HOST=redis

# LLM配置 (生产级)
LLM_PROVIDER=dashscope
DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}

# 性能配置 (生产)
TRADINGAGENTS_MAX_CONCURRENT_ANALYSIS=5
TRADINGAGENTS_CACHE_TTL_HOURS=24
TRADINGAGENTS_TOKEN_LIMIT_PER_REQUEST=30000

# 监控配置
ENABLE_COST_TRACKING=true
COST_ALERT_THRESHOLD=500.0
USE_MONGODB_STORAGE=true
```

### 2. 配置验证脚本

创建配置验证工具：

```bash
# scripts/docker/validate-config.sh
#!/bin/bash
echo "🔍 验证Docker环境配置..."

# 检查必需的环境变量
required_vars=(
    "DASHSCOPE_API_KEY"
    "FINNHUB_API_KEY"
    "TUSHARE_TOKEN"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ 缺少必需的环境变量: $var"
        exit 1
    else
        echo "✅ $var 已配置"
    fi
done

# 检查服务连接
echo "🔍 检查数据库连接..."
python scripts/validation/check_system_status.py

echo "✅ 配置验证完成"
```

## 部署操作指南

### 1. 快速启动脚本

#### 智能启动脚本 (scripts/docker/smart-deploy.sh)
```bash
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
        COMPOSE_FILE="docker-compose.yml:docker-compose.dev.yml"
        ENV_FILE=".env.development"
        ;;
    "testing")
        COMPOSE_FILE="docker-compose.yml:docker-compose.test.yml"
        ENV_FILE=".env.testing"
        ;;
    "production")
        COMPOSE_FILE="docker-compose.yml"
        ENV_FILE=".env.production"
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
bash scripts/docker/validate-config.sh

# 构建决策
if [ "$REBUILD" = "auto" ]; then
    if docker images | grep -q "tradingagents-cn"; then
        if git diff --quiet HEAD~1 HEAD -- . ':!*.md' ':!docs/'; then
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
else
    docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE up -d $BUILD_FLAG
fi

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 30

# 健康检查
echo "🔍 健康检查..."
bash scripts/docker/health-check.sh

echo "✅ 部署完成!"
echo ""
echo "🌐 访问地址:"
echo "  Web应用: http://localhost:8501"
echo "  Redis管理: http://localhost:8081"
echo "  MongoDB管理: http://localhost:8082 (需要--profile management)"
echo ""
echo "📊 查看日志:"
echo "  docker-compose logs -f web"
echo "  docker-compose logs -f mongodb"
echo "  docker-compose logs -f redis"
```

#### 健康检查脚本 (scripts/docker/health-check.sh)
```bash
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
    if netstat -tln | grep -q ":$port "; then
        echo "  ✅ $name ($port): 端口开放"
    else
        echo "  ❌ $name ($port): 端口关闭"
    fi
done

# 检查应用功能
echo ""
echo "🧪 检查应用功能..."

# Web应用健康检查
if curl -s -f http://localhost:8501/_stcore/health > /dev/null; then
    echo "  ✅ Web应用: 响应正常"
else
    echo "  ❌ Web应用: 响应异常"
fi

# 数据库连接检查
docker exec tradingagents-mongodb mongo --eval "db.adminCommand('ping')" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "  ✅ MongoDB: 连接正常"
else
    echo "  ❌ MongoDB: 连接失败"
fi

# Redis连接检查
docker exec tradingagents-redis redis-cli ping > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "  ✅ Redis: 连接正常"
else
    echo "  ❌ Redis: 连接失败"
fi

echo ""
echo "🎯 系统状态检查完成"
```

### 2. 一键部署命令

```bash
# 开发环境部署
./scripts/docker/smart-deploy.sh development auto

# 测试环境部署
./scripts/docker/smart-deploy.sh testing force

# 生产环境部署 (带分析Worker)
./scripts/docker/smart-deploy.sh production auto analysis-worker

# 快速重启
docker-compose restart web

# 查看实时日志
docker-compose logs -f --tail=100 web
```

## 性能优化建议

### 1. 容器资源配置

#### 推荐配置表
| 组件 | CPU | 内存 | 说明 |
|------|-----|------|------|
| Web应用 | 2核 | 3GB | 主要分析服务 |
| MongoDB | 1核 | 1GB | 数据存储 |
| Redis | 0.5核 | 512MB | 缓存服务 |
| Analysis Worker | 1核 | 2GB | 可选分析队列 |

#### 资源限制配置
```yaml
# docker-compose.yml中的资源配置
deploy:
  resources:
    limits:
      memory: 3G
      cpus: '2.0'
    reservations:
      memory: 1G
      cpus: '0.5'
```

### 2. 缓存策略优化

#### MongoDB优化配置
```javascript
// scripts/mongo-indexes.js - MongoDB索引优化
db = db.getSiblingDB('tradingagents');

// 股票数据索引
db.stock_data.createIndex({ 
    "symbol": 1, 
    "date": -1, 
    "data_source": 1 
});

// 分析结果索引
db.analysis_results.createIndex({ 
    "symbol": 1, 
    "analysis_date": -1, 
    "analysis_type": 1 
});

// TTL索引 - 自动清理过期数据
db.cache_data.createIndex(
    { "created_at": 1 }, 
    { expireAfterSeconds: 86400 * 7 } // 7天过期
);

print("索引创建完成");
```

#### Redis优化配置
```bash
# Redis配置优化
redis-server \
  --maxmemory 512mb \
  --maxmemory-policy allkeys-lru \
  --save 900 1 \
  --save 300 10 \
  --save 60 10000
```

### 3. 并发处理优化

#### 环境变量配置
```bash
# 性能调优环境变量
TRADINGAGENTS_MAX_CONCURRENT_ANALYSIS=3    # 最大并发分析数
TRADINGAGENTS_ANALYSIS_TIMEOUT=300         # 分析超时时间(秒)
TRADINGAGENTS_CACHE_TTL_HOURS=24          # 缓存生存时间
TRADINGAGENTS_MAX_MEMORY_MB=2048          # 最大内存使用
TRADINGAGENTS_WORKER_POOL_SIZE=4          # 工作线程池大小
```

## 监控和运维

### 1. 日志管理

#### 日志配置
```yaml
# docker-compose.yml中的日志配置
logging:
  driver: "json-file"
  options:
    max-size: "100m"
    max-file: "5"
    compress: "true"
```

#### 日志查看脚本
```bash
# scripts/docker/view-logs.sh
#!/bin/bash

SERVICE=${1:-web}
LINES=${2:-100}

echo "📋 查看 $SERVICE 服务日志 (最近 $LINES 行)"
echo "============================================"

case $SERVICE in
    "web"|"app")
        docker-compose logs -f --tail=$LINES web
        ;;
    "db"|"mongodb")
        docker-compose logs -f --tail=$LINES mongodb
        ;;
    "cache"|"redis")
        docker-compose logs -f --tail=$LINES redis
        ;;
    "all")
        docker-compose logs -f --tail=$LINES
        ;;
    *)
        echo "支持的服务: web, db, cache, all"
        ;;
esac
```

### 2. 性能监控

#### 监控脚本 (scripts/docker/monitor.sh)
```bash
#!/bin/bash
# 系统性能监控脚本

echo "📊 TradingAgents-CN 性能监控"
echo "=============================="

# 容器资源使用
echo "📦 容器资源使用:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}" | grep tradingagents

# 磁盘使用
echo ""
echo "💾 磁盘使用:"
docker system df

# 数据库状态
echo ""
echo "🗄️ 数据库状态:"

# MongoDB状态
mongo_stats=$(docker exec tradingagents-mongodb mongo --quiet --eval "
db.runCommand({serverStatus: 1}).connections
")
echo "MongoDB连接数: $mongo_stats"

# Redis状态
redis_memory=$(docker exec tradingagents-redis redis-cli info memory | grep used_memory_human | cut -d: -f2)
redis_keys=$(docker exec tradingagents-redis redis-cli dbsize)
echo "Redis内存使用: $redis_memory"
echo "Redis键数量: $redis_keys"

# 应用状态
echo ""
echo "🚀 应用状态:"
python scripts/validation/check_system_status.py --brief
```

### 3. 备份和恢复

#### 自动备份脚本 (scripts/docker/backup.sh)
```bash
#!/bin/bash
# 数据备份脚本

BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "💾 开始数据备份到: $BACKUP_DIR"

# MongoDB备份
echo "📄 备份MongoDB数据..."
docker exec tradingagents-mongodb mongodump \
    --host localhost:27017 \
    --username admin \
    --password tradingagents123 \
    --authenticationDatabase admin \
    --db tradingagents \
    --out /tmp/backup

docker cp tradingagents-mongodb:/tmp/backup "$BACKUP_DIR/mongodb"

# Redis备份
echo "📄 备份Redis数据..."
docker exec tradingagents-redis redis-cli --rdb /tmp/dump.rdb
docker cp tradingagents-redis:/tmp/dump.rdb "$BACKUP_DIR/redis.rdb"

# 配置备份
echo "📄 备份配置文件..."
cp .env "$BACKUP_DIR/"
cp docker-compose.yml "$BACKUP_DIR/"

# 日志备份
echo "📄 备份日志文件..."
cp -r logs "$BACKUP_DIR/" 2>/dev/null || true

echo "✅ 备份完成: $BACKUP_DIR"
```

#### 恢复脚本 (scripts/docker/restore.sh)
```bash
#!/bin/bash
# 数据恢复脚本

BACKUP_DIR=${1}

if [ -z "$BACKUP_DIR" ] || [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ 请指定有效的备份目录"
    echo "用法: $0 <backup_directory>"
    exit 1
fi

echo "🔄 从备份恢复: $BACKUP_DIR"

# 停止服务
echo "⏹️ 停止服务..."
docker-compose down

# 恢复MongoDB
if [ -d "$BACKUP_DIR/mongodb" ]; then
    echo "📄 恢复MongoDB数据..."
    docker-compose up -d mongodb
    sleep 10
    docker cp "$BACKUP_DIR/mongodb" tradingagents-mongodb:/tmp/
    docker exec tradingagents-mongodb mongorestore \
        --host localhost:27017 \
        --username admin \
        --password tradingagents123 \
        --authenticationDatabase admin \
        --drop \
        /tmp/mongodb
fi

# 恢复Redis
if [ -f "$BACKUP_DIR/redis.rdb" ]; then
    echo "📄 恢复Redis数据..."
    docker cp "$BACKUP_DIR/redis.rdb" tradingagents-redis:/data/dump.rdb
fi

# 启动所有服务
echo "🚀 启动服务..."
docker-compose up -d

echo "✅ 恢复完成"
```

### 4. 故障排除指南

#### 常见问题和解决方案

| 问题 | 症状 | 解决方案 |
|------|------|----------|
| 内存不足 | 容器OOM, 分析失败 | 增加内存限制，优化Token使用 |
| 数据库连接失败 | MongoDB/Redis连接错误 | 检查网络配置，重启数据库服务 |
| API配额超限 | LLM调用失败 | 检查API密钥，调整并发数 |
| 缓存问题 | 数据加载缓慢 | 清理缓存，检查Redis状态 |
| 端口冲突 | 服务启动失败 | 修改端口映射，检查端口占用 |

#### 故障诊断脚本 (scripts/docker/diagnose.sh)
```bash
#!/bin/bash
# 故障诊断脚本

echo "🔍 TradingAgents-CN 故障诊断"
echo "============================"

# 检查Docker状态
echo "🐳 Docker环境检查:"
docker --version
docker-compose --version
docker system df

# 检查容器状态
echo ""
echo "📦 容器状态检查:"
docker-compose ps

# 检查网络连接
echo ""
echo "🌐 网络连接检查:"
docker network ls | grep tradingagents

# 检查日志错误
echo ""
echo "📋 最近错误日志:"
docker-compose logs --tail=50 | grep -i error

# 检查资源使用
echo ""
echo "📊 资源使用检查:"
docker stats --no-stream

# 检查环境配置
echo ""
echo "⚙️ 环境配置检查:"
python scripts/validation/check_system_status.py

echo ""
echo "🎯 诊断完成"
```

## 总结

本部署指南提供了TradingAgents-CN项目A股分析多智能体系统的完整Docker部署方案，包括：

1. **完整的容器化架构** - 基于现有Docker基础设施的优化配置
2. **分环境配置管理** - 开发、测试、生产环境的差异化配置
3. **自动化部署脚本** - 一键部署和智能构建决策
4. **性能优化策略** - 资源限制、缓存优化、并发控制
5. **完善的监控运维** - 日志管理、性能监控、备份恢复
6. **故障排除指南** - 常见问题诊断和解决方案

通过这套部署方案，可以实现A股分析多智能体系统的可靠、高效、可维护的容器化部署。