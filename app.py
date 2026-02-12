from flask import Flask, request, jsonify, render_template
import pandas as pd
import os
import shutil
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import threading
import time

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['CACHE_FOLDER'] = 'cache'
app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'xls'}
app.config['CACHE_DAYS'] = 7  # 缓存保留天数

# 确保目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['CACHE_FOLDER'], exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def clean_column_name(col_name):
    """清理列名：去掉换行符和多余空格"""
    return str(col_name).replace('\n', '').strip()


def get_standard_fields():
    """返回标准字段列表（可配置）"""
    return ['姓名', '电话', '身份证', '残疾证', '身份证到期时间', '残疾证到期时间', '残疾证等级', '残疾证类型', '残疾证号']


def get_cache_path(filename):
    """生成缓存文件路径"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    cache_name = f"{timestamp}_{filename}"
    return os.path.join(app.config['CACHE_FOLDER'], cache_name)


def copy_to_cache(original_path):
    """复制文件到缓存目录，去除公式"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    original_name = os.path.basename(original_path)
    cache_name = f"{timestamp}_{original_name}"
    cache_path = os.path.join(app.config['CACHE_FOLDER'], cache_name)

    try:
        # 读取Excel文件，pandas会自动计算公式值
        excel_data = pd.ExcelFile(original_path)

        with pd.ExcelWriter(cache_path, engine='openpyxl') as writer:
            for sheet_name in excel_data.sheet_names:
                # 读取数据，公式会被计算为实际值
                df = pd.read_excel(original_path, sheet_name=sheet_name)
                df.to_excel(writer, sheet_name=sheet_name, index=False)

        return cache_name
    except Exception as e:
        raise Exception(f'缓存文件创建失败: {str(e)}')


def cleanup_old_cache():
    """清理过期的缓存文件"""
    try:
        now = datetime.now()
        cutoff = now - timedelta(days=app.config['CACHE_DAYS'])

        for filename in os.listdir(app.config['CACHE_FOLDER']):
            filepath = os.path.join(app.config['CACHE_FOLDER'], filename)
            if os.path.isfile(filepath):
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                if file_time < cutoff:
                    os.remove(filepath)
                    print(f'清理过期缓存: {filename}')
    except Exception as e:
        print(f'清理缓存失败: {str(e)}')


def start_cleanup_scheduler():
    """启动定时清理任务"""
    def cleanup_task():
        while True:
            time.sleep(3600)  # 每小时检查一次
            cleanup_old_cache()

    cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
    cleanup_thread.start()
    print('缓存清理任务已启动')


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

        # 保存原始文件
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        original_filename = f"{timestamp}_{filename}"
        original_filepath = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
        file.save(original_filepath)

        # 创建缓存文件（去除公式）
        cache_filename = copy_to_cache(original_filepath)

        # 读取缓存文件信息
        excel_data = pd.ExcelFile(os.path.join(app.config['CACHE_FOLDER'], cache_filename))
        sheets_info = []

        for sheet_name in excel_data.sheet_names:
            df = pd.read_excel(os.path.join(app.config['CACHE_FOLDER'], cache_filename), sheet_name=sheet_name)
            sheets_info.append({
                'name': sheet_name,
                'rows': len(df),
                'columns': len(df.columns)
            })

        return jsonify({
            'success': True,
            'filename': cache_filename,
            'original_filename': original_filename,
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

        # 使用缓存文件
        filepath = os.path.join(app.config['CACHE_FOLDER'], filename)
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
                sheet_mapping = mappings.get(sheet_name, {})
                header_row = sheet_mapping.get('header_row', 0)
                field_mapping = sheet_mapping.get('fields', {})

                # 确保field_mapping不为None
                if field_mapping is None:
                    field_mapping = {}

                df = pd.read_excel(filepath, sheet_name=sheet_name, header=header_row)

                extracted_data = []
                for idx, row in df.iterrows():
                    record = {}

                    for field in get_standard_fields():
                        col_name = field_mapping.get(field)
                        if col_name and col_name.strip() and col_name in df.columns:
                            value = str(row[col_name]) if pd.notna(row[col_name]) else ''
                            record[field] = value
                        else:
                            # 未映射的字段或列不存在，留空
                            record[field] = ''

                    # 保留所有原始数据行
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
        return jsonify({'error': f'映射失败: {str(e)}'}), 500


@app.route('/api/sheet-preview', methods=['POST'])
def sheet_preview():
    """获取Sheet的前N行预览数据"""
    try:
        data = request.json
        filename = data.get('filename')
        sheet_name = data.get('sheet_name')
        max_rows = data.get('max_rows', 5)

        if not filename or not sheet_name:
            return jsonify({'error': '缺少必要参数'}), 400

        # 使用缓存文件
        filepath = os.path.join(app.config['CACHE_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({'error': '文件不存在'}), 404

        # 读取前N行原始数据
        df = pd.read_excel(filepath, sheet_name=sheet_name, header=None, nrows=max_rows)

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

        # 使用缓存文件
        filepath = os.path.join(app.config['CACHE_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({'error': '文件不存在'}), 404

        df = pd.read_excel(filepath, sheet_name=sheet_name, header=header_row)

        columns = [clean_column_name(col) for col in df.columns if not str(col).startswith('Unnamed')]

        return jsonify({
            'success': True,
            'columns': columns
        })

    except Exception as e:
        return jsonify({'error': f'获取列名失败: {str(e)}'}), 500


@app.route('/api/compare', methods=['POST'])
def compare_data():
    """数据比对：基于姓名+身份证号识别同一人，检测跨Sheet数据差异"""
    try:
        data = request.json
        filename = data.get('filename')
        mappings = data.get('mappings', {})

        if not filename:
            return jsonify({'error': '未提供文件名'}), 400

        filepath = os.path.join(app.config['CACHE_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({'error': '文件不存在'}), 404

        # 获取映射后的数据
        excel_data = pd.ExcelFile(filepath)
        all_records = []
        sheet_names = []

        for sheet_name in excel_data.sheet_names:
            sheet_names.append(sheet_name)
            sheet_mapping = mappings.get(sheet_name, {})
            header_row = sheet_mapping.get('header_row', 0)
            field_mapping = sheet_mapping.get('fields', {})

            if field_mapping is None:
                field_mapping = {}

            df = pd.read_excel(filepath, sheet_name=sheet_name, header=header_row)

            for idx, row in df.iterrows():
                record = {'_sheet_name': sheet_name, '_row_index': idx}

                for field in get_standard_fields():
                    col_name = field_mapping.get(field)
                    if col_name and col_name.strip() and col_name in df.columns:
                        value = str(row[col_name]) if pd.notna(row[col_name]) else ''
                        record[field] = value
                    else:
                        record[field] = ''

                # 只保留有姓名的记录
                if record.get('姓名') and record['姓名'].strip():
                    all_records.append(record)

        # 按姓名+身份证号分组
        people_dict = {}

        for record in all_records:
            name = record.get('姓名', '').strip()
            id_card = record.get('身份证', '').strip()

            # 使用姓名+身份证号作为唯一键
            key = f"{name}_{id_card}" if name else None

            if not key:
                continue

            if key not in people_dict:
                people_dict[key] = {
                    '_key': key,
                    '_name': name,
                    '_sheets': {},
                    '_records': []
                }

            sheet_name = record['_sheet_name']
            people_dict[key]['_sheets'][sheet_name] = record
            people_dict[key]['_records'].append(record)

        # 分析每组数据，检测差异
        result_groups = []

        for key, person in people_dict.items():
            records = person['_records']
            sheets = list(person['_sheets'].keys())

            # 计算完善度（每个Sheet的完善度）
            completeness_scores = []
            for sheet, record in person['_sheets'].items():
                non_empty = sum(1 for f in get_standard_fields() if record.get(f) and record.get(f).strip())
                completeness_scores.append(non_empty)

            avg_completeness = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0

            # 检测字段差异
            field_diffs = {}
            for field in get_standard_fields():
                values = {}
                for sheet, record in person['_sheets'].items():
                    val = record.get(field, '').strip()
                    if val:
                        values[sheet] = val

                # 检查是否有差异
                unique_values = set(values.values())
                if len(unique_values) > 1:
                    field_diffs[field] = values

            # 合并数据（取最完善的记录）
            merged = {}
            for field in get_standard_fields():
                # 优先取非空值
                for record in records:
                    val = record.get(field, '').strip()
                    if val:
                        merged[field] = val
                        break
                if field not in merged:
                    merged[field] = ''

            result_groups.append({
                '_key': key,
                '_name': person['_name'],
                '_sheets': sheets,
                '_sheet_data': person['_sheets'],
                '_completeness': avg_completeness,
                '_has_diff': len(field_diffs) > 0,
                '_field_diffs': field_diffs,
                **merged
            })

        # 排序：按完善度降序，然后按姓名
        result_groups.sort(key=lambda x: (-x['_completeness'], x['_name']))

        # 分类：完善（≥7字段且无差异）vs 不完善
        complete_groups = [g for g in result_groups if g['_completeness'] >= 7 and not g['_has_diff']]
        incomplete_groups = [g for g in result_groups if g['_completeness'] < 7 or g['_has_diff']]

        return jsonify({
            'success': True,
            'sheet_names': sheet_names,
            'complete_groups': complete_groups,
            'incomplete_groups': incomplete_groups,
            'stats': {
                'total_groups': len(result_groups),
                'complete_count': len(complete_groups),
                'incomplete_count': len(incomplete_groups),
                'with_diff_count': sum(1 for g in result_groups if g['_has_diff'])
            }
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'比对失败: {str(e)}'}), 500


if __name__ == '__main__':
    # 启动缓存清理任务
    start_cleanup_scheduler()

    app.run(debug=True, host='0.0.0.0', port=8080)
