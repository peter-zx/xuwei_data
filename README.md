# 数据处理工具

专业Excel数据整理解决方案，支持智能表头映射与数据提取。

## 功能特性

### 核心功能

#### Excel文件处理
- 支持上传 .xlsx 和 .xls 格式文件
- 自动识别并处理多个Sheet
- 提供文件信息和Sheet数量展示

#### 智能表头映射
- 为每个Sheet单独设置表头所在行号
- 支持自动映射和手动自定义映射
- 特别优化"佳哥26年数据信息"sheet的映射逻辑（使用预定义的 A2 B2 D2 J2 I2 M2 L2 K2 映射关系）

#### 数据处理和分析
- 根据映射关系提取数据
- 处理多个标准字段：姓名、电话、身份证、残疾证、身份证到期时间、残疾证到期时间、残疾证等级、残疾证类型
- 支持数据验证和错误处理

#### 结果展示
- 清晰展示每个Sheet的处理结果
- 显示映射关系和实际数据
- 支持多Sheet结果的横向滚动浏览

### 用户体验优化

#### 现代化界面设计
- 响应式布局，适配不同屏幕尺寸
- 步骤式引导流程（上传→映射→分析→结果）
- 卡片式设计，清晰的信息层级
- 拖拽上传功能

#### 交互体验
- 直观的文件上传区域
- 清晰的步骤指示器
- 专业的错误提示和加载状态
- 现代化的视觉反馈

## 安装和运行

### 环境要求
- Python 3.8+
- pip

### 安装步骤

1. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 运行应用
```bash
python app/main.py
```

4. 访问应用
打开浏览器访问：http://localhost:5000

## 项目结构

```
data-processing-tool/
├── app/                    # 应用核心模块
│   ├── __init__.py
│   ├── main.py            # Flask主应用
│   ├── excel_processor.py # Excel处理模块
│   └── header_matcher.py  # 表头匹配模块
├── config/                # 配置模块
│   ├── __init__.py
│   └── settings.py        # 配置文件
├── static/                # 静态资源
│   ├── css/
│   │   └── style.css      # 样式文件
│   ├── js/
│   │   └── app.js         # 前端JavaScript
│   └── images/            # 图片资源
├── templates/             # 模板文件
│   └── index.html         # 主页面
├── uploads/               # 上传文件目录
├── requirements.txt       # Python依赖
└── README.md             # 项目说明
```

## 使用说明

### 第一步：上传文件
1. 点击上传区域或拖拽Excel文件
2. 支持 .xlsx 和 .xls 格式
3. 最大文件大小：16MB

### 第二步：设置映射
1. 为每个Sheet设置表头所在行
2. 查看自动匹配的映射关系
3. 手动调整映射（可选）
4. 佳哥26年数据信息sheet会自动使用预定义映射

### 第三步：分析数据
1. 点击"开始分析"按钮
2. 等待数据处理完成

### 第四步：查看结果
1. 查看每个Sheet的提取结果
2. 检查映射关系和数据
3. 点击"导出Excel"下载结果文件
4. 或点击"重新开始"处理新文件

## 技术栈

### 后端
- Flask 3.0.0 - Web框架
- pandas 2.1.4 - 数据处理
- openpyxl 3.1.2 - Excel文件处理
- numpy 1.26.2 - 数值计算

### 前端
- 原生JavaScript - 无框架依赖
- CSS3 - 现代化样式
- Font Awesome - 图标库

## 开发说明

### 配置文件
配置文件位于 `config/settings.py`，包含：
- 标准表头定义
- 佳哥sheet预定义映射
- 关键词映射表
- 应用配置

### 添加新的标准字段
在 `config/settings.py` 中修改 `STANDARD_HEADERS` 列表。

### 添加新的关键词映射
在 `config/settings.py` 中修改 `KEYWORD_MAP` 字典。

## 许可证

MIT License

## 联系方式

如有问题或建议，请联系开发团队。
