# 部署指南

## 快速开始

### 本地开发环境

#### 1. 环境准备
```bash
# 克隆项目
git clone <repository-url>
cd ai_agent

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

#### 2. 配置环境
```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env，添加你的API密钥
# CLAUDE_API_KEY=sk_***
```

#### 3. 初始化数据库
```bash
# 创建必要的目录
mkdir -p data/memories data/vectors logs

# 数据库会在第一次运行时自动初始化
```

#### 4. 运行应用
```bash
# 方式1：直接运行
python server.py

# 方式2：使用uvicorn
uvicorn server:app --reload

# 方式3：使用make
make run
```

访问 API 文档: http://localhost:8000/docs

### Docker部署

#### 1. 构建镜像
```bash
docker build -t ai-agent:latest .
```

#### 2. 运行容器
```bash
docker run -d \
  --name ai-agent \
  -p 8000:8000 \
  -e CLAUDE_API_KEY=your_key_here \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  ai-agent:latest
```

#### 3. 查看日志
```bash
docker logs -f ai-agent
```

### Docker Compose部署

#### 1. 启动服务
```bash
docker-compose up -d
```

#### 2. 查看状态
```bash
docker-compose ps
```

#### 3. 停止服务
```bash
docker-compose down
```

## 生产部署

### AWS 部署

#### 方案1: EC2 + 手动部署

```bash
# 1. SSH到实例
ssh -i key.pem ubuntu@your-instance-ip

# 2. 安装依赖
sudo apt-get update
sudo apt-get install -y python3.9 python3-pip git

# 3. 克隆项目
git clone <repository-url>
cd ai_agent

# 4. 创建虚拟环境
python3.9 -m venv venv
source venv/bin/activate

# 5. 安装依赖
pip install -r requirements.txt

# 6. 配置环境
cp .env.example .env
# 编辑 .env 添加密钥

# 7. 使用Systemd管理
sudo tee /etc/systemd/system/ai-agent.service > /dev/null <<EOF
[Unit]
Description=AI Agent Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/ai_agent
ExecStart=/home/ubuntu/ai_agent/venv/bin/python server.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable ai-agent
sudo systemctl start ai-agent

# 8. 检查状态
sudo systemctl status ai-agent
```

#### 方案2: ECS + Docker

```bash
# 1. 推送镜像到ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

docker build -t ai-agent .
docker tag ai-agent:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/ai-agent:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/ai-agent:latest

# 2. 在ECS中创建任务定义和服务
# 使用AWS控制台或CLI
```

#### 方案3: Lambda + API Gateway

```python
# handler.py
import json
from app.agent.agent import Agent

def lambda_handler(event, context):
    user_id = event['pathParameters']['user_id']
    message = json.loads(event['body'])['message']
    
    agent = Agent(user_id=user_id)
    response = agent.chat(message)
    
    return {
        'statusCode': 200,
        'body': json.dumps({'response': response})
    }
```

### Google Cloud 部署

#### Cloud Run

```bash
# 1. 建立项目
gcloud config set project YOUR_PROJECT_ID

# 2. 构建并推送镜像
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/ai-agent

# 3. 部署到Cloud Run
gcloud run deploy ai-agent \
  --image gcr.io/YOUR_PROJECT_ID/ai-agent \
  --platform managed \
  --region us-central1 \
  --set-env-vars CLAUDE_API_KEY=your_key_here
```

### Azure 部署

#### App Service

```bash
# 1. 创建资源组
az group create --name ai-agent-rg --location eastus

# 2. 创建App Service计划
az appservice plan create \
  --name ai-agent-plan \
  --resource-group ai-agent-rg \
  --sku B1 \
  --is-linux

# 3. 创建Web应用
az webapp create \
  --resource-group ai-agent-rg \
  --plan ai-agent-plan \
  --name ai-agent-app \
  --runtime "PYTHON:3.9"

# 4. 配置环境变量
az webapp config appsettings set \
  --resource-group ai-agent-rg \
  --name ai-agent-app \
  --settings CLAUDE_API_KEY=your_key_here

# 5. 部署代码
az webapp up --name ai-agent-app
```

### Kubernetes部署

#### 1. 创建配置
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-agent
  template:
    metadata:
      labels:
        app: ai-agent
    spec:
      containers:
      - name: ai-agent
        image: your-registry/ai-agent:latest
        ports:
        - containerPort: 8000
        env:
        - name: CLAUDE_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: claude-api-key
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 1Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

#### 2. 部署
```bash
# 创建Secret
kubectl create secret generic api-keys --from-literal=claude-api-key=your_key

# 部署应用
kubectl apply -f deployment.yaml

# 创建Service
kubectl expose deployment ai-agent --type=LoadBalancer --port=80 --target-port=8000

# 检查状态
kubectl get pods
kubectl get svc
```

## 监控与日志

### 日志管理

```python
# 查看日志
tail -f logs/agent.log

# 日志级别配置在 .env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### 性能监控

```bash
# 使用Prometheus + Grafana
# 添加到 requirements.txt
pip install prometheus-client
```

```python
# 在server.py中集成
from prometheus_client import Counter, Histogram, generate_latest

chat_counter = Counter('chat_requests_total', 'Total chat requests')
response_time = Histogram('response_time_seconds', 'Response time')
```

### 健康检查

```bash
# 测试API健康状态
curl http://localhost:8000/health

# 监控脚本
#!/bin/bash
while true; do
  curl -f http://localhost:8000/health || echo "Service is down"
  sleep 60
done
```

## 备份与恢复

### 备份数据库

```bash
# SQLite备份
cp data/memories/memory.db data/memories/memory.db.backup
cp data/vectors/vectors.db data/vectors/vectors.db.backup

# 或使用脚本
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
sqlite3 data/memories/memory.db ".backup 'data/memories/memory_${DATE}.db'"
sqlite3 data/vectors/vectors.db ".backup 'data/vectors/vectors_${DATE}.db'"
```

### 恢复数据库

```bash
cp data/memories/memory.db.backup data/memories/memory.db
cp data/vectors/vectors.db.backup data/vectors/vectors.db
```

## 故障排查

### 常见问题

#### 1. Claude API 错误

```
错误: APIError: Authentication failed
解决: 检查CLAUDE_API_KEY是否正确设置
```

#### 2. 内存不足

```
错误: MemoryError
解决: 增加系统内存或优化向量存储
      - 减少MAX_MEMORIES
      - 清理过期数据
      - 启用向量缓存
```

#### 3. 数据库锁定

```
错误: Database is locked
解决: 检查是否有多个进程访问数据库
      - 使用连接池
      - 增加超时时间
```

### 调试模式

```bash
# 启用调试
export LOG_LEVEL=DEBUG
export API_DEBUG=true
python server.py
```

## 性能优化

### 1. 缓存优化

```python
# 启用Redis缓存
pip install redis

# 在config中配置
CACHE_BACKEND = "redis"
REDIS_URL = "redis://localhost:6379"
```

### 2. 数据库优化

```sql
-- 分析查询性能
EXPLAIN QUERY PLAN SELECT * FROM memories WHERE user_id = ?;

-- 创建复合索引
CREATE INDEX idx_user_memory ON memories(user_id, memory_type);
```

### 3. 并发优化

```python
# 使用连接池
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=4)
```

## 安全加固

### 1. API 认证

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/chat")
async def chat(request: ChatRequest, credentials: HTTPAuthCredentials = Depends(security)):
    # 验证token
    pass
```

### 2. HTTPS

```bash
# 使用Let's Encrypt
sudo certbot certonly --standalone -d your-domain.com

# 配置Nginx反向代理
```

### 3. 环境变量加密

```bash
# 使用密钥管理服务
# AWS Secrets Manager
# Azure Key Vault
# Google Cloud Secret Manager
```

## 升级与维护

### 版本升级

```bash
# 备份现有数据
cp -r data data.backup

# 拉取新版本
git pull origin main

# 安装新依赖
pip install -r requirements.txt --upgrade

# 重启服务
systemctl restart ai-agent
```

### 数据迁移

```bash
# 如果修改了数据库模式
python scripts/migrate_db.py
```

---

**最后更新**: 2026年5月8日
