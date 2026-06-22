"""
配置文件 - 存放API密钥和其他配置
支持多模型切换：1=MiniMax, 2=DeepSeek V3
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ============================================
# 模型选择配置
# 设置 MODEL_SELECTION = 1 使用 MiniMax
# 设置 MODEL_SELECTION = 2 使用 DeepSeek V3
# ============================================
MODEL_SELECTION = 2  # 默认使用 DeepSeek V3

# ============================================
# MiniMax 模型配置 (MODEL_SELECTION = 1)
# ============================================
# MiniMax 使用标准 OpenAI 兼容接口
# API文档: https://platform.minimaxi.com/docs/api-reference/text-chat-completions
# 支持模型: MiniMax-M2.7, MiniMax-M1, MiniMax-Text-01
MINIMAX_CONFIG = {
    "api_key": os.getenv("MINIMAX_API_KEY", ""),  # 请在 .env 文件中设置 MINIMAX_API_KEY
    "api_url": os.getenv("MINIMAX_API_URL", "https://api.minimaxi.com/v1/chat/completions"),  # MiniMax 官方 API 地址
    "model": "MiniMax-M2.7",  # MiniMax 2.7 模型
    "temperature": 0.7,
    "max_tokens": 32000,
    "stream": False
}

# ============================================
# DeepSeek V3 模型配置 (MODEL_SELECTION = 2)
# ============================================
DEEPSEEK_CONFIG = {
    "api_key": os.getenv("DEEPSEEK_API_KEY", ""),  # 请在 .env 文件中设置 DEEPSEEK_API_KEY
    "api_url": os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions"),
    "model": "deepseek-chat",  # DeepSeek V3 模型
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
