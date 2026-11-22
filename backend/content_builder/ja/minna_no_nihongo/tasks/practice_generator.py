from __future__ import annotations

import json


class MinnaNoNihongoPracticeGenerator:
    """Generate Japanese practice items in a Chinese Task2-style pipeline."""

    VISIBLE_CONJUGATION_FROM_LESSON = 14
    MAX_VISIBLE_CONJUGATION_ITEMS = 4
    WORD_BATCH_SIZE = 8
    SENTENCE_TARGET = 8
    SPEECH_MIN = 3
    SPEECH_MAX = 5
    LISTEN_WRITE_MIN = 3
    LISTEN_WRITE_MAX = 5
    ALLOWED_TYPES = {
        "JA_TO_CN",
        "CN_TO_JA",
        "JA_LISTEN_WRITE",
        "JA_SPEAK",
        "PARTICLE_FILL",
        "PATTERN_DRILL",
        "CONJUGATION",
    }
    TYPE_ALIASES = {
        "JA_TO_SUPPORT": "JA_TO_CN",
        "SUPPORT_TO_JA": "CN_TO_JA",
        "TARGET_TO_SUPPORT": "JA_TO_CN",
        "SUPPORT_TO_TARGET": "CN_TO_JA",
        "TARGET_LISTEN_WRITE": "JA_LISTEN_WRITE",
        "TARGET_SPEAK": "JA_SPEAK",
    }
    NON_QUIZ_TERMS = {
        "は",
        "が",
        "を",
        "に",
        "で",
        "へ",
        "と",
        "も",
        "の",
        "か",
        "ね",
        "よ",
        "です",
        "ます",
        "さん",
    }
    NON_QUIZ_POS_HINTS = {"助詞", "助動詞", "particle", "auxiliary"}
    PROPER_NOUN_CATEGORIES = {
        "person_name",
        "family_name",
        "given_name",
        "company_name",
        "organization_name",
        "school_name",
        "university_name",
        "hospital_name",
        "place_name",
        "brand_name",
        "fictional_name",
        "proper_noun",
    }
    PROPER_NOUN_POS_HINTS = {"固有名詞", "proper noun", "proper_noun", "name"}

    def normalize_practice_items(
        self,
        items: list[dict],
        sentence_patterns: list[dict],
        dialogue: dict,
        lesson_id: int | None = None,
    ) -> list[dict]:
        normalized = []
        visible_conjugation_count = 0
        for item in items or []:
            if not isinstance(item, dict):
                continue
            question_type = self._canonical_question_type(item.get("question_type"))
            if question_type == "CONJUGATION":
                if not self.visible_conjugation_allowed(lesson_id):
                    continue
                if visible_conjugation_count >= self.MAX_VISIBLE_CONJUGATION_ITEMS:
                    continue
                visible_conjugation_count += 1
            prompt = self._text_value(item.get("prompt") or item.get("original_text"))
            answers = self._normalize_answers(item.get("standard_answers"))
            if not prompt and not answers:
                continue
            metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
            if question_type == "CONJUGATION":
                metadata = self._ensure_skill_tag(metadata, "conjugation")
            normalized.append({
                "question_id": len(normalized) + 1,
                "question_type": question_type,
                "prompt": prompt,
                "standard_answers": answers,
                "context": item.get("context") if isinstance(item.get("context"), dict) else {},
                **({"metadata": metadata} if metadata else {}),
            })

        if normalized:
            return normalized

        question_id = 1
        for pattern in sentence_patterns[:4]:
            text = pattern.get("text", "")
            translation = pattern.get("translation", "")
            if text and translation:
                normalized.append({
                    "question_id": question_id,
                    "question_type": "JA_TO_CN",
                    "prompt": text,
                    "standard_answers": [translation],
                    "context": {"pattern_id": pattern.get("pattern_id")},
                })
                question_id += 1

        for line in (dialogue.get("lines") or [])[:4]:
            text = line.get("text", "")
            translation = (line.get("translation") or "").strip()
            if text:
                normalized.append({
                    "question_id": question_id,
                    "question_type": "JA_SPEAK",
                    "prompt": translation or f"请朗读：{text}",
                    "standard_answers": [text],
                    "context": {"line_ref": line.get("line_ref")},
                    "metadata": {"answer_mode": "speech", "speech_language": "ja"},
                })
                question_id += 1
        return normalized

    def build_database_items(self, lesson_data: dict, llm_provider=None) -> list[dict]:
        metadata = lesson_data.get("lesson_metadata", {}) if isinstance(lesson_data.get("lesson_metadata"), dict) else {}
        content = lesson_data.get("course_content", {}) if isinstance(lesson_data.get("course_content"), dict) else {}
        lesson_id = metadata.get("lesson_id", "")
        course_id = metadata.get("course_id", "")

        vocabulary = content.get("vocabulary", []) if isinstance(content.get("vocabulary"), list) else []
        materials = self._collect_sentence_materials(content)
        grammar_materials = [
            item for item in materials
            if item["source_section"] in {"sentence_patterns", "example_sentences", "grammar_sections"}
        ]
        speech_materials = self._select_sentence_materials(materials, max_items=max(self.SPEECH_MAX * 2, 10))
        listen_write_materials = [
            item for item in self._select_sentence_materials(materials, max_items=max(self.LISTEN_WRITE_MAX * 2, 10))
            if item.get("audio_id")
        ]

        print(f"  ▶️ [MNN Task 7.1] 词汇题素材: {len(vocabulary)} 条。")
        word_items = self._build_word_database_items(
            vocabulary=vocabulary,
            lesson_id=lesson_id,
            course_id=course_id,
            llm_provider=llm_provider,
        )

        print(f"  ▶️ [MNN Task 7.2] 句子表达素材: {len(grammar_materials)} 条。")
        sentence_items = self._build_sentence_database_items(
            materials=grammar_materials,
            lesson_id=lesson_id,
            course_id=course_id,
            llm_provider=llm_provider,
        )

        print(f"  ▶️ [MNN Task 7.3] 口语素材: {len(speech_materials)} 条。")
        speech_items = self._build_speech_database_items(
            materials=speech_materials,
            lesson_id=lesson_id,
            course_id=course_id,
            llm_provider=llm_provider,
        )

        print(f"  ▶️ [MNN Task 7.4] 听写素材: {len(listen_write_materials)} 条。")
        listen_write_items = self._build_listen_write_database_items(
            materials=listen_write_materials,
            lesson_id=lesson_id,
            course_id=course_id,
            llm_provider=llm_provider,
        )

        print("  ▶️ [MNN Task 7.5] 日语活用专项题。")
        conjugation_items = self._build_conjugation_database_items(
            lesson_data=lesson_data,
            lesson_id=lesson_id,
            course_id=course_id,
            llm_provider=llm_provider,
        )

        explicit_items = self._database_items_from_practice(
            lesson_data.get("practice_items", []),
            lesson_id=lesson_id,
            course_id=course_id,
        )

        return self._dedupe_and_sort_database_items(
            word_items + sentence_items + speech_items + listen_write_items + conjugation_items + explicit_items,
            lesson_id=lesson_id,
            course_id=course_id,
        )

    def _build_word_database_items(
        self,
        *,
        vocabulary: list[dict],
        lesson_id,
        course_id,
        llm_provider,
    ) -> list[dict]:
        quizable_vocab = [
            vocab for vocab in vocabulary or []
            if isinstance(vocab, dict) and self._is_quizable_vocab(vocab)
        ]
        if not quizable_vocab:
            return []

        fallback_items = self._fallback_word_items(quizable_vocab, lesson_id, course_id)
        if llm_provider is None:
            self._print_generation_stats("Task 7.1", len(quizable_vocab), [], fallback_items, fallback_items)
            return fallback_items

        generated = []
        vocab_by_term = {
            (item.get("term") or item.get("word") or "").strip(): item
            for item in quizable_vocab
            if (item.get("term") or item.get("word") or "").strip()
        }
        for batch in self._chunks(quizable_vocab, self.WORD_BATCH_SIZE):
            result = self._call_llm(llm_provider, self._build_word_quiz_prompt(lesson_id, course_id, batch))
            raw_items = result.get("database_items") if isinstance(result, dict) else []
            for raw_item in raw_items if isinstance(raw_items, list) else []:
                normalized = self._normalize_database_item(raw_item, lesson_id, course_id)
                if not normalized:
                    continue
                if self._word_item_matches_vocab(normalized, vocab_by_term):
                    generated.append(normalized)

        merged = self._merge_with_fallback(generated, fallback_items)
        self._print_generation_stats("Task 7.1", len(quizable_vocab), generated, fallback_items, merged)
        return merged

    def _build_sentence_database_items(
        self,
        *,
        materials: list[dict],
        lesson_id,
        course_id,
        llm_provider,
    ) -> list[dict]:
        materials = materials[:12]
        if not materials:
            return []
        fallback_items = self._fallback_sentence_items(materials, lesson_id, course_id)
        if llm_provider is None:
            self._print_generation_stats("Task 7.2", len(materials), [], fallback_items, fallback_items)
            return fallback_items

        result = self._call_llm(llm_provider, self._build_sentence_quiz_prompt(lesson_id, course_id, materials))
        raw_items = result.get("database_items") if isinstance(result, dict) else []
        generated = [
            item for item in (
                self._normalize_database_item(raw_item, lesson_id, course_id)
                for raw_item in (raw_items if isinstance(raw_items, list) else [])
            )
            if item and item.get("question_type") in {"JA_TO_CN", "CN_TO_JA"}
        ]
        merged = self._merge_with_fallback(generated, fallback_items)
        self._print_generation_stats("Task 7.2", len(materials), generated, fallback_items, merged)
        return merged

    def _build_speech_database_items(
        self,
        *,
        materials: list[dict],
        lesson_id,
        course_id,
        llm_provider,
    ) -> list[dict]:
        materials = materials[:10]
        if not materials:
            return []
        fallback_items = self._fallback_speech_items(materials, lesson_id, course_id)
        if llm_provider is None:
            self._print_generation_stats("Task 7.3", len(materials), [], fallback_items, fallback_items[: self.SPEECH_MAX])
            return fallback_items

        result = self._call_llm(llm_provider, self._build_speech_quiz_prompt(lesson_id, course_id, materials))
        raw_items = result.get("database_items") if isinstance(result, dict) else []
        generated = [
            item for item in (
                self._normalize_database_item(raw_item, lesson_id, course_id)
                for raw_item in (raw_items if isinstance(raw_items, list) else [])
            )
            if item and item.get("question_type") == "JA_SPEAK"
        ][: self.SPEECH_MAX]
        merged = self._merge_with_fallback(generated, fallback_items)[: self.SPEECH_MAX]
        self._print_generation_stats("Task 7.3", len(materials), generated, fallback_items, merged)
        return merged

    def _build_listen_write_database_items(
        self,
        *,
        materials: list[dict],
        lesson_id,
        course_id,
        llm_provider,
    ) -> list[dict]:
        materials = materials[:10]
        if not materials:
            return []
        fallback_items = self._fallback_listen_write_items(materials, lesson_id, course_id)
        if llm_provider is None:
            self._print_generation_stats("Task 7.4", len(materials), [], fallback_items, fallback_items[: self.LISTEN_WRITE_MAX])
            return fallback_items

        result = self._call_llm(llm_provider, self._build_listen_write_prompt(lesson_id, course_id, materials))
        raw_items = result.get("database_items") if isinstance(result, dict) else []
        generated = []
        for raw_item in raw_items if isinstance(raw_items, list) else []:
            normalized = self._normalize_database_item(raw_item, lesson_id, course_id)
            if not normalized or normalized.get("question_type") != "JA_LISTEN_WRITE":
                continue
            answer = (normalized.get("standard_answers") or [""])[0]
            material = self._find_material_by_text(materials, answer)
            if material:
                normalized["metadata"] = self._metadata_with_material(
                    normalized.get("metadata", {}),
                    material,
                    answer_mode="text",
                )
                generated.append(normalized)
        merged = self._merge_with_fallback(generated, fallback_items)[: self.LISTEN_WRITE_MAX]
        self._print_generation_stats("Task 7.4", len(materials), generated, fallback_items, merged)
        return merged

    def _build_conjugation_database_items(self, *, lesson_data: dict, lesson_id, course_id, llm_provider) -> list[dict]:
        if not self.visible_conjugation_allowed(lesson_id) or llm_provider is None:
            return []
        content = lesson_data.get("course_content", {}) if isinstance(lesson_data.get("course_content"), dict) else {}
        grammar_sections = content.get("grammar_sections") if isinstance(content.get("grammar_sections"), list) else []
        prompt = self._build_conjugation_prompt(lesson_id, course_id, grammar_sections)
        result = self._call_llm(llm_provider, prompt)
        raw_items = result.get("database_items") if isinstance(result, dict) else []
        generated = []
        for raw_item in raw_items if isinstance(raw_items, list) else []:
            normalized = self._normalize_database_item(raw_item, lesson_id, course_id)
            if not normalized or normalized.get("question_type") != "CONJUGATION":
                continue
            normalized["metadata"] = self._ensure_skill_tag(normalized.get("metadata", {}), "conjugation")
            generated.append(normalized)
            if len(generated) >= self.MAX_VISIBLE_CONJUGATION_ITEMS:
                break
        print(f"     📊 Task 7.5 generated={len(generated)} fallback_added=0 final={len(generated)}")
        return generated

    def _fallback_word_items(self, vocabulary: list[dict], lesson_id, course_id) -> list[dict]:
        items = []
        for vocab in vocabulary:
            term = (vocab.get("term") or vocab.get("word") or "").strip()
            translation = (vocab.get("translation") or vocab.get("definition") or "").strip()
            if not term or not translation:
                continue
            reading = (vocab.get("reading") or "").strip()
            knowledge = self._knowledge_payload(vocab)
            context_examples = self._context_examples_for_vocab(vocab)
            base_metadata = {
                "knowledge": knowledge,
                "context": {
                    "source": "vocabulary",
                    "lesson_section": vocab.get("lesson_section", ""),
                    "memory_status": vocab.get("memory_status", "new"),
                },
            }
            items.append({
                "lesson_id": lesson_id,
                "course_id": course_id,
                "question_id": 0,
                "question_type": "JA_TO_CN",
                "original_text": term,
                "original_pinyin": reading,
                "standard_answers": [translation],
                "context_examples": context_examples,
                "metadata": base_metadata | {"audio_language": "ja", "speech_language": "zh"},
            })
            items.append({
                "lesson_id": lesson_id,
                "course_id": course_id,
                "question_id": 0,
                "question_type": "CN_TO_JA",
                "original_text": translation,
                "original_pinyin": "",
                "standard_answers": [term],
                "context_examples": context_examples,
                "metadata": base_metadata | {"audio_language": "zh", "speech_language": "ja"},
            })
        return items

    def _fallback_sentence_items(self, materials: list[dict], lesson_id, course_id) -> list[dict]:
        items = []
        for material in materials[: self.SENTENCE_TARGET]:
            items.append({
                "lesson_id": lesson_id,
                "course_id": course_id,
                "question_id": 0,
                "question_type": "CN_TO_JA",
                "original_text": material["translation"],
                "original_pinyin": "",
                "standard_answers": [material["text"]],
                "context_examples": [self._context_example_from_material(material)],
                "metadata": self._metadata_with_material(
                    {"skill_tags": material.get("skill_tags", [])},
                    material,
                    answer_mode="text",
                ),
            })
        for material in materials[: max(2, self.SENTENCE_TARGET // 3)]:
            items.append({
                "lesson_id": lesson_id,
                "course_id": course_id,
                "question_id": 0,
                "question_type": "JA_TO_CN",
                "original_text": material["text"],
                "original_pinyin": material.get("reading", ""),
                "standard_answers": [material["translation"]],
                "context_examples": [self._context_example_from_material(material)],
                "metadata": self._metadata_with_material(
                    {"skill_tags": material.get("skill_tags", [])},
                    material,
                    answer_mode="text",
                ),
            })
        return items

    def _fallback_speech_items(self, materials: list[dict], lesson_id, course_id) -> list[dict]:
        items = []
        for material in materials[: self.SPEECH_MAX]:
            items.append({
                "lesson_id": lesson_id,
                "course_id": course_id,
                "question_id": 0,
                "question_type": "JA_SPEAK",
                "original_text": material["translation"],
                "original_pinyin": "",
                "standard_answers": [material["text"]],
                "context_examples": [self._context_example_from_material(material)],
                "metadata": self._metadata_with_material(
                    {
                        "answer_mode": "speech",
                        "speech_language": "ja",
                        "skill_tags": material.get("skill_tags", []),
                    },
                    material,
                    answer_mode="speech",
                ),
            })
        return items

    def _fallback_listen_write_items(self, materials: list[dict], lesson_id, course_id) -> list[dict]:
        items = []
        for material in materials[: self.LISTEN_WRITE_MAX]:
            items.append({
                "lesson_id": lesson_id,
                "course_id": course_id,
                "question_id": 0,
                "question_type": "JA_LISTEN_WRITE",
                "original_text": material["translation"],
                "original_pinyin": material.get("reading", ""),
                "standard_answers": [material["text"]],
                "context_examples": [self._context_example_from_material(material)],
                "metadata": self._metadata_with_material(
                    {
                        "answer_mode": "text",
                        "audio_language": "ja",
                        "skill_tags": material.get("skill_tags", []),
                    },
                    material,
                    answer_mode="text",
                ),
            })
        return items

    def _build_word_quiz_prompt(self, lesson_id, course_id, vocabulary: list[dict]) -> str:
        payload = json.dumps(self._word_prompt_payload(vocabulary), ensure_ascii=False, indent=2)
        return f"""
        你是一名严谨的日语词汇练习编写专家。请为提供的【本课新词】生成全量词汇翻译练习。

        lesson_id: {lesson_id}
        course_id: {course_id}

        【素材清单】
        {payload}

        【硬性规则】
        1. 必须为每一个词生成两道题：
           - JA_TO_CN：日语词面 -> 中文释义。
           - CN_TO_JA：中文释义 -> 日语词面。
        2. 这些词已经过滤掉复现词和不适合独立考查的助词/功能词。
        3. context_examples 只能来自 example_sentence 或 historical_examples，不要编造。
        4. 如果有 historical_usages，只能用于辨析旧义项，当前答案必须优先采用本课词义。
        5. 只输出 JSON，不要 Markdown。

        输出结构：
        {{
          "database_items": [
            {{
              "lesson_id": {lesson_id},
              "course_id": {json.dumps(course_id, ensure_ascii=False)},
              "question_id": 0,
              "question_type": "JA_TO_CN 或 CN_TO_JA",
              "original_text": "题面",
              "original_pinyin": "日语题面的假名读音；中文题面留空",
              "standard_answers": ["标准答案"],
              "context_examples": [
                {{"text": "日语例句", "reading": "假名", "translation": "中文"}}
              ],
              "metadata": {{"context": {{"source": "vocabulary"}}}}
            }}
          ]
        }}
        """

    def _build_sentence_quiz_prompt(self, lesson_id, course_id, materials: list[dict]) -> str:
        payload = json.dumps(materials, ensure_ascii=False, indent=2)
        return f"""
        你是一名日语表达练习设计专家。请根据【文型 / 例文 / 语法例句】生成句子级练习。

        lesson_id: {lesson_id}
        course_id: {course_id}

        【素材清单】
        {payload}

        【题型定位】
        - CN_TO_JA：核心表达题，给中文意思，让学习者从头组织日语句子。
        - JA_TO_CN：少量理解题，检查学习者能否理解本课句型。

        【硬性规则】
        1. 生成 6-8 道 CN_TO_JA，2-3 道 JA_TO_CN。
        2. 题目必须 100% 来源于素材，可以轻微简化但不能引入新语法。
        3. 不要生成 PARTICLE_FILL 或 PATTERN_DRILL；这些只做讲解页即时检查。
        4. 每道题 metadata.skill_tags 尽量保留素材中的 skill_tags。
        5. 只输出 JSON，不要 Markdown。

        输出结构：
        {{
          "database_items": [
            {{
              "lesson_id": {lesson_id},
              "course_id": {json.dumps(course_id, ensure_ascii=False)},
              "question_id": 0,
              "question_type": "CN_TO_JA 或 JA_TO_CN",
              "original_text": "题面",
              "original_pinyin": "日语题面的假名读音；中文题面留空",
              "standard_answers": ["标准答案"],
              "context_examples": [],
              "metadata": {{"skill_tags": [], "context": {{"source_section": "sentence_patterns", "source_ref": 1}}}}
            }}
          ]
        }}
        """

    def _build_speech_quiz_prompt(self, lesson_id, course_id, materials: list[dict]) -> str:
        payload = json.dumps(materials, ensure_ascii=False, indent=2)
        return f"""
        你是一名日语口语练习设计专家。请根据课文句子素材生成 JA_SPEAK 题。

        【题型定义】
        - question_type 固定为 JA_SPEAK。
        - original_text 使用中文意思提示。
        - standard_answers 使用日语原句。
        - metadata.answer_mode 固定为 speech，speech_language 固定为 ja。

        lesson_id: {lesson_id}
        course_id: {course_id}

        【素材清单】
        {payload}

        【硬性规则】
        1. 生成 3-5 道，优先选择会話和例文中的自然短句。
        2. 不要让用户只跟读日语原文；题面要促使用户用日语表达。
        3. 不得引入素材外句子。
        4. 只输出 JSON，不要 Markdown。

        输出结构：
        {{
          "database_items": [
            {{
              "lesson_id": {lesson_id},
              "course_id": {json.dumps(course_id, ensure_ascii=False)},
              "question_id": 0,
              "question_type": "JA_SPEAK",
              "original_text": "中文意思提示",
              "original_pinyin": "",
              "standard_answers": ["日语答案"],
              "context_examples": [],
              "metadata": {{"answer_mode": "speech", "speech_language": "ja", "skill_tags": []}}
            }}
          ]
        }}
        """

    def _build_listen_write_prompt(self, lesson_id, course_id, materials: list[dict]) -> str:
        payload = json.dumps(materials, ensure_ascii=False, indent=2)
        return f"""
        你是一名日语听写练习设计专家。请根据已有课文音频素材生成 JA_LISTEN_WRITE 题。

        【题型定义】
        - question_type 固定为 JA_LISTEN_WRITE。
        - 学习者听日语音频，然后写出听到的日语句子。
        - original_text 填中文意思提示；standard_answers 填日语原句。
        - metadata.audio_id / source_section / source_ref 必须来自素材。

        lesson_id: {lesson_id}
        course_id: {course_id}

        【素材清单】
        {payload}

        【硬性规则】
        1. 生成 3-5 道，优先选择短句、会話句、例文句。
        2. 不得选择没有 audio_id 的素材。
        3. 不得引入素材外句子。
        4. 只输出 JSON，不要 Markdown。

        输出结构：
        {{
          "database_items": [
            {{
              "lesson_id": {lesson_id},
              "course_id": {json.dumps(course_id, ensure_ascii=False)},
              "question_id": 0,
              "question_type": "JA_LISTEN_WRITE",
              "original_text": "中文意思提示",
              "original_pinyin": "假名读音",
              "standard_answers": ["日语原句"],
              "context_examples": [],
              "metadata": {{"answer_mode": "text", "audio_id": "dialogue_001", "source_section": "dialogue", "source_ref": 1}}
            }}
          ]
        }}
        """

    def _build_conjugation_prompt(self, lesson_id, course_id, grammar_sections: list[dict]) -> str:
        payload = json.dumps(grammar_sections, ensure_ascii=False, indent=2)
        return f"""
        你是一名日语活用练习设计专家。请只在本课明确涉及动词/形容词活用时，生成少量 CONJUGATION 题。

        lesson_id: {lesson_id}
        course_id: {course_id}

        【语法素材】
        {payload}

        【硬性规则】
        1. 第 14 课以后才允许本题型；当前 lesson_id 已通过代码门槛。
        2. 最多生成 4 道。
        3. 只考本课明确出现的活用，例如 て形、ない形、辞書形、た形、普通形。
        4. 如果本课没有明确活用，请返回空数组。
        5. 只输出 JSON，不要 Markdown。

        输出结构：
        {{
          "database_items": [
            {{
              "lesson_id": {lesson_id},
              "course_id": {json.dumps(course_id, ensure_ascii=False)},
              "question_id": 0,
              "question_type": "CONJUGATION",
              "original_text": "飲みます -> て形",
              "original_pinyin": "",
              "standard_answers": ["飲んで"],
              "context_examples": [],
              "metadata": {{"skill_tags": ["conjugation:te_form"]}}
            }}
          ]
        }}
        """

    def _collect_sentence_materials(self, content: dict) -> list[dict]:
        materials = []
        for index, item in enumerate(content.get("sentence_patterns") or [], start=1):
            material = self._line_to_material(item, "sentence_patterns", item.get("pattern_id") or index, f"pattern_{index:03d}")
            if material:
                materials.append(material)
        for index, item in enumerate(content.get("example_sentences") or [], start=1):
            material = self._line_to_material(item, "example_sentences", item.get("line_ref") or index, f"example_{index:03d}")
            if material:
                materials.append(material)
        dialogue = content.get("dialogue") if isinstance(content.get("dialogue"), dict) else {}
        for index, item in enumerate(dialogue.get("lines") or [], start=1):
            material = self._line_to_material(item, "dialogue", item.get("line_ref") or index, f"dialogue_{index:03d}")
            if material:
                materials.append(material)
        for section_index, section in enumerate(content.get("grammar_sections") or [], start=1):
            if not isinstance(section, dict):
                continue
            for example_index, example in enumerate(section.get("examples") or [], start=1):
                material = self._line_to_material(
                    example,
                    "grammar_sections",
                    example.get("source_ref") or f"{section_index}.{example_index}",
                    "",
                    extra_tags=[self._skill_tag("pattern", section.get("title", ""))],
                )
                if material:
                    material["grammar_title"] = section.get("title", "")
                    materials.append(material)
        return self._dedupe_materials(materials)

    def _line_to_material(
        self,
        item: dict,
        source_section: str,
        source_ref,
        audio_id: str,
        extra_tags: list[str] | None = None,
    ) -> dict:
        if not isinstance(item, dict):
            return {}
        text = (item.get("text") or item.get("ja") or "").strip()
        translation = (item.get("translation") or item.get("definition") or "").strip()
        if not text or not translation:
            return {}
        skill_tags = []
        for focus in item.get("grammar_focus", []) if isinstance(item.get("grammar_focus"), list) else []:
            tag = self._skill_tag("pattern", str(focus))
            if tag:
                skill_tags.append(tag)
        for tag in extra_tags or []:
            if tag:
                skill_tags.append(tag)
        return {
            "text": text,
            "reading": (item.get("reading") or "").strip(),
            "romaji": (item.get("romaji") or "").strip(),
            "translation": translation,
            "source_section": source_section,
            "source_ref": source_ref,
            "audio_id": audio_id,
            "skill_tags": self._unique(skill_tags),
        }

    def _select_sentence_materials(self, materials: list[dict], max_items: int) -> list[dict]:
        selected = []
        for material in materials:
            text = material.get("text", "")
            translation = material.get("translation", "")
            if len(text) < 3 or len(translation) < 2:
                continue
            selected.append(material)
            if len(selected) >= max_items:
                break
        return selected

    def _dedupe_materials(self, materials: list[dict]) -> list[dict]:
        deduped = []
        seen = set()
        for material in materials:
            key = (material.get("text", ""), material.get("translation", ""))
            if not key[0] or key in seen:
                continue
            seen.add(key)
            deduped.append(material)
        return deduped

    def _normalize_database_item(self, item: dict, lesson_id, course_id) -> dict:
        if not isinstance(item, dict):
            return {}
        question_type = self._canonical_question_type(item.get("question_type"))
        if question_type not in self.ALLOWED_TYPES:
            return {}
        original_text = self._text_value(item.get("original_text") or item.get("prompt"))
        answers = self._normalize_answers(item.get("standard_answers"))
        if not original_text or not answers:
            return {}
        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        context_examples = item.get("context_examples") if isinstance(item.get("context_examples"), list) else []
        return {
            "lesson_id": item.get("lesson_id") or lesson_id,
            "course_id": item.get("course_id") or course_id,
            "question_id": 0,
            "question_type": question_type,
            "original_text": original_text,
            "original_pinyin": (item.get("original_pinyin") or "").strip(),
            "standard_answers": answers,
            "context_examples": [example for example in context_examples if isinstance(example, dict)][:2],
            "metadata": metadata,
        }

    def _database_items_from_practice(self, practice_items: list, lesson_id, course_id) -> list[dict]:
        database_items = []
        for item in practice_items or []:
            if not isinstance(item, dict):
                continue
            normalized = self._normalize_database_item(
                {
                    "lesson_id": lesson_id,
                    "course_id": course_id,
                    "question_type": item.get("question_type"),
                    "original_text": item.get("prompt") or item.get("original_text"),
                    "original_pinyin": item.get("original_pinyin", ""),
                    "standard_answers": item.get("standard_answers", []),
                    "metadata": item.get("metadata", {}) | {"context": item.get("context", {})},
                    "context_examples": item.get("context_examples", []),
                },
                lesson_id,
                course_id,
            )
            if normalized:
                database_items.append(normalized)
        return database_items

    def _dedupe_and_sort_database_items(self, items: list[dict], lesson_id, course_id) -> list[dict]:
        seen = set()
        deduped = []
        for item in items:
            if not isinstance(item, dict):
                continue
            question_type = self._canonical_question_type(item.get("question_type"))
            if question_type == "CONJUGATION" and not self.visible_conjugation_allowed(lesson_id):
                continue
            key = (
                question_type,
                (item.get("original_text") or "").strip(),
                tuple(item.get("standard_answers") or []),
            )
            if not key[1] or not key[2] or key in seen:
                continue
            seen.add(key)
            item["question_type"] = question_type
            item["lesson_id"] = item.get("lesson_id") or lesson_id
            item["course_id"] = item.get("course_id") or course_id
            deduped.append(item)

        order = {
            "CN_TO_JA": 1,
            "CONJUGATION": 2,
            "JA_LISTEN_WRITE": 3,
            "JA_TO_CN": 4,
            "JA_SPEAK": 5,
            "PATTERN_DRILL": 6,
            "PARTICLE_FILL": 7,
        }
        deduped.sort(key=lambda item: order.get(item.get("question_type"), 99))
        for index, item in enumerate(deduped, start=1):
            item["question_id"] = index
        return deduped

    def visible_conjugation_allowed(self, lesson_id: int | None) -> bool:
        try:
            return int(lesson_id) >= self.VISIBLE_CONJUGATION_FROM_LESSON
        except (TypeError, ValueError):
            return False

    def _canonical_question_type(self, question_type: str | None) -> str:
        normalized = (question_type or "JA_TO_CN").strip()
        normalized = self.TYPE_ALIASES.get(normalized, normalized)
        return normalized if normalized in self.ALLOWED_TYPES else "JA_TO_CN"

    def _is_quizable_vocab(self, vocab: dict) -> bool:
        if vocab.get("is_new_vocabulary") is False:
            return False
        term = (vocab.get("term") or vocab.get("word") or "").strip()
        translation = (vocab.get("translation") or vocab.get("definition") or "").strip()
        if not term or not translation:
            return False
        if term in self.NON_QUIZ_TERMS:
            return False
        if self._is_proper_noun_vocab(vocab):
            return False
        part_of_speech = (vocab.get("part_of_speech") or "").strip().lower()
        return not any(hint.lower() in part_of_speech for hint in self.NON_QUIZ_POS_HINTS)

    def _is_proper_noun_vocab(self, vocab: dict) -> bool:
        category = (vocab.get("category") or vocab.get("type") or "").strip().lower()
        if category in self.PROPER_NOUN_CATEGORIES:
            return True
        lesson_section = (vocab.get("lesson_section") or "").strip().lower()
        if lesson_section in {"display_only", "reference", "proper_noun"}:
            return True
        part_of_speech = (vocab.get("part_of_speech") or "").strip().lower()
        if any(hint.lower() in part_of_speech for hint in self.PROPER_NOUN_POS_HINTS):
            return True
        memory_context = vocab.get("memory_context") if isinstance(vocab.get("memory_context"), dict) else {}
        memory_category = (memory_context.get("category") or "").strip().lower()
        return memory_category in self.PROPER_NOUN_CATEGORIES

    def _knowledge_payload(self, vocab: dict) -> dict:
        return {
            "word": vocab.get("term") or vocab.get("word") or "",
            "reading": vocab.get("reading", ""),
            "part_of_speech": vocab.get("part_of_speech", ""),
            "definition": vocab.get("translation") or vocab.get("definition") or "",
            "romaji": vocab.get("romaji", ""),
            "accent": vocab.get("accent", ""),
            "lesson_section": vocab.get("lesson_section", ""),
            "example_sentence": vocab.get("example_sentence", {}),
            "memory_status": vocab.get("memory_status", "new"),
            "historical_usages": vocab.get("historical_usages", []),
        }

    def _context_examples_for_vocab(self, vocab: dict) -> list[dict]:
        examples = []
        if isinstance(vocab.get("example_sentence"), dict) and vocab["example_sentence"].get("text"):
            examples.append(vocab["example_sentence"])
        historical_examples = vocab.get("historical_examples") if isinstance(vocab.get("historical_examples"), list) else []
        for example in historical_examples:
            if isinstance(example, dict) and example.get("text") and example not in examples:
                examples.append(example)
            if len(examples) >= 2:
                break
        return examples

    def _word_prompt_payload(self, vocabulary: list[dict]) -> list[dict]:
        payload = []
        for vocab in vocabulary:
            payload.append({
                "term": vocab.get("term") or vocab.get("word") or "",
                "reading": vocab.get("reading", ""),
                "romaji": vocab.get("romaji", ""),
                "part_of_speech": vocab.get("part_of_speech", ""),
                "translation": vocab.get("translation") or vocab.get("definition") or "",
                "example_sentence": vocab.get("example_sentence", {}),
                "historical_usages": vocab.get("historical_usages", []),
                "memory_status": vocab.get("memory_status", "new"),
            })
        return payload

    def _word_item_matches_vocab(self, item: dict, vocab_by_term: dict) -> bool:
        answers = item.get("standard_answers") or []
        answer = answers[0] if answers else ""
        original = item.get("original_text") or ""
        if item.get("question_type") == "JA_TO_CN":
            return original in vocab_by_term
        if item.get("question_type") == "CN_TO_JA":
            return answer in vocab_by_term
        return False

    def _merge_with_fallback(self, generated: list[dict], fallback: list[dict]) -> list[dict]:
        if not generated:
            return fallback
        seen = {
            (item.get("question_type"), item.get("original_text"), tuple(item.get("standard_answers") or []))
            for item in generated
        }
        merged = list(generated)
        for item in fallback:
            key = (item.get("question_type"), item.get("original_text"), tuple(item.get("standard_answers") or []))
            if key not in seen:
                merged.append(item)
        return merged

    def _print_generation_stats(
        self,
        label: str,
        source_count: int,
        generated: list[dict],
        fallback: list[dict],
        merged: list[dict],
    ) -> None:
        generated_count = len(generated or [])
        merged_count = len(merged or [])
        fallback_added = max(0, merged_count - generated_count)
        print(
            f"     📊 {label} source={source_count} "
            f"llm_generated={generated_count} "
            f"fallback_candidates={len(fallback or [])} "
            f"fallback_added={fallback_added} final={merged_count}"
        )

    def _call_llm(self, llm_provider, prompt: str) -> dict:
        try:
            result = llm_provider.generate_structured_json(prompt, file_path=None)
        except TypeError:
            result = llm_provider.generate_structured_json(prompt)
        return result if isinstance(result, dict) else {}

    def _find_material_by_text(self, materials: list[dict], text: str) -> dict:
        normalized = (text or "").strip()
        for material in materials:
            if material.get("text") == normalized:
                return material
        return {}

    def _context_example_from_material(self, material: dict) -> dict:
        return {
            "text": material.get("text", ""),
            "reading": material.get("reading", ""),
            "romaji": material.get("romaji", ""),
            "translation": material.get("translation", ""),
            "source_section": material.get("source_section", ""),
            "source_ref": material.get("source_ref"),
        }

    def _metadata_with_material(self, metadata: dict, material: dict, answer_mode: str) -> dict:
        normalized = dict(metadata) if isinstance(metadata, dict) else {}
        normalized["answer_mode"] = answer_mode
        normalized.setdefault("context", {})
        normalized["context"].update({
            "source_section": material.get("source_section", ""),
            "source_ref": material.get("source_ref"),
        })
        normalized["source_section"] = material.get("source_section", "")
        normalized["source_ref"] = material.get("source_ref")
        if material.get("audio_id"):
            normalized["audio_id"] = material["audio_id"]
        if material.get("skill_tags"):
            normalized["skill_tags"] = self._unique((normalized.get("skill_tags") or []) + material["skill_tags"])
        return normalized

    def _ensure_skill_tag(self, metadata: dict, tag: str) -> dict:
        normalized = dict(metadata) if isinstance(metadata, dict) else {}
        skill_tags = normalized.get("skill_tags")
        if not isinstance(skill_tags, list):
            skill_tags = []
        if tag not in skill_tags:
            skill_tags.append(tag)
        normalized["skill_tags"] = skill_tags
        return normalized

    def _skill_tag(self, kind: str, value: str) -> str:
        normalized = " ".join((value or "").split())
        return f"{kind}:{normalized}" if normalized else ""

    def _normalize_answers(self, answers) -> list[str]:
        if isinstance(answers, str):
            answers = [answers]
        if not isinstance(answers, list):
            return []
        return [text for answer in answers if (text := self._text_value(answer))]

    def _text_value(self, value) -> str:
        if isinstance(value, str):
            return value.strip()
        if value is None:
            return ""
        if isinstance(value, dict):
            for key in (
                "text",
                "ja",
                "jp",
                "translation",
                "zh",
                "cn",
                "answer",
                "prompt",
                "original_text",
            ):
                text = self._text_value(value.get(key))
                if text:
                    return text
            return json.dumps(value, ensure_ascii=False, sort_keys=True)
        if isinstance(value, list):
            parts = [text for item in value if (text := self._text_value(item))]
            return " / ".join(parts)
        return str(value).strip()

    def _chunks(self, items: list, batch_size: int):
        for start in range(0, len(items), batch_size):
            yield items[start:start + batch_size]

    def _unique(self, items: list[str]) -> list[str]:
        result = []
        seen = set()
        for item in items or []:
            if not item or item in seen:
                continue
            seen.add(item)
            result.append(item)
        return result
