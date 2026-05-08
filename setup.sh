#!/bin/bash
# 快速启动脚本

set -e

echo "================================"
echo "AI Agent Setup & Start"
echo "================================"

# 检查Python版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 升级pip
echo "Upgrading pip..."
pip install --upgrade pip

# 安装依赖
echo "Installing dependencies..."
pip install -r requirements.txt

# 创建.env文件
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env file and add your CLAUDE_API_KEY"
fi

# 创建数据目录
mkdir -p data/memories
mkdir -p data/vectors
mkdir -p logs

echo ""
echo "================================"
echo "✓ Setup completed!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your CLAUDE_API_KEY"
echo "2. Run 'python test.py' to test the system"
echo "3. Run 'python server.py' to start the server"
echo ""
