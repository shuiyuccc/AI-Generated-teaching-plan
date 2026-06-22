#!/usr/bin/env python3
"""
MiniMax API 测试脚本
用于验证 MiniMax API 连接是否正常
"""
import requests
import json
import sys

# 测试配置
API_KEY = ""  # 请在 .env 文件中设置 MINIMAX_API_KEY 或在此处填写
API_URL = "https://api.minimaxi.com/v1/chat/completions"
MODEL = "MiniMax-M2.7"


def test_minimax_api():
    """测试 MiniMax API 连接"""
    print("=" * 60)
    print("🧪 MiniMax API 连接测试")
    print("=" * 60)

    if not API_KEY or API_KEY == "":
        print("❌ 错误：请先在脚本中填写你的 MiniMax API Key")
        print("   位置：第12行的 API_KEY 变量")
        return False

    print(f"\n📋 配置信息：")
    print(f"   API URL: {API_URL}")
    print(f"   Model: {MODEL}")
    print(f"   API Key: {API_KEY[:10]}...{API_KEY[-4:] if len(API_KEY) > 14 else ''}")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": "Hi, how are you?"}
        ],
        "temperature": 0.7,
        "max_tokens": 100
    }

    print(f"\n📤 发送请求...")
    print(f"   请求体: {json.dumps(data, ensure_ascii=False, indent=2)}")

    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json=data,
            timeout=30
        )

        print(f"\n📥 响应状态: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ 请求成功！")
            print(f"\n📝 响应内容:")
            print(json.dumps(result, ensure_ascii=False, indent=2))

            # 提取回复内容
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0].get("message", {}).get("content", "")
                print(f"\n💬 模型回复: {content}")
            return True
        else:
            print(f"\n❌ 请求失败！")
            print(f"   状态码: {response.status_code}")
            print(f"   响应内容: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print(f"\n❌ 请求超时！")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ 连接错误: {e}")
        return False
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        return False


def test_with_config():
    """使用 config.py 中的配置测试"""
    print("\n" + "=" * 60)
    print("🧪 使用 config.py 配置测试")
    print("=" * 60)

    try:
        from config import get_current_model_config, MODEL_SELECTION

        # 临时切换到 MiniMax
        original_selection = MODEL_SELECTION

        # 获取 MiniMax 配置
        import config
        config.MODEL_SELECTION = 1
        model_config = get_current_model_config()

        print(f"\n📋 当前模型: {model_config.get('name')}")
        print(f"   API URL: {model_config.get('api_url')}")
        print(f"   Model: {model_config.get('model')}")

        api_key = model_config.get('api_key', '')
        if not api_key:
            print("\n❌ 错误：config.py 中未配置 MiniMax API Key")
            print("   请在 MINIMAX_CONFIG['api_key'] 中填写")
            config.MODEL_SELECTION = original_selection
            return False

        print(f"   API Key: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else ''}")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": model_config.get('model'),
            "messages": [
                {"role": "user", "content": "你好，请介绍一下自己"}
            ],
            "temperature": model_config.get('temperature', 0.7),
            "max_tokens": model_config.get('max_tokens', 100)
        }

        print(f"\n📤 发送请求...")
        response = requests.post(
            model_config.get('api_url'),
            headers=headers,
            json=data,
            timeout=30
        )

        print(f"📥 响应状态: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ 请求成功！")
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0].get("message", {}).get("content", "")
                print(f"\n💬 模型回复: {content[:200]}...")
            config.MODEL_SELECTION = original_selection
            return True
        else:
            print(f"\n❌ 请求失败: {response.text}")
            config.MODEL_SELECTION = original_selection
            return False

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n🔧 MiniMax API 测试工具\n")

    # 测试方式1：直接测试
    print("请选择测试方式:")
    print("1. 使用脚本内配置直接测试")
    print("2. 使用 config.py 配置测试")
    print("3. 两种都测试")

    choice = input("\n请输入选项 (1/2/3): ").strip()

    if choice == "1":
        success = test_minimax_api()
    elif choice == "2":
        success = test_with_config()
    elif choice == "3":
        success1 = test_minimax_api()
        success2 = test_with_config()
        success = success1 and success2
    else:
        print("❌ 无效选项")
        sys.exit(1)

    print("\n" + "=" * 60)
    if success:
        print("✅ 测试通过！MiniMax API 连接正常")
    else:
        print("❌ 测试失败！请检查 API Key 和网络连接")
    print("=" * 60)
