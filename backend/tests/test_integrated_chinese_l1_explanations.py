import contextlib
import io
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch


BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if "json_repair" not in sys.modules:
    json_repair_mod = types.ModuleType("json_repair")
    json_repair_mod.repair_json = lambda text, **kwargs: text  # noqa: ARG005
    sys.modules["json_repair"] = json_repair_mod

from content_builder.zh.integrated_chinese.scripts import localize  # noqa: E402
from content_builder.zh.integrated_chinese.scripts import run_resumable_enhanced_english as english_runner  # noqa: E402
from content_builder.zh.integrated_chinese.scripts import run_resumable_l1_rebuild as l1_runner  # noqa: E402
from content_builder.zh.integrated_chinese.tasks._explanation_writer import (  # noqa: E402
    Task3ExplanationGenerator,
)
from content_builder.zh.integrated_chinese.tasks.render_planner import (  # noqa: E402
    Task4CExplanationComposer,
)


def _l1_focus(language_name: str) -> dict:
    return {
        "likely_misunderstanding": f"Erreur probable pour un locuteur {language_name}.",
        "contrast_with_l1": f"Contraste entre le chinois et le {language_name}.",
        "correction_strategy": "Appliquer une stratégie de correction concrète.",
    }


class _SequenceLLM:
    def __init__(self, responses):
        self.responses = list(responses)
        self.prompts = []

    def generate_structured_json(self, prompt, file_path=None, file_obj=None):  # noqa: ARG002
        self.prompts.append(prompt)
        return self.responses.pop(0)


class IntegratedChineseL1ExplanationTests(unittest.TestCase):
    def test_french_prompt_requires_native_transfer_on_every_segment(self):
        writer = Task3ExplanationGenerator(_SequenceLLM([]))

        prompt = writer._build_prompt(
            metadata={"lesson_id": 101, "title": "问好"},
            dialogues=[{"line_ref": 1, "hanzi": "你好", "translation": "Bonjour"}],
            teaching_materials={"grammar_sections": []},
            vocabulary=[],
            grammar=[],
            batch_mode="foundation",
            support_language="fr",
        )

        self.assertIn("French native speakers learning Chinese", prompt)
        self.assertIn("每一个 segment", prompt)
        self.assertIn("learner_l1_focus.likely_misunderstanding", prompt)
        self.assertIn("不能先写英文再逐句翻译", prompt)
        self.assertIn("法语疑问句可用 est-ce que", prompt)
        self.assertIn("La salutation [zh:你好]", prompt)
        self.assertIn("先完整朗读，再讲解", prompt)
        self.assertIn("reading_text", prompt)
        self.assertIn("单个 [zh:reading_text]", prompt)
        self.assertNotIn("讲解对象是以英文为母语", prompt)

    def test_batch_retries_when_a_page_omits_l1_focus(self):
        incomplete = {
            "global_config": {},
            "segments": [{"narration": {"subtitle_en": "Bonjour."}}],
        }
        complete = {
            "global_config": {},
            "segments": [
                {
                    "narration": {"subtitle_en": "Bonjour."},
                    "learner_l1_focus": _l1_focus("français"),
                }
            ],
        }
        llm = _SequenceLLM([incomplete, complete])
        writer = Task3ExplanationGenerator(llm)

        with contextlib.redirect_stdout(io.StringIO()):
            result = writer._request_batch(
                metadata={"title": "问好"},
                dialogues=[{"line_ref": 1, "hanzi": "你好"}],
                teaching_materials={},
                vocabulary=[],
                grammar=[],
                batch_mode="foundation",
                support_language="fr",
            )

        self.assertEqual(result, complete)
        self.assertEqual(len(llm.prompts), 2)

    def test_batch_deterministically_repairs_a_partial_readthrough(self):
        base = {
            "segment_type": "line_walkthrough",
            "source_line_refs": [1],
            "on_screen_text": {"focus_text": "你贵姓？我姓王。"},
            "learner_l1_focus": _l1_focus("français"),
        }
        incomplete = {
            "global_config": {},
            "segments": [
                {
                    **base,
                    "reading_text": "你贵姓？",
                    "narration": {"subtitle_en": "Écoutez [zh:贵姓], puis regardons la phrase."},
                }
            ],
        }
        llm = _SequenceLLM([incomplete])
        writer = Task3ExplanationGenerator(llm)

        with contextlib.redirect_stdout(io.StringIO()):
            result = writer._request_batch(
                metadata={"title": "问好"},
                dialogues=[{"line_ref": 1, "hanzi": "你贵姓？我姓王。"}],
                teaching_materials={},
                vocabulary=[],
                grammar=[],
                batch_mode="foundation",
                support_language="fr",
            )

        segment = result["segments"][0]
        self.assertEqual(segment["reading_text"], "你贵姓？我姓王。")
        self.assertTrue(segment["narration"]["subtitle_en"].startswith("[zh:你贵姓？我姓王。]"))
        self.assertEqual(writer._batch_quality_issues(result), [])
        self.assertEqual(len(llm.prompts), 1)

        late = json.loads(json.dumps(result, ensure_ascii=False))
        late["segments"][0]["narration"]["subtitle_en"] = (
            "Commençons par le sens. Regardons ensuite la structure. "
            "Écoutons seulement maintenant [zh:你贵姓？我姓王。]."
        )
        self.assertTrue(
            any("appears too late" in issue for issue in writer._batch_quality_issues(late))
        )

    def test_optional_erhua_parentheses_are_normalized_without_a_separator(self):
        source_line = "七点半我去白英爱的宿舍跟她聊天（儿）。"
        normalized_line = "七点半我去白英爱的宿舍跟她聊天儿。"
        incomplete = {
            "global_config": {},
            "segments": [
                {
                    "segment_type": "line_walkthrough",
                    "source_line_refs": [13],
                    "reading_text": "七点半我去白英爱的宿舍跟她聊天。",
                    "narration": {"subtitle_en": "First listen to [zh:聊天], then study the line."},
                    "on_screen_text": {"focus_text": normalized_line},
                    "learner_l1_focus": _l1_focus("English"),
                }
            ],
        }
        llm = _SequenceLLM([incomplete])
        writer = Task3ExplanationGenerator(llm)

        with contextlib.redirect_stdout(io.StringIO()):
            result = writer._request_batch(
                metadata={"title": "A Day in the Life"},
                dialogues=[{"line_ref": 13, "hanzi": source_line}],
                teaching_materials={},
                vocabulary=[],
                grammar=[],
                batch_mode="foundation",
                support_language="en",
            )

        segment = result["segments"][0]
        self.assertEqual(writer._reading_from_value(source_line), normalized_line)
        self.assertEqual(writer._reading_from_value(source_line.replace("（儿）", "(儿)")), normalized_line)
        self.assertEqual(segment["reading_text"], normalized_line)
        self.assertTrue(segment["narration"]["subtitle_en"].startswith(f"[zh:{normalized_line}]"))
        self.assertEqual(writer._batch_quality_issues(result), [])
        self.assertEqual(len(llm.prompts), 1)

    def test_stray_ocr_quote_does_not_split_a_full_readthrough(self):
        source_line = "这个饭馆儿的菜是“不错,但是没有我们杭州的饭馆儿好。"
        normalized_line = "这个饭馆儿的菜是不错，但是没有我们杭州的饭馆儿好。"
        incomplete = {
            "global_config": {},
            "segments": [
                {
                    "segment_type": "line_walkthrough",
                    "source_line_refs": [26],
                    "reading_text": "这个饭馆的菜是不错。",
                    "narration": {"subtitle_en": "First listen to [zh:这个饭馆的菜是不错]."},
                    "on_screen_text": {"focus_text": normalized_line},
                    "learner_l1_focus": _l1_focus("English"),
                }
            ],
        }
        llm = _SequenceLLM([incomplete])
        writer = Task3ExplanationGenerator(llm)

        with contextlib.redirect_stdout(io.StringIO()):
            result = writer._request_batch(
                metadata={"title": "在饭馆儿"},
                dialogues=[{"line_ref": 26, "hanzi": source_line}],
                teaching_materials={},
                vocabulary=[],
                grammar=[],
                batch_mode="foundation",
                support_language="en",
            )

        segment = result["segments"][0]
        self.assertEqual(writer._reading_from_value(source_line), normalized_line)
        self.assertEqual(segment["reading_text"], normalized_line)
        self.assertTrue(segment["narration"]["subtitle_en"].startswith(f"[zh:{normalized_line}]"))
        self.assertEqual(writer._batch_quality_issues(result), [])
        self.assertEqual(len(llm.prompts), 1)

    def test_translation_collection_excludes_the_old_english_explanation(self):
        data = {
            "lesson_metadata": {"title_localized": "Greetings"},
            "video_render_plan": {
                "explanation": {
                    "target_audience": "English native speakers learning Chinese",
                    "segments": [
                        {
                            "segment_title": "Greeting",
                            "narration_track": {"subtitle_en": "Old English teaching script."},
                        }
                    ],
                }
            },
        }

        items = localize._collect_translatable(data)
        paths = [path for path, _ in items]

        self.assertEqual(paths, ["lesson_metadata.title_localized"])
        self.assertNotIn("Old English teaching script.", [value for _, value in items])

    def test_localization_replaces_video_plan_with_regenerated_french_teaching(self):
        source_data = {
            "lesson_metadata": {
                "lesson_id": 101,
                "course_id": 1,
                "title": "问好",
                "title_localized": "Greetings",
            },
            "course_content": {
                "dialogues": [
                    {
                        "lines": [
                            {
                                "role": "王朋",
                                "translation": "Hello.",
                                "tokens": [
                                    {"surface": "你", "annotation": "nǐ"},
                                    {"surface": "好", "annotation": "hǎo"},
                                ],
                            }
                        ]
                    }
                ],
                "vocabulary": [],
            },
            "teaching_materials": {"grammar_sections": []},
            "video_plan": {
                "lesson_video_plan": {"support_language": "en"},
                "explanation": {"segments": [{"narration": {"subtitle_en": "Old English."}}]},
            },
            "video_render_plan": {
                "explanation": {
                    "segments": [{"narration_track": {"subtitle_en": "Old English."}}]
                }
            },
            "database_items": [],
        }

        regenerated = {
            "global_config": {
                "target_audience": "French native speakers learning Chinese",
                "support_language": "fr",
            },
            "segments": [
                {
                    "segment_id": 1,
                    "segment_type": "line_walkthrough",
                    "source_line_refs": [1],
                    "segment_title": "Saluer quelqu'un",
                    "teaching_goal": "Employer la salutation naturellement.",
                    "reading_text": "你好",
                    "narration": {"subtitle_en": "En français, attention au ton de [zh:你好]."},
                    "learner_l1_focus": _l1_focus("français"),
                    "on_screen_text": {
                        "main_title": "问好",
                        "focus_text": "你好",
                        "focus_pinyin": "nǐ hǎo",
                        "focus_gloss_en": "Bonjour",
                        "notes": "Deux tons lexicaux.",
                    },
                    "highlight_words": [],
                    "grammar_points": [],
                    "estimated_duration_seconds": 12,
                }
            ],
        }
        writer_calls = []

        class _FakeWriter:
            def __init__(self, llm, fallback_llm=None):  # noqa: ARG002
                pass

            def run(self, **kwargs):
                writer_calls.append(kwargs)
                return regenerated

        with tempfile.TemporaryDirectory(prefix="ic-l1-") as temp_dir:
            source_path = Path(temp_dir) / "lesson101_data.json"
            source_path.write_text(json.dumps(source_data, ensure_ascii=False), encoding="utf-8")
            with patch.object(
                localize,
                "_run_translation",
                return_value={"lesson_metadata.title_localized": "Salutations"},
            ), patch.object(localize, "Task3ExplanationGenerator", _FakeWriter):
                with contextlib.redirect_stdout(io.StringIO()):
                    result = localize.translate_lesson(source_path, "fr", object())

        self.assertEqual(writer_calls[0]["support_language"], "fr")
        self.assertEqual(result["video_plan"]["lesson_video_plan"]["support_language"], "fr")
        self.assertEqual(
            result["video_plan"]["lesson_video_plan"]["target_audience"],
            "French native speakers learning Chinese",
        )
        render_explanation = result["video_render_plan"]["explanation"]
        self.assertEqual(render_explanation["support_language"], "fr")
        self.assertEqual(
            render_explanation["segments"][0]["narration_track"]["subtitle_fr"],
            "En français, attention au ton de [zh:你好].",
        )
        self.assertNotIn("Old English.", json.dumps(result, ensure_ascii=False))
        self.assertEqual(
            result["localization"]["explanation_strategy"],
            "regenerated_from_structured_lesson_content",
        )

    def test_render_plan_keeps_legacy_subtitle_and_adds_language_specific_field(self):
        explanation = {
            "global_config": {},
            "segments": [
                {
                    "segment_id": 1,
                    "segment_type": "line_walkthrough",
                    "narration": {"subtitle_en": "Une explication française."},
                    "learner_l1_focus": _l1_focus("français"),
                    "on_screen_text": {"focus_text": "你好"},
                }
            ],
        }

        plan = Task4CExplanationComposer().run(
            {"lesson_id": 101, "course_id": 1, "title": "问好"},
            explanation,
            support_language="fr",
        )

        segment = plan["segments"][0]
        self.assertEqual(segment["narration_track"]["script"], "Une explication française.")
        self.assertEqual(segment["narration_track"]["subtitle_en"], "Une explication française.")
        self.assertEqual(segment["narration_track"]["subtitle_fr"], "Une explication française.")
        self.assertEqual(segment["learner_l1_focus"], _l1_focus("français"))

    def test_enhanced_english_runner_maps_textbook_indexes_by_archived_lesson_id(self):
        with tempfile.TemporaryDirectory(prefix="ic-archive-") as temp_dir:
            archive = Path(temp_dir)
            for name in ("lesson201.pdf", "lesson102.pdf", "lesson101.pdf", "notes.pdf"):
                (archive / name).write_bytes(b"PDF")

            lesson_ids = english_runner._lesson_ids_from_archive(archive)

        self.assertEqual(lesson_ids, [101, 102, 201])

    def test_enhanced_english_checkpoint_requires_script_tts_and_every_slide_asset(self):
        with tempfile.TemporaryDirectory(prefix="ic-checkpoint-") as temp_dir:
            root = Path(temp_dir)
            narration = root / "narration.mp3"
            image = root / "slide.webp"
            slide_audio = root / "slide.mp3"
            for path in (narration, image, slide_audio):
                path.write_bytes(b"asset")
            focus = {
                "likely_misunderstanding": "Likely English transfer error.",
                "contrast_with_l1": "Chinese and English differ here.",
                "correction_strategy": "Use this correction strategy.",
            }
            json_path = root / "lesson101_data.json"
            json_path.write_text(
                json.dumps(
                    {
                        "video_plan": {
                            "production_notes": {
                                "explanation_generation_version": localize.L1_EXPLANATION_VERSION,
                            },
                            "explanation": {"segments": [{"learner_l1_focus": focus}]},
                        },
                        "video_render_plan": {
                            "explanation": {
                                "support_language": "en",
                                "target_audience": "English native speakers learning Chinese",
                                "segments": [
                                    {
                                        "learner_l1_focus": focus,
                                        "sentence_texts": ["English narration."],
                                        "sentence_timings_seconds": [0.0],
                                    }
                                ],
                            }
                        },
                        "explanation_narration_audio": {
                            "status": "ok",
                            "audio_file": str(narration),
                        },
                        "teaching_slide_deck": {
                            "render_version": english_runner.SLIDE_RENDER_VERSION,
                            "lang": "en",
                            "slide_count": 1,
                            "slides": [
                                {
                                    "image": {"local_path": str(image)},
                                    "audio": {"local_path": str(slide_audio)},
                                }
                            ],
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            complete = english_runner.inspect_lesson(json_path, 101)
            complete_image_refresh = english_runner._can_refresh_images_only(json_path, "en")
            narration.unlink()
            per_slide_narration = english_runner.inspect_lesson(json_path, 101)
            narration.write_bytes(b"asset")
            stale_payload = json.loads(json_path.read_text(encoding="utf-8"))
            stale_payload["teaching_slide_deck"]["render_version"] = "1-caption-baked-into-image"
            json_path.write_text(json.dumps(stale_payload, ensure_ascii=False), encoding="utf-8")
            stale_slides = english_runner.inspect_lesson(json_path, 101)
            stale_image_refresh = english_runner._can_refresh_images_only(json_path, "en")

            stale_payload["teaching_slide_deck"]["render_version"] = english_runner.SLIDE_RENDER_VERSION
            json_path.write_text(json.dumps(stale_payload, ensure_ascii=False), encoding="utf-8")
            french_payload = json.loads(json_path.read_text(encoding="utf-8"))
            french_explanation = french_payload["video_render_plan"]["explanation"]
            french_explanation["support_language"] = "fr"
            french_explanation["target_audience"] = "French native speakers learning Chinese"
            french_payload["teaching_slide_deck"]["lang"] = "fr"
            json_path.write_text(json.dumps(french_payload, ensure_ascii=False), encoding="utf-8")
            french_complete = english_runner.inspect_lesson(json_path, 101, lang="fr")
            french_image_refresh = english_runner._can_refresh_images_only(json_path, "fr")

            french_explanation["support_language"] = "de"
            french_explanation["target_audience"] = "German native speakers learning Chinese"
            french_payload["teaching_slide_deck"]["lang"] = "de"
            json_path.write_text(json.dumps(french_payload, ensure_ascii=False), encoding="utf-8")
            german_complete = english_runner.inspect_lesson(json_path, 101, lang="de")
            german_image_refresh = english_runner._can_refresh_images_only(json_path, "de")

            french_explanation["support_language"] = "en"
            french_explanation["target_audience"] = "English native speakers learning Chinese"
            french_payload["teaching_slide_deck"]["lang"] = "en"
            json_path.write_text(json.dumps(french_payload, ensure_ascii=False), encoding="utf-8")
            slide_audio.unlink()
            interrupted = english_runner.inspect_lesson(json_path, 101)
            interrupted_image_refresh = english_runner._can_refresh_images_only(json_path, "en")

        self.assertTrue(complete.complete)
        self.assertTrue(complete_image_refresh)
        self.assertTrue(per_slide_narration.narration)
        self.assertTrue(per_slide_narration.complete)
        self.assertTrue(stale_slides.enhanced)
        self.assertTrue(stale_slides.narration)
        self.assertFalse(stale_slides.slides)
        self.assertTrue(stale_image_refresh)
        self.assertEqual(english_runner._stage2_force_flags(stale_slides, False), (False, True))
        self.assertTrue(french_complete.complete)
        self.assertTrue(french_image_refresh)
        self.assertTrue(german_complete.complete)
        self.assertTrue(german_image_refresh)
        self.assertTrue(interrupted.enhanced)
        self.assertTrue(interrupted.narration)
        self.assertFalse(interrupted.slides)
        self.assertFalse(interrupted_image_refresh)
        self.assertEqual(english_runner._stage2_force_flags(interrupted, False), (False, True))

    def test_enhanced_english_runner_rerenders_slides_when_narration_is_rebuilt(self):
        state = english_runner.LessonState(
            lesson_id=101,
            json_path=Path("lesson101_data.json"),
            readable=True,
            enhanced=True,
            narration=False,
            slides=True,
        )

        self.assertEqual(english_runner._stage2_force_flags(state, False), (True, True))

    def test_l1_runner_restores_synced_localized_checkpoint_without_overwriting_work(self):
        with tempfile.TemporaryDirectory(prefix="ic-l1-resume-") as temp_dir:
            root = Path(temp_dir)
            output_dir = root / "output_json" / "de"
            synced_dir = root / "synced_json" / "de"
            synced_dir.mkdir(parents=True)
            synced_path = synced_dir / "lesson101_data_de.json"
            synced_path.write_text('{"checkpoint": "synced"}', encoding="utf-8")

            l1_runner._restore_localized_checkpoints(
                lesson_ids=[101],
                output_dir=output_dir,
                synced_dir=synced_dir,
                lang="de",
            )
            output_path = output_dir / synced_path.name
            self.assertEqual(json.loads(output_path.read_text(encoding="utf-8"))["checkpoint"], "synced")

            output_path.write_text('{"checkpoint": "working"}', encoding="utf-8")
            l1_runner._restore_localized_checkpoints(
                lesson_ids=[101],
                output_dir=output_dir,
                synced_dir=synced_dir,
                lang="de",
            )
            self.assertEqual(json.loads(output_path.read_text(encoding="utf-8"))["checkpoint"], "working")

    def test_enhanced_english_seed_preserves_working_json_and_fills_only_missing(self):
        with tempfile.TemporaryDirectory(prefix="ic-seed-") as temp_dir:
            root = Path(temp_dir)
            output = root / "output"
            synced = root / "synced"
            output.mkdir()
            synced.mkdir()
            (output / "lesson101_data.json").write_text('{"source":"working"}', encoding="utf-8")
            (synced / "lesson102_data.json").write_text('{"source":"synced"}', encoding="utf-8")

            def fake_export(course_id, export_dir, backup=False):  # noqa: ARG001
                export_dir.mkdir(parents=True, exist_ok=True)
                (export_dir / "lesson201_data.json").write_text('{"source":"database"}', encoding="utf-8")
                return 1

            with patch.object(english_runner, "export_lessons", side_effect=fake_export):
                with contextlib.redirect_stdout(io.StringIO()):
                    english_runner._seed_missing_sources(
                        lesson_ids=[101, 102, 201],
                        output_dir=output,
                        synced_dir=synced,
                        course_id=1,
                    )

            sources = {
                lesson: json.loads((output / f"lesson{lesson}_data.json").read_text(encoding="utf-8"))["source"]
                for lesson in (101, 102, 201)
            }

        self.assertEqual(sources, {101: "working", 102: "synced", 201: "database"})


if __name__ == "__main__":
    unittest.main()
