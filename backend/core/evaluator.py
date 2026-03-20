import json
import logging
import re
import time
import google.generativeai as genai
from typing import Dict, List

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Evaluator:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        
        # 🌟 1. 更新为最新的高效推理模型
        self.model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            # 🌟 2. 核心魔法：强制大模型以 JSON 格式输出，告别正则表达式清洗
            generation_config={"response_mime_type": "application/json"}
        )
        
        # 3. 提示词模板 (包含 JSON Schema 定义)
        self.PROMPT_TEMPLATES = {
            "CN_TO_EN": """
                You are a strict English coach.
                Source: "{question}"
                Reference: {standards}
                Student: "{user_answer}"
                
                Task: Evaluate the translation.
                Output JSON exactly:
                {{
                    "level": int (1=perfect, 2=good, 3=needs work, 4=wrong),
                    "is_correct": bool (true for 1&2, false for 3&4),
                    "explanation": "string (Max 2 short sentences. Directly point out the error or say 'Perfect'.)"
                }}
            """,
            "EN_TO_CN": """
                你是一名严格的中文导师。
                原题: "{question}"
                标准参考: {standards}
                学生回答: "{user_answer}"

                任务：评估翻译准确度。
                必须输出如下 JSON 格式：
                {{
                    "level": int (1为完美, 2为可接受, 3为需改进, 4为错误),
                    "is_correct": bool (1级和2级为 true，3和4为 false),
                    "explanation": "string (最多2句短话！直接指出错误，或者说'非常完美'。不要废话。)"
                }}
            """
        }

    # ==========================================
    # 🌟 Tier 1: 纯文本正则匹配模块 (0 API 消耗)
    # ==========================================
    @staticmethod
    def _clean_text(text: str) -> str:
        """内部方法：清洗文本，转小写，移除标点和空白"""
        if not text: return ""
        text = re.sub(r'[^\w\s\u4e00-\u9fa5]', '', text)
        text = re.sub(r'\s+', '', text)
        return text.lower()

    def is_exact_match(self, user_answer: str, standard_answers: List[str]) -> bool:
        """判断是否与任何一个标准答案字面完全一致（忽略大小写和标点）"""
        cleaned_user = self._clean_text(user_answer)
        return any(cleaned_user == self._clean_text(ans) for ans in standard_answers)

    def get_exact_match_result(self) -> Dict:
        """返回第一级正则匹配的固定结果"""
        return {
            "level": 1, 
            "isCorrect": True, 
            "message": "完美匹配！(极速通道)", 
            "judgedBy": "Regex Engine"
        }

    # ==========================================
    # 🌟 Tier 2: 向量生成模块
    # ==========================================
    def get_embedding(self, text: str) -> List[float]:
        """生成文本的语义特征向量 (用于极速判题)"""
        try:
            # 保持与数据库入库时相同的配置，不加 task_type
            result = genai.embed_content(
                model="models/gemini-embedding-001",
                content=text
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return []

    # ==========================================
    # 🌟 Tier 3: 大模型深度判卷模块
    # ==========================================
    async def judge(self, q_type: str, user_input: str, orig_text: str, std_answers: List[str], score: float) -> Dict:
        """
        双引擎判题系统 (向量拦截 + LLM 兜底)
        score: 用户输入与标准答案之一的向量余弦相似度 (Cosine Similarity)
        """
        # 引擎 2.1：向量极速放行路径
        if score > 0.95:
            logger.info("Fast Track: Vector match > 0.95")
            return {
                "level": 1, 
                "isCorrect": True, 
                "message": "完美匹配！表达非常地道。", 
                "judgedBy": "Vector Engine"
            }
        
        # 引擎 2.2：LLM 深度语义导师
        logger.info(f"LLM Track: Vector score is {score:.3f}, invoking Gemini...")
        template = self.PROMPT_TEMPLATES.get(q_type, self.PROMPT_TEMPLATES["EN_TO_CN"])
        full_prompt = template.format(question=orig_text, standards=std_answers, user_answer=user_input)
        
        try:
            # ⏱️ 1. 记录发起请求的绝对起点
            start_time = time.perf_counter() 
            first_token_time = None
            full_response_text = ""
            
            # 🧠 2. 开启流式生成 (stream=True)，让我们能精准捕获“首字时间”
            response_stream = self.model.generate_content(
                full_prompt,
                stream=True
            )
            
            # 逐块接收大模型吐出的数据
            for chunk in response_stream:
                if first_token_time is None:
                    # ⏱️ 记录收到网络回包的第一个字节的时间 (TTFT)
                    first_token_time = time.perf_counter()
                full_response_text += chunk.text
                
            # ⏱️ 3. 接收完毕的时间
            end_time = time.perf_counter()
            
            # 🧮 4. 计算细分指标
            # 如果因为某种原因没收到数据，做个兜底
            if first_token_time is None:
                first_token_time = end_time 

            ttft = first_token_time - start_time          # 首字耗时 (网络握手 + 模型思考)
            decode_time = end_time - first_token_time     # 纯吐字耗时 (生成 JSON)
            total_latency = end_time - start_time         # 总耗时
            
            # 🌟 5. 打印史诗级的详细体检报告
            logger.info(f"📊 [性能体检报告] ⚡ 总耗时: {total_latency:.3f} 秒")
            logger.info(f"   ├─ 🌐 网络建连+模型思考 (TTFT): {ttft:.3f} 秒")
            logger.info(f"   └─ ✍️ 模型纯生成输出 (Decode): {decode_time:.3f} 秒")
            
            # 将收集完的完整字符串解析为 JSON
            feedback_data = json.loads(full_response_text)
            
            return {
                "level": feedback_data.get("level", 2),
                "isCorrect": feedback_data.get("is_correct", False),
                "message": feedback_data.get("explanation", "判卷完成。"),
                "judgedBy": "LLM Mentor"
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {full_response_text}")
            return {
                "level": 4, 
                "isCorrect": False, 
                "message": "AI 解析你的答案时出了点小状况，换个说法试试？", 
                "judgedBy": "System Error"
            }
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return {
                "level": 4, 
                "isCorrect": False, 
                "message": "服务器正忙，请稍后再试。", 
                "judgedBy": "System Error"
            }