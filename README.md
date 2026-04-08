# Doc2PDF 文档转PDF工具

一款简洁高效的文档批量转换工具，支持将 Word、Excel、PPT、TXT 文件批量转换为 PDF 格式。

## 功能特性

- 📁 **文件夹选择** - 点击选择本地文件夹，自动扫描多层级结构
- ✅ **灵活选择** - 支持按文件夹批量勾选，精确选择要转换的文件
- 📄 **多格式支持** - 支持 Word(.doc/.docx)、Excel(.xls/.xlsx)、PPT(.ppt/.pptx)、TXT 转 PDF
- 📋 **保持结构** - 转换后保持原文件夹结构不变
- 🔧 **格式兼容** - 支持 WPS、Office COM 接口转换旧版 .doc 格式
- 🎨 **终端风格** - 黑色主题日志展示，清晰显示转换结果

## 快速开始

### 1. 安装依赖

```bash
cd C:\Users\Administrator\Desktop\doc2pdf_tool
.\venv\Scripts\Activate
pip install -r requirements.txt
```

### 2. 启动工具

```bash
python backend\main.py
```

### 3. 访问

打开浏览器访问：**http://localhost:8503**

## 使用方法

1. **选择源文件夹** - 点击大框选择要转换的文件夹
2. **选择文件** - 勾选要转换的文件或文件夹
3. **设置输出** - 选择输出位置（默认桌面）
4. **开始转换** - 点击按钮，查看日志结果

## 输出说明

转换后的文件保存在：
```
C:\Users\Administrator\Desktop\Output_MMDD_HHMMSS\源文件夹名\子文件夹\文件.pdf
```

示例：
```
C:\Users\Administrator\Desktop\Output_0408_115547\01\02\03\data\文档.pdf
```

## 项目结构

```
doc2pdf_tool/
├── backend/
│   ├── main.py        # FastAPI 服务 + HTML前端
│   └── scanner.py     # 文件夹扫描器
├── converters/
│   └── doc2pdf.py    # PDF转换器
├── venv/              # Python虚拟环境
├── requirements.txt    # 依赖列表
└── start.bat          # 一键启动脚本
```

## 技术栈

| 组件 | 技术 |
|------|------|
| Web框架 | FastAPI + Uvicorn |
| 前端 | HTML5 + CSS3 + JavaScript |
| 文档转换 | python-docx / openpyxl / python-pptx / reportlab |
| COM接口 | pywin32 (支持WPS/Office) |

## 系统要求

- Windows 10/11
- Python 3.10+
- WPS Office 或 Microsoft Office（用于.doc格式转换）

## 常见问题

**Q: .doc 文件转换失败？**  
A: 确保已安装 WPS Office 或 Microsoft Office，程序会自动调用 COM 接口转换。

**Q: 转换的PDF是空白或格式错乱？**  
A: 可能是文档格式较复杂，尝试用 WPS/Office 手动另存为 PDF。

## 版本历史

- v1.0 - 正式发布版本，支持多格式转换和文件夹结构保持
