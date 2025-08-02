# TradingAgents-CN A股分析多智能体系统
# Docker部署快速入门指南

## 系统要求

- Docker 20.10+
- Docker Compose 1.29+
- 4GB+ 可用内存
- 2GB+ 可用磁盘空间

## 快速开始

### 1. 准备配置文件
```bash
# 复制环境配置模板
cp .env.example .env

# 编辑配置文件，至少配置以下API密钥：
# - DASHSCOPE_API_KEY (阿里云百炼)
# - FINNHUB_API_KEY (美股数据)
# - TUSHARE_TOKEN (A股数据，推荐)
vim .env
```

### 2. 一键部署
```bash
# 使用智能部署脚本
./scripts/docker/smart-deploy.sh production auto

# 或使用传统方式
docker-compose up -d --build
```

### 3. 验证部署
```bash
# 健康检查
./scripts/docker/health-check.sh

# 访问应用
open http://localhost:8501
```

## 管理命令

### 服务管理
```bash
# 查看服务状态
docker-compose ps

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 查看日志
docker-compose logs -f web
```

### 系统监控
```bash
# 性能监控
./scripts/docker/monitor.sh

# 故障诊断
./scripts/docker/diagnose.sh
```

### 数据管理
```bash
# 备份数据
./scripts/docker/backup.sh

# 恢复数据
./scripts/docker/restore.sh ./backups/20240101_120000
```

## 服务端口

| 服务 | 端口 | 用途 |
|------|------|------|
| Web应用 | 8501 | 主要界面 |
| MongoDB | 27017 | 数据库 |
| Redis | 6379 | 缓存 |
| Redis管理 | 8081 | Redis管理界面 |
| MongoDB管理 | 8082 | MongoDB管理界面 (可选) |

## 故障排除

### 常见问题
1. **端口冲突** - 修改docker-compose.yml中的端口映射
2. **内存不足** - 减少并发分析数量或增加系统内存
3. **API配额超限** - 检查API密钥配置和使用量
4. **容器启动失败** - 查看容器日志定位问题

### 获取帮助
```bash
# 完整诊断
./scripts/docker/diagnose.sh

# 查看详细文档
docs/deployment/DOCKER_DEPLOYMENT_GUIDE.md
```

## 高级配置

### 启用MongoDB管理界面
```bash
docker-compose up -d --profile management
```

### 启用分析Worker
```bash
./scripts/docker/smart-deploy.sh production auto analysis-worker
```

### 自定义资源限制
编辑docker-compose.yml中的deploy.resources配置段。