# Docker部署脚本说明

本目录包含TradingAgents-CN项目的Docker部署和运维脚本。

## 脚本功能

### 部署脚本
- **smart-deploy.sh** - 智能部署脚本，支持多环境部署
- **validate-config.sh** - 配置验证脚本
- **health-check.sh** - 系统健康检查脚本

### 运维脚本
- **monitor.sh** - 系统性能监控脚本
- **backup.sh** - 数据备份脚本
- **restore.sh** - 数据恢复脚本
- **diagnose.sh** - 故障诊断脚本

### 健康检查
- **healthcheck.sh** - Docker容器健康检查脚本

### 原有脚本
- `docker-compose-start.bat` - 启动Docker Compose (Windows)
- `start_docker_services.*` - 启动Docker服务
- `stop_docker_services.*` - 停止Docker服务
- `mongo-init.js` - MongoDB初始化脚本

## 使用方法

### 快速部署
```bash
# 生产环境部署
./scripts/docker/smart-deploy.sh production auto

# 开发环境部署
./scripts/docker/smart-deploy.sh development auto

# 强制重新构建
./scripts/docker/smart-deploy.sh production force
```

### 系统监控
```bash
# 健康检查
./scripts/docker/health-check.sh

# 性能监控
./scripts/docker/monitor.sh

# 故障诊断
./scripts/docker/diagnose.sh
```

### 数据管理
```bash
# 数据备份
./scripts/docker/backup.sh

# 数据备份(包含缓存)
./scripts/docker/backup.sh --include-cache

# 数据恢复
./scripts/docker/restore.sh ./backups/20240101_120000
```

## 环境要求

- Docker 20.10+
- Docker Compose 1.29+
- Bash 4.0+
- curl (用于健康检查)

## 注意事项

1. 所有脚本需要在项目根目录执行
2. 确保Docker服务正在运行
3. 备份前请确保有足够的磁盘空间
4. 恢复操作会覆盖现有数据，请谨慎操作
