# -*- coding: utf-8 -*-
"""
数据处理工具 - Flask主应用
"""

from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from config import Config
from app.excel_processor import ExcelProcessor

# 创建Flask应用
template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')

app = Flask(__name__,
            template_folder=template_dir,
            static_folder=static_dir)
app.config.from_object(Config)

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 初始化处理器
excel_processor = ExcelProcessor()


@app.route('/')
def home():
    """首页"""
    return render_template('index.html')


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    上传Excel文件

    Request:
        - file: Excel文件（.xlsx或.xls格式）

    Response:
        - filepath: 文件路径
        - sheet_info: sheet信息字典
    """
    if 'file' not in request.files:
        return jsonify({'error': '未上传文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400

    # 检查文件扩展名
    if not _allowed_file(file.filename):
        return jsonify({
            'error': '不支持的文件格式，请上传 .xlsx 或 .xls 文件'
        }), 400

    # 保存文件
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        # 获取Excel文件信息
        sheet_info = excel_processor.get_excel_info(filepath)
        return jsonify({
            'success': True,
            'filepath': filepath,
            'sheet_info': sheet_info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/analyze', methods=['POST'])
def analyze_data():
    """
    分析数据

    Request:
        - filepath: 文件路径
        - mappings_config: 映射配置
            {
                'sheet_name': {
                    'header_row': 2,
                    'custom_mappings': {'姓名': 'A2', ...}
                }
            }

    Response:
        - sheet_results: 处理结果字典
    """
    data = request.json
    filepath = data.get('filepath')
    mappings_config = data.get('mappings_config', {})

    if not filepath:
        return jsonify({'error': '缺少文件路径'}), 400

    try:
        # 处理Excel文件
        sheet_results = excel_processor.process_with_mappings(filepath, mappings_config)
        return jsonify({
            'success': True,
            'sheet_results': sheet_results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/export', methods=['POST'])
def export_data():
    """
    导出数据为Excel文件

    Request:
        - sheet_results: 处理结果字典

    Response:
        - Excel文件下载
    """
    data = request.json
    sheet_results = data.get('sheet_results', {})

    if not sheet_results:
        return jsonify({'error': '没有可导出的数据'}), 400

    try:
        # 创建输出文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join(
            app.config['UPLOAD_FOLDER'],
            f'export_{timestamp}.xlsx'
        )

        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for sheet_name, sheet_data in sheet_results.items():
                # 构建数据列表
                data_list = []

                # 添加表头行
                header_row = ['序号'] + sheet_data['standard_headers']
                data_list.append(header_row)

                # 添加映射关系行
                mapping_row = ['映射关系'] + sheet_data['matched_headers']
                data_list.append(mapping_row)

                # 添加数据行
                for row in sheet_data['data']:
                    data_list.append(row)

                # 创建DataFrame并写入
                df = pd.DataFrame(data_list)
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)

        # 返回文件
        return send_file(
            output_path,
            as_attachment=True,
            download_name=f'数据整理结果_{timestamp}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'导出失败: {str(e)}'
        }), 500


def _allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {ext[1:] for ext in Config.ALLOWED_EXTENSIONS}


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
