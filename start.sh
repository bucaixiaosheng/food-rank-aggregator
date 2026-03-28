#!/bin/bash

# 餐饮聚合推荐平台启动脚本

echo "🍽️  正在启动餐饮聚合推荐平台..."

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装"
    exit 1
fi

# 检查.env文件
if [ ! -f .env ]; then
    echo "⚠️  未找到.env文件，从.env.example创建..."
    cp .env.example .env
fi

# 创建数据目录
mkdir -p data

# 停止旧容器
echo "🛑 停止旧容器..."
docker-compose down

# 构建镜像
echo "🔨 构建Docker镜像..."
docker-compose build

# 启动服务
echo "🚀 启动服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 5

# 检查服务状态
if docker-compose ps | grep -q "Up"; then
    echo "✅ 服务启动成功！"
    echo ""
    echo "📱 访问地址："
    echo "   前端: http://localhost:5173"
    echo "   后端API: http://localhost:8000"
    echo "   API文档: http://localhost:8000/docs"
    echo ""
    echo "🛑 停止服务: docker-compose down"
    echo "📊 查看日志: docker-compose logs -f"
else
    echo "❌ 服务启动失败，请检查日志"
    docker-compose logs
    exit 1
fi
