import requests
import json

# 后端地址
URL = "https://chilan-ai-language-learning-platform.onrender.com/evaluate"

def run_tests():
    # 你想要测试的各种变体
    test_cases = [
        "你周二一般做什么？",       # 完全一致
        "你周二一般干什么？",       # 少量同义词替换
        "你周二一般做什么",         # 少了标点
        "一般你周二干什么",         # 语序变动
        "你周二干什么",             # 略微精简
        "你干什么",                 # 严重缺失核心（时间）
        "你周二",                   # 严重缺失核心（动作）
        "你",                      # 极端碎片
        "今天天气不错"              # 完全无关
    ]

    print(f"{'用户输入':<20} | {'得分 (Score)':<10} | {'判定 (Verdict)':<10}")
    print("-" * 50)

    for text in test_cases:
        payload = {"user_input": text}
        try:
            response = requests.post(URL, json=payload)
            if response.status_code == 200:
                data = response.json()
                score = data.get("score")
                verdict = data.get("verdict")
                print(f"{text:<24} | {score:<12} | {verdict}")
            else:
                print(f"❌ 错误: {text} - 状态码 {response.status_code}")
        except Exception as e:
            print(f"❌ 连接失败: {e}")

if __name__ == "__main__":
    run_tests()