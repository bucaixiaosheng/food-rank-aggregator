# 部署指南

## 环境要求

### 必需
- Docker 20.10+
- Docker Compose 2.0+
- 2GB+ 内存
- 10GB+ 磁盘空间

### 可选
- 高德地图API Key（用于POI搜索）
- Playwright浏览器缓存（加速爬虫）

## 快速部署

### 1. 克隆项目

```bash
git clone git@github.com:bucaixiaosheng/food-rank-aggregator.git
cd food-rank-aggregator
```

### 2. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件
vim .env
```

**必须配置的环境变量:**
```bash
# 数据库路径
DATABASE_URL=sqlite:///data/food_rank.db

# 高德地图API Key（可选）
AMAP_API_KEY=your_amap_api_key_here

# 前端API地址
VITE_API_BASE_URL=http://localhost:8000
```

### 3. 一键启动

```bash
# 给启动脚本执行权限
chmod +x start.sh

# 启动服务
./start.sh
```

### 4. 访问应用

- **前端**: http://localhost:5173
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 详细部署步骤

### 使用Docker Compose

```bash
# 构建镜像
docker-compose build

# 后台启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启服务
docker-compose restart
```

### 手动部署（开发环境）

#### 后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -e .

# 安装Playwright浏览器
playwright install chromium

# 初始化数据库
python scripts/init_db.py

# 启动服务
uvicorn app.main:app --reload --port 8000
```

#### 前端

```bash
cd frontend

# 安装依赖
npm install

# 开发模式
npm run dev

# 生产构建
npm run build
npm run preview
```

## 生产环境部署

### 1. 使用Nginx反向代理

```nginx
# /etc/nginx/sites-available/food-rank
server {
    listen 80;
    server_name your-domain.com;

    # 前端
    location / {
        proxy_pass http://localhost:5173;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 后端API
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2. 使用Supervisor管理进程

```ini
# /etc/supervisor/conf.d/food-rank.conf
[program:food-rank-backend]
command=/path/to/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
directory=/path/to/food-rank-aggregator/backend
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/food-rank/backend.log

[program:food-rank-frontend]
command=npm run preview
directory=/path/to/food-rank-aggregator/frontend
user=www-data
autostart=true
autorestart=true
```

### 3. 性能优化

#### 数据库索引

```sql
-- 餐厅表索引
CREATE INDEX idx_restaurant_cuisine ON restaurant(cuisine_type);
CREATE INDEX idx_restaurant_rating ON restaurant(rating);
CREATE INDEX idx_restaurant_location ON restaurant(latitude, longitude);

-- 用户活动索引
CREATE INDEX idx_user_activity_user ON user_activity(user_id);
CREATE INDEX idx_user_activity_created ON user_activity(created_at);
```

#### 缓存配置

推荐使用Redis作为缓存（未来优化）:
```bash
# 添加到docker-compose.yml
redis:
  image: redis:alpine
  ports:
    - "6379:6379"
```

### 4. 日志管理

```bash
# 查看后端日志
docker-compose logs -f backend

# 查看前端日志
docker-compose logs -f frontend

# 日志轮转配置（logrotate）
# /etc/logrotate.d/food-rank
/var/log/food-rank/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

## 监控和告警

### 健康检查脚本

```bash
#!/bin/bash
# health_check.sh

RESPONSE=$(curl -s http://localhost:8000/health)

if echo "$RESPONSE" | grep -q "healthy"; then
    echo "✅ 服务正常"
    exit 0
else
    echo "❌ 服务异常"
    # 发送告警（邮件/短信/钉钉等）
    exit 1
fi
```

### Cron定时任务

```bash
# 每5分钟检查一次
*/5 * * * * /path/to/health_check.sh >> /var/log/food-rank/health.log 2>&1

# 每天凌晨2点清理过期数据
0 2 * * * cd /path/to/food-rank && python scripts/cleanup.py >> /var/log/food-rank/cleanup.log 2>&1
```

## 故障排查

### 常见问题

#### 1. 数据库连接失败
```bash
# 检查数据库文件权限
ls -la data/food_rank.db

# 重新初始化数据库
python scripts/init_db.py
```

#### 2. 爬虫失败
```bash
# 检查Playwright浏览器
playwright install

# 检查网络连接
curl -I https://www.meituan.com
```

#### 3. 前端无法访问后端
```bash
# 检查CORS配置
# 确保.env中的VITE_API_BASE_URL正确

# 检查防火墙
sudo ufw status
```

### 日志分析

```bash
# 查看错误日志
grep "ERROR" /var/log/food-rank/backend.log

# 实时监控
tail -f /var/log/food-rank/backend.log
```

## 备份和恢复

### 数据库备份

```bash
# 备份
sqlite3 data/food_rank.db ".backup data/backup_$(date +%Y%m%d).db"

# 恢复
sqlite3 data/food_rank.db ".recover data/backup_20260328.db"
```

### 自动备份脚本

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# 备份数据库
sqlite3 data/food_rank.db ".backup $BACKUP_DIR/food_rank_$DATE.db"

# 删除7天前的备份
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
```

## 升级指南

### 从v1.0升级到v2.0

1. 备份数据库
2. 拉取最新代码
3. 重新构建镜像
4. 迁移数据库
5. 重启服务

```bash
# 拉取代码
git pull origin main

# 备份数据
cp data/food_rank.db data/food_rank_backup.db

# 重新构建
docker-compose build

# 迁移数据（如果有）
python scripts/migrate.py

# 重启服务
docker-compose down
docker-compose up -d
```

## 安全建议

1. **修改默认端口**
2. **配置HTTPS**（使用Let's Encrypt）
3. **限制API访问频率**
4. **定期更新依赖**
5. **敏感信息使用环境变量**
6. **启用日志审计**

## 联系支持

- **GitHub Issues**: https://github.com/bucaixiaosheng/food-rank-aggregator/issues
- **邮箱**: support@example.com
