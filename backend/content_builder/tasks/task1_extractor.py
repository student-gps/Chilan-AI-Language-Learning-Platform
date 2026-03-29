import json
import os
from llm_providers import BaseLLMProvider

class Task1Extractor:
    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm = llm_provider
        self.pinyin_batch_size = max(1, int(os.getenv("CB_TASK1_PINYIN_BATCH_SIZE", "5")))

    def _build_extract_prompt(self, lesson_id: int, course_id: int) -> str:
        # 🚀 第一步：文本提取 + 强力去噪
        return f"""
        你是一名数据提取专家。请解析提供的教材 PDF，提取核心课文对话。
        只需输出 JSON。不要做拼音拆解。

        【解析要求】
        1. lesson_metadata: course_id({course_id}), lesson_id({lesson_id}), title(根据内容生成中文标题)。
        2. dialogues: 按照原文顺序提取。只需提取：role (角色), chinese (中文原文), english (英文翻译)。

        【🚨 视觉去噪指令 - 极其重要】
        - 必须剔除教材中的所有注脚符号、字母标记和参考数字。
        - 例如：剔除上标字母（a, b, c, d）、注脚数字（1, 2, 3）以及特殊符号（1*）。
        - 示例：原文 "我姓 1* 李" 提取后应为 "我姓李"。
        - 必须【原封不动】地保留句子中的所有标点符号（，。？！：）。

        【强制输出结构】
        {{
            "lesson_metadata": {{ "course_id": {course_id}, "lesson_id": {lesson_id}, "title": "..." }},
            "course_content": {{
                "dialogues": [
                    {{ "role": "姓名", "chinese": "纯净对话内容", "english": "translation" }}
                ]
            }}
        }}
        """

    def _build_pinyin_prompt(self, dialogues_to_process: list) -> str:
        # 🚀 第二步：拼音标注 + 自动识别新词高亮
        text_content = json.dumps(dialogues_to_process, ensure_ascii=False)
        return f"""
        你是一名中文拼音标注专家。请将对话中的中文句子 (chinese) 拆分为词或字，并标注拼音。
        素材：{text_content}

        【输出要求】
        1. 保持 role 和 english 不变。
        2. words 数组：每个对象包含 cn (中文)、py (拼音) 和 highlight (布尔值)。
        
        【🚨 高亮与标点规则】
        - highlight: 如果该词是本课的核心新词（如动词、代词、关键名词），设为 true，否则为 false。
        - 标点处理：标点符号必须独立成项，py 为空 ""，highlight 为 false。
        - 示例："我姓李。" 拆分为：
          [ {{"cn": "我", "py": "wǒ", "highlight": false}}, {{"cn": "姓", "py": "xìng", "highlight": true}}, {{"cn": "李", "py": "lǐ", "highlight": false}}, {{"cn": "。", "py": "", "highlight": false}} ]

        【输出结构】
        [
            {{ 
              "role": "姓名", 
              "english": "...", 
              "words": [ {{ "cn": "词", "py": "pinyin", "highlight": true/false }} ] 
            }}
        ]
        """

    def _chunk_dialogues(self, dialogues: list):
        for start in range(0, len(dialogues), self.pinyin_batch_size):
            yield dialogues[start:start + self.pinyin_batch_size]

    def _annotate_pinyin_in_batches(self, raw_dialogues: list) -> list:
        if not raw_dialogues:
            return []

        if len(raw_dialogues) <= self.pinyin_batch_size:
            pinyin_prompt = self._build_pinyin_prompt(raw_dialogues)
            return self.llm.generate_structured_json(pinyin_prompt, file_path=None)

        print(f"     📦 Task 1.2 将按批次处理拼音标注 (共 {len(raw_dialogues)} 句, 每批 {self.pinyin_batch_size} 句)...")
        merged_result = []

        for index, batch in enumerate(self._chunk_dialogues(raw_dialogues), start=1):
            print(f"     📦 正在处理第 {index} 组拼音标注...")
            pinyin_prompt = self._build_pinyin_prompt(batch)
            batch_result = self.llm.generate_structured_json(pinyin_prompt, file_path=None)
            if isinstance(batch_result, list):
                merged_result.extend(batch_result)
            else:
                raise ValueError(f"❌ Task 1.2 第 {index} 组返回结构异常，期望 list。")

        return merged_result

    def run(self, lesson_id: int, course_id: int, file_path: str = None, file_obj=None):
        print(f"  ▶️ [Task 1.1] 正在从 PDF 提取纯净对话文本...")
        extract_prompt = self._build_extract_prompt(lesson_id, course_id)
        raw_result = self.llm.generate_structured_json(extract_prompt, file_path=file_path, file_obj=file_obj)
        
        if not raw_result: return None

        print(f"  ▶️ [Task 1.2] 正在标注拼音并识别重点词汇...")
        raw_dialogues = raw_result.get("course_content", {}).get("dialogues", [])
        pinyin_result = self._annotate_pinyin_in_batches(raw_dialogues)

        # 🚀 【结构封装】：匹配前端 .flatMap(t => t.lines)
        raw_result["course_content"]["dialogues"] = [
            {
                "lines": pinyin_result
            }
        ]
        
        print(f"  ✨ Task 1 解析完毕 (已净化文本并添加变色高亮标记)。")
        return raw_result
