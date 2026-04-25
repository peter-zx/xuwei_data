FROM python:3.10-slim

LABEL maintainer="Doc2PDF Cloud Server"

WORKDIR /app

# 腾讯云镜像源 + 清华pip源
RUN sed -i 's/deb.debian.org/mirrors.cloud.tencent.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's/deb.debian.org/mirrors.cloud.tencent.com/g' /etc/apt/sources.list 2>/dev/null || true

# 安装 LibreOffice（云端转换备选方案）+ 中文字体
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice-writer \
    libreoffice-calc \
    libreoffice-impress \
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖（云端版本，不含 pywin32/pywinauto）
COPY requirements-cloud.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制项目代码
COPY config/ ./config/
COPY app/ ./app/
COPY .env.production .env

# 创建存储目录
RUN mkdir -p storage/uploads storage/outputs logs

# 暴露端口
EXPOSE 8503

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8503/api/health')" || exit 1

# 启动服务
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8503"]
