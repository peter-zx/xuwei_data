# 🚀 开始使用

## 快速启动（3步）

### 1️⃣ 安装依赖
```bash
cd data-processing-tool
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
```

### 2️⃣ 启动应用
```bash
python run.py
```

### 3️⃣ 访问应用
打开浏览器访问：**http://localhost:5000**

---

## 📋 功能清单

### ✅ Excel文件处理
- 支持 .xlsx 和 .xls 格式
- 自动识别多个Sheet
- 拖拽上传
- 文件大小限制：16MB

### ✅ 智能表头映射
- 自动匹配表头
- 手动调整映射
- 佳哥26年数据信息sheet自动映射
- 支持Excel坐标（A2, B3等）

### ✅ 数据提取
- 8个标准字段：姓名、电话、身份证、残疾证、身份证到期时间、残疾证到期时间、残疾证等级、残疾证类型
- 自动处理空值
- 数据验证

### ✅ 结果展示
- 清晰的表格展示
- 显示映射关系
- 记录数量统计
- 多Sheet支持

### ✅ 数据导出
- 导出为Excel文件
- 保留表头和映射
- 自动命名（带时间戳）

---

## 🎯 使用流程

```
上传文件 → 设置映射 → 分析数据 → 查看结果 → 导出Excel
```

### 第一步：上传文件
1. 点击上传区域或拖拽文件
2. 系统自动识别Sheet数量
3. 显示文件信息预览

### 第二步：设置映射
1. 为每个Sheet设置表头所在行
2. 查看自动匹配结果
3. 手动调整映射（可选）
4. 佳哥sheet自动使用预定义映射

### 第三步：分析数据
1. 点击"开始分析"
2. 等待处理完成
3. 自动跳转到结果页面

### 第四步：查看结果
1. 查看每个Sheet的提取结果
2. 检查映射关系
3. 点击"导出Excel"下载
4. 或点击"重新开始"处理新文件

---

## 📁 项目文件说明

| 文件/目录 | 说明 |
|-----------|------|
| `app/main.py` | Flask主应用，API端点 |
| `app/excel_processor.py` | Excel数据处理核心逻辑 |
| `app/header_matcher.py` | 表头智能匹配 |
| `config/settings.py` | 配置文件（表头、映射规则） |
| `static/css/style.css` | 现代化CSS样式 |
| `static/js/app.js` | 前端交互逻辑 |
| `templates/index.html` | 主页面模板 |
| `run.py` | 应用启动脚本 |
| `requirements.txt` | Python依赖列表 |

---

## 🔧 常见问题

### Q: 端口被占用怎么办？
A: 修改 `run.py` 中的端口号：
```python
app.run(host='0.0.0.0', port=5001, debug=True)
```

### Q: 如何添加新的标准字段？
A: 编辑 `config/settings.py`：
```python
STANDARD_HEADERS = [
    '姓名', '电话', '身份证', '残疾证',
    '身份证到期时间', '残疾证到期时间',
    '残疾证等级', '残疾证类型',
    '新字段'  # 添加这里
]
```

### Q: 佳哥sheet的映射规则是什么？
A: 在 `config/settings.py` 中定义：
```python
JIAGE_SHEET_HEADERS = {
    '姓名': 'A2',
    '电话': 'B2',
    '身份证': 'D2',
    '残疾证': 'J2',
    '身份证到期时间': 'I2',
    '残疾证到期时间': 'M2',
    '残疾证等级': 'L2',
    '残疾证类型': 'K2'
}
```

### Q: 如何修改自动匹配的关键词？
A: 编辑 `config/settings.py` 中的 `KEYWORD_MAP`

---

## 📖 文档

- **README.md** - 完整项目说明
- **QUICKSTART.md** - 快速启动指南
- **PROJECT_SUMMARY.md** - 项目完成总结

---

## 🎨 界面特点

- ✨ 现代化设计
- 📱 响应式布局
- 🎯 步骤式引导
- 💫 流畅动画
- 🔔 实时反馈
- 🎨 Font Awesome图标

---

## 💡 技术特点

### 后端
- Flask 3.0.0
- pandas 2.1.4
- openpyxl 3.1.2

### 前端
- 原生JavaScript（无框架）
- CSS3（Flexbox + Grid）
- Font Awesome 6.4.0

---

## 🎉 开始使用

现在就启动应用，体验强大的Excel数据处理功能！

```bash
python run.py
```

然后访问：**http://localhost:5000**

---

**祝使用愉快！** 🚀
