import argparse
import copy
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from content_builder.core.artifacts import apply_narration_timings, atomic_write_json, narration_fingerprint, resolve_artifact_path
from content_builder.core.checkpoints import CheckpointStore, build_lock
from content_builder.zh.integrated_chinese.quality import audit_lesson
from content_builder.zh.integrated_chinese.scripts.build_teaching_slide_deck import _caption_cues, _split_narration_audio, build_deck
from content_builder.zh.integrated_chinese.tasks.quiz_generator import Task2QuizGenerator
from content_builder.zh.integrated_chinese.workflow import run
from services.maintenance.content_builder_runner import build_content_builder_request, preview_content_builder


def lesson():
    return {
        "workflow_version": "1.0", "lesson_metadata": {"lesson_id": 101, "course_id": 1, "title": "问候"},
        "course_content": {"dialogues": [{"role": "李友", "chinese": "你好！", "pinyin": "nǐ hǎo", "translation": "Hello!"}],
            "vocabulary": [{"word": "你好", "pinyin": "nǐ hǎo", "definition": "hello", "example_sentence": {"cn": "你好！", "py": "nǐ hǎo", "translation": "Hello!"}}]},
        "teaching_materials": {"grammar_sections": [{"grammar_id": "G-1", "title": "Greeting", "explanation_en": "Use this greeting.", "examples": [{"hanzi": "你好！"}]}]},
        "database_items": [{"question_id": 1, "question_type": "CN_LISTEN_WRITE", "lesson_id": 101, "course_id": 1,
            "original_text": "Hello!", "standard_answers": ["你好！"], "metadata": {"line_ref": 1}}],
        "video_render_plan": {"explanation": {"lesson_id": 101, "segments": [{"segment_id": 1, "segment_type": "line_walkthrough", "template_name": "line_focus",
            "source_line_refs": [1], "source_grammar_ids": ["G-1"], "duration_seconds": 1.0,
            "narration_track": {"subtitle_en": "Say [zh:你好]."},
            "visual_blocks": [{"block_type": "hero_line", "content": {"focus_text": "你好！", "focus_pinyin": "nǐ hǎo", "focus_gloss_en": "Hello!"}}]}]}}
    }


def audio(path, duration=1):
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(24000)
        handle.writeframes(b"\x00\x00" * int(24000 * duration))
    return path


class IntegratedChineseQualityTests(unittest.TestCase):
    def audit(self, data):
        return audit_lesson(data, artifact_root=Path("unused"))

    def test_complete_content_passes(self):
        self.assertTrue(self.audit(lesson())["ok"])

    def test_missing_walkthrough_is_not_replaced_by_narration_mention(self):
        data = lesson()
        segment = data["video_render_plan"]["explanation"]["segments"][0]
        segment["segment_type"] = "grammar_focus"
        report = self.audit(data)
        self.assertIn("teaching_coverage", {item["code"] for item in report["issues"]})

    def test_filling_a_source_reference_without_teaching_the_text_fails(self):
        data = lesson()
        data["video_render_plan"]["explanation"]["segments"][0]["visual_blocks"][0]["content"]["focus_text"] = "再见！"
        self.assertIn("teaching_coverage", {item["code"] for item in self.audit(data)["issues"]})

    def test_empty_grammar_skeleton_and_missing_example_fail(self):
        data = lesson()
        data["teaching_materials"]["grammar_sections"][0]["explanation_en"] = ""
        data["course_content"]["vocabulary"][0]["example_sentence"]["py"] = ""
        codes = {item["code"] for item in self.audit(data)["issues"]}
        self.assertTrue({"grammar_skeleton", "vocabulary_example"}.issubset(codes))

    def test_listening_answer_must_match_referenced_text(self):
        data = lesson()
        data["database_items"][0]["standard_answers"] = ["再见！"]
        self.assertIn("listening_source", {item["code"] for item in self.audit(data)["issues"]})

    def test_unmarked_chinese_and_missing_grammar_reference_fail(self):
        data = lesson()
        segment = data["video_render_plan"]["explanation"]["segments"][0]
        segment["source_grammar_ids"] = []
        segment["narration_track"]["subtitle_en"] = "Say 你好."
        codes = {item["code"] for item in self.audit(data)["issues"]}
        self.assertTrue({"grammar_coverage", "tts_language"}.issubset(codes))

    def test_pinyin_cannot_be_spoken_by_the_english_voice(self):
        data = lesson()
        data["video_render_plan"]["explanation"]["segments"][0]["narration_track"]["subtitle_en"] = "Say nǐ hǎo."
        self.assertIn("tts_pinyin", {item["code"] for item in self.audit(data)["issues"]})

    def test_reference_fixes_incorrect_integer_in_llm_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            generator = Task2QuizGenerator(None, Path(tmp))
            material = {"你好！": {"line_ref": 1, "translation": "Hello!", "py": "nǐ hǎo"}}
            item = {"original_text": "Wrong hint", "standard_answers": ["你好！"], "metadata": {"line_ref": 23}}
            fixed = generator._normalize_listen_write_item(item, material)
            self.assertEqual(fixed["metadata"]["line_ref"], 1)
            self.assertEqual(fixed["original_text"], "Hello!")
            item["standard_answers"] = ["Invented answer"]
            self.assertEqual(generator._normalize_listen_write_item(item, material), {})

    def test_short_caption_does_not_overrun_audio(self):
        segment = {"duration_seconds": 0.4, "sentence_texts": ["Hello!"], "sentence_timings_seconds": [0]}
        self.assertEqual(_caption_cues(segment)[0]["end_ms"], 400)
        segment["sentence_texts"].append("Extra sentence")
        with self.assertRaises(ValueError):
            _caption_cues(segment)

    def test_voice_and_text_invalidate_narration_but_timing_does_not(self):
        data = lesson()
        original = narration_fingerprint(data, "en")
        data["video_render_plan"]["explanation"]["segments"][0]["duration_seconds"] = 23
        self.assertEqual(original, narration_fingerprint(data, "en"))
        with patch.dict(os.environ, {"TTS_EXPLANATION_VOICE_EN": "different-voice"}):
            self.assertNotEqual(original, narration_fingerprint(data, "en"))
        data["video_render_plan"]["explanation"]["segments"][0]["narration_track"]["subtitle_en"] = "New script."
        self.assertNotEqual(original, narration_fingerprint(data, "en"))

    def test_measured_timings_must_be_complete_and_finite(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = lesson()
            path = audio(Path(tmp) / "narration.wav")
            result = {"status": "ok", "audio_file": str(path), "segment_count": 1,
                      "segment_actual_durations": {"1": 1}, "segment_sentences": {"1": ["Hello"]}, "segment_timings": {"1": [0]}}
            apply_narration_timings(data, result)
            self.assertEqual(data["video_render_plan"]["explanation"]["timeline"]["total_duration_seconds"], 1)
            result["segment_actual_durations"]["1"] = math.nan
            with self.assertRaises(ValueError):
                apply_narration_timings(data, result)


class CheckpointTests(unittest.TestCase):
    def test_empty_extraction_is_never_saved_as_a_successful_task(self):
        from content_builder.zh.integrated_chinese.agent import ContentCreatorAgent
        from unittest.mock import Mock
        class Provider:
            model_id = "test-model"
            def upload_pdf(self, path):
                return "test-file"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdf = root / "lesson101.pdf"
            pdf.write_bytes(b"test-pdf")
            agent = ContentCreatorAgent(Provider(), root)
            agent.task1.run = Mock(return_value={})
            agent.task2.run = Mock(side_effect=AssertionError("Practice must not run after failed extraction"))
            with patch("content_builder.zh.integrated_chinese.agent.traceback.print_exc"):
                with self.assertRaisesRegex(ValueError, "extract_text"):
                    agent.generate_content(str(pdf), 101, checkpoint_dir=root / "checkpoints", render_lesson_audio=False, update_memory=False, raise_on_error=True)
            self.assertFalse((root / "checkpoints/extract_text.json").exists())
            self.assertEqual(json.loads((root / "checkpoints/extract_text.run.json").read_text())["status"], "failed")
    def test_reuse_verifies_artifact_bytes_and_failed_stage_does_not_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = CheckpointStore(root / "checkpoints")
            file = root / "clip.mp3"
            calls = []
            def action():
                calls.append(1)
                file.write_bytes(b"original")
                return {"ok": True}
            store.run("audio", {"text": "hello"}, action, outputs=lambda value: [file])
            store.run("audio", {"text": "hello"}, action, outputs=lambda value: [file])
            self.assertEqual(len(calls), 1)
            file.write_bytes(b"corrupt")
            store.run("audio", {"text": "hello"}, action, outputs=lambda value: [file])
            self.assertEqual(len(calls), 2)
            def fail():
                raise RuntimeError("provider failure")
            with self.assertRaises(RuntimeError):
                store.run("audio", {"text": "changed"}, fail)
            self.assertEqual(json.loads((store.root / "audio.run.json").read_text())["status"], "failed")
            self.assertEqual(json.loads((store.root / "audio.json").read_text())["status"], "complete")

    def test_lock_is_released_after_exception(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "build.lock"
            with self.assertRaises(RuntimeError):
                with build_lock(path):
                    raise RuntimeError("interrupted")
            with build_lock(path):
                pass

    def test_moved_legacy_narration_resolves_to_language_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "output_audio/en/lesson101_narration/lesson101_slide_001.mp3"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"audio")
            legacy = r"C:\old\artifacts\integrated_chinese\output_audio\lesson101_narration\lesson101_slide_001.mp3"
            self.assertEqual(resolve_artifact_path(legacy, root), target.resolve())

    def test_vertex_uses_only_the_configured_credential_basename(self):
        from content_builder.core.llm_providers import resolve_google_credentials
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            key = root / "credentials/expected.json"
            key.parent.mkdir()
            key.write_text("{}")
            with patch("content_builder.core.llm_providers.BACKEND_DIR", root), \
                 patch.dict(os.environ, {"GOOGLE_APPLICATION_CREDENTIALS": "C:/old/credentials/expected.json"}):
                resolve_google_credentials()
                self.assertEqual(Path(os.environ["GOOGLE_APPLICATION_CREDENTIALS"]), key.resolve())
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:/old/credentials/another.json"
                with self.assertRaises(FileNotFoundError):
                    resolve_google_credentials()

    def test_failed_tts_resumes_from_successful_sentence_cache(self):
        from content_builder.zh.integrated_chinese.tasks.narration_audio import Task4DExplanationNarrator
        with tempfile.TemporaryDirectory() as tmp:
            narrator = Task4DExplanationNarrator()
            narrator.provider = "edge"
            calls = []
            def synthesize(text, output):
                calls.append(text)
                if text == "Second." and calls.count("Second.") == 1:
                    raise RuntimeError("temporary provider failure")
                output.write_bytes(b"audio" * 100)
            def concat(files, output):
                shutil.copyfile(files[0], output)
            def pad(source, output, duration):
                shutil.copyfile(source, output)
            plan = {"lesson_id": 101, "segments": [{"segment_id": i, "narration_track": {"subtitle_en": text}} for i, text in enumerate(["First.", "Second."], start=1)]}
            with patch.object(narrator, "_configure_for_lang"), patch.object(narrator, "_synthesize", side_effect=synthesize), \
                 patch.object(narrator, "_get_audio_duration", return_value=1), patch.object(narrator, "_concat_audio", side_effect=concat), \
                 patch.object(narrator, "_pad_to_duration", side_effect=pad), patch("content_builder.zh.integrated_chinese.tasks.narration_audio.time.sleep"):
                self.assertEqual(narrator.run(plan, Path(tmp))["status"], "error")
                self.assertEqual(narrator.run(plan, Path(tmp))["status"], "ok")
            self.assertEqual(calls, ["First.", "Second.", "Second."])


class WorkflowTests(unittest.TestCase):
    def test_different_teaching_pages_cannot_reuse_the_same_image(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = root / "slide.webp"
            Image.new("RGB", (1920, 1080), "green").save(image, "WEBP")
            clip = audio(root / "clip.wav")
            data = lesson()
            first = data["video_render_plan"]["explanation"]["segments"][0]
            first["segment_title"] = "First teaching point"
            second = copy.deepcopy(first)
            second["segment_id"] = 2
            second["segment_title"] = "Different teaching point"
            data["video_render_plan"]["explanation"]["segments"].append(second)
            data["explanation_narration_audio"] = {"status": "ok", "audio_file": str(clip)}
            data["teaching_slide_deck"] = {"lesson_id": 101, "lang": "en", "slide_count": 2,
                "render_recipe": {"version": 3, "caption_mode": "external"}, "slides": [{"segment_id": i + 1,
                    "duration_ms": 1000, "image": {"local_path": str(image)}, "audio": {"local_path": str(clip), "source_start_ms": i * 1000},
                    "caption_cues": [{"start_ms": 0, "end_ms": 1000, "text": "Hello"}]} for i in range(2)]}
            report = audit_lesson(data, artifact_root=root, media=True)
            self.assertIn("duplicate_slide_image", {item["code"] for item in report["issues"]})
            second["segment_title"] = first["segment_title"]
            report = audit_lesson(data, artifact_root=root, media=True)
            self.assertNotIn("duplicate_slide_image", {item["code"] for item in report["issues"]})
    def test_adopted_content_resumes_without_llm_and_recovers_missing_narration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "artifacts"
            source = Path(tmp) / "lesson101_data.json"
            atomic_write_json(source, lesson())
            args = argparse.Namespace(from_stage="content", through="narration", input_json=source,
                source=None, lesson=101, lang="en", course_id=1, force=[], images_only=False)
            def target(lesson_data, output_dir):
                clip = audio(root / "output_audio/lesson101/line1.wav")
                return {"lesson_audio_assets": {"items": [{"line_ref": 1, "status": "ready", "local_audio_file": str(clip), "hanzi": "你好！"}]}}
            def narrate(plan, output_dir, lang):
                clip = audio(output_dir / "narration.wav")
                return {"status": "ok", "audio_file": str(clip), "segment_count": 1,
                        "segment_actual_durations": {"1": 1}, "segment_sentences": {"1": ["Say [zh:你好]."]}, "segment_timings": {"1": [0]}}
            with patch("content_builder.zh.integrated_chinese.workflow.preflight"), \
                 patch("content_builder.zh.integrated_chinese.tasks.dialogue_audio.Task4BLessonAudioRenderer.render_sentence_audio_assets", side_effect=target) as target_mock, \
                 patch("content_builder.zh.integrated_chinese.tasks.narration_audio.Task4DExplanationNarrator.run", side_effect=narrate) as narrator_mock, \
                 patch("content_builder.core.llm_providers.LLMFactory.create_provider", side_effect=AssertionError("LLM should not initialize")):
                self.assertEqual(run(args, root)["status"], "draft")
                run(args, root)
                self.assertEqual((target_mock.call_count, narrator_mock.call_count), (1, 1))
                (root / "output_audio/en/lesson101_narration/narration.wav").unlink()
                run(args, root)
                self.assertEqual((target_mock.call_count, narrator_mock.call_count), (1, 2))
                updated = lesson()
                updated["video_render_plan"]["explanation"]["segments"][0]["visual_blocks"][0]["content"]["focus_gloss_en"] = "Hello there!"
                atomic_write_json(source, updated)
                run(args, root)
                self.assertEqual(narrator_mock.call_count, 2)
                final = json.loads((root / "output_json/en/lesson101_data.json").read_text(encoding="utf-8"))
                self.assertEqual(final["video_render_plan"]["explanation"]["segments"][0]["visual_blocks"][0]["content"]["focus_gloss_en"], "Hello there!")

    def test_invalid_content_never_commits_vocabulary_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "artifacts"
            source = Path(tmp) / "input.json"
            data = lesson()
            data["database_items"] = []
            atomic_write_json(source, data)
            args = argparse.Namespace(from_stage="content", through="content", input_json=source,
                source=None, lesson=101, lang="en", course_id=1, force=[], images_only=False)
            with self.assertRaises(ValueError):
                run(args, root)
            self.assertFalse((root / "vocab_memory/global_vocab_memory.json").exists())

    def test_console_routes_chinese_image_refresh_through_verification(self):
        request = build_content_builder_request(pipeline="integrated_chinese", lang="en", lesson_start=101,
            run_stage1=False, stage2_mode="slides_only")
        argv = preview_content_builder(request)["commands"][0]["argv"]
        self.assertIn("content_builder.zh.integrated_chinese.workflow", argv)
        self.assertIn("--images-only", argv)
        self.assertEqual(argv[argv.index("--through") + 1], "verify")
        self.assertNotIn("--force", argv)

    def test_publishing_requires_storage_and_does_not_ignore_upload_failure(self):
        from database.sync_to_db import upload_assets_to_r2
        with patch("database.sync_to_db.get_media_storage", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "configured"):
                upload_assets_to_r2({}, strict=True)
        with tempfile.TemporaryDirectory() as tmp:
            clip = audio(Path(tmp) / "clip.wav")
            data = {"lesson_audio_assets": {"items": [{"local_audio_file": str(clip), "object_key": "zh/audio/clip.wav"}]}}
            from unittest.mock import Mock
            storage = Mock()
            storage.upload_file.side_effect = RuntimeError("storage unavailable")
            with patch("database.sync_to_db.get_media_storage", return_value=storage):
                with self.assertRaisesRegex(RuntimeError, "upload failed"):
                    upload_assets_to_r2(data, strict=True)

    def test_webp_is_uploaded_with_its_actual_media_type(self):
        from database.sync_to_db import upload_assets_to_r2
        from unittest.mock import Mock
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "slide.webp"
            image.write_bytes(b"test-image")
            data = {"teaching_slide_deck": {"slides": [{"image": {"local_path": str(image), "object_key": "zh/slides/en/lesson101/slide.webp"}}]}}
            storage = Mock()
            storage.upload_file.return_value = {"object_key": "zh/slides/en/lesson101/slide.webp"}
            with patch("database.sync_to_db.get_media_storage", return_value=storage):
                upload_assets_to_r2(data, strict=True)
            self.assertEqual(storage.upload_file.call_args.kwargs["content_type"], "image/webp")


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg/ffprobe required")
class MediaIntegrationTests(unittest.TestCase):
    def test_audio_boundary_changes_invalidate_cached_split_and_truncation_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            master = audio(root / "master.wav", 2)
            kwargs = dict(narration_file=master, output_dir=root, lesson_digits="101", lang="en", slide_index=1, force=False)
            first = _split_narration_audio(**kwargs, start_ms=0, duration_ms=700)
            second = _split_narration_audio(**kwargs, start_ms=700, duration_ms=700)
            self.assertNotEqual(first, second)
            self.assertEqual(first, _split_narration_audio(**kwargs, start_ms=0, duration_ms=700))
            with self.assertRaises(ValueError):
                _split_narration_audio(**kwargs, start_ms=1800, duration_ms=1000)

    def test_formal_renderer_failure_is_not_silently_replaced_by_svg(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = lesson()
            master = audio(Path(tmp) / "master.wav", 1)
            data["explanation_narration_audio"] = {"status": "ok", "audio_file": str(master)}
            file = Path(tmp) / "lesson101_data.json"
            atomic_write_json(file, data)
            from content_builder.core.paths import ContentBuilderPaths
            paths = ContentBuilderPaths.from_content_builder_dir(Path(tmp) / "backend/content_builder")
            with patch("content_builder.zh.integrated_chinese.scripts.build_teaching_slide_deck.default_paths", return_value=paths), \
                 patch("content_builder.zh.integrated_chinese.scripts.build_teaching_slide_deck._render_remotion_slides", side_effect=RuntimeError("renderer failed")):
                with self.assertRaisesRegex(RuntimeError, "renderer failed"):
                    build_deck(file, "integrated_chinese", "en")
            self.assertNotIn("teaching_slide_deck", json.loads(file.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
