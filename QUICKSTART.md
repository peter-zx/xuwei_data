# 快速启动指南

## 第一次运行

### 1. 创建虚拟环境
```bash
cd data-processing-tool
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 启动应用
```bash
python run.py
```

### 4. 访问应用
打开浏览器访问：http://localhost:5000

## 日常使用

### 启动应用
```bash
cd data-processing-tool
source venv/bin/activate
python run.py
```

## 常见问题

### 问题1：端口被占用
修改 `run.py` 中的端口号：
```python
app.run(host='0.0.0.0', port=5001, debug=True)
```

### 问题2：文件上传失败
- 检查文件格式是否为 .xlsx 或 .xls
- 检查文件大小是否超过 16MB
- 检查 uploads 目录是否有写入权限

### 问题3：依赖安装失败
升级 pip：
```bash
pip install --upgrade pip
```

## 功能说明

### 支持的标准字段
- 姓名
- 电话
- 身份证
- 残疾证
- 身份证到期时间
- 残疾证到期时间
- 残疾证等级
- 残疾证类型

### 佳哥26年数据信息sheet
自动使用预定义映射：
- 姓名: A2
- 电话: B2
- 身份证: D2
- 残疾证: J2
- 身份证到期时间: I2
- 残疾证到期时间: M2
- 残疾证等级: L2
- 残疾证类型: K2

## 开发相关

### 项目结构
```
data-processing-tool/
├── app/                    # 应用核心
├── config/                # 配置文件
├── static/                # 静态资源
├── templates/             # HTML模板
├── uploads/               # 上传文件
└── run.py                # 启动脚本
```

### 添加新字段
编辑 `config/settings.py`：
```python
STANDARD_HEADERS = [
    '姓名', '电话', '身份证', '残疾证',
    '身份证到期时间', '残疾证到期时间',
    '残疾证等级', '残疾证类型',
    '新字段'  # 添加新字段
]
```

### 修改映射规则
编辑 `config/settings.py`：
```python
KEYWORD_MAP = {
    '姓名': ['姓名', '名字', '名称', '人员'],
    # 添加新的关键词映射
}
```
