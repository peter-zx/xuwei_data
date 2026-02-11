from flask import Flask, request, jsonify, render_template
import pandas as pd
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'xls'}

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def clean_column_name(col_name):
    """清理列名：去掉换行符和多余空格"""
    return str(col_name).replace('\n', '').strip()


def get_standard_fields():
    """返回标准字段列表（可配置）"""
    return ['姓名', '电话', '身份证', '残疾证', '身份证到期时间', '残疾证到期时间', '残疾证等级', '残疾证类型']


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有文件上传'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '未选择文件'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': '只支持 .xlsx 和 .xls 文件格式'}), 400

        # 保存文件
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # 读取Excel文件信息
        excel_data = pd.ExcelFile(filepath)
        sheets_info = []

        for sheet_name in excel_data.sheet_names:
            df = pd.read_excel(filepath, sheet_name=sheet_name)
            sheets_info.append({
                'name': sheet_name,
                'rows': len(df),
                'columns': len(df.columns)
            })

        return jsonify({
            'success': True,
            'filename': filename,
            'sheets': sheets_info,
            'sheet_count': len(sheets_info)
        })

    except Exception as e:
        return jsonify({'error': f'文件上传失败: {str(e)}'}), 500


@app.route('/api/analyze', methods=['POST'])
def analyze_sheets():
    try:
        data = request.json
        filename = data.get('filename')
        mappings = data.get('mappings', {})

        if not filename:
            return jsonify({'error': '未提供文件名'}), 400

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({'error': '文件不存在'}), 404

        results = []
        excel_data = pd.ExcelFile(filepath)

        for sheet_name in excel_data.sheet_names:
            sheet_result = {
                'name': sheet_name,
                'mapping': {},
                'data': [],
                'success': True,
                'error': None
            }

            try:
                # 获取该Sheet的映射配置
                sheet_mapping = mappings.get(sheet_name, {})
                header_row = sheet_mapping.get('header_row', 0)
                field_mapping = sheet_mapping.get('fields', {})

                # 读取数据
                df = pd.read_excel(filepath, sheet_name=sheet_name, header=header_row)

                # 提取数据
                extracted_data = []
                for idx, row in df.iterrows():
                    record = {}
                    has_data = False

                    for field in get_standard_fields():
                        col_name = field_mapping.get(field)
                        if col_name and col_name in df.columns:
                            value = str(row[col_name]) if pd.notna(row[col_name]) else ''
                            record[field] = value
                            if value:
                                has_data = True
                        else:
                            record[field] = ''

                    if has_data:  # 只保存有数据的记录
                        extracted_data.append(record)

                sheet_result['mapping'] = field_mapping
                sheet_result['data'] = extracted_data
                sheet_result['record_count'] = len(extracted_data)
                results.append(sheet_result)

            except Exception as e:
                sheet_result['success'] = False
                sheet_result['error'] = str(e)
                results.append(sheet_result)

        return jsonify({
            'success': True,
            'results': results
        })

    except Exception as e:
        return jsonify({'error': f'分析失败: {str(e)}'}), 500


@app.route('/api/sheet-preview', methods=['POST'])
def sheet_preview():
    """获取Sheet的前N行预览数据"""
    try:
        data = request.json
        filename = data.get('filename')
        sheet_name = data.get('sheet_name')
        header_row = data.get('header_row', 0)
        max_rows = data.get('max_rows', 5)

        if not filename or not sheet_name:
            return jsonify({'error': '缺少必要参数'}), 400

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({'error': '文件不存在'}), 404

        # 读取前N行数据（不设置header，获取原始数据）
        df = pd.read_excel(filepath, sheet_name=sheet_name, header=None, nrows=max_rows)

        # 转换为列表格式
        preview_data = []
        for idx, row in df.iterrows():
            row_data = [clean_column_name(cell) if pd.notna(cell) else '' for cell in row]
            preview_data.append(row_data)

        return jsonify({
            'success': True,
            'data': preview_data,
            'max_rows': max_rows
        })

    except Exception as e:
        return jsonify({'error': f'预览失败: {str(e)}'}), 500


@app.route('/api/columns', methods=['POST'])
def get_columns():
    """获取指定行作为表头的列名"""
    try:
        data = request.json
        filename = data.get('filename')
        sheet_name = data.get('sheet_name')
        header_row = data.get('header_row', 0)

        if not filename or not sheet_name:
            return jsonify({'error': '缺少必要参数'}), 400

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({'error': '文件不存在'}), 404

        # 读取Excel，设置指定的header_row
        df = pd.read_excel(filepath, sheet_name=sheet_name, header=header_row)

        # 清理并过滤列名
        columns = [clean_column_name(col) for col in df.columns if not str(col).startswith('Unnamed')]

        return jsonify({
            'success': True,
            'columns': columns
        })

    except Exception as e:
        return jsonify({'error': f'获取列名失败: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
