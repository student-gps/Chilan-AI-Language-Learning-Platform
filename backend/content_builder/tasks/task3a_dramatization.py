import json
from llm_providers import BaseLLMProvider


class Task3DramatizationGenerator:
    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm = llm_provider

    def _build_prompt(self, metadata: dict, dialogues: list, batch_mode: str) -> str:
        context = {
            "metadata": metadata,
            "dialogues": dialogues,
            "batch_mode": batch_mode,
        }
        content_str = json.dumps(context, ensure_ascii=False)

        if batch_mode == "foundation":
            batch_guidance = """
        【本轮生成目标】
        - 只生成课文前半段的情景演绎分镜。
        - 覆盖当前提供的课文句子，不要补写后半段内容。
        - 建议生成 2-4 个 scenes。
            """
        else:
            batch_guidance = """
        【本轮生成目标】
        - 只生成课文后半段的情景演绎分镜。
        - 覆盖当前提供的课文句子，不要重复前半段内容。
        - 建议生成 2-4 个 scenes。
            """

        return f"""
        你是一位中文教学短视频的剧情导演。你的任务不是讲解知识点，而是把课文内容转化成一段自然、连贯、适合后续视频生成模型制作的【情景演绎分镜脚本】。
        只输出合法 JSON，不要包含任何 Markdown。

        课文内容：
        {content_str}

        {batch_guidance}

        【任务目标】
        1. 把课文内容改编成 3-8 个情景分镜，完整覆盖课文主要内容。
        2. 重点表现人物、场景、动作、情绪和镜头感。
        3. 不要进入“老师讲解”模式，不要解释语法和词汇。
        4. 每个 scene 要尽量直接对应原课文里的句子或对话轮次。
        5. 画面提示词必须使用英文，适合后续 image-to-video 或 text-to-video 模型。

        【输出要求】
        1. 在 global_config 中给出统一视觉风格、场景摘要和角色设定。
        2. 在 scenes 中给出每一幕对应课文的哪几句、场景、角色、镜头、旁白和字幕设置。
        3. source_text 中必须同时提供 hanzi / pinyin / english 三种文本轨道；如果某项无法精确生成，也要尽量填写。
        4. subtitle_tracks 必须固定输出 default 和 optional 字段，default 默认填 "hanzi"。
        5. estimated_duration_seconds 只是建议时长，不需要强行压缩。
        6. voice_over 必须始终是一个对象，绝不能输出空字符串、null、数组或省略。
        7. 如果某个字段没有内容，也必须返回空字符串或空数组，不能改变字段类型。
        8. 你收到的每一条输入句子都绝对不能省略，每一句都必须至少出现在一个 scene 的 source_line_refs 中。
        9. 即使某一句只是回应、追问、过渡句，或者是复合句中的一部分，也必须保留，绝对不能因为镜头流畅或剧情压缩而跳过。
        10. 你可以把相邻句子合并进同一个 scene，但禁止遗漏任何一句；不要只保留“更精彩”的句子而省略中间句。
        11. 在输出前必须自检：所有 source_line_refs 的并集必须覆盖本轮输入中的全部句子编号；如果不能完整覆盖，则当前输出视为不合格。

        【输出结构】
        {{
          "global_config": {{
            "visual_style": "统一视觉风格",
            "setting_summary_cn": "中文场景摘要",
            "setting_summary_en": "brief setting summary in English",
            "character_definitions": [
              {{
                "name": "角色名",
                "appearance_description_en": "detailed appearance prompt in English"
              }}
            ]
          }},
          "scenes": [
            {{
              "scene_id": 1,
              "source_line_refs": [1, 2],
              "source_text": {{
                "hanzi": ["原课文句子1", "原课文句子2"],
                "pinyin": ["拼音1", "拼音2"],
                "english": ["English 1", "English 2"]
              }},
              "scene_goal": "这一幕的剧情目标",
              "scene_description_cn": "中文分镜描述",
              "setting_en": "English scene setting",
              "characters_on_screen": ["角色A", "角色B"],
              "camera_movement": "镜头运动",
              "shot_type": "镜头景别",
              "video_prompt_en": "detailed English prompt for video generation",
              "voice_over": {{
                "speaker": "说话人",
                "hanzi": "课文原句",
                "pinyin": "拼音",
                "english": "English subtitle"
              }},
              "subtitle_tracks": {{
                "default": "hanzi",
                "optional": ["pinyin", "english"]
              }},
              "estimated_duration_seconds": 8
            }}
          ]
        }}
        """

    def _request_batch(self, metadata: dict, dialogues: list, batch_mode: str) -> dict:
        prompt = self._build_prompt(metadata, dialogues, batch_mode)
        result = self.llm.generate_structured_json(
            prompt,
            file_path=None,
            file_obj=None
        )
        return result if isinstance(result, dict) else {
            "global_config": {},
            "scenes": []
        }

    def _build_single_line_recovery_prompt(self, metadata: dict, line_item: dict, last_scene: dict | None) -> str:
        context = {
            "metadata": metadata,
            "missing_line": line_item,
            "previous_scene_context": {
                "setting_en": (last_scene.get("setting_en") or "").strip() if isinstance(last_scene, dict) else "",
                "characters_on_screen": last_scene.get("characters_on_screen", []) if isinstance(last_scene, dict) and isinstance(last_scene.get("characters_on_screen"), list) else [],
                "camera_movement": (last_scene.get("camera_movement") or "").strip() if isinstance(last_scene, dict) else "",
                "shot_type": (last_scene.get("shot_type") or "").strip() if isinstance(last_scene, dict) else "",
                "video_prompt_en": (last_scene.get("video_prompt_en") or "").strip() if isinstance(last_scene, dict) else "",
            }
        }
        payload = json.dumps(context, ensure_ascii=False)

        return f"""
        你是一位中文教学短视频导演。现在只需要为一条缺失的课文台词补生成一个 scene。
        只输出合法 JSON，不要包含 Markdown。

        输入信息：
        {payload}

        【硬性要求】
        1. 只生成 1 个 scene。
        2. source_line_refs 必须只包含这一条缺失台词的 ref。
        3. source_text.hanzi / pinyin / english 必须与提供的 missing_line 完全一致，不要改写。
        4. voice_over 必须是对象，且内容与 missing_line 一致。
        5. 画面风格尽量与 previous_scene_context 保持一致。
        6. 不要额外编造别的台词或别的课文行。

        【输出结构】
        {{
          "scene": {{
            "scene_id": 1,
            "source_line_refs": [缺失行ref],
            "source_text": {{
              "hanzi": ["原句"],
              "pinyin": ["原拼音"],
              "english": ["原英文"]
            }},
            "scene_goal": "这一幕的剧情目标",
            "scene_description_cn": "中文分镜描述",
            "setting_en": "English scene setting",
            "characters_on_screen": ["角色A"],
            "camera_movement": "镜头运动",
            "shot_type": "镜头景别",
            "video_prompt_en": "detailed English prompt for video generation",
            "voice_over": {{
              "speaker": "说话人",
              "hanzi": "原句",
              "pinyin": "原拼音",
              "english": "原英文"
            }},
            "subtitle_tracks": {{
              "default": "hanzi",
              "optional": ["pinyin", "english"]
            }},
            "estimated_duration_seconds": 6
          }}
        }}
        """

    def _generate_single_line_scene(self, metadata: dict, line_item: dict, fallback_scene_id: int, last_scene: dict | None) -> dict | None:
        result = self.llm.generate_structured_json(
            self._build_single_line_recovery_prompt(metadata, line_item, last_scene),
            file_path=None,
            file_obj=None
        )
        if not isinstance(result, dict):
            return None
        raw_scene = result.get("scene")
        if not isinstance(raw_scene, dict):
            return None

        normalized_scene = self._normalize_scene(raw_scene, fallback_scene_id)
        expected_ref = line_item.get("ref")
        actual_refs = normalized_scene.get("source_line_refs", [])
        if actual_refs != [expected_ref]:
            return None
        if not normalized_scene.get("video_prompt_en"):
            return None
        if not (normalized_scene.get("voice_over") or {}).get("hanzi"):
            return None
        return normalized_scene

    def _normalize_voice_over(self, voice_over):
        if isinstance(voice_over, dict):
            return {
                "speaker": (voice_over.get("speaker") or "").strip(),
                "hanzi": (voice_over.get("hanzi") or "").strip(),
                "pinyin": (voice_over.get("pinyin") or "").strip(),
                "english": (voice_over.get("english") or "").strip(),
            }
        return {
            "speaker": "",
            "hanzi": "",
            "pinyin": "",
            "english": "",
        }

    def _normalize_scene(self, scene: dict, fallback_id: int, line_ref_offset: int = 0) -> dict:
        if not isinstance(scene, dict):
            scene = {}

        source_text = scene.get("source_text") if isinstance(scene.get("source_text"), dict) else {}
        subtitle_tracks = scene.get("subtitle_tracks") if isinstance(scene.get("subtitle_tracks"), dict) else {}
        raw_source_line_refs = scene.get("source_line_refs", []) if isinstance(scene.get("source_line_refs"), list) else []
        normalized_source_line_refs = []
        for ref in raw_source_line_refs:
            try:
                normalized_source_line_refs.append(int(ref) + line_ref_offset)
            except (TypeError, ValueError):
                continue

        return {
            "scene_id": scene.get("scene_id", fallback_id),
            "source_line_refs": normalized_source_line_refs,
            "source_text": {
                "hanzi": source_text.get("hanzi", []) if isinstance(source_text.get("hanzi"), list) else [],
                "pinyin": source_text.get("pinyin", []) if isinstance(source_text.get("pinyin"), list) else [],
                "english": source_text.get("english", []) if isinstance(source_text.get("english"), list) else [],
            },
            "scene_goal": (scene.get("scene_goal") or "").strip(),
            "scene_description_cn": (scene.get("scene_description_cn") or "").strip(),
            "setting_en": (scene.get("setting_en") or "").strip(),
            "characters_on_screen": scene.get("characters_on_screen", []) if isinstance(scene.get("characters_on_screen"), list) else [],
            "camera_movement": (scene.get("camera_movement") or "").strip(),
            "shot_type": (scene.get("shot_type") or "").strip(),
            "video_prompt_en": (scene.get("video_prompt_en") or "").strip(),
            "voice_over": self._normalize_voice_over(scene.get("voice_over")),
            "subtitle_tracks": {
                "default": (subtitle_tracks.get("default") or "hanzi").strip() or "hanzi",
                "optional": subtitle_tracks.get("optional", ["pinyin", "english"]) if isinstance(subtitle_tracks.get("optional"), list) else ["pinyin", "english"],
            },
            "estimated_duration_seconds": scene.get("estimated_duration_seconds", 8),
        }

    def _normalize_result(self, result: dict, line_ref_offset: int = 0) -> dict:
        if not isinstance(result, dict):
            result = {}

        global_config = result.get("global_config") if isinstance(result.get("global_config"), dict) else {}
        raw_scenes = result.get("scenes") if isinstance(result.get("scenes"), list) else []

        return {
            "global_config": {
                "visual_style": (global_config.get("visual_style") or "").strip(),
                "setting_summary_cn": (global_config.get("setting_summary_cn") or "").strip(),
                "setting_summary_en": (global_config.get("setting_summary_en") or "").strip(),
                "character_definitions": global_config.get("character_definitions", []) if isinstance(global_config.get("character_definitions"), list) else [],
            },
            "scenes": [
                self._normalize_scene(scene, index, line_ref_offset=line_ref_offset)
                for index, scene in enumerate(raw_scenes, start=1)
            ]
        }

    def _extract_input_lines_with_global_refs(self, dialogues: list, line_ref_offset: int) -> list:
        extracted = []
        if len(dialogues) == 1 and isinstance(dialogues[0], dict) and isinstance(dialogues[0].get("lines"), list):
            for local_index, line in enumerate(dialogues[0].get("lines", []), start=1):
                if not isinstance(line, dict):
                    continue
                words = line.get("words", []) if isinstance(line.get("words"), list) else []
                hanzi = "".join(
                    token.get("cn", "")
                    for token in words
                    if isinstance(token, dict)
                ).strip()
                pinyin = " ".join(
                    token.get("py", "").strip()
                    for token in words
                    if isinstance(token, dict) and token.get("py")
                ).strip()
                english = (line.get("english") or "").strip()
                extracted.append({
                    "ref": line_ref_offset + local_index,
                    "role": (line.get("role") or "").strip(),
                    "hanzi": hanzi,
                    "pinyin": pinyin,
                    "english": english,
                })
        return extracted

    def _build_fallback_scene(self, line_item: dict, fallback_scene_id: int, last_scene: dict | None) -> dict:
        role = (line_item.get("role") or "角色").strip() or "角色"
        hanzi = (line_item.get("hanzi") or "").strip()
        pinyin = (line_item.get("pinyin") or "").strip()
        english = (line_item.get("english") or "").strip()

        inherited_setting = ""
        inherited_characters = [role]
        if isinstance(last_scene, dict):
            inherited_setting = (last_scene.get("setting_en") or "").strip()
            previous_characters = last_scene.get("characters_on_screen", [])
            if isinstance(previous_characters, list) and previous_characters:
                inherited_characters = previous_characters if role in previous_characters else previous_characters + [role]

        if not inherited_setting:
            inherited_setting = "Same lesson setting, continuing the dialogue naturally."

        inherited_camera = "Static"
        inherited_shot = "Medium shot"
        inherited_prompt_anchor = "Keep the same cinematic tone and visual continuity."
        if isinstance(last_scene, dict):
            inherited_camera = (last_scene.get("camera_movement") or "").strip() or inherited_camera
            inherited_shot = (last_scene.get("shot_type") or "").strip() or inherited_shot
            previous_prompt = (last_scene.get("video_prompt_en") or "").strip()
            if previous_prompt:
                inherited_prompt_anchor = "Maintain the same setting, lighting, and character continuity as the previous scene."

        sentence_type = "statement"
        if "？" in hanzi or "?" in hanzi:
            sentence_type = "question"
        elif hanzi.startswith("我叫") or hanzi.startswith("我是") or hanzi.startswith("我姓"):
            sentence_type = "introduction"

        if sentence_type == "question":
            scene_goal = f"{role}顺势发问，让对话自然推进。"
            scene_description_cn = f"{role}带着自然的好奇与礼貌，看着对方提出问题，语气轻松流畅。"
            prompt_en = (
                f"{inherited_shot}. {role} looks at the other character with a curious, engaged expression and asks a natural follow-up question. "
                f"{inherited_prompt_anchor}"
            )
        elif sentence_type == "introduction":
            scene_goal = f"{role}自然介绍自己的身份信息，让对话关系更清晰。"
            scene_description_cn = f"{role}带着友好而自信的神情，说出自己的身份或名字，语气真诚自然。"
            prompt_en = (
                f"{inherited_shot}. {role} speaks with a friendly, confident expression while introducing themself. "
                f"{inherited_prompt_anchor}"
            )
        else:
            scene_goal = f"{role}回应对方的话语，保持对话节奏自然连贯。"
            scene_description_cn = f"{role}顺着上一句自然回应，对话气氛轻松，交流流畅。"
            prompt_en = (
                f"{inherited_shot}. {role} gives a natural spoken response, maintaining warm eye contact and smooth conversational rhythm. "
                f"{inherited_prompt_anchor}"
            )

        return {
            "scene_id": fallback_scene_id,
            "source_line_refs": [line_item.get("ref")],
            "source_text": {
                "hanzi": [hanzi] if hanzi else [],
                "pinyin": [pinyin] if pinyin else [],
                "english": [english] if english else [],
            },
            "scene_goal": scene_goal,
            "scene_description_cn": scene_description_cn,
            "setting_en": inherited_setting,
            "characters_on_screen": inherited_characters,
            "camera_movement": inherited_camera,
            "shot_type": inherited_shot,
            "video_prompt_en": prompt_en,
            "voice_over": {
                "speaker": role,
                "hanzi": hanzi,
                "pinyin": pinyin,
                "english": english,
            },
            "subtitle_tracks": {
                "default": "hanzi",
                "optional": ["pinyin", "english"]
            },
            "estimated_duration_seconds": 6,
        }

    def _append_fallback_scenes_for_missing_refs(self, metadata: dict, normalized_result: dict, dialogues: list, line_ref_offset: int) -> dict:
        if not isinstance(normalized_result, dict):
            normalized_result = {"global_config": {}, "scenes": []}

        scenes = normalized_result.get("scenes", []) if isinstance(normalized_result.get("scenes"), list) else []
        input_lines = self._extract_input_lines_with_global_refs(dialogues, line_ref_offset)
        expected_refs = {item["ref"] for item in input_lines}
        actual_refs = set()
        for scene in scenes:
            refs = scene.get("source_line_refs", []) if isinstance(scene, dict) else []
            for ref in refs:
                try:
                    actual_refs.add(int(ref))
                except (TypeError, ValueError):
                    continue

        missing_refs = sorted(expected_refs - actual_refs)
        if not missing_refs:
            return normalized_result

        line_lookup = {item["ref"]: item for item in input_lines}
        fallback_scenes = []
        last_scene = scenes[-1] if scenes else None
        next_scene_id = len(scenes) + 1

        print(f"  ⚠️ Task 3A 检测到缺失台词行 {missing_refs}，正在优先尝试单行补生成...")
        for ref in missing_refs:
            line_item = line_lookup.get(ref)
            if not line_item:
                continue
            recovered_scene = self._generate_single_line_scene(
                metadata=metadata,
                line_item=line_item,
                fallback_scene_id=next_scene_id,
                last_scene=last_scene
            )
            if recovered_scene:
                print(f"    ↳ 第 {ref} 行单行补生成成功。")
                fallback_scene = recovered_scene
            else:
                print(f"    ↳ 第 {ref} 行单行补生成失败，回退到保守 fallback。")
                fallback_scene = self._build_fallback_scene(line_item, next_scene_id, last_scene)
            fallback_scenes.append(fallback_scene)
            last_scene = fallback_scene
            next_scene_id += 1

        merged_scenes = scenes + fallback_scenes
        merged_scenes.sort(key=lambda scene: min(scene.get("source_line_refs", [10**9])) if scene.get("source_line_refs") else 10**9)
        normalized_result["scenes"] = [
            {
                **scene,
                "scene_id": index
            }
            for index, scene in enumerate(merged_scenes, start=1)
        ]
        return normalized_result

    def _split_dialogues(self, dialogues: list):
        if not dialogues:
            return ([], 0), ([], 0)

        if len(dialogues) == 1 and isinstance(dialogues[0], dict) and isinstance(dialogues[0].get("lines"), list):
            lines = dialogues[0].get("lines", [])
            if len(lines) <= 2:
                return (dialogues, 0), ([], 0)
            split_index = max(1, len(lines) // 2)
            first_half = [{"lines": lines[:split_index]}]
            second_half = [{"lines": lines[split_index:]}]
            return (first_half, 0), (second_half, split_index)

        if len(dialogues) <= 2:
            return (dialogues, 0), ([], 0)

        split_index = max(1, len(dialogues) // 2)
        return (dialogues[:split_index], 0), (dialogues[split_index:], split_index)

    def run(self, metadata: dict, dialogues: list):
        print("  ▶️ [Task 3A] 正在生成课文情景演绎脚本...")

        (first_half, first_offset), (second_half, second_offset) = self._split_dialogues(dialogues or [])
        foundation_result = self._request_batch(
            metadata=metadata,
            dialogues=first_half,
            batch_mode="foundation",
        )
        advanced_result = self._request_batch(
            metadata=metadata,
            dialogues=second_half if second_half else first_half,
            batch_mode="advanced",
        ) if second_half else {"global_config": {}, "scenes": []}

        foundation_normalized = self._normalize_result(foundation_result, line_ref_offset=first_offset)
        foundation_normalized = self._append_fallback_scenes_for_missing_refs(
            metadata,
            foundation_normalized,
            first_half,
            first_offset
        )
        advanced_normalized = self._normalize_result(advanced_result, line_ref_offset=second_offset)
        advanced_normalized = self._append_fallback_scenes_for_missing_refs(
            metadata,
            advanced_normalized,
            second_half if second_half else [],
            second_offset
        ) if second_half else advanced_normalized

        merged_scenes = []
        merged_scenes.extend(foundation_normalized.get("scenes", []))
        merged_scenes.extend(advanced_normalized.get("scenes", []))

        if merged_scenes:
            normalized_result = {
                "global_config": {
                    "visual_style": foundation_normalized["global_config"].get("visual_style") or advanced_normalized["global_config"].get("visual_style") or "",
                    "setting_summary_cn": foundation_normalized["global_config"].get("setting_summary_cn") or advanced_normalized["global_config"].get("setting_summary_cn") or "",
                    "setting_summary_en": foundation_normalized["global_config"].get("setting_summary_en") or advanced_normalized["global_config"].get("setting_summary_en") or "",
                    "character_definitions": foundation_normalized["global_config"].get("character_definitions") or advanced_normalized["global_config"].get("character_definitions") or [],
                },
                "scenes": [
                    {
                        **scene,
                        "scene_id": index
                    }
                    for index, scene in enumerate(merged_scenes, start=1)
                ]
            }
            scenes_count = len(normalized_result.get("scenes", []))
            print(f"  ✨ 情景演绎脚本完成，共生成 {scenes_count} 个分镜。")
            return normalized_result

        return {
            "global_config": {
                "visual_style": "",
                "setting_summary_cn": "",
                "setting_summary_en": "",
                "character_definitions": []
            },
            "scenes": []
        }
