from __future__ import annotations

from content_builder.core.pipeline import get_pipeline


def find_legacy_keys(value, path: str = "$"):
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in {"cn", "py", "pinyin", "chinese"}:
                yield child_path
            yield from find_legacy_keys(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from find_legacy_keys(child, f"{path}[{index}]")


def assert_pipeline_registration(
    testcase,
    *,
    pipeline_id: str,
    target_language: str,
    default_output_lang: str | None = None,
    aliases: tuple[str, ...] = (),
):
    pipeline = get_pipeline(pipeline_id)
    testcase.assertEqual(pipeline.pipeline_id, pipeline_id)
    testcase.assertEqual(pipeline.target_language, target_language)
    if default_output_lang is not None:
        testcase.assertEqual(pipeline.default_output_lang, default_output_lang)
    for alias in aliases:
        testcase.assertIs(get_pipeline(alias), pipeline)
    return pipeline


def assert_schema_v2_payload(
    testcase,
    payload: dict,
    *,
    pipeline_id: str,
    target_language: str,
    support_language: str | None = None,
):
    testcase.assertIsNotNone(payload)
    testcase.assertEqual(payload["schema_version"], "2.0")
    testcase.assertEqual(payload["pipeline_id"], pipeline_id)
    testcase.assertEqual(payload["target_language"], target_language)
    if support_language is not None:
        testcase.assertEqual(payload["support_language"], support_language)


def assert_render_plan_minimum(
    testcase,
    payload: dict,
    *,
    subtitle_keys: tuple[str, ...] = (),
):
    render_plan = payload["video_render_plan"]["explanation"]
    testcase.assertGreater(len(render_plan["segments"]), 0)
    if subtitle_keys:
        narration_track = render_plan["segments"][0].get("narration_track", {})
        for key in subtitle_keys:
            testcase.assertIn(key, narration_track)
    return render_plan


def assert_no_legacy_keys(testcase, value):
    testcase.assertEqual(list(find_legacy_keys(value)), [])
