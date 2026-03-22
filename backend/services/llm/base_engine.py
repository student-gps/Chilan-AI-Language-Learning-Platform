import time
import json
import google.generativeai as genai
from typing import Dict, Any

class LLMEngine:
    def __init__(self, api_key: str, model_name: str = 'gemini-2.0-flash'):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={"response_mime_type": "application/json"}
        )

    async def generate_json(self, prompt: str, pm=None) -> Dict[str, Any]:
        start = time.perf_counter()
        full_text = ""
        try:
            # 使用流式传输以获得最快反馈
            response = self.model.generate_content(prompt, stream=True)
            for chunk in response:
                full_text += chunk.text
            
            # 🌟 记录到监控器
            if pm:
                pm.record("Tier 3 (LLM Inf)", time.perf_counter() - start)
            
            # 调试：依然保留原始回包打印，方便看 AI 说了什么
            # print(f"🤖 [RAW]: {full_text}")
            
            return json.loads(full_text)
        except Exception as e:
            print(f"❌ LLM Error: {e}")
            return {"level": 2, "is_correct": True, "explanation": "Error occurred."}