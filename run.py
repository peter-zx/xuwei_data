#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
应用启动脚本
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app

if __name__ == '__main__':
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║                                                            ║
    ║           数据处理工具 - 专业Excel整理解决方案              ║
    ║                                                            ║
    ╚════════════════════════════════════════════════════════════╝

    启动中...

    """)

    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True
    )
