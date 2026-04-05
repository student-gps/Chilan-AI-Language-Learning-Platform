import json
import os
import re
import time
from pathlib import Path
from llm_providers import BaseLLMProvider
import sys

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

from config.env import get_env, get_env_bool, get_env_float, get_env_int

class Task2QuizGenerator:
    def __init__(self, llm_provider: BaseLLMProvider, memory_dir: Path):
        self.llm = llm_provider
        self.memory_file = memory_dir / "global_vocab_memory.json"
        # 🚀 这里的 global_vocab 现在的结构是字典: { "单词": [ {词义1...}, {词义2...} ] }
        self.global_vocab = self._load_memory()
        self.example_batch_size = max(1, get_env_int("CONTENT_TASK2_EXAMPLE_BATCH_SIZE", "CB_TASK2_EXAMPLE_BATCH_SIZE", default=3))
        self.word_quiz_batch_size = max(1, get_env_int("CONTENT_TASK2_WORD_QUIZ_BATCH_SIZE", "CB_TASK2_WORD_QUIZ_BATCH_SIZE", default=4))
        self.speech_quiz_min = max(1, get_env_int("PRACTICE_SPEECH_QUIZ_MIN", "CB_TASK2_SPEECH_QUIZ_MIN", default=3))
        self.speech_quiz_max = max(self.speech_quiz_min, get_env_int("PRACTICE_SPEECH_QUIZ_MAX", "CB_TASK2_SPEECH_QUIZ_MAX", default=5))
        target_default = min(self.speech_quiz_max, 4)
        self.speech_quiz_target = get_env_int("PRACTICE_SPEECH_QUIZ_TARGET", "CB_TASK2_SPEECH_QUIZ_TARGET", default=target_default)
        self.speech_quiz_target = max(self.speech_quiz_min, min(self.speech_quiz_target, self.speech_quiz_max))
        self.speech_allow_paraphrase = get_env_bool("PRACTICE_VOICE_ALLOW_PARAPHRASE", "VOICE_ALLOW_PARAPHRASE", default=True)

    def _load_memory(self) -> dict:
        if self.memory_file.exists():
            with open(self.memory_file, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except:
                    return {}
        return {}

    def save_memory(self, new_vocab_list: list, lesson_id: int):
        """
        🚀 升级版保存逻辑：将本课新词的完整信息（释义、例句）追加到全局词典中
        """
        # 重新加载一次以确保数据最新
        full_dict = self._load_memory()

        for v in new_vocab_list:
            word = v.get("word")
            definition = v.get("definition")
            example_sentence = self._normalize_example(v.get("example_sentence"))
            
            entry = {
                "definition": definition,
                "pinyin": v.get("pinyin"),
                "part_of_speech": v.get("part_of_speech"),
                "example": example_sentence,
                "lesson_id": lesson_id
            }

            if word not in full_dict:
                full_dict[word] = []
            
            # 💡 防重复检查：如果该单词下已存在完全相同的释义，则不重复添加
            learned_definitions = [e["definition"] for e in full_dict[word]]
            if definition not in learned_definitions:
                full_dict[word].append(entry)

        # 创建目录（如果不存在）
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.memory_file, "w", encoding="utf-8") as f:
            json.dump(full_dict, f, ensure_ascii=False, indent=2)

    def _inject_historical_context(self, current_vocab: list) -> list:
        """
        🚀 打捞逻辑：为当前生词注入该词在之前课程中学过的所有用法
        """
        for v in current_vocab:
            word = v.get("word")
            # 如果记忆库里有这个词的历史记录，则捞出来
            if word in self.global_vocab:
                historical_usages = self.global_vocab[word]
                current_definition = (v.get("definition") or "").strip().lower()
                same_definition = [
                    usage for usage in historical_usages
                    if (usage.get("definition") or "").strip().lower() == current_definition
                ]
                other_definitions = [
                    usage for usage in historical_usages
                    if (usage.get("definition") or "").strip().lower() != current_definition
                ]
                v["historical_usages"] = same_definition + other_definitions
        return current_vocab

    def _chunk_items(self, items: list, batch_size: int):
        for start in range(0, len(items), batch_size):
            yield items[start:start + batch_size]

    def _dedupe_sentence_materials(self, items: list) -> list:
        seen = set()
        deduped = []

        for item in items:
            if not isinstance(item, dict):
                continue

            cn = (item.get("cn") or "").strip()
            en = (item.get("en") or "").strip()
            py = (item.get("py") or "").strip()

            if not cn and not en:
                continue

            dedupe_key = (cn, en)
            if dedupe_key in seen:
                continue

            seen.add(dedupe_key)
            deduped.append({"cn": cn, "py": py, "en": en})

        return deduped

    def _normalize_example(self, example: dict | None) -> dict:
        if not isinstance(example, dict):
            return {"cn": "", "py": "", "en": ""}
        return {
            "cn": (example.get("cn") or "").strip(),
            "py": (example.get("py") or "").strip(),
            "en": (example.get("en") or "").strip()
        }

    def _is_blank_example(self, example: dict | None) -> bool:
        normalized = self._normalize_example(example)
        return not normalized["cn"] and not normalized["py"] and not normalized["en"]

    def _definition_keywords(self, definition: str) -> set:
        text = (definition or "").lower()
        raw_tokens = re.findall(r"[a-z]+", text)
        stop_words = {
            "a", "an", "the", "to", "of", "and", "or", "be", "is", "are", "am",
            "one", "ones", "form", "see", "grammar", "somebody", "something",
            "lit", "its", "it", "this", "that"
        }
        keywords = {token for token in raw_tokens if len(token) > 2 and token not in stop_words}
        synonym_map = {
            "fine": {"good", "fine", "well", "ok", "okay", "nice"},
            "good": {"good", "fine", "well", "ok", "okay", "nice"},
            "nice": {"good", "nice", "fine"},
            "very": {"very", "so", "quite", "really"},
            "busy": {"busy"},
            "tired": {"tired"},
            "ask": {"ask", "question"},
            "please": {"please"},
        }
        expanded = set()
        for token in keywords:
            expanded.update(synonym_map.get(token, {token}))
        return expanded or keywords

    def _example_matches_current_sense(self, vocab_item: dict, example: dict) -> bool:
        normalized = self._normalize_example(example)
        english = normalized["en"].lower()
        if not english:
            return False

        keywords = self._definition_keywords(vocab_item.get("definition") or "")
        if not keywords:
            return True

        return any(keyword in english for keyword in keywords)

    def _example_contains_word(self, vocab_item: dict, example: dict) -> bool:
        normalized = self._normalize_example(example)
        word = (vocab_item.get("word") or "").strip()
        return bool(word and word in normalized["cn"])

    def _pick_dialogue_fallback_example(self, vocab_item: dict, source_dialogues: list) -> dict:
        word = (vocab_item.get("word") or "").strip()
        if not word:
            return {"cn": "", "py": "", "en": ""}

        historical_same_definition = [
            usage for usage in (vocab_item.get("historical_usages") or [])
            if (usage.get("definition") or "").strip().lower() == (vocab_item.get("definition") or "").strip().lower()
        ]

        sentence_candidates = self._extract_dialogue_sentence_fallback(source_dialogues)
        containing_word = [
            sentence for sentence in sentence_candidates
            if word in (sentence.get("cn") or "")
        ]
        if not containing_word:
            if historical_same_definition:
                historical_example = self._normalize_example(historical_same_definition[0].get("example"))
                if not self._is_blank_example(historical_example):
                    return historical_example
            return {"cn": "", "py": "", "en": ""}

        matching_sense = [
            sentence for sentence in containing_word
            if self._example_matches_current_sense(vocab_item, sentence)
        ]
        if matching_sense:
            return self._normalize_example(matching_sense[0])

        if historical_same_definition:
            historical_example = self._normalize_example(historical_same_definition[0].get("example"))
            if not self._is_blank_example(historical_example):
                return historical_example

        # 如果本课原文里确实出现了该词，但英文是整句自由翻译，
        # 也优先保留这条“本课真实原句”，不要因为逐词对不上就留空。
        return self._normalize_example(containing_word[0])

    def _extract_dialogue_sentence_fallback(self, source_dialogues: list) -> list:
        fallback_items = []

        for dialogue_block in source_dialogues or []:
            lines = dialogue_block.get("lines", []) if isinstance(dialogue_block, dict) else []
            for line in lines:
                if not isinstance(line, dict):
                    continue

                words = line.get("words", [])
                cn = "".join(
                    token.get("cn", "")
                    for token in words
                    if isinstance(token, dict)
                ).strip()
                en = (line.get("english") or "").strip()
                py = " ".join(
                    token.get("py", "").strip()
                    for token in words
                    if isinstance(token, dict) and token.get("py")
                ).strip()

                if cn and en:
                    fallback_items.append({"cn": cn, "py": py, "en": en})

        return self._dedupe_sentence_materials(fallback_items)

    # --- Task 2.1a: 提取单词基本信息 (骨架) ---
    def _build_vocab_base_prompt(self) -> str:
        return """
        你是一名数据提取专家。
        🚨 【核心禁令】：严禁使用你自身的知识储备！你必须【且仅能】提取 PDF 页面中物理显示的文字。
        
        【提取要求】
        1. 仅定位 PDF 中的“生词表/Vocabulary”板块。
        2. 仅提取字段：单词(word)、拼音(pinyin)、词性(part_of_speech)、英文定义(definition)。
        3. 单词请提取全部，拼音格式为标准汉语拼音(即辅音大写、元音小写、并直接在元音上标注声调)，词性请使用英文全称(Noun, Adjective, Verb, etc.)，定义提取对应的英文。
        3. 如果当前 PDF 页面没有任何生词表，请直接返回 {"vocabulary": []}。
        4. 严禁自行添加任何 PDF 中不存在的单词（哪怕你觉得这一课应该学这些词）。
        
        【输出格式】
        只输出合法的 JSON，不包含任何 Markdown 标记。
        { "vocabulary": [ { "word": "...", "pinyin": "...", "part_of_speech": "...", "definition": "..." } ] }
        """
    
    def _build_vocab_example_prompt(self, word_list: list) -> str:
        vocab_payload = json.dumps([
            {
                "word": item.get("word", ""),
                "pinyin": item.get("pinyin", ""),
                "part_of_speech": item.get("part_of_speech", ""),
                "definition": item.get("definition", "")
            }
            for item in word_list
        ], ensure_ascii=False)
        return f"""
        你是一名数据提取专家。请从 PDF 中为以下【词义】提取原书中的真实例句。
        词义清单：{vocab_payload}

        【🚨 提取准则】
        1. 必须且仅能提取 PDF 中物理显示的原文例句，严禁（FATAL ERROR）自行造句，严禁使用外部知识。
        2. 你要处理的是“词义”，不是单纯的“词形”。
           - 必须优先匹配当前条目的 definition 和 part_of_speech。
           - 如果同一个词在本课里出现了不同意思，只能返回与当前义项一致的那一句。
        3. 先查找词汇表/生词表里配套的官方例句；如果没有，再去本课课文原文中找包含该词的真实句子。
           - 只要本课正文里确实出现了该词，就应优先返回这条本课原句。
           - 即使英文是整句自由翻译、不是逐词直译，也仍然算有效原句，不能因此留空。
        4. 必须保持中文、拼音、英文严格对齐。
        5. 只有当词汇表和本课正文里都找不到包含该词的真实原句时，才返回空对象。
        6. 如果同一个词在本课里有多种用法，优先返回最贴近当前 definition / part_of_speech 的那一句；如果无法完全判定，也应返回最自然、最核心的本课原句，而不是空对象。

        【强制输出结构】
        - 必须返回一个 JSON 数组，长度必须为 {len(word_list)}。
        - 如果某个单词在 PDF 中没有找到配套例句，该项必须返回以下空对象：
          {{ "cn": "", "py": "", "en": "" }}
        - 示例结构：
          [
            {{ "cn": "我是学生。", "py": "Wǒ shì xuésheng.", "en": "I am a student." }},
            {{ "cn": "", "py": "", "en": "" }} 
          ]
        """

    def _attach_examples_with_fallback(self, vocab_batch: list, example_batch: list, source_dialogues: list) -> list:
        merged = []

        for idx, vocab in enumerate(vocab_batch):
            raw_example = example_batch[idx] if idx < len(example_batch) else {}
            normalized_example = self._normalize_example(raw_example)

            if self._is_blank_example(normalized_example):
                normalized_example = self._pick_dialogue_fallback_example(vocab, source_dialogues)
            elif not self._example_contains_word(vocab, normalized_example):
                normalized_example = self._pick_dialogue_fallback_example(vocab, source_dialogues)
            elif not self._example_matches_current_sense(vocab, normalized_example):
                normalized_example = self._pick_dialogue_fallback_example(vocab, source_dialogues)

            merged.append({**vocab, "example_sentence": normalized_example})

        return merged

    def _fill_vocab_examples_in_batches(self, new_vocab_base: list, file_path: str = None, file_obj=None, source_dialogues: list = None) -> list:
        if not new_vocab_base:
            return []

        if len(new_vocab_base) <= self.example_batch_size:
            v_ex_res = self.llm.generate_structured_json(
                self._build_vocab_example_prompt(new_vocab_base),
                file_path=file_path,
                file_obj=file_obj
            )
            if isinstance(v_ex_res, list) and len(v_ex_res) == len(new_vocab_base):
                return self._attach_examples_with_fallback(new_vocab_base, v_ex_res, source_dialogues)
            return new_vocab_base

        print(f"     📦 Task 2.1b 将按批次回填官方例句 (共 {len(new_vocab_base)} 个词义, 每批 {self.example_batch_size} 个)...")
        merged_vocab = []

        for index, batch in enumerate(self._chunk_items(new_vocab_base, self.example_batch_size), start=1):
            print(f"     📦 正在回填第 {index} 组官方例句...")
            v_ex_res = self.llm.generate_structured_json(
                self._build_vocab_example_prompt(batch),
                file_path=file_path,
                file_obj=file_obj
            )

            if isinstance(v_ex_res, list) and len(v_ex_res) == len(batch):
                merged_vocab.extend(self._attach_examples_with_fallback(batch, v_ex_res, source_dialogues))
            else:
                merged_vocab.extend(batch)

            time.sleep(1)

        return merged_vocab

    def _build_grammar_extract_prompt(self) -> str:
        return """
        你是一名数据提取专家。请解析 PDF，提取书中的“语法/练习(Grammar/Exercises)”部分。
        只输出合法的 JSON 格式。

        【🚨 提取准则】
        1. 仅限提取课后习题中用于“翻译练习”或“完成句子”的原文。
        2. 严禁（STOP）引入任何与本教材内容、本课主题无关的句子。
        3. 严禁为了凑数而自行生成练习题。

        【强制输出结构】
        - 如果在 PDF 中未发现适合的练习句，请务必返回：{{ "grammar_practice": [] }}
        - 正常结构示例：
          {{
            "grammar_practice": [
                {{ "cn": "练习句原文", "py": "liànxíjù yuánwén", "en": "exercise" }}
            ]
          }}
        """
    
    def _summarize_historical_usages_for_prompt(self, vocab_item: dict) -> list:
        grouped = {}
        current_definition = (vocab_item.get("definition") or "").strip().lower()

        for usage in (vocab_item.get("historical_usages") or []):
            if not isinstance(usage, dict):
                continue

            definition = (usage.get("definition") or "").strip()
            key = definition.lower()
            if key not in grouped:
                grouped[key] = {
                    "definition": definition,
                    "part_of_speech": usage.get("part_of_speech"),
                    "pinyin": usage.get("pinyin"),
                    "lesson_ids": [],
                    "representative_example": {"cn": "", "py": "", "en": ""}
                }

            lesson_id = usage.get("lesson_id")
            if lesson_id and lesson_id not in grouped[key]["lesson_ids"]:
                grouped[key]["lesson_ids"].append(lesson_id)

            normalized_example = self._normalize_example(usage.get("example"))
            if self._is_blank_example(grouped[key]["representative_example"]) and not self._is_blank_example(normalized_example):
                grouped[key]["representative_example"] = normalized_example

        ordered_items = []
        if current_definition and current_definition in grouped:
            ordered_items.append(grouped.pop(current_definition))
        ordered_items.extend(grouped.values())
        return ordered_items

    def _build_word_quiz_vocab_payload(self, vocabulary_with_history: list) -> list:
        prompt_vocab = []

        for item in vocabulary_with_history:
            if not isinstance(item, dict):
                continue

            prompt_vocab.append({
                "word": item.get("word"),
                "pinyin": item.get("pinyin"),
                "part_of_speech": item.get("part_of_speech"),
                "definition": item.get("definition"),
                "example_sentence": self._normalize_example(item.get("example_sentence")),
                "historical_usages_summary": self._summarize_historical_usages_for_prompt(item)
            })

        return prompt_vocab

    # --- Task 2.3a: 专门生成单词题 (100% 覆盖) ---
    def _build_word_quiz_prompt(self, lesson_id: int, course_id: int, vocabulary_with_history: list) -> str:
        prompt_vocab = self._build_word_quiz_vocab_payload(vocabulary_with_history)
        vocab_str = json.dumps(prompt_vocab, ensure_ascii=False)
        vocab_count = len(prompt_vocab)
        
        return f"""
        你是一名严谨的词汇练习编写专家。请为提供的【核心词汇表】生成全量翻译练习。
        
        【素材清单】
        本课核心词汇（共 {vocab_count} 个）：{vocab_str}

        【🚨 核心生成规则 - 必须 100% 遵守】
        1. **词汇全覆盖 (Word-Level Full Coverage)**：
           - 你必须为【核心词汇表】中的【每一个】单词生成两道题：
             * 一道中译英 (CN_TO_EN)
             * 一道英译中 (EN_TO_CN)
           - 意味着如果你收到了 {vocab_count} 个词，你【必须】产出 {vocab_count * 2} 道词汇题。
        
        2. **单例句约束 (One Context Example)**：
           - 每道题目【只需且仅能】提供 1 个关联例句（context_examples 数组长度必须为 1）。
           - 必须从素材中提供的 example_sentence 或 historical_usages_summary 中提取。
           - historical_usages_summary 是历史义项的压缩视图：当前义项排在前面，其他义项仅作辨义参考。
           - 如果当前义项与其他历史义项冲突，必须优先遵循当前义项，避免把别的意思的例句错配进来。

        3. **禁止幻觉**：
           - 题目和例句必须 100% 来源于提供的素材，严禁引入清单外的任何主题或复杂句型。

        4. **专名题面可答性**：
           - 如果词条是人名、姓氏或其他专有名词，题目的 original_text 不能只写抽象释义（例如 "(a personal name)"）。
           - 对于 EN_TO_CN 题目，必须把具体词面一并写出，使用户知道要翻译的是哪一个名字或姓氏。
           - 示例：
             * "李友" 应写成 "Li You (a personal name)"
             * "李" 应写成 "Li (a family name); plum"

        【强制输出结构】
        {{
            "database_items": [
                {{
                    "lesson_id": {lesson_id},
                    "question_id": 0,
                    "course_id": {course_id},
                    "question_type": "CN_TO_EN 或 EN_TO_CN",
                    "original_text": "单词文本",
                    "original_pinyin": "拼音(中文题目必填)",
                    "standard_answers": ["标准答案"],
                    "context_examples": [
                        {{ "cn": "唯一例句", "py": "pinyin", "en": "translation" }}
                    ]
                }}
            ]
        }}
        """

    def _build_answer_display_text(self, vocab_item: dict) -> str:
        word = (vocab_item.get("word") or "").strip()
        pinyin = (vocab_item.get("pinyin") or "").strip()

        if not pinyin:
            return word

        display_name = " ".join(part.capitalize() for part in pinyin.replace("'", " ").split())
        return display_name or word

    def _normalize_word_quiz_item(self, item: dict, vocab_lookup: dict) -> dict:
        if not isinstance(item, dict):
            return item

        question_type = item.get("question_type")
        standard_answers = item.get("standard_answers") or []
        answer_word = standard_answers[0] if standard_answers else ""
        vocab_item = vocab_lookup.get(answer_word)

        if question_type == "EN_TO_CN" and vocab_item:
            original_text = (item.get("original_text") or "").strip()
            answer_display = self._build_answer_display_text(vocab_item)

            if answer_display and (
                original_text.startswith("(")
                or "personal name" in original_text.lower()
                or "family name" in original_text.lower()
            ):
                item["original_text"] = f"{answer_display} {original_text}".strip()

        return item

    # --- Task 2.3b: 专门生成句子题 (精选生成) ---
    def _build_sentence_quiz_prompt(self, lesson_id: int, course_id: int, combined_practice: list) -> str:
        grammar_str = json.dumps(combined_practice, ensure_ascii=False)
        
        return f"""
        你是一名资深的对外汉语专家。请根据提供的【原句素材】生成精选翻译题库。
        
        【素材清单】
        课文/语法原句素材：{grammar_str}

        【🚨 核心生成规则 - 必须 100% 遵守】
        1. **句子翻译 (Sentence-Level)**：
           - 从素材中挑选最核心的句子生成 6-8 道精选翻译题。
           - 句子不能太复杂，要精简，可以做一定的切割，但必须保持原文的核心意思和关键词。
           - 必须包含英译中书写题 (EN_TO_CN)。
           - 不要生成任何句子级的中译英题 (CN_TO_EN)，这部分已经被语音句子题替代。

        2. **无例句要求**：
           - 句子翻译题【不需要】提供 context_examples，直接返回题目即可。

        3. **禁止幻觉**：
           - 题目必须 100% 来源于提供的素材，严禁自行编造清单外的内容。

        【强制输出结构】
        {{
            "database_items": [
                {{
                    "lesson_id": {lesson_id},
                    "question_id": 0,
                    "course_id": {course_id},
                    "question_type": "EN_TO_CN",
                    "original_text": "句子原文",
                    "original_pinyin": "拼音(中文题目必填)",
                    "standard_answers": ["标准答案"]
                }}
            ]
        }}
        """

    def _get_speech_eval_config(self) -> dict:
        return {
            "pass_threshold": get_env_float("PRACTICE_VOICE_PASS_THRESHOLD", "VOICE_PASS_THRESHOLD", default=0.88),
            "review_threshold": get_env_float("PRACTICE_VOICE_REVIEW_THRESHOLD", "VOICE_REVIEW_THRESHOLD", default=0.78),
            "min_asr_confidence": get_env_float("PRACTICE_VOICE_MIN_ASR_CONFIDENCE", "VOICE_MIN_ASR_CONFIDENCE", default=0.60),
            "max_attempts": get_env_int("PRACTICE_VOICE_MAX_ATTEMPTS", "VOICE_MAX_ATTEMPTS", default=3),
            "max_duration_sec": get_env_int("PRACTICE_VOICE_MAX_DURATION_SEC", "VOICE_MAX_DURATION_SEC", default=15),
            "allow_paraphrase": self.speech_allow_paraphrase,
        }

    def _select_speech_materials(self, combined_practice: list, max_items: int) -> list:
        selected = []
        seen = set()

        for item in combined_practice or []:
            if not isinstance(item, dict):
                continue

            cn = (item.get("cn") or "").strip()
            en = (item.get("en") or "").strip()
            py = (item.get("py") or "").strip()
            if not cn or not en:
                continue
            if len(cn) < 2 or len(en) < 3:
                continue

            key = (cn, en)
            if key in seen:
                continue

            seen.add(key)
            selected.append({"cn": cn, "py": py, "en": en})
            if len(selected) >= max_items:
                break

        return selected

    def _build_speech_quiz_prompt(self, lesson_id: int, course_id: int, speech_materials: list) -> str:
        speech_source = json.dumps(speech_materials, ensure_ascii=False)
        speech_eval_config = json.dumps(self._get_speech_eval_config(), ensure_ascii=False)

        return f"""
        你是一名中文教学题库设计专家。请根据给定课文句子素材，生成“语音作答题”。

        【题型定义】
        - 题型代码固定为: EN_TO_CN_SPEAK
        - 出题形式: 给出英文句子(original_text)，要求学习者口语说出中文
        - 这组题目用来替代原先句子层的中译英题，不要生成句子级 CN_TO_EN
        - 标准答案: 中文原句(standard_answers)

        【输入素材】
        {speech_source}

        【硬性规则】
        1. 只能使用输入素材中的中英对应句，不得新增教材外内容。
        2. 题目数量: {self.speech_quiz_min} 到 {self.speech_quiz_max} 道，优先输出 {self.speech_quiz_target} 道。
        3. original_text 必须是英文句子；standard_answers 必须是中文句子数组。
        4. 每道题都要带 metadata，结构如下:
           {{
             "answer_mode": "speech",
             "speech_eval_config": {speech_eval_config}
           }}
        5. 每道题都要带 1 条 context_examples，使用同一条中英句作为上下文。

        【输出格式】
        仅输出 JSON:
        {{
          "database_items": [
            {{
              "lesson_id": {lesson_id},
              "question_id": 0,
              "course_id": {course_id},
              "question_type": "EN_TO_CN_SPEAK",
              "original_text": "English sentence",
              "original_pinyin": "对应中文拼音",
              "standard_answers": ["中文原句"],
              "context_examples": [{{"cn":"中文","py":"拼音","en":"English"}}],
              "metadata": {{
                "answer_mode": "speech",
                "speech_eval_config": {speech_eval_config}
              }}
            }}
          ]
        }}
        """

    def _normalize_speech_quiz_item(self, item: dict, speech_eval_config: dict) -> dict:
        if not isinstance(item, dict):
            return {}

        original_text = (item.get("original_text") or "").strip()
        if not original_text:
            return {}

        raw_answers = item.get("standard_answers", [])
        if isinstance(raw_answers, str):
            raw_answers = [raw_answers]
        if not isinstance(raw_answers, list):
            raw_answers = []

        standard_answers = [str(ans).strip() for ans in raw_answers if str(ans).strip()]
        if not standard_answers:
            return {}

        context_examples = item.get("context_examples", [])
        if not isinstance(context_examples, list):
            context_examples = []

        metadata = item.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
        metadata["answer_mode"] = "speech"
        metadata["speech_eval_config"] = speech_eval_config

        return {
            "lesson_id": item.get("lesson_id"),
            "question_id": 0,
            "course_id": item.get("course_id"),
            "question_type": "EN_TO_CN_SPEAK",
            "original_text": original_text,
            "original_pinyin": (item.get("original_pinyin") or "").strip(),
            "standard_answers": standard_answers,
            "context_examples": context_examples[:1],
            "metadata": metadata,
        }

    def _build_speech_fallback_items(
        self,
        lesson_id: int,
        course_id: int,
        speech_materials: list,
        speech_eval_config: dict,
    ) -> list:
        fallback = []
        target = max(self.speech_quiz_min, min(self.speech_quiz_target, self.speech_quiz_max))

        for material in speech_materials:
            if len(fallback) >= target:
                break
            if not isinstance(material, dict):
                continue

            cn = (material.get("cn") or "").strip()
            en = (material.get("en") or "").strip()
            py = (material.get("py") or "").strip()
            if not cn or not en:
                continue

            fallback.append({
                "lesson_id": lesson_id,
                "question_id": 0,
                "course_id": course_id,
                "question_type": "EN_TO_CN_SPEAK",
                "original_text": en,
                "original_pinyin": py,
                "standard_answers": [cn],
                "context_examples": [{"cn": cn, "py": py, "en": en}],
                "metadata": {
                    "answer_mode": "speech",
                    "speech_eval_config": speech_eval_config,
                },
            })

        return fallback

    def run(self, lesson_id: int, course_id: int, file_path: str = None, file_obj=None, source_dialogues: list = None):
        # --- [Task 2.1a] 提取词汇基本信息 ---
        print(f"  ▶️ [Task 2.1a] 提取词汇基本信息 (骨架)...")
        v_base_res = self.llm.generate_structured_json(self._build_vocab_base_prompt(), file_path=file_path, file_obj=file_obj)
        raw_vocab = v_base_res.get("vocabulary", []) if isinstance(v_base_res, dict) else []
        
        new_vocab_base = []
        if isinstance(raw_vocab, list):
            for v in raw_vocab:
                if isinstance(v, dict):
                    word = v.get("word")
                    definition = v.get("definition")
                    # 校验一词多义
                    if word not in self.global_vocab or definition not in [e["definition"] for e in self.global_vocab[word]]:
                        new_vocab_base.append(v)
                    else:
                        print(f"  ⏭️ 跳过已掌握的词义: {word} ({definition})")
        
        if not new_vocab_base:
            print("  ⚠️ 本课无新生词义。")
        
        time.sleep(2)

        # --- [Task 2.1b] 提取官方例句 ---
        new_vocab = []
        if new_vocab_base:
            print(f"  ▶️ [Task 2.1b] 正在回填官方例句 (针对 {len(new_vocab_base)} 个新词义)...")
            new_vocab = self._fill_vocab_examples_in_batches(
                new_vocab_base,
                file_path=file_path,
                file_obj=file_obj,
                source_dialogues=source_dialogues
            )

        time.sleep(2)

        # --- [Task 2.2a/b] 提取素材 ---
        print(f"  ▶️ [Task 2.2a/b] 提取课文原文句与语法练习...")
        dialogue_sentences = self._extract_dialogue_sentence_fallback(source_dialogues)
        g_result = self.llm.generate_structured_json(self._build_grammar_extract_prompt(), file_path=file_path, file_obj=file_obj)
        grammar_exercises = g_result.get("grammar_practice", []) if isinstance(g_result, dict) and isinstance(g_result.get("grammar_practice"), list) else []

        combined_practice = self._dedupe_sentence_materials(dialogue_sentences + grammar_exercises)

        print(f"     📊 课文原文句提取: {len(dialogue_sentences)} 条")
        print(f"     📊 语法练习提取: {len(grammar_exercises)} 条")
        print(f"     📊 句子题素材池: {len(combined_practice)} 条")

        # 注入历史上下文
        vocab_with_history = self._inject_historical_context(new_vocab)
        time.sleep(1)

        # --- [Task 2.3 拆分生成 - 微批处理版] ---
        
        # 🚀 2.3a 单词翻译题 (分批生成)
        all_word_items = []
        batch_size = self.word_quiz_batch_size  
        vocab_lookup = {
            (v.get("word") or "").strip(): v
            for v in vocab_with_history
            if isinstance(v, dict) and (v.get("word") or "").strip()
        }
        
        if vocab_with_history:
            print(f"  ▶️ [Task 2.3a] 开始微批处理单词题 (共 {len(vocab_with_history)} 个词)...")
            for i in range(0, len(vocab_with_history), batch_size):
                batch = vocab_with_history[i : i + batch_size]
                current_batch_num = (i // batch_size) + 1
                print(f"     📦 正在生成第 {current_batch_num} 组单词题目...")
                
                word_q_prompt = self._build_word_quiz_prompt(lesson_id, course_id, batch)
                word_q_res = self.llm.generate_structured_json(word_q_prompt, file_path=None, file_obj=None)
                
                if word_q_res and isinstance(word_q_res, dict):
                    batch_items = word_q_res.get("database_items", [])
                    batch_items = [
                        self._normalize_word_quiz_item(batch_item, vocab_lookup)
                        for batch_item in batch_items
                    ]
                    all_word_items.extend(batch_items)
                
                time.sleep(2)

        # 🚀 2.3b 句子翻译题
        print(f"  ▶️ [Task 2.3b] 正在生成精选句子题库...")
        sent_q_prompt = self._build_sentence_quiz_prompt(lesson_id, course_id, combined_practice)
        sent_q_res = self.llm.generate_structured_json(sent_q_prompt, file_path=None, file_obj=None)
        sent_items = sent_q_res.get("database_items", []) if isinstance(sent_q_res, dict) else []

        # 🚀 2.3c 语音句子题，用来替代句子层 CN_TO_EN
        speech_items = []
        speech_eval_config = self._get_speech_eval_config()
        speech_materials = self._select_speech_materials(
            combined_practice,
            max_items=max(self.speech_quiz_max * 2, 10)
        )

        if speech_materials:
            print(f"  ▶️ [Task 2.3c] 正在生成语音句子题库...")
            speech_prompt = self._build_speech_quiz_prompt(lesson_id, course_id, speech_materials)
            speech_res = self.llm.generate_structured_json(speech_prompt, file_path=None, file_obj=None)
            raw_speech_items = speech_res.get("database_items", []) if isinstance(speech_res, dict) else []

            if isinstance(raw_speech_items, list):
                for raw_item in raw_speech_items:
                    normalized = self._normalize_speech_quiz_item(raw_item, speech_eval_config)
                    if normalized:
                        speech_items.append(normalized)

            seen_en = set()
            deduped_speech_items = []
            for item in speech_items:
                key = (item.get("original_text") or "").strip().lower()
                if not key or key in seen_en:
                    continue
                seen_en.add(key)
                deduped_speech_items.append(item)
            speech_items = deduped_speech_items[:self.speech_quiz_max]

            if len(speech_items) < self.speech_quiz_min:
                existing = {(i.get("original_text") or "").strip().lower() for i in speech_items}
                fallback_items = self._build_speech_fallback_items(
                    lesson_id=lesson_id,
                    course_id=course_id,
                    speech_materials=speech_materials,
                    speech_eval_config=speech_eval_config,
                )
                for fb in fallback_items:
                    key = (fb.get("original_text") or "").strip().lower()
                    if key and key not in existing:
                        speech_items.append(fb)
                        existing.add(key)
                    if len(speech_items) >= self.speech_quiz_min:
                        break

        print(f"     📊 语音题生成: {len(speech_items)} 条")

        # 🚀 【核心修改：按类型强制排序】
        # 1. 汇总所有题目
        all_raw_items = all_word_items + sent_items + speech_items
        
        # 2. 按照题型分类到两个桶里
        cn_to_en_pool = [i for i in all_raw_items if i.get("question_type") == "CN_TO_EN"]
        en_to_cn_pool = [i for i in all_raw_items if i.get("question_type") == "EN_TO_CN"]
        en_to_cn_speak_pool = [i for i in all_raw_items if i.get("question_type") == "EN_TO_CN_SPEAK"]
        
        # 3. 按照“先中译英，后英译中”重新组合
        sorted_items = cn_to_en_pool + en_to_cn_pool + en_to_cn_speak_pool

        # 🚀 【结果清理与重排 ID】
        valid_items = []
        for index, item in enumerate(sorted_items):
            if isinstance(item, dict) and item.get("original_text") and item.get("standard_answers"):
                item["question_id"] = index + 1  # 重新分配连续的递增 ID
                valid_items.append(item)

        # 🚀 持久化更新
        if new_vocab:
            self.save_memory(new_vocab, lesson_id)
            print(f"  ✅ Task 2 完整结束，已将新词义及例句存入词典。")

        return {
            "vocabulary": new_vocab,
            "database_items": valid_items,
            "grammar_practice": combined_practice
        }
