# 液相色谱仪系统 Docker 部署方案

## 🐳 方案概述

基于Docker容器化部署，最小化对树莓派系统的修改，提供简单、可靠、易维护的部署方案。

### 核心优势
- **最小化系统修改**: 只需安装Docker，无需复杂配置
- **环境隔离**: 应用运行在容器中，不污染宿主系统
- **一键部署**: `docker-compose up -d` 即可启动
- **易于维护**: 容器化管理，更新重启简单
- **跨平台**: 可在任何支持Docker的ARM64设备运行

## 📦 容器架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                     树莓派宿主机                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐ │
│  │   Frontend      │  │    Backend      │  │     Redis     │ │
│  │  (Nginx+Vue)    │  │ (FastAPI+SQLite)│  │  (缓存/队列)   │ │
│  │  Port: 80       │  │  Port: 8008     │  │ Port: 6379    │ │
│  └─────────────────┘  └─────────────────┘  └───────────────┘ │
│           │                     │                     │      │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │   SQLite DB     │  │     MQTT        │                   │
│  │  (本地文件)      │  │   (消息队列)     │                   │
│  │  持久化存储      │  │  外部broker     │                   │
│  └─────────────────┘  └─────────────────┘                   │
│                                                             │
│  设备访问: /dev/ttyAMA* → Backend容器 (privileged)           │
│  网络设备: Host网络模式                                      │
│  数据库: SQLite文件映射到宿主机                              │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 快速部署指南

### 1. 系统要求

#### 最小配置
- **硬件**: 树莓派3B+ (1GB RAM)
- **存储**: 32GB MicroSD卡
- **系统**: Raspberry Pi OS Lite (64-bit)
- **Docker**: 20.10+

#### 推荐配置
- **硬件**: 树莓派4B (4GB/8GB RAM)
- **存储**: 64GB+ MicroSD卡或SSD
- **系统**: Raspberry Pi OS Lite (64-bit)
- **网络**: 千兆网卡 + WiFi

### 2. 安装Docker

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 添加用户到docker组
sudo usermod -aG docker $USER

# 安装Docker Compose
sudo apt install docker-compose-plugin -y

# 验证安装
docker --version
docker compose version

# 重启应用用户组权限
newgrp docker
```

### 3. 系统配置（最小化修改）

```bash
# 启用串口（唯一需要的系统修改）
sudo raspi-config
# Interface Options → Serial Port → No (login shell) → Yes (hardware enabled)

# 添加串口配置到 /boot/config.txt
echo 'enable_uart=1' | sudo tee -a /boot/config.txt

# 重启应用配置
sudo reboot
```

## 📁 项目文件结构

创建以下Docker部署文件：

### 1. docker-compose.yml

```yaml
version: '3.8'

services:
  # Redis 缓存
  redis:
    image: redis:7-alpine
    container_name: chromatography-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # FastAPI 后端 (使用SQLite)
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: chromatography-backend
    environment:
      - DATABASE_URL=sqlite:///app/data/chromatography.db
      - REDIS_URL=redis://redis:6379/0
      - MQTT_BROKER=${MQTT_BROKER:-broker.emqx.io}
      - MQTT_PORT=${MQTT_PORT:-1883}
    ports:
      - "8008:8008"
    volumes:
      - ./backend:/app
      - ./data/logs:/app/logs
      - ./data/database:/app/data  # SQLite数据库文件目录
    devices:
      - /dev/ttyAMA0:/dev/ttyAMA0  # 压力传感器
      - /dev/ttyAMA1:/dev/ttyAMA1
      - /dev/ttyAMA2:/dev/ttyAMA2  # 泵控制器
      - /dev/ttyAMA3:/dev/ttyAMA3  # 检测器
    privileged: true  # 访问串口设备需要特权模式
    network_mode: host  # 使用主机网络访问IP设备
    depends_on:
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8008/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Vue 前端
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: chromatography-frontend
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./docker/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - backend
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  redis_data:

networks:
  default:
    name: chromatography-network
```

### 2. 后端Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim-bookworm

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要目录
RUN mkdir -p /app/logs /app/data

# 暴露端口
EXPOSE 8008

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8008/health || exit 1

# 启动命令
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8008", "--reload"]
```

### 3. 前端Dockerfile

```dockerfile
# frontend/Dockerfile
# 构建阶段
FROM node:18-alpine AS builder

WORKDIR /app

# 复制package文件
COPY package*.json ./

# 安装依赖
RUN npm ci --only=production

# 复制源代码
COPY . .

# 构建生产版本
RUN npm run build

# 生产阶段
FROM nginx:alpine

# 复制构建结果
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制nginx配置
COPY docker/nginx.conf /etc/nginx/nginx.conf

# 暴露端口
EXPOSE 80 443

# 启动nginx
CMD ["nginx", "-g", "daemon off;"]
```

### 4. Nginx配置

```nginx
# docker/nginx.conf
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # 日志配置
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log;

    # 基本配置
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_proxied expired no-cache no-store private must-revalidate;
    gzip_types text/plain text/css text/xml text/javascript
               application/x-javascript application/xml+rss
               application/javascript application/json;

    server {
        listen 80;
        server_name _;
        root /usr/share/nginx/html;
        index index.html index.htm;

        # 前端静态文件
        location / {
            try_files $uri $uri/ /index.html;

            # 缓存静态资源
            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
                expires 1y;
                add_header Cache-Control "public, immutable";
            }
        }

        # API代理到后端
        location /api/ {
            proxy_pass http://chromatography-backend:8008;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # 超时设置
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # WebSocket支持
        location /ws/ {
            proxy_pass http://chromatography-backend:8008;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # 健康检查
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
```

### 5. 环境变量配置

```bash
# .env
# 数据库配置 (SQLite - 无需用户名密码)
DATABASE_URL=sqlite:///app/data/chromatography.db

# MQTT配置
MQTT_BROKER=broker.emqx.io
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=

# 应用配置
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# 安全配置
SECRET_KEY=your_secret_key_here
JWT_SECRET=your_jwt_secret_here
```

### 6. SQLite数据库初始化脚本

```python
# backend/init_database.py
import sqlite3
import os
from datetime import datetime

def init_sqlite_database(db_path="/app/data/chromatography.db"):
    """初始化SQLite数据库"""

    # 确保目录存在
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # 连接数据库（不存在会自动创建）
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 设备数据表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS device_data (
            id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
            device_id VARCHAR(50) NOT NULL,
            device_type VARCHAR(20) NOT NULL,
            value REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20) DEFAULT 'normal'
        )
    """)

    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_device_data_timestamp ON device_data(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_device_data_device_id ON device_data(device_id)")

    # MQTT消息日志表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mqtt_messages (
            id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
            topic VARCHAR(255) NOT NULL,
            payload TEXT,
            qos INTEGER DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 系统日志表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_logs (
            id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
            level VARCHAR(10) NOT NULL,
            message TEXT NOT NULL,
            module VARCHAR(50),
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 插入初始数据
    cursor.execute("""
        INSERT OR IGNORE INTO device_data (device_id, device_type, value) VALUES
        ('pressure_sensor_1', 'pressure', 0.0),
        ('detector_1', 'detector', 0.0),
        ('pump_1', 'pump', 0.0)
    """)

    # 提交更改
    conn.commit()
    conn.close()

    print(f"SQLite数据库初始化完成: {db_path}")

if __name__ == "__main__":
    init_sqlite_database()
```

```bash
# 在Dockerfile中添加初始化命令
# 修改backend/Dockerfile，在启动命令前添加：
RUN python init_database.py
```

## 🚀 部署命令

### 1. 一键部署

```bash
# 克隆代码到树莓派
git clone <your-repo-url> /opt/chromatography
cd /opt/chromatography

# 复制环境变量文件
cp .env.example .env
# 编辑 .env 文件设置MQTT等配置（SQLite无需密码）

# 创建数据目录
mkdir -p data/database data/logs

# 构建并启动所有服务
docker compose up -d

# 查看服务状态
docker compose ps
docker compose logs -f
```

### 2. 单独管理服务

```bash
# 启动特定服务
docker compose up -d redis
docker compose up -d backend
docker compose up -d frontend

# 查看日志
docker compose logs -f backend
docker compose logs -f frontend

# 重启服务
docker compose restart backend

# 停止所有服务
docker compose down

# 完全清理（包括数据卷）
docker compose down -v
```

### 3. 更新部署

```bash
# 更新代码
git pull

# 重新构建并启动
docker compose build
docker compose up -d

# 或者仅更新特定服务
docker compose build backend
docker compose up -d backend
```

## 📊 监控和维护

### 1. 服务监控脚本

```bash
#!/bin/bash
# docker/monitor.sh

echo "=== Docker服务状态 ==="
docker compose ps

echo -e "\n=== 容器资源使用 ==="
docker stats --no-stream

echo -e "\n=== 系统资源 ==="
echo "内存使用:"
free -h

echo "磁盘使用:"
df -h

echo "系统温度:"
vcgencmd measure_temp 2>/dev/null || echo "无法读取温度"

echo -e "\n=== 服务健康检查 ==="
curl -s http://localhost/health && echo "Frontend: OK" || echo "Frontend: FAIL"
curl -s http://localhost:8008/health && echo "Backend: OK" || echo "Backend: FAIL"

echo -e "\n=== 最近日志 ==="
echo "Backend错误日志:"
docker compose logs --tail=5 backend | grep -i error

echo "前端访问日志:"
docker compose logs --tail=5 frontend | grep -v "/health"
```

### 2. 自动备份脚本

```bash
#!/bin/bash
# docker/backup.sh

BACKUP_DIR="/opt/chromatography/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份SQLite数据库
cp ./data/database/chromatography.db $BACKUP_DIR/db_$DATE.db

# 备份配置文件
tar -czf $BACKUP_DIR/config_$DATE.tar.gz .env docker/

# 清理旧备份（保留7天）
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "备份完成: $BACKUP_DIR"
```

### 3. 定时任务设置

```bash
# 添加到crontab
crontab -e

# 每天3点自动备份
0 3 * * * /opt/chromatography/docker/backup.sh >> /var/log/chromatography-backup.log 2>&1

# 每小时检查服务状态
0 * * * * /opt/chromatography/docker/monitor.sh >> /var/log/chromatography-monitor.log 2>&1
```

## 🔒 安全配置

### 1. 防火墙设置

```bash
# 安装并配置ufw
sudo apt install ufw -y

# 基本安全规则
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 允许必要端口
sudo ufw allow ssh
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS

# 启用防火墙
sudo ufw enable
```

### 2. Docker安全配置

```yaml
# docker-compose.override.yml (生产环境)
version: '3.8'

services:
  backend:
    # 限制容器权限
    cap_drop:
      - ALL
    cap_add:
      - DAC_OVERRIDE  # 访问设备文件
    # 只读根文件系统
    read_only: true
    tmpfs:
      - /tmp
      - /app/logs
    # 资源限制
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '1.0'

  frontend:
    read_only: true
    tmpfs:
      - /tmp
      - /var/cache/nginx
      - /var/run
    deploy:
      resources:
        limits:
          memory: 128M
          cpus: '0.5'
```

## 🐛 故障排除

### 常见问题解决

#### 1. 容器启动失败

```bash
# 查看详细错误日志
docker compose logs backend
docker compose logs frontend

# 检查端口占用
sudo netstat -tlnp | grep -E ':(80|8008|5432|6379)'

# 检查磁盘空间
df -h

# 检查内存使用
free -h
```

#### 2. 串口设备访问失败

```bash
# 检查设备文件权限
ls -l /dev/ttyAMA*

# 检查用户组权限
groups $USER

# 添加用户到dialout组
sudo usermod -aG dialout $USER

# 重新启动后端容器
docker compose restart backend
```

#### 3. 数据库连接问题

```bash
# 检查SQLite数据库文件
ls -la ./data/database/chromatography.db

# 连接数据库测试
docker compose exec backend python -c "
import sqlite3
conn = sqlite3.connect('/app/data/chromatography.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM device_data')
print(f'设备数据记录数: {cursor.fetchone()[0]}')
conn.close()
print('SQLite数据库连接正常')
"

# 查看数据库表结构
docker compose exec backend python -c "
import sqlite3
conn = sqlite3.connect('/app/data/chromatography.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type=\\"table\\"')
tables = cursor.fetchall()
print('数据库表:', [table[0] for table in tables])
conn.close()
"
```

#### 4. 网络连接问题

```bash
# 检查容器网络
docker network ls
docker network inspect chromatography-network

# 测试容器间连通性
docker compose exec backend ping redis
docker compose exec frontend ping backend

# 检查MQTT连接
docker compose exec backend python -c "
import paho.mqtt.client as mqtt
client = mqtt.Client()
client.connect('broker.emqx.io', 1883, 60)
print('MQTT连接成功')
"
```

## 📈 性能优化

### 1. 资源配置优化

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    environment:
      - SQLITE_JOURNAL_MODE=WAL  # 提升并发性能
      - SQLITE_SYNCHRONOUS=NORMAL  # 平衡性能和安全性
      - SQLITE_CACHE_SIZE=-64000  # 64MB缓存
      - SQLITE_TEMP_STORE=memory  # 临时表存储在内存

  redis:
    command: redis-server --maxmemory 128mb --maxmemory-policy allkeys-lru

  backend:
    environment:
      - WORKERS=2
      - MAX_CONNECTIONS=100
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '1.0'
        reservations:
          memory: 256M
          cpus: '0.5'
```

### 2. 监控指标

```bash
# 系统性能监控
#!/bin/bash
echo "=== 性能指标 ==="
echo "CPU使用率:"
top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//'

echo "内存使用:"
free | grep Mem | awk '{printf "使用: %.1f%% (%s/%s)\n", $3/$2 * 100.0, $3, $2}'

echo "磁盘IO:"
iostat -x 1 1 | grep -A1 mmcblk

echo "网络流量:"
cat /proc/net/dev | grep eth0

echo "Docker容器资源:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
```

## ✅ 部署检查清单

### 部署前检查
- [ ] 树莓派硬件规格确认 (推荐4GB+ RAM)
- [ ] SD卡空间充足 (推荐64GB+)
- [ ] 网络连接正常
- [ ] 串口设备连接正确 (/dev/ttyAMA*)
- [ ] Docker环境安装完成

### 部署过程检查
- [ ] 代码克隆/上传完成
- [ ] 环境变量文件配置 (.env)
- [ ] Docker镜像构建成功
- [ ] 所有容器启动正常
- [ ] 数据库初始化完成
- [ ] 健康检查通过

### 功能测试检查
- [ ] Web界面访问正常 (http://树莓派IP)
- [ ] API接口响应正常 (/api/docs)
- [ ] MQTT连接和数据接收正常
- [ ] 串口设备通信正常
- [ ] 网络设备控制正常
- [ ] 数据采集和图表显示正常

## 🎯 预期性能指标

### 系统性能
- **启动时间**: <45秒 (首次构建), <10秒 (后续启动)
- **内存使用**: ~800MB (所有容器，无PostgreSQL)
- **CPU使用**: <15% (正常运行)
- **存储空间**: ~1.5GB (包含数据和日志，SQLite更轻量)

### 应用性能
- **Web响应时间**: <200ms
- **API响应时间**: <100ms
- **MQTT消息延迟**: <50ms
- **SQLite查询**: <10ms (本地文件，更快)
- **串口通信**: <100ms

## 📞 技术支持

### 维护建议
1. **定期更新**: 每月更新Docker镜像
2. **数据备份**: 每天自动备份数据库
3. **日志管理**: 配置日志轮转，避免磁盘占满
4. **性能监控**: 设置告警阈值
5. **安全更新**: 及时更新基础镜像

### 联系方式
- **系统日志**: `docker compose logs -f`
- **监控脚本**: `/opt/chromatography/docker/monitor.sh`
- **备份脚本**: `/opt/chromatography/docker/backup.sh`

---

## 🎉 部署成功

部署完成后，您可以通过以下方式访问系统：

- **Web界面**: http://树莓派IP地址
- **API文档**: http://树莓派IP地址:8008/docs
- **系统监控**: `docker compose ps`

**SQLite优势总结:**
- ✅ 零配置数据库：无需用户名密码，自动创建
- ✅ 轻量级：无需独立数据库容器，节省资源
- ✅ 高性能：本地文件访问，查询更快
- ✅ 简单备份：直接复制.db文件即可
- ✅ 适合嵌入式：完美适配树莓派等小型设备

**部署优势总结:**
- ✅ 零污染部署：除Docker外无需修改系统
- ✅ 一键启动：`docker compose up -d`
- ✅ 易于维护：容器化管理
- ✅ 资源隔离：各服务独立运行
- ✅ 高可用性：自动重启和健康检查
- ✅ 更轻量：SQLite减少内存和存储占用