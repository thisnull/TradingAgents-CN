#!/bin/bash
# 数据恢复脚本

BACKUP_DIR=${1}

if [ -z "$BACKUP_DIR" ] || [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ 请指定有效的备份目录"
    echo "用法: $0 <backup_directory>"
    echo ""
    echo "可用的备份目录:"
    if [ -d "./backups" ]; then
        ls -la ./backups/
    else
        echo "  (未找到备份目录)"
    fi
    exit 1
fi

echo "🔄 从备份恢复: $BACKUP_DIR"

# 检查备份完整性
echo "🔍 检查备份完整性..."
missing_files=0

if [ ! -f "$BACKUP_DIR/backup_info.txt" ]; then
    echo "  ⚠️  备份信息文件缺失"
fi

if [ ! -d "$BACKUP_DIR/mongodb" ] && [ ! -f "$BACKUP_DIR/redis.rdb" ]; then
    echo "  ❌ 未找到数据库备份文件"
    missing_files=1
fi

if [ $missing_files -eq 1 ]; then
    echo "❌ 备份文件不完整，无法恢复"
    exit 1
fi

# 显示备份信息
if [ -f "$BACKUP_DIR/backup_info.txt" ]; then
    echo ""
    echo "📋 备份信息:"
    cat "$BACKUP_DIR/backup_info.txt"
    echo ""
fi

# 确认恢复
read -p "⚠️  确认要恢复数据吗？这将覆盖现有数据 (y/N): " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "❌ 恢复操作已取消"
    exit 0
fi

# 停止服务
echo "⏹️ 停止服务..."
docker-compose down

# 恢复MongoDB
if [ -d "$BACKUP_DIR/mongodb" ]; then
    echo "📄 恢复MongoDB数据..."
    
    # 启动MongoDB
    docker-compose up -d mongodb
    echo "  ⏳ 等待MongoDB启动..."
    sleep 15
    
    # 检查MongoDB是否启动成功
    retry_count=0
    while [ $retry_count -lt 10 ]; do
        if docker exec tradingagents-mongodb mongo --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
            echo "  ✅ MongoDB启动成功"
            break
        fi
        echo "  ⏳ 等待MongoDB启动... ($((retry_count + 1))/10)"
        sleep 5
        retry_count=$((retry_count + 1))
    done
    
    if [ $retry_count -eq 10 ]; then
        echo "  ❌ MongoDB启动失败"
        exit 1
    fi
    
    # 复制备份文件到容器
    docker cp "$BACKUP_DIR/mongodb" tradingagents-mongodb:/tmp/
    
    # 执行恢复
    docker exec tradingagents-mongodb mongorestore \
        --host localhost:27017 \
        --username admin \
        --password tradingagents123 \
        --authenticationDatabase admin \
        --drop \
        /tmp/mongodb/tradingagents
    
    if [ $? -eq 0 ]; then
        echo "  ✅ MongoDB数据恢复完成"
    else
        echo "  ❌ MongoDB数据恢复失败"
    fi
    
    # 停止MongoDB
    docker-compose stop mongodb
else
    echo "  ⚠️  MongoDB备份不存在，跳过恢复"
fi

# 恢复Redis
if [ -f "$BACKUP_DIR/redis.rdb" ]; then
    echo "📄 恢复Redis数据..."
    
    # 启动Redis
    docker-compose up -d redis
    sleep 5
    
    # 停止Redis进程
    docker exec tradingagents-redis redis-cli shutdown
    sleep 2
    
    # 复制备份文件
    docker cp "$BACKUP_DIR/redis.rdb" tradingagents-redis:/data/dump.rdb
    
    if [ $? -eq 0 ]; then
        echo "  ✅ Redis数据恢复完成"
    else
        echo "  ❌ Redis数据恢复失败"
    fi
    
    # 停止Redis
    docker-compose stop redis
else
    echo "  ⚠️  Redis备份不存在，跳过恢复"
fi

# 恢复配置文件
echo "📄 恢复配置文件..."
if [ -f "$BACKUP_DIR/.env" ]; then
    cp "$BACKUP_DIR/.env" ./
    echo "  ✅ 环境配置恢复完成"
fi

if [ -f "$BACKUP_DIR/docker-compose.yml" ]; then
    if [ -f "./docker-compose.yml" ]; then
        cp "./docker-compose.yml" "./docker-compose.yml.backup"
        echo "  📁 原配置文件已备份为 docker-compose.yml.backup"
    fi
    cp "$BACKUP_DIR/docker-compose.yml" ./
    echo "  ✅ Docker配置恢复完成"
fi

# 恢复日志文件
if [ -d "$BACKUP_DIR/logs" ]; then
    echo "📄 恢复日志文件..."
    cp -r "$BACKUP_DIR/logs" ./
    echo "  ✅ 日志文件恢复完成"
fi

# 恢复分析结果
if [ -d "$BACKUP_DIR/results" ]; then
    echo "📄 恢复分析结果..."
    cp -r "$BACKUP_DIR/results" ./
    echo "  ✅ 分析结果恢复完成"
fi

# 恢复缓存数据 (可选)
if [ -d "$BACKUP_DIR/cache" ]; then
    echo "📄 恢复缓存数据..."
    cp -r "$BACKUP_DIR/cache" ./
    echo "  ✅ 缓存数据恢复完成"
fi

# 启动所有服务
echo "🚀 启动服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 30

# 验证恢复
echo "🔍 验证恢复结果..."
if [ -f "scripts/docker/health-check.sh" ]; then
    bash scripts/docker/health-check.sh
else
    docker-compose ps
fi

echo ""
echo "✅ 恢复完成!"
echo "🌐 Web应用: http://localhost:8501"
echo "📋 查看日志: docker-compose logs -f"