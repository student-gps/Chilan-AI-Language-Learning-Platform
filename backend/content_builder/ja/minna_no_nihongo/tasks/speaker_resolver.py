from __future__ import annotations

import json
import re
from copy import deepcopy

try:
    from content_builder.core.llm_providers import BaseLLMProvider
except ImportError:
    from content_builder.core.llm_providers import BaseLLMProvider


class MinnaNoNihongoSpeakerResolver:
    """Repair dialogue speaker attribution before lesson normalization.

    The extractor can mistake a vocative such as "佐藤さん、..." for the speaker.
    This task first applies conservative deterministic fixes, then optionally
    asks the LLM to audit the whole dialogue using only compact line data.
    """

    HONORIFIC_RE = re.compile(r"^(?P<name>[\u3040-\u30ff\u3400-\u9fffA-Za-z・ー]+?)(さん|先生|せんせい|ちゃん|くん|君|様|さま)[、,，]")
    SPEAKER_SUFFIX_RE = re.compile(r"(さん|先生|せんせい|ちゃん|くん|君|様|さま)$")

    def run(
        self,
        lesson_data: dict,
        llm_provider: BaseLLMProvider | None = None,
        lesson_id: int | None = None,
    ) -> dict:
        repaired = deepcopy(lesson_data if isinstance(lesson_data, dict) else {})
        deterministic = self._apply_deterministic_repairs(repaired)
        llm_corrections = []
        if llm_provider is not None:
            llm_corrections = self._apply_llm_audit(repaired, llm_provider, lesson_id=lesson_id)

        if deterministic or llm_corrections:
            diagnostics = repaired.setdefault("pipeline_diagnostics", {})
            diagnostics["speaker_resolution"] = {
                "deterministic_corrections": deterministic,
                "llm_corrections": llm_corrections,
            }
        return repaired

    def _apply_deterministic_repairs(self, lesson_data: dict) -> list[dict]:
        lines = self._dialogue_lines(lesson_data)
        corrections = []
        previous_speaker = ""
        for line in lines:
            if not isinstance(line, dict):
                continue
            line_ref = line.get("line_ref")
            speaker = (line.get("speaker") or line.get("role") or "").strip()
            text = (line.get("text") or line.get("ja") or "").strip()
            addressed = self._leading_addressee(text)

            if addressed and previous_speaker:
                speaker_key = self._speaker_key(speaker)
                addressed_key = self._speaker_key(addressed)
                previous_key = self._speaker_key(previous_speaker)
                if speaker_key == addressed_key and previous_key != addressed_key:
                    line["speaker"] = previous_speaker
                    corrections.append({
                        "line_ref": line_ref,
                        "from": speaker,
                        "to": previous_speaker,
                        "reason": "leading_addressee_is_not_speaker",
                    })
                    speaker = previous_speaker

            if speaker:
                previous_speaker = speaker
        return corrections

    def _apply_llm_audit(
        self,
        lesson_data: dict,
        llm_provider: BaseLLMProvider,
        lesson_id: int | None = None,
    ) -> list[dict]:
        lines = self._dialogue_lines(lesson_data)
        if not lines:
            return []

        candidates = sorted({
            self._speaker_key(line.get("speaker") or line.get("role") or "")
            for line in lines
            if isinstance(line, dict) and (line.get("speaker") or line.get("role"))
        })
        compact_lines = [
            {
                "line_ref": line.get("line_ref") or index,
                "current_speaker": line.get("speaker") or line.get("role") or "",
                "text": line.get("text") or line.get("ja") or "",
                "translation": line.get("translation") or "",
            }
            for index, line in enumerate(lines, start=1)
            if isinstance(line, dict)
        ]
        prompt = self._build_prompt(lesson_id=lesson_id, lines=compact_lines, candidates=candidates)
        result = llm_provider.generate_structured_json(prompt, file_path=None)
        corrections = result.get("speaker_corrections") if isinstance(result, dict) else []
        if not isinstance(corrections, list):
            return []

        by_ref = {
            int(line.get("line_ref") or index): line
            for index, line in enumerate(lines, start=1)
            if isinstance(line, dict)
        }
        applied = []
        candidate_keys = {self._speaker_key(candidate) for candidate in candidates if candidate}
        for correction in corrections:
            if not isinstance(correction, dict):
                continue
            try:
                line_ref = int(correction.get("line_ref"))
            except (TypeError, ValueError):
                continue
            speaker = (correction.get("speaker") or "").strip()
            if not speaker:
                continue
            speaker_key = self._speaker_key(speaker)
            if candidate_keys and speaker_key not in candidate_keys:
                continue
            line = by_ref.get(line_ref)
            if not line:
                continue
            current = (line.get("speaker") or line.get("role") or "").strip()
            if self._speaker_key(current) == speaker_key:
                continue
            line["speaker"] = speaker
            applied.append({
                "line_ref": line_ref,
                "from": current,
                "to": speaker,
                "reason": (correction.get("reason") or "llm_speaker_audit").strip(),
            })
        return applied

    def _build_prompt(self, lesson_id: int | None, lines: list[dict], candidates: list[str]) -> str:
        return f"""
        你是一名日语教材对话标注审校员。请根据整段会话内容判断每一行的 speaker 是否正确。
        只输出 JSON，不要输出 Markdown。

        规则：
        1. 句首的「Xさん、」「X先生、」通常是被称呼的人，不一定是说话人。
        2. 如果一行没有明显换说话人，可能沿用上一行 speaker。
        3. 只在明显错误时给出修正；不确定就不要修。
        4. speaker 必须优先从候选 speaker 中选择。

        lesson_id: {lesson_id}
        候选 speaker:
        {json.dumps(candidates, ensure_ascii=False)}

        当前会话行：
        {json.dumps(lines, ensure_ascii=False, indent=2)}

        输出结构：
        {{
          "speaker_corrections": [
            {{"line_ref": 3, "speaker": "山田", "reason": "佐藤さん is the addressee, not the speaker"}}
          ]
        }}
        """

    def _dialogue_lines(self, lesson_data: dict) -> list[dict]:
        content = lesson_data.get("course_content") if isinstance(lesson_data.get("course_content"), dict) else {}
        dialogue = content.get("dialogue") if isinstance(content.get("dialogue"), dict) else {}
        lines = dialogue.get("lines")
        return lines if isinstance(lines, list) else []

    def _leading_addressee(self, text: str) -> str:
        match = self.HONORIFIC_RE.match(text or "")
        if not match:
            return ""
        return match.group("name").strip()

    def _speaker_key(self, speaker: str) -> str:
        key = str(speaker or "").strip()
        key = key.replace("：", "").replace(":", "").strip()
        key = self.SPEAKER_SUFFIX_RE.sub("", key).strip()
        return key
