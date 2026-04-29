import json
import os
try:
    from content_builder.core.llm_providers import BaseLLMProvider
except ImportError:
    from core.llm_providers import BaseLLMProvider
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

from config.env import get_env_int

class Task1Extractor:
    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm = llm_provider
        self.pinyin_batch_size = max(1, get_env_int("CONTENT_TASK1_PINYIN_BATCH_SIZE", default=3))
        self.pinyin_batch_char_limit = max(200, get_env_int("CONTENT_TASK1_PINYIN_BATCH_CHAR_LIMIT", default=600))
        self.translation_repair_batch_size = max(
            1,
            get_env_int("CONTENT_TASK1_TRANSLATION_REPAIR_BATCH_SIZE", default=6)
        )

    def _build_extract_prompt(self, lesson_id: int, course_id: int) -> str:
        # 🚀 第一步：文本提取 + 强力去噪
        return f"""
        你是一名数据提取专家。请解析提供的教材 PDF，提取核心课文内容。
        只需输出 JSON。不要做拼音拆解。
        【重要】所有汉字内容必须统一输出简体中文，如遇繁体字请主动转换为简体，不要原样照搬繁体。

        【解析要求】
        1. lesson_metadata: course_id({course_id}), lesson_id({lesson_id}), title(根据内容生成中文标题), title_localized(将中文标题翻译为英文，简短自然，3-6个单词，适合教学标题，例如 "Exchanging Greetings"), content_type(课文主要形式)。
        2. content_type 仅能从以下枚举中选择一个：
           - "dialogue": 以人物对话为主
           - "diary": 日记体
           - "article": 短文/文章
           - "passage": 一般叙述性课文/段落
           - "mixed": 对话与叙述混合
        3. dialogues: 按照原文顺序提取。只需提取：role (角色), chinese (中文原文), english (英文翻译)。
           - 如果教材页面上给出了对应英文翻译，english 必须提取该翻译。
           - 如果教材页面上没有英文翻译，必须根据中文原句自动生成自然、简洁、适合教学展示的英文翻译，english 不要留空。
        4. 如果是对话类课文，按说话轮次提取，role 使用教材中的角色名。
        5. 如果是日记/文章/段落类课文，按自然句顺序切分提取；role 不要编造人物名，可统一填写为 "日记"、"课文" 或 "旁白" 中最合适的一项，并在整课内保持一致。

        【简繁去重规则 — 极其重要】本教材同时提供简体和繁体两个版本，不同册次呈现方式不同：
        - 格式A（旧册）：同一句话在同一页内连续两行，第一行简体、第二行繁体。
        - 格式B（新册）：整篇课文先完整出现简体版，紧接着下一页完整出现繁体版。
        无论哪种格式，规则统一：只提取简体中文，完全忽略繁体中文，不要把同一内容提取两次。
        识别简繁的方法：简体字笔画更少（如"学"vs"學"，"爱"vs"愛"，"长"vs"長"）。
        若发现某一页的内容与已提取内容完全对应、仅繁简写法不同，则该页为繁体页，整页跳过。
        如遇词汇表同时提供"Simplified"和"Traditional"两列，只取 Simplified 列。

        【🚨 视觉去噪指令 - 极其重要】
        - 必须剔除教材中的所有注脚符号、字母标记和参考数字。
        - 例如：剔除上标字母（a, b, c, d）、注脚数字（1, 2, 3）以及特殊符号（1*）。
        - 示例：原文 "我姓 1* 李" 提取后应为 "我姓李"。
        - 必须【原封不动】地保留句子中的所有标点符号（，。？！：）。

        【强制输出结构】
        {{
            "lesson_metadata": {{
                "course_id": {course_id},
                "lesson_id": {lesson_id},
                "title": "...",
                "title_localized": "...",
                "content_type": "dialogue"
            }},
            "course_content": {{
                "dialogues": [
                    {{ "role": "姓名", "chinese": "纯净对话内容", "translation": "translation" }}
                ]
            }}
        }}
        """

    def _build_translation_repair_prompt(self, dialogue_batch: list) -> str:
        payload = json.dumps([
            {
                "role": item.get("role", ""),
                "chinese": item.get("chinese", ""),
                "translation": item.get("translation", "")
            }
            for item in dialogue_batch
        ], ensure_ascii=False)

        return f"""
        你是一名教材内容修复专家。下面这些课文句子在第一次提取后 translation 为空或疑似漏提。
        请你重新检查这些句子的英文翻译，并按原顺序返回结果。
        素材：{payload}

        【规则】
        1. 如果 PDF 页面中有现成英文翻译，优先提取原文英文。
        2. 如果 PDF 页面中没有英文翻译，则必须根据中文原句自动补写自然、简洁、适合教学展示的英文翻译。
        3. 不要改动 role 和 chinese。
        4. translation 应尽量补全，不要留空。

        【输出结构】
        [
          {{
            "role": "角色",
            "chinese": "中文原句",
            "translation": "补全后的英文翻译"
          }}
        ]
        """

    def _build_pinyin_prompt(self, dialogues_to_process: list) -> str:
        # 🚀 第二步：拼音标注 + 自动识别新词高亮
        text_content = json.dumps(dialogues_to_process, ensure_ascii=False)
        return f"""
        你是一名中文拼音标注专家。请将对话中的中文句子 (chinese) 拆分为词或字，并标注拼音。
        素材：{text_content}

        【输出要求】
        1. 保持 role 和 translation 不变。
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
              "translation": "...",
              "words": [ {{ "cn": "词", "py": "pinyin", "highlight": true/false }} ]
            }}
        ]
        """

    def _estimate_dialogue_size(self, dialogue: dict) -> int:
        if not isinstance(dialogue, dict):
            return 0
        role = dialogue.get("role", "") or ""
        chinese = dialogue.get("chinese", "") or ""
        translation = dialogue.get("translation", "") or ""
        return len(role) + len(chinese) + len(translation)

    def _chunk_dialogues(self, dialogues: list):
        current_batch = []
        current_chars = 0

        for dialogue in dialogues:
            dialogue_chars = self._estimate_dialogue_size(dialogue)
            should_split = (
                current_batch
                and (
                    len(current_batch) >= self.pinyin_batch_size
                    or current_chars + dialogue_chars > self.pinyin_batch_char_limit
                )
            )
            if should_split:
                yield current_batch
                current_batch = []
                current_chars = 0

            current_batch.append(dialogue)
            current_chars += dialogue_chars

        if current_batch:
            yield current_batch

    def _generate_pinyin_batch(self, batch: list):
        pinyin_prompt = self._build_pinyin_prompt(batch)
        return self.llm.generate_structured_json(pinyin_prompt, file_path=None)

    def _repair_missing_english(self, raw_dialogues: list, file_path: str = None, file_obj=None) -> list:
        if not raw_dialogues:
            return raw_dialogues

        missing_indices = [
            idx for idx, item in enumerate(raw_dialogues)
            if isinstance(item, dict) and not (item.get("translation") or "").strip()
        ]
        if not missing_indices:
            return raw_dialogues

        print(f"     🩹 检测到 {len(missing_indices)} 句缺少英文翻译，正在启动英译补全...")

        for start in range(0, len(missing_indices), self.translation_repair_batch_size):
            index_batch = missing_indices[start:start + self.translation_repair_batch_size]
            dialogue_batch = [raw_dialogues[idx] for idx in index_batch]
            repair_result = self.llm.generate_structured_json(
                self._build_translation_repair_prompt(dialogue_batch),
                file_path=file_path,
                file_obj=file_obj
            )

            if isinstance(repair_result, list) and len(repair_result) == len(dialogue_batch):
                for local_idx, repaired_item in enumerate(repair_result):
                    repaired_english = ""
                    if isinstance(repaired_item, dict):
                        repaired_english = (repaired_item.get("translation") or "").strip()
                    if repaired_english:
                        raw_dialogues[index_batch[local_idx]]["translation"] = repaired_english

        return raw_dialogues

    def _annotate_batch_with_retry(self, batch: list, batch_label: str) -> list:
        try:
            batch_result = self._generate_pinyin_batch(batch)
            if isinstance(batch_result, list):
                return batch_result
            raise ValueError(f"❌ Task 1.2 {batch_label} 返回结构异常，期望 list。")
        except Exception as exc:
            error_text = str(exc)
            if "MAX_TOKENS" in error_text and len(batch) > 1:
                split_point = max(1, len(batch) // 2)
                print(
                    f"     ⚠️ {batch_label} 命中 MAX_TOKENS，正在自动拆分为 "
                    f"{split_point} + {len(batch) - split_point} 句重试..."
                )
                left_result = self._annotate_batch_with_retry(batch[:split_point], f"{batch_label}-A")
                right_result = self._annotate_batch_with_retry(batch[split_point:], f"{batch_label}-B")
                return left_result + right_result
            raise

    def _annotate_pinyin_in_batches(self, raw_dialogues: list) -> list:
        if not raw_dialogues:
            return []

        batches = list(self._chunk_dialogues(raw_dialogues))
        if len(batches) == 1:
            only_batch = batches[0]
            print(
                f"     📦 Task 1.2 以单批处理拼音标注 "
                f"(共 {len(only_batch)} 句, 约 {sum(self._estimate_dialogue_size(x) for x in only_batch)} 字符)..."
            )
            return self._annotate_batch_with_retry(only_batch, "Task 1.2 单批")

        print(
            f"     📦 Task 1.2 将按批次处理拼音标注 "
            f"(共 {len(raw_dialogues)} 句, 最多 {self.pinyin_batch_size} 句/批, "
            f"约 {self.pinyin_batch_char_limit} 字符/批, 实际 {len(batches)} 批)..."
        )
        merged_result = []

        for index, batch in enumerate(batches, start=1):
            batch_chars = sum(self._estimate_dialogue_size(x) for x in batch)
            print(f"     📦 正在处理第 {index} 组拼音标注 ({len(batch)} 句, 约 {batch_chars} 字符)...")
            batch_result = self._annotate_batch_with_retry(batch, f"Task 1.2 第 {index} 组")
            merged_result.extend(batch_result)

        return merged_result

    def run(self, lesson_id: int, course_id: int, file_path: str = None, file_obj=None):
        print(f"  ▶️ [Task 1.1] 正在从 PDF 提取纯净对话文本...")
        extract_prompt = self._build_extract_prompt(lesson_id, course_id)
        raw_result = self.llm.generate_structured_json(extract_prompt, file_path=file_path, file_obj=file_obj)
        
        if not raw_result: return None

        # 防御：新模型可能直接返回 dialogues 数组而非外层 dict
        if isinstance(raw_result, list):
            print(f"  ⚠️ Task 1.1 返回了裸数组，自动补全外层结构...")
            raw_result = {
                "lesson_metadata": {"course_id": course_id, "lesson_id": lesson_id, "title": "", "content_type": "dialogue"},
                "course_content": {"dialogues": raw_result},
            }
        elif not isinstance(raw_result, dict):
            print(f"  ❌ Task 1.1 返回了未知类型 {type(raw_result)}，终止。")
            return None

        raw_dialogues = raw_result.get("course_content", {}).get("dialogues", [])
        raw_dialogues = self._repair_missing_english(raw_dialogues, file_path=file_path, file_obj=file_obj)
        raw_result["course_content"]["dialogues"] = raw_dialogues

        print(f"  ▶️ [Task 1.2] 正在标注拼音并识别重点词汇...")
        pinyin_result = self._annotate_pinyin_in_batches(raw_dialogues)

        # 🚀 【结构封装】：匹配前端 .flatMap(t => t.lines)
        raw_result["course_content"]["dialogues"] = [
            {
                "lines": pinyin_result
            }
        ]
        
        print(f"  ✨ Task 1 解析完毕 (已净化文本并添加变色高亮标记)。")
        return raw_result
