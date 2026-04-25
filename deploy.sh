#!/bin/bash
# Doc2PDF 云端部署脚本
# 在服务器上执行：bash deploy.sh

set -e

APP_NAME="doc2pdf"
APP_DIR="$HOME/doc2pdf"
PORT=8503

echo "========================================="
echo "  Doc2PDF 云端部署"
echo "========================================="

# 1. 拉取最新代码
echo "[1/5] 同步代码..."
cd "$APP_DIR"
git fetch origin
git reset --hard origin/main 2>/dev/null || git reset --hard origin/master 2>/dev/null || true

# 2. 构建镜像
echo "[2/5] 构建 Docker 镜像（含 LibreOffice，较慢请耐心）..."
sudo docker build -t "$APP_NAME" .

# 3. 停止旧容器
echo "[3/5] 停止旧容器..."
sudo docker stop "$APP_NAME" 2>/dev/null || true
sudo docker rm "$APP_NAME" 2>/dev/null || true

# 4. 启动新容器
echo "[4/5] 启动新容器..."
sudo docker run -d \
    --name "$APP_NAME" \
    --memory=512m \
    --memory-swap=1g \
    --restart=always \
    -p ${PORT}:${PORT} \
    -v "$APP_DIR/storage:/app/storage" \
    -v "$APP_DIR/logs:/app/logs" \
    "$APP_NAME"

# 5. 等待健康检查
echo "[5/5] 等待服务启动..."
sleep 5

# 验证
if sudo docker exec "$APP_NAME" python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:${PORT}/api/health').read().decode())" 2>/dev/null; then
    echo ""
    echo "✅ 部署成功！"
    echo "   Web界面: http://122.51.231.239:${PORT}"
    echo "   健康检查: http://122.51.231.239:${PORT}/api/health"
else
    echo ""
    echo "❌ 服务启动异常，查看日志："
    sudo docker logs "$APP_NAME" --tail 20
fi
