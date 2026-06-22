"""
配置文件 - 通用 LLM 配置
支持任意兼容 OpenAI Chat Completions API 的大模型

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
# 预置模型列表（方便用户快速切换）
# ============================================
MODEL_PRESETS = {
    "deepseek": {
        "name": "DeepSeek V3",
        "api_url": "https://api.deepseek.com/v1/chat/completions",
        "model": "deepseek-chat",
        "description": "性价比高，注册即送免费额度"
    },
    "minimax": {
        "name": "MiniMax-M2.7",
        "api_url": "https://api.minimaxi.com/v1/chat/completions",
        "model": "MiniMax-M2.7",
        "description": "国产模型，支持长文本"
    },
    "kimi": {
        "name": "Kimi (月之暗面)",
        "api_url": "https://api.moonshot.cn/v1/chat/completions",
        "model": "moonshot-v1-8k",
        "description": "长文本理解能力强"
    },
    "openai": {
        "name": "OpenAI GPT",
        "api_url": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-4o",
        "description": "需海外 API Key"
    },
    "qwen": {
        "name": "通义千问 (Qwen)",
        "api_url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        "model": "qwen-plus",
        "description": "阿里云大模型"
    },
    "glm": {
        "name": "智谱 GLM",
        "api_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "model": "glm-4",
        "description": "清华智谱大模型"
    },
    "custom": {
        "name": "自定义模型",
        "api_url": "",
        "model": "",
        "description": "手动填写 API 地址和模型名"
    }
}

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

_file_settings = load_settings_from_file()

# ============================================
# 通用 LLM 配置
# 优先级：环境变量 > JSON 文件 > 默认值
# ============================================
LLM_CONFIG = {
    "api_key": os.getenv("LLM_API_KEY", _file_settings.get("api_key", "")),
    "api_url": os.getenv("LLM_API_URL", _file_settings.get("api_url", "https://api.deepseek.com/v1/chat/completions")),
    "model": os.getenv("LLM_MODEL", _file_settings.get("model", "deepseek-chat")),
    "temperature": float(os.getenv("LLM_TEMPERATURE", _file_settings.get("temperature", 0.7))),
    "max_tokens": int(os.getenv("LLM_MAX_TOKENS", _file_settings.get("max_tokens", 32000))),
    "stream": False
}

# 当前使用的预置名称（仅用于 UI 显示）
CURRENT_PRESET = _file_settings.get("preset", "deepseek")

def get_current_model_config():
    """获取当前 LLM 配置"""
    settings = load_settings_from_file()
    # 重新加载（支持运行时更新）
    api_key = os.getenv("LLM_API_KEY", settings.get("api_key", LLM_CONFIG["api_key"]))
    api_url = os.getenv("LLM_API_URL", settings.get("api_url", LLM_CONFIG["api_url"]))
    model = os.getenv("LLM_MODEL", settings.get("model", LLM_CONFIG["model"]))

    # 尝试匹配预置名称
    preset_name = settings.get("preset", "custom")
    matched_name = None
    for key, preset in MODEL_PRESETS.items():
        if preset["api_url"] == api_url:
            matched_name = preset["name"]
            break
    if not matched_name:
        matched_name = model or "自定义模型"

    return {
        "name": matched_name,
        "api_key": api_key,
        "api_url": api_url,
        "model": model,
        "temperature": LLM_CONFIG["temperature"],
        "max_tokens": LLM_CONFIG["max_tokens"],
        "stream": LLM_CONFIG["stream"]
    }

def reload_config():
    """重新加载配置文件（修改设置后调用）"""
    settings = load_settings_from_file()
    LLM_CONFIG["api_key"] = os.getenv("LLM_API_KEY", settings.get("api_key", ""))
    LLM_CONFIG["api_url"] = os.getenv("LLM_API_URL", settings.get("api_url", "https://api.deepseek.com/v1/chat/completions"))
    LLM_CONFIG["model"] = os.getenv("LLM_MODEL", settings.get("model", "deepseek-chat"))
    LLM_CONFIG["temperature"] = float(os.getenv("LLM_TEMPERATURE", settings.get("temperature", 0.7)))
    LLM_CONFIG["max_tokens"] = int(os.getenv("LLM_MAX_TOKENS", settings.get("max_tokens", 32000)))

# ============================================
# 兼容旧代码的别名
# ============================================
LLM_API_KEY = LLM_CONFIG["api_key"]
LLM_API_URL = LLM_CONFIG["api_url"]
MODEL_CONFIG = {
    "model": LLM_CONFIG["model"],
    "temperature": LLM_CONFIG["temperature"],
    "max_tokens": LLM_CONFIG["max_tokens"],
    "stream": LLM_CONFIG["stream"]
}

# ============================================
# 以下为兼容旧版本的别名（逐步废弃）
# ============================================
MODEL_SELECTION = 2  # 已废弃，仅兼容旧代码

MINIMAX_CONFIG = {
    "api_key": os.getenv("MINIMAX_API_KEY", _file_settings.get("minimax_api_key", "")),
    "api_url": os.getenv("MINIMAX_API_URL", _file_settings.get("minimax_api_url", "https://api.minimaxi.com/v1/chat/completions")),
    "model": "MiniMax-M2.7",
    "temperature": 0.7,
    "max_tokens": 32000,
    "stream": False
}

DEEPSEEK_CONFIG = {
    "api_key": os.getenv("DEEPSEEK_API_KEY", _file_settings.get("deepseek_api_key", "")),
    "api_url": os.getenv("DEEPSEEK_API_URL", _file_settings.get("deepseek_api_url", "https://api.deepseek.com/v1/chat/completions")),
    "model": "deepseek-chat",
    "temperature": 0.7,
    "max_tokens": 32000,
    "stream": False
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

DEFAULT_VARIABLE_COURSE_INFO = {
    "课题名称": "焊接5步法",
    "授课地点": "焊接实训室",
    "授课时间": "2026年2月",
    "授课学时": "3学时",
    "授课类型": "理实一体化"
}

DEFAULT_COURSE_INFO = {
    **DEFAULT_FIXED_COURSE_INFO,
    **DEFAULT_VARIABLE_COURSE_INFO
}
