# Excel 数据处理器

一个现代化的 Web 应用，用于智能处理 Excel 文件，支持多 Sheet 数据提取、表头映射配置和数据比对分析。

## 核心功能

### 1. 文件上传
- 支持 `.xlsx` 和 `.xls` 格式文件
- 拖拽上传和点击上传两种方式
- 自动识别文件中的所有 Sheet
- 显示每个 Sheet 的行数和列数统计
- 16MB 文件大小限制
- **配置缓存**：自动缓存相同文件的映射配置，下次上传时自动加载

### 2. 数据预览
- 显示每个 Sheet 的前 5 行原始数据
- 支持人工选择表头所在行（前 10 行可选）
- 选中的表头行会高亮显示
- 便于确认数据结构和表头位置

### 3. 表头映射配置
- 完全使用下拉列表选择映射关系
- 自动尝试匹配列名
- 支持自定义字段映射
- 标准字段可配置
- 界面美观，下拉框宽度适中，字体清晰

### 4. 数据映射
- 根据映射关系提取数据
- 支持多 Sheet 批量处理
- 自动过滤空数据记录
- **公式处理**：自动计算Excel公式，确保数据正确映射
- **日期格式化**：到期时间字段只显示年月日，去除时间部分
- 完善的错误处理机制

### 5. 数据比对 ⭐
- **三列并排显示**：每个Sheet并排展示，便于对比
- **智能人员匹配**：
  - 必要元素：姓名
  - 校对信息：身份证号、残疾证号
  - 匹配规则：姓名相同，且（身份证号相同 OR 残疾证号相同）视为同一人
- **相同人判定**：
  - 在所有Sheet中都有记录
  - 身份证号在所有Sheet中一致
  - 残疾证号在所有Sheet中一致
- **筛选功能**：全部 / 相同人 / 非相同人
- **数据量显示**：每个Sheet表头显示实际数据量
- **在线编辑**：双击单元格可编辑数据
- **搜索功能**：按姓名搜索
- **导出功能**：导出比对结果为CSV

### 6. 结果展示
- 清晰展示每个 Sheet 的处理结果
- 显示提取的数据记录数
- Tab 切换浏览不同 Sheet 的结果
- 支持横向滚动查看完整数据
- 统计总 Sheet 数、总记录数、成功处理数

### 7. 用户体验
- 步骤式引导流程（上传→预览→映射→映射→比对→结果）
- 实时操作反馈和错误提示
- 卡片式现代化设计
- 响应式布局，适配不同屏幕
- 流畅的过渡动画效果

## 技术栈

### 后端
- **Flask** - 轻量级 Python Web 框架
- **Pandas** - 强大的数据分析和 Excel 处理库
- **Openpyxl** - 处理 `.xlsx` 文件
- **xlrd** - 处理 `.xls` 文件
- **Werkzeug** - 文件上传和安全处理

### 前端
- **HTML5** - 语义化页面结构
- **CSS3** - 现代化样式设计
  - CSS 变量实现主题配色
  - Flexbox 和 Grid 布局
  - 响应式设计
  - 过渡动画
- **JavaScript (ES6+)** - 交互逻辑
  - Fetch API 进行异步请求
  - 模板字符串动态渲染
  - 事件委托

### 视觉效果
- 渐变色主题背景（紫色系）
- 卡片式设计
- 圆角和阴影效果
- 步骤进度指示器
- Toast 提示框动画
- 表格行悬停高亮
- 加载旋转动画

## 标准字段

系统支持提取以下 8 个标准字段：

| 字段名 | 说明 | 特殊处理 |
|--------|------|----------|
| 姓名 | 人员姓名 | 必要字段，用于匹配 |
| 电话 | 联系电话 | - |
| 身份证号 | 身份证号码 | 用于人员匹配和比对 |
| 残疾证号 | 残疾证号码 | 用于人员匹配和比对 |
| 身份证到期时间 | 身份证有效期 | 自动格式化为 YYYY-MM-DD |
| 残疾证到期时间 | 残疾证有效期 | 自动格式化为 YYYY-MM-DD |
| 残疾证等级 | 残疾等级 | - |
| 残疾证类型 | 残疾类型 | - |

这些字段可以通过修改 `get_standard_fields()` 函数进行扩展或修改。

## 项目结构

```
demo02/
├── app.py                 # Flask 后端应用
├── excel_processor.py     # Excel公式处理模块
├── requirements.txt       # Python 依赖
├── uploads/               # 上传文件存储目录（自动创建）
├── cache/                 # 缓存文件目录（自动清理，保留7天）
├── templates/
│   └── index.html         # 主页面模板
└── static/
    ├── style.css          # 样式文件
    ├── script.js          # 主要交互逻辑
    ├── mapping-cache.js   # 映射配置缓存模块
    └── event-bindings.js  # 事件绑定模块
```

## API 接口

### POST `/api/upload`
上传 Excel 文件并获取 Sheet 信息

**请求：**
- FormData 包含 `file` 字段

**响应：**
```json
{
  "success": true,
  "filename": "20240211_123456_file.xlsx",
  "sheets": [
    {
      "name": "Sheet1",
      "rows": 100,
      "columns": 10
    }
  ],
  "sheet_count": 1
}
```

### POST `/api/sheet-preview`
获取 Sheet 的前 N 行预览数据

**请求：**
```json
{
  "filename": "file.xlsx",
  "sheet_name": "Sheet1",
  "max_rows": 5
}
```

**响应：**
```json
{
  "success": true,
  "data": [
    ["列1", "列2", "列3"],
    ["数据1", "数据2", "数据3"]
  ]
}
```

### POST `/api/columns`
获取指定行作为表头的列名列表

**请求：**
```json
{
  "filename": "file.xlsx",
  "sheet_name": "Sheet1",
  "header_row": 0
}
```

**响应：**
```json
{
  "success": true,
  "columns": ["列1", "列2", "列3"]
}
```

### POST `/api/analyze`
根据映射配置分析提取数据

**请求：**
```json
{
  "filename": "file.xlsx",
  "mappings": {
    "Sheet1": {
      "header_row": 0,
      "fields": {
        "姓名": "姓名列",
        "身份证号": "身份证列"
      }
    }
  }
}
```

**响应：**
```json
{
  "success": true,
  "results": [
    {
      "name": "Sheet1",
      "mapping": {"姓名": "姓名列"},
      "data": [
        {
          "姓名": "张三",
          "身份证号": "123456",
          "身份证到期时间": "2024-12-31"
        }
      ],
      "record_count": 1,
      "success": true
    }
  ]
}
```

### POST `/api/compare`
数据比对，识别相同人员

**请求：**
```json
{
  "filename": "file.xlsx",
  "mappings": {
    "Sheet1": {...},
    "Sheet2": {...}
  }
}
```

**响应：**
```json
{
  "success": true,
  "sheet_names": ["Sheet1", "Sheet2"],
  "people_list": [
    {
      "_key": "person_0",
      "_name": "张三",
      "_id_cards": ["123456"],
      "_disability_cards": ["789012"],
      "_sheets": {
        "Sheet1": {"姓名": "张三", ...},
        "Sheet2": {"姓名": "张三", ...}
      },
      "_is_same": true,
      "_sheet_count": 2
    }
  ],
  "stats": {
    "total": 10,
    "same_count": 8,
    "diff_count": 2
  }
}
```

## 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行服务
```bash
python3 app.py
```

服务将在 `http://0.0.0.0:8080` 启动。

### 访问应用
在浏览器中打开 `http://localhost:8080`

## 配置说明

### 修改端口
编辑 `app.py` 最后一行：
```python
app.run(debug=True, host='0.0.0.0', port=YOUR_PORT)
```

### 修改文件大小限制
编辑 `app.py`：
```python
app.config['MAX_CONTENT_LENGTH'] = YOUR_SIZE * 1024 * 1024  # MB
```

### 修改标准字段
编辑 `app.py` 中的 `get_standard_fields()` 函数。

### 修改预览行数
编辑 `index.html` 中的 `CONFIG` 对象：
```javascript
const CONFIG = {
    maxPreviewRows: 10,  // 修改预览行数
    headerRowOptions: 20   // 修改表头可选行数
};
```

## 浏览器兼容性

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## 最新更新 (v2.0)

### 新增功能
- ✅ **配置缓存**：自动缓存映射配置，相同文件自动加载历史配置
- ✅ **数据比对**：多Sheet并排显示，智能识别相同人员
- ✅ **公式处理**：自动计算Excel公式，确保数据正确
- ✅ **日期格式化**：到期时间只显示年月日

### 优化改进
- ✅ **字段优化**：字段名称更规范，从9个精简到8个
  - '身份证' → '身份证号'
  - '残疾证' → '残疾证号'
  - 删除重复的'残疾证号'字段
- ✅ **界面优化**：
  - 移除重复的筛选按钮
  - Sheet表头显示实际数据量
  - 表格增加竖向分割线
  - 序号列居中对齐
- ✅ **匹配逻辑**：
  - 智能人员匹配：姓名 + (身份证号 OR 残疾证号)
  - 准确判断相同人：所有Sheet一致

## 开发者

本项目由 CodeBuddy 辅助开发。
