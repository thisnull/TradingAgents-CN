#!/bin/bash
# 数据备份脚本

BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "💾 开始数据备份到: $BACKUP_DIR"

# 检查容器是否运行
if ! docker ps | grep -q tradingagents; then
    echo "❌ TradingAgents容器未运行，请先启动服务"
    exit 1
fi

# MongoDB备份
if docker ps | grep -q tradingagents-mongodb; then
    echo "📄 备份MongoDB数据..."
    docker exec tradingagents-mongodb mongodump \
        --host localhost:27017 \
        --username admin \
        --password tradingagents123 \
        --authenticationDatabase admin \
        --db tradingagents \
        --out /tmp/backup

    docker cp tradingagents-mongodb:/tmp/backup "$BACKUP_DIR/mongodb"
    
    if [ $? -eq 0 ]; then
        echo "  ✅ MongoDB备份完成"
    else
        echo "  ❌ MongoDB备份失败"
    fi
else
    echo "  ⚠️  MongoDB容器未运行，跳过备份"
fi

# Redis备份
if docker ps | grep -q tradingagents-redis; then
    echo "📄 备份Redis数据..."
    docker exec tradingagents-redis redis-cli --rdb /tmp/dump.rdb
    docker cp tradingagents-redis:/tmp/dump.rdb "$BACKUP_DIR/redis.rdb"
    
    if [ $? -eq 0 ]; then
        echo "  ✅ Redis备份完成"
    else
        echo "  ❌ Redis备份失败"
    fi
else
    echo "  ⚠️  Redis容器未运行，跳过备份"
fi

# 配置备份
echo "📄 备份配置文件..."
[ -f ".env" ] && cp .env "$BACKUP_DIR/"
[ -f "docker-compose.yml" ] && cp docker-compose.yml "$BACKUP_DIR/"
[ -f ".env.example" ] && cp .env.example "$BACKUP_DIR/"

# 日志备份
echo "📄 备份日志文件..."
if [ -d "logs" ]; then
    cp -r logs "$BACKUP_DIR/" 2>/dev/null || true
    echo "  ✅ 日志备份完成"
else
    echo "  ⚠️  日志目录不存在，跳过备份"
fi

# 分析结果备份
echo "📄 备份分析结果..."
if [ -d "results" ]; then
    cp -r results "$BACKUP_DIR/" 2>/dev/null || true
    echo "  ✅ 分析结果备份完成"
else
    echo "  ⚠️  结果目录不存在，跳过备份"
fi

# 缓存数据备份 (选择性)
if [ "$1" = "--include-cache" ] && [ -d "cache" ]; then
    echo "📄 备份缓存数据..."
    cp -r cache "$BACKUP_DIR/" 2>/dev/null || true
    echo "  ✅ 缓存数据备份完成"
fi

# 创建备份信息文件
echo "📄 创建备份信息..."
cat > "$BACKUP_DIR/backup_info.txt" << EOF
TradingAgents-CN 系统备份
========================
备份时间: $(date)
备份版本: $(git rev-parse HEAD 2>/dev/null || echo "未知")
备份包含:
- MongoDB数据库
- Redis缓存
- 配置文件
- 日志文件
- 分析结果
$([ "$1" = "--include-cache" ] && echo "- 缓存数据")

恢复命令:
./scripts/docker/restore.sh $BACKUP_DIR
EOF

# 计算备份大小
backup_size=$(du -sh "$BACKUP_DIR" | cut -f1)
echo ""
echo "✅ 备份完成!"
echo "📁 备份位置: $BACKUP_DIR"
echo "📊 备份大小: $backup_size"
echo ""
echo "🔄 恢复命令:"
echo "  ./scripts/docker/restore.sh $BACKUP_DIR"