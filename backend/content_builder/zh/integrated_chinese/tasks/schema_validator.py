"""Stable structure for Integrated Chinese stage-one artifacts.

Structural defaults never replace the semantic and media gates in quality.py.
"""
from copy import deepcopy


def normalize_stage1_output(payload: dict, *, lesson_id: int, course_id: int,
                            support_language: str = 'en') -> dict:
    data = deepcopy(payload)
    data.update(schema_version='2.0', pipeline_id='integrated_chinese',
                target_language='zh', support_language=support_language)
    metadata = data.setdefault('lesson_metadata', {})
    metadata.setdefault('lesson_id', lesson_id)
    metadata.setdefault('course_id', course_id)
    content = data.setdefault('course_content', {})
    content.setdefault('dialogues', [])
    content.setdefault('vocabulary', [])
    data.setdefault('database_items', [])
    data.setdefault('teaching_materials', {})
    data.setdefault('lesson_audio_assets', {}).setdefault('items', [])
    explanation = data.setdefault('video_render_plan', {}).setdefault('explanation', {})
    explanation.setdefault('segments', [])
    explanation.setdefault('timeline', {})
    explanation.setdefault('video_style', {}).setdefault('aspect_ratio', '16:9')
    return data


class IntegratedChineseStage1Validator:
    def validate(self, data: dict) -> dict:
        if not isinstance(data, dict):
            raise ValueError('lesson_data must be a dict')
        for key in ('lesson_id', 'course_id'):
            value = (data.get('lesson_metadata') or {}).get(key)
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise ValueError(f'lesson_metadata.{key} missing or invalid')
        for key, expected in [('schema_version', '2.0'), ('pipeline_id', 'integrated_chinese'),
                              ('target_language', 'zh')]:
            if data.get(key) != expected:
                raise ValueError(f'{key} must be {expected}')
        content = data.get('course_content')
        if not isinstance(content, dict):
            raise ValueError('course_content missing')
        for key in ('dialogues', 'vocabulary'):
            if not isinstance(content.get(key), list):
                raise ValueError(f'course_content.{key} must be a list')
        if not isinstance(data.get('database_items'), list):
            raise ValueError('database_items must be a list')
        return data
