from llm_providers import BaseLLMProvider
from tasks.task3a_dramatization import Task3DramatizationGenerator
from tasks.task3b_explanation import Task3ExplanationGenerator


class Task3LessonVideoPlanner:
    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm = llm_provider
        self.dramatization_generator = Task3DramatizationGenerator(llm_provider)
        self.explanation_generator = Task3ExplanationGenerator(llm_provider)

    def run(self, metadata: dict, dialogues: list, teaching_materials: dict = None, vocabulary: list = None, grammar: list = None):
        print("  ▶️ [Task 3/3] 正在拆分生成“情景演绎 + 教学讲解”双段式视频脚本...")

        teaching_materials = teaching_materials if isinstance(teaching_materials, dict) else {}
        vocabulary = vocabulary if vocabulary else []
        grammar = grammar if grammar else []

        dramatization = self.dramatization_generator.run(
            metadata=metadata,
            dialogues=dialogues or [],
        )
        if not _has_min_dramatization_shape(dramatization):
            print("  ⚠️ Task 3A 输出结构不完整，已回退为空分镜结果。")
            dramatization = {
                "global_config": {},
                "scenes": []
            }
        explanation = self.explanation_generator.run(
            metadata=metadata,
            dialogues=dialogues or [],
            teaching_materials=teaching_materials,
            vocabulary=vocabulary,
            grammar=grammar,
        )
        if not _has_min_explanation_shape(explanation):
            print("  ⚠️ Task 3B 输出结构不完整，已回退为空讲解结果。")
            explanation = {
                "global_config": {},
                "segments": []
            }

        dramatization_scenes = dramatization.get("scenes", []) if isinstance(dramatization, dict) else []
        explanation_segments = explanation.get("segments", []) if isinstance(explanation, dict) else []

        print(
            "  ✨ 双段式教学视频脚本规划完成，"
            f"情景演绎 {len(dramatization_scenes)} 段，"
            f"教学讲解 {len(explanation_segments)} 段。"
        )

        lesson_title = metadata.get("title", "") if isinstance(metadata, dict) else ""
        lesson_id = metadata.get("lesson_id") if isinstance(metadata, dict) else None
        course_id = metadata.get("course_id") if isinstance(metadata, dict) else None

        return {
            "lesson_video_plan": {
                "lesson_id": lesson_id,
                "course_id": course_id,
                "lesson_title": lesson_title,
                "target_audience": "English native speakers learning Chinese",
                "primary_language": "zh",
                "support_language": "en",
                "subtitle_options": {
                    "hanzi": True,
                    "pinyin": True,
                    "english": True
                }
            },
            "dramatization": dramatization if isinstance(dramatization, dict) else {
                "global_config": {},
                "scenes": []
            },
            "explanation": explanation if isinstance(explanation, dict) else {
                "global_config": {},
                "segments": []
            },
            "production_notes": {
                "recommended_workflow": [
                    "generate dramatization visuals",
                    "generate explanation visuals",
                    "generate voice-over",
                    "compose subtitles"
                ],
                "remarks": "This schema is model-agnostic and designed for script planning plus downstream rendering."
            }
        }


def _has_min_dramatization_shape(payload: dict) -> bool:
    if not isinstance(payload, dict):
        return False
    scenes = payload.get("scenes", [])
    if not isinstance(scenes, list) or not scenes:
        return False
    for scene in scenes:
        if not isinstance(scene, dict):
            return False
        if not isinstance(scene.get("voice_over"), dict):
            return False
    return True


def _has_min_explanation_shape(payload: dict) -> bool:
    if not isinstance(payload, dict):
        return False
    segments = payload.get("segments", [])
    if not isinstance(segments, list) or not segments:
        return False
    for segment in segments:
        if not isinstance(segment, dict):
            return False
        narration = segment.get("narration")
        if not isinstance(narration, dict):
            return False
    return True


Task3VideoGenerator = Task3LessonVideoPlanner
