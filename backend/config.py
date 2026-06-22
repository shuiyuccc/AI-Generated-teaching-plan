"""
配置文件 - 存放API密钥和其他配置
支持多模型切换：1=MiniMax, 2=DeepSeek V3

配置优先级：环境变量 > llm_settings.json > 内置默认值
首次使用时会自动创建 llm_settings.json 模板文件
"""
import os
import json

# 加载环境变量（可选）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ============================================
# 从 JSON 文件加载用户配置
# ============================================
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'llm_settings.json')

def load_settings_from_file():
    """从 llm_settings.json 加载用户保存的配置"""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_settings_to_file(settings):
    """保存配置到 llm_settings.json"""
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

# 加载文件中的设置
_file_settings = load_settings_from_file()

# ============================================
# 模型选择配置
# 设置 MODEL_SELECTION = 1 使用 MiniMax
# 设置 MODEL_SELECTION = 2 使用 DeepSeek V3
# ============================================
MODEL_SELECTION = _file_settings.get('model_selection', 2)  # 默认 DeepSeek V3

# ============================================
# MiniMax 模型配置 (MODEL_SELECTION = 1)
# ============================================
MINIMAX_CONFIG = {
    "api_key": os.getenv("MINIMAX_API_KEY", _file_settings.get('minimax_api_key', '')),
    "api_url": os.getenv("MINIMAX_API_URL", _file_settings.get('minimax_api_url', 'https://api.minimaxi.com/v1/chat/completions')),
    "model": "MiniMax-M2.7",
    "temperature": 0.7,
    "max_tokens": 32000,
    "stream": False
}

# ============================================
# DeepSeek V3 模型配置 (MODEL_SELECTION = 2)
# ============================================
DEEPSEEK_CONFIG = {
    "api_key": os.getenv("DEEPSEEK_API_KEY", _file_settings.get('deepseek_api_key', '')),
    "api_url": os.getenv("DEEPSEEK_API_URL", _file_settings.get('deepseek_api_url', 'https://api.deepseek.com/v1/chat/completions')),
    "model": "deepseek-chat",
    "temperature": 0.7,
    "max_tokens": 32000,
    "stream": False
}

# ============================================
# 根据 MODEL_SELECTION 获取当前使用的模型配置
# ============================================
def get_current_model_config():
    """获取当前选中的模型配置"""
    if MODEL_SELECTION == 1:
        return {
            "name": "MiniMax",
            "api_key": MINIMAX_CONFIG["api_key"],
            "api_url": MINIMAX_CONFIG["api_url"],
            "model": MINIMAX_CONFIG["model"],
            "temperature": MINIMAX_CONFIG["temperature"],
            "max_tokens": MINIMAX_CONFIG["max_tokens"],
            "stream": MINIMAX_CONFIG["stream"]
        }
    else:
        return {
            "name": "DeepSeek V3",
            "api_key": DEEPSEEK_CONFIG["api_key"],
            "api_url": DEEPSEEK_CONFIG["api_url"],
            "model": DEEPSEEK_CONFIG["model"],
            "temperature": DEEPSEEK_CONFIG["temperature"],
            "max_tokens": DEEPSEEK_CONFIG["max_tokens"],
            "stream": DEEPSEEK_CONFIG["stream"]
        }

def reload_config():
    """重新加载配置文件（修改设置后调用）"""
    global MODEL_SELECTION, MINIMAX_CONFIG, DEEPSEEK_CONFIG, LLM_API_KEY, LLM_API_URL, MODEL_CONFIG
    settings = load_settings_from_file()
    MODEL_SELECTION = settings.get('model_selection', 2)

    MINIMAX_CONFIG["api_key"] = os.getenv("MINIMAX_API_KEY", settings.get('minimax_api_key', ''))
    MINIMAX_CONFIG["api_url"] = os.getenv("MINIMAX_API_URL", settings.get('minimax_api_url', 'https://api.minimaxi.com/v1/chat/completions'))

    DEEPSEEK_CONFIG["api_key"] = os.getenv("DEEPSEEK_API_KEY", settings.get('deepseek_api_key', ''))
    DEEPSEEK_CONFIG["api_url"] = os.getenv("DEEPSEEK_API_URL", settings.get('deepseek_api_url', 'https://api.deepseek.com/v1/chat/completions'))

    cfg = get_current_model_config()
    LLM_API_KEY = cfg["api_key"]
    LLM_API_URL = cfg["api_url"]
    MODEL_CONFIG = {
        "model": cfg["model"],
        "temperature": cfg["temperature"],
        "max_tokens": cfg["max_tokens"],
        "stream": cfg["stream"]
    }

# 兼容旧配置的别名
LLM_API_KEY = get_current_model_config()["api_key"]
LLM_API_URL = get_current_model_config()["api_url"]
MODEL_CONFIG = {
    "model": get_current_model_config()["model"],
    "temperature": get_current_model_config()["temperature"],
    "max_tokens": get_current_model_config()["max_tokens"],
    "stream": get_current_model_config()["stream"]
}

# ============================================
# 固定课程信息（批量生成时不变）
# ============================================
DEFAULT_FIXED_COURSE_INFO = {
    "院系": "智能装备学院",
    "授课班级": "电气自动化（2）班",
    "专业名称": "电气自动化",
    "课程名称": "电子焊接",
    "授课教师": "张老师"
}

# 可变课程信息（每节课不同）
DEFAULT_VARIABLE_COURSE_INFO = {
    "课题名称": "焊接5步法",
    "授课地点": "焊接实训室",
    "授课时间": "2026年2月",
    "授课学时": "3学时",
    "授课类型": "理实一体化"
}

# 默认完整课程信息
DEFAULT_COURSE_INFO = {
    **DEFAULT_FIXED_COURSE_INFO,
    **DEFAULT_VARIABLE_COURSE_INFO
}
