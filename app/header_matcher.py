# -*- coding: utf-8 -*-
"""
表头匹配模块
智能匹配原始表头与标准表头
"""

import re
from config import STANDARD_HEADERS, KEYWORD_MAP, JIAGE_SHEET_HEADERS


class HeaderMatcher:
    """表头匹配器 - 支持多种匹配策略"""

    def __init__(self):
        self.standard_headers = STANDARD_HEADERS
        self.keyword_map = KEYWORD_MAP
        self.jiage_headers = JIAGE_SHEET_HEADERS

    def find_best_match(self, target, headers):
        """
        在原始表头中找到与目标最匹配的字段

        Args:
            target: 目标标准表头
            headers: 原始表头列表

        Returns:
            匹配到的表头名称或空字符串
        """
        if not headers:
            return ''

        # 1. 首先尝试精确匹配
        if target in headers:
            return target

        # 2. 尝试关键词匹配（忽略大小写）
        if target in self.keyword_map:
            for keyword in self.keyword_map[target]:
                for header in headers:
                    if keyword in str(header).lower():
                        return header

        # 3. 尝试模糊匹配（包含关系）
        for header in headers:
            header_str = str(header).lower()
            target_lower = target.lower()
            if target_lower in header_str or header_str in target_lower:
                return header

        # 4. 最后返回第一个非空表头或空字符串
        for header in headers:
            if header and str(header).strip():
                return header

        return ''

    def match_headers(self, original_headers):
        """
        为每个标准表头找到匹配的原始表头

        Args:
            original_headers: 原始表头列表

        Returns:
            匹配结果列表
        """
        matched_headers = []
        for standard_header in self.standard_headers:
            best_match = self.find_best_match(standard_header, original_headers)
            matched_headers.append(best_match)
        return matched_headers

    def is_jiage_sheet(self, sheet_name):
        """
        判断是否为佳哥26年数据信息sheet

        Args:
            sheet_name: sheet名称

        Returns:
            bool: 是否为佳哥sheet
        """
        return '佳哥' in sheet_name and '26' in sheet_name

    def get_jiage_mappings(self):
        """获取佳哥sheet的预定义映射"""
        return self.jiage_headers.copy()

    def match_for_sheet(self, sheet_name, original_headers, custom_mappings=None):
        """
        为指定sheet生成匹配映射

        Args:
            sheet_name: sheet名称
            original_headers: 原始表头列表
            custom_mappings: 用户自定义映射（可选）

        Returns:
            匹配结果列表
        """
        matched_headers = []

        # 判断是否为佳哥sheet
        is_jiage = self.is_jiage_sheet(sheet_name)

        for standard_header in self.standard_headers:
            # 优先级：自定义映射 > 佳哥预定义映射 > 自动匹配
            if custom_mappings and standard_header in custom_mappings:
                matched_headers.append(custom_mappings[standard_header])
            elif is_jiage and standard_header in self.jiage_headers:
                matched_headers.append(self.jiage_headers[standard_header])
            else:
                best_match = self.find_best_match(standard_header, original_headers)
                matched_headers.append(best_match)

        return matched_headers
