from flask import Flask, request, jsonify, render_template
import pandas as pd
import os
import shutil
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import threading
import time
from excel_processor import process_excel_with_formulas, convert_xls_to_xlsx_with_calculation

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
    """清理列名和单元格内容：去掉换行符、多余空格、科学计数法等"""
    if col_name is None:
        return ''
    
    # 转换为字符串
    text = str(col_name)
    
    # 去除换行符、制表符
    text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    
    # 去除首尾空格
    text = text.strip()
    
    # 合并多个连续空格为一个
    while '  ' in text:
        text = text.replace('  ', ' ')
    
    return text


def get_standard_fields():
    """返回标准字段列表（可配置）"""
    return ['姓名', '电话', '身份证', '残疾证', '身份证到期时间', '残疾证到期时间', '残疾证等级', '残疾证类型', '残疾证号']


def get_cache_path(filename):
    """生成缓存文件路径"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    cache_name = f"{timestamp}_{filename}"
    return os.path.join(app.config['CACHE_FOLDER'], cache_name)


def copy_to_cache(original_path):
    """复制文件到缓存目录，处理公式并保留计算后的值"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    original_name = os.path.basename(original_path)
    
    # 转换为绝对路径
    original_path = os.path.abspath(original_path)
    
    # 获取缓存目录的绝对路径
    cache_dir = os.path.abspath(app.config['CACHE_FOLDER'])
    
    # 检测文件实际格式
    with open(original_path, 'rb') as f:
        header = f.read(8)
        # XLS 格式的文件头: D0 CF 11 E0 A1 B1 1A E1
        is_xls = header[:8] == b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'
        # XLSX 格式的文件头: PK (ZIP格式)
        is_xlsx = header[:2] == b'PK'
    
    print(f'文件格式检测: XLS={is_xls}, XLSX={is_xlsx}, 文件名={original_name}')
    
    # 确定缓存文件名（强制使用 .xlsx）
    base_name = original_name.rsplit('.', 1)[0] if '.' in original_name else original_name
    cache_name = f"{timestamp}_{base_name}.xlsx"
    cache_path = os.path.join(cache_dir, cache_name)
    
    print(f'缓存文件路径: {cache_path}')
    
    try:
        # 直接使用 pandas 读取并保存（会自动处理公式）
        print('使用 pandas 处理文件...')
        
        # 根据 format 选择引擎
        engine = 'xlrd' if is_xls else None
        excel_data = pd.ExcelFile(original_path, engine=engine)
        
        with pd.ExcelWriter(cache_path, engine='openpyxl') as writer:
            for sheet_name in excel_data.sheet_names:
                print(f'  处理 Sheet: {sheet_name}')
                df = pd.read_excel(original_path, sheet_name=sheet_name, engine=engine)
                
                # 格式化数据（可选）
                for col in df.columns:
                    if df[col].dtype == 'float64':
                        df[col] = df[col].apply(
                            lambda x: f"{x:.10f}".rstrip('0').rstrip('.') if pd.notna(x) else ''
                        )
                    elif df[col].dtype == 'object':
                        df[col] = df[col].apply(
                            lambda x: clean_column_name(str(x)) if pd.notna(x) and str(x) != 'nan' else ''
                        )
                
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # 验证缓存文件
        if not os.path.exists(cache_path):
            raise Exception('缓存文件创建失败')
        
        excel_data = pd.ExcelFile(cache_path)
        print(f'缓存文件创建成功: {cache_name} ({len(excel_data.sheet_names)} 个 Sheet)')
        
        return cache_name
        
    except Exception as e:
        import traceback
        traceback.print_exc()
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

                if field_mapping is None:
                    field_mapping = {}

                df = pd.read_excel(filepath, sheet_name=sheet_name, header=header_row)

                extracted_data = []
                for idx, row in df.iterrows():
                    record = {}

                    for field in get_standard_fields():
                        col_name = field_mapping.get(field)
                        if col_name and col_name.strip() and col_name in df.columns:
                            value = row[col_name]
                            if pd.notna(value):
                                if isinstance(value, float):
                                    record[field] = f"{value:.10f}".rstrip('0').rstrip('.')
                                else:
                                    record[field] = clean_column_name(str(value))
                            else:
                                record[field] = ''
                        else:
                            record[field] = ''

                    extracted_data.append(record)

                sheet_result['mapping'] = field_mapping
                sheet_result['data'] = extracted_data
                sheet_result['record_count'] = len(extracted_data)
                results.append(sheet_result)

            except Exception as e:
                import traceback
                traceback.print_exc()
                sheet_result['success'] = False
                sheet_result['error'] = str(e)
                results.append(sheet_result)

        return jsonify({
            'success': True,
            'results': results
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'映射失败: {str(e)}'}), 500

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
            row_data = []
            for cell in row:
                if pd.notna(cell):
                    if isinstance(cell, float):
                        formatted = f"{cell:.10f}".rstrip('0').rstrip('.')
                        row_data.append(formatted)
                    else:
                        row_data.append(clean_column_name(str(cell)))
                else:
                    row_data.append('')
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

        columns = []
        for col in df.columns:
            col_name = clean_column_name(col)
            if col_name and not col_name.startswith('Unnamed'):
                columns.append(col_name)

        return jsonify({
            'success': True,
            'columns': columns
        })

    except Exception as e:
        return jsonify({'error': f'获取列名失败: {str(e)}'}), 500


@app.route('/api/compare', methods=['POST'])
def compare_data():
    """数据比对：三列并排显示，按姓名+身份证号对齐"""
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
        sheets_data = {}

        for sheet_name in excel_data.sheet_names:
            sheet_mapping = mappings.get(sheet_name, {})
            header_row = sheet_mapping.get('header_row', 0)
            field_mapping = sheet_mapping.get('fields', {})

            if field_mapping is None:
                field_mapping = {}

            df = pd.read_excel(filepath, sheet_name=sheet_name, header=header_row)
            records = []

            for idx, row in df.iterrows():
                record = {'_row_index': idx}

                for field in get_standard_fields():
                    col_name = field_mapping.get(field)
                    if col_name and col_name.strip() and col_name in df.columns:
                        value = row[col_name]
                        if pd.notna(value):
                            if isinstance(value, float):
                                record[field] = f"{value:.10f}".rstrip('0').rstrip('.')
                            else:
                                record[field] = clean_column_name(str(value))
                        else:
                            record[field] = ''
                    else:
                        record[field] = ''

                # 只保留有姓名的记录
                if record.get('姓名') and record['姓名'].strip():
                    records.append(record)

            sheets_data[sheet_name] = records

        # 获取所有唯一的人（按姓名+身份证号）
        all_people = {}

        for sheet_name, records in sheets_data.items():
            for record in records:
                name = record.get('姓名', '').strip()
                id_card = record.get('身份证', '').strip()
                key = f"{name}_{id_card}" if name else None

                if not key:
                    continue

                if key not in all_people:
                    all_people[key] = {
                        '_key': key,
                        '_name': name,
                        '_id_card': id_card,
                        '_sheets': {}
                    }

                all_people[key]['_sheets'][sheet_name] = record

        # 转换为列表并排序
        people_list = list(all_people.values())
        people_list.sort(key=lambda x: (x['_name'], x['_id_card']))

        # 判断是否为相同人
        sheet_names = list(sheets_data.keys())
        total_sheets = len(sheet_names)

        for person in people_list:
            person['_is_same'] = len(person['_sheets']) == total_sheets
            person['_sheet_count'] = len(person['_sheets'])

        # 统计
        same_count = sum(1 for p in people_list if p['_is_same'])
        diff_count = len(people_list) - same_count

        return jsonify({
            'success': True,
            'sheet_names': sheet_names,
            'people_list': people_list,
            'stats': {
                'total': len(people_list),
                'same_count': same_count,
                'diff_count': diff_count,
                'sheet_count': total_sheets
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
