# -*- coding: utf-8 -*-
"""
Excel处理模块
核心数据处理逻辑
"""

import pandas as pd
from config import STANDARD_HEADERS
from app.header_matcher import HeaderMatcher


class ExcelProcessor:
    """Excel文件处理器"""

    def __init__(self):
        self.header_matcher = HeaderMatcher()

    def get_excel_info(self, filepath):
        """
        获取Excel文件的基本信息

        Args:
            filepath: Excel文件路径

        Returns:
            dict: 包含sheet信息的字典
        """
        try:
            excel_file = pd.ExcelFile(filepath)
            sheet_info = {}

            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(filepath, sheet_name=sheet_name, header=None)
                original_headers = []

                if len(df) > 0:
                    original_headers = df.iloc[0].tolist()

                sheet_info[sheet_name] = {
                    'standard_headers': STANDARD_HEADERS,
                    'original_headers': [str(h) for h in original_headers],
                    'row_count': len(df),
                    'col_count': len(df.columns) if len(df) > 0 else 0
                }

            return sheet_info
        except Exception as e:
            raise Exception(f"获取Excel信息失败: {str(e)}")

    def process_with_mappings(self, filepath, mappings_config):
        """
        根据映射配置处理Excel文件

        Args:
            filepath: Excel文件路径
            mappings_config: 映射配置字典
                {
                    'sheet_name': {
                        'header_row': 2,  # 表头所在行（1-based）
                        'custom_mappings': {'姓名': 'A2', '电话': 'B2', ...}
                    }
                }

        Returns:
            dict: 处理结果
        """
        try:
            excel_file = pd.ExcelFile(filepath)
            sheet_results = {}

            for sheet_name in excel_file.sheet_names:
                sheet_config = mappings_config.get(sheet_name, {})
                header_row = sheet_config.get('header_row', 1) - 1  # 转换为0-based
                custom_mappings = sheet_config.get('custom_mappings', {})

                # 读取数据（从指定行开始）
                df = pd.read_excel(filepath, sheet_name=sheet_name, header=header_row)

                if len(df) == 0:
                    sheet_results[sheet_name] = self._create_empty_result(sheet_name)
                    continue

                # 获取原始表头
                original_headers = [str(h) for h in df.columns.tolist()]

                # 生成匹配映射
                matched_headers = self.header_matcher.match_for_sheet(
                    sheet_name, original_headers, custom_mappings
                )

                # 处理数据行
                processed_data = []
                for i in range(len(df)):
                    row_data = self._process_data_row(df, i, matched_headers, original_headers)
                    processed_data.append(row_data)

                sheet_results[sheet_name] = {
                    'sheet_name': sheet_name,
                    'standard_headers': STANDARD_HEADERS,
                    'matched_headers': matched_headers,
                    'mappings': matched_headers,
                    'original_headers': original_headers,
                    'data': processed_data,
                    'row_count': len(processed_data)
                }

            return sheet_results
        except Exception as e:
            raise Exception(f"处理Excel文件失败: {str(e)}")

    def _create_empty_result(self, sheet_name):
        """创建空结果"""
        return {
            'sheet_name': sheet_name,
            'standard_headers': STANDARD_HEADERS,
            'matched_headers': [''] * len(STANDARD_HEADERS),
            'mappings': [''] * len(STANDARD_HEADERS),
            'original_headers': [],
            'data': [],
            'row_count': 0
        }

    def _process_data_row(self, df, row_index, matched_headers, original_headers):
        """
        处理单行数据

        Args:
            df: DataFrame
            row_index: 行索引
            matched_headers: 匹配后的表头列表
            original_headers: 原始表头列表

        Returns:
            list: 处理后的行数据
        """
        row_data = []

        # 第一列：序号
        row_data.append(str(row_index + 1))

        # 处理每个标准字段
        for j, standard_header in enumerate(STANDARD_HEADERS):
            mapping_value = matched_headers[j]

            # 检查是否是Excel坐标格式（如A2, B3等）
            if isinstance(mapping_value, str) and self._is_excel_coordinate(mapping_value):
                cell_value = self._get_value_by_coordinate(df, mapping_value, row_index)
            else:
                # 按表头名查找
                cell_value = self._get_value_by_header(df, mapping_value, original_headers, row_index)

            # 处理 NaN 值
            if pd.isna(cell_value):
                row_data.append('')
            else:
                row_data.append(str(cell_value))

        return row_data

    def _is_excel_coordinate(self, value):
        """判断是否为Excel坐标格式"""
        if not isinstance(value, str) or len(value) < 2:
            return False

        # 检查格式：字母 + 数字
        return value[0].isalpha() and value[1:].isdigit()

    def _get_value_by_coordinate(self, df, coordinate, current_row):
        """根据Excel坐标获取单元格值"""
        try:
            # 解析坐标
            col_part = ''
            row_part = ''

            for char in coordinate:
                if char.isalpha():
                    col_part += char
                else:
                    row_part += char

            # 转换列字母为列索引
            col_index = 0
            for char in col_part.upper():
                col_index = col_index * 26 + (ord(char) - ord('A') + 1)
            col_index -= 1  # 转换为0-based

            # 转换行号为行索引
            row_index = int(row_part) - 1

            # 获取单元格数据
            if 0 <= row_index < len(df) and 0 <= col_index < len(df.columns):
                return df.iloc[row_index, col_index]
            else:
                return ''
        except:
            return ''

    def _get_value_by_header(self, df, header, original_headers, row_index):
        """根据表头名获取单元格值"""
        if not header or header not in original_headers:
            return ''

        try:
            col_index = original_headers.index(header)
            return df.iloc[row_index, col_index]
        except:
            return ''
