#!/bin/bash
# Web应用健康检查脚本

# 检查Streamlit健康状态
if curl -s -f http://localhost:8501/_stcore/health > /dev/null 2>&1; then
    exit 0
else
    exit 1
fi