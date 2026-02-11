# 项目架构文档

## 📦 前端模块化架构

### 目录结构

```
static/
├── js/
│   ├── app-main.js              # 主应用入口
│   ├── components/              # UI组件
│   │   ├── StepIndicator.js     # 步骤指示器组件
│   │   ├── FileUploader.js      # 文件上传组件
│   │   ├── MappingEditor.js     # 映射编辑器组件
│   │   └── ResultsViewer.js     # 结果查看器组件
│   ├── services/                # 服务层
│   │   └── api.js              # API服务
│   └── utils/                   # 工具函数
│       ├── constants.js        # 常量定义
│       └── helpers.js          # 工具函数
└── css/
    └── style.css               # 样式文件
```

## 🏗️ 模块说明

### 1. 主应用模块 (app-main.js)

**职责：**
- 应用状态管理
- 组件协调
- 全局事件处理

**核心类：**
```javascript
class Application {
    - state: 应用状态
    - components: 组件实例
    - init(): 初始化应用
    - handleUploadSuccess(): 处理上传成功
    - handleAnalyze(): 处理数据分析
    - handleExport(): 处理数据导出
    - handleReset(): 重置应用
}
```

### 2. 组件模块 (components/)

#### StepIndicator.js
**职责：** 步骤指示器UI和状态更新

```javascript
export class StepIndicator {
    - update(step): 更新当前步骤
    - reset(): 重置到第一步
}
```

#### FileUploader.js
**职责：** 文件上传和验证

```javascript
export class FileUploader {
    - init(): 初始化拖拽和点击事件
    - handleUpload(file): 处理文件上传
    - showFilePreview(file): 显示文件预览
    - reset(): 重置上传器
}
```

#### MappingEditor.js
**职责：** 映射关系编辑

```javascript
export class MappingEditor {
    - render(sheetInfo): 渲染映射编辑器
    - createSheetCard(): 创建Sheet卡片
    - getAutoMappings(): 获取自动映射
    - collectMappings(): 收集映射配置
    - reset(): 重置编辑器
}
```

#### ResultsViewer.js
**职责：** 结果查看和导出（Excel式标签切换）

```javascript
export class ResultsViewer {
    - render(sheetResults): 渲染结果
    - createTabs(): 创建标签导航
    - switchSheet(sheetName): 切换Sheet
    - createSheetContent(): 创建Sheet内容
    - export(): 导出数据
    - reset(): 重置查看器
}
```

### 3. 服务模块 (services/)

#### api.js
**职责：** API请求封装

```javascript
export async function uploadFile(file)          // 上传文件
export async function analyzeData(filepath, mappingsConfig)  // 分析数据
export async function exportData(sheetResults) // 导出数据
```

### 4. 工具模块 (utils/)

#### constants.js
**职责：** 常量定义

```javascript
export const APP_CONFIG = {...}           // 应用配置
export const STEP_CONFIG = {...}          // 步骤配置
export const STANDARD_HEADERS = [...]     // 标准表头
export const JIAGE_MAPPINGS = {...}      // 佳哥映射
```

#### helpers.js
**职责：** 通用工具函数

```javascript
export function showToast(message, type)     // 显示提示
export function formatFileSize(bytes)       // 格式化文件大小
export function validateFile(file)          // 验证文件
export function getColumnLetter(index)      // 获取列字母
```

## 🔄 数据流

```
用户操作
    ↓
事件触发（HTML onclick事件）
    ↓
全局函数（window.analyzeData等）
    ↓
Application主应用
    ↓
相应组件方法
    ↓
服务层API调用
    ↓
后端Flask API
    ↓
返回数据
    ↓
更新状态和UI
```

## 🎯 设计原则

### 1. 单一职责原则
每个模块只负责一个功能领域

### 2. 依赖注入
组件通过构造函数接收回调函数

### 3. 模块化
使用ES6模块系统，支持按需导入

### 4. 可扩展性
新增功能只需添加新模块，不影响现有代码

## 📝 开发指南

### 添加新组件

1. 在 `components/` 目录创建新文件
2. 导出组件类
3. 在 `app-main.js` 中导入和实例化
4. 在HTML中添加必要的DOM元素

### 添加新API

1. 在 `services/api.js` 中添加新函数
2. 在相应组件中调用
3. 处理返回数据

### 修改常量

1. 在 `utils/constants.js` 中修改
2. 所有引用该常量的模块自动更新

## 🔧 调试技巧

### 查看组件状态
```javascript
console.log(app.state);
console.log(app.components);
```

### 查看网络请求
打开浏览器开发者工具 → Network标签

### 查看错误信息
打开浏览器开发者工具 → Console标签

## 🚀 性能优化

### 按需加载
使用ES6模块，浏览器自动按需加载

### 事件委托
尽量使用事件委托减少事件监听器数量

### 防抖节流
对频繁触发的事件使用防抖或节流

## 📚 参考资源

- [ES6模块](https://developer.mozilla.org/zh-CN/docs/Web/JavaScript/Guide/Modules)
- [Flask官方文档](https://flask.palletsprojects.com/)
- [MDN Web文档](https://developer.mozilla.org/zh-CN/)
