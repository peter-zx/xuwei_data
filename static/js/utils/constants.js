/**
 * 应用常量定义
 */

export const APP_CONFIG = {
    API_BASE_URL: '/api',
    MAX_FILE_SIZE: 16 * 1024 * 1024, // 16MB
    ALLOWED_EXTENSIONS: ['.xlsx', '.xls']
};

export const STEP_CONFIG = {
    UPLOAD: 1,
    PREVIEW: 2,
    MAPPING: 3,
    ANALYZING: 4,
    RESULT: 5
};

export const STANDARD_HEADERS = [
    '姓名', '电话', '身份证', '残疾证',
    '身份证到期时间', '残疾证到期时间',
    '残疾证等级', '残疾证类型'
];

export const JIAGE_MAPPINGS = {
    '姓名': 'A2',
    '电话': 'B2',
    '身份证': 'D2',
    '残疾证': 'J2',
    '身份证到期时间': 'I2',
    '残疾证到期时间': 'M2',
    '残疾证等级': 'L2',
    '残疾证类型': 'K2'
};
