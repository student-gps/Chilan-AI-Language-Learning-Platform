from pathlib import Path
import sys
import unittest
from copy import deepcopy
import json
import tempfile


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

from content_builder.core.pipeline import get_pipeline
from content_builder.ja.minna_no_nihongo.agent import MinnaNoNihongoAgent
from content_builder.ja.minna_no_nihongo.book_profiles import book1, intermediate, lesson_profile as resolve_lesson_profile
from content_builder.ja.minna_no_nihongo.tasks.content_extractor import MinnaNoNihongoExtractor
from content_builder.ja.minna_no_nihongo.tasks.explanation_composer import (
    DIRECTOR_PLAN_VERSION,
    MinnaNoNihongoExplanationComposer,
)
from content_builder.ja.minna_no_nihongo.tasks.explanation_writer import MinnaNoNihongoExplanationWriter
from content_builder.ja.minna_no_nihongo.scripts.render_lesson_audio import parse_lesson, parse_only
from content_builder.ja.minna_no_nihongo.tasks.grammar_refiner import MinnaNoNihongoGrammarRefiner
from content_builder.ja.minna_no_nihongo.tasks.lesson_audio import MinnaNoNihongoLessonAudioRenderer
from content_builder.ja.minna_no_nihongo.tasks.lesson_normalizer import MinnaNoNihongoLessonNormalizer
from content_builder.ja.minna_no_nihongo.tasks.practice_generator import MinnaNoNihongoPracticeGenerator
from content_builder.ja.minna_no_nihongo.tasks.reading_annotator import JapaneseReadingAnnotator
from content_builder.ja.minna_no_nihongo.tasks.reading_auditor import MinnaNoNihongoReadingAuditor
from content_builder.ja.minna_no_nihongo.tasks.render_plan_builder import (
    RENDER_PLAN_VERSION,
    MinnaNoNihongoRenderPlanBuilder,
)
from content_builder.ja.minna_no_nihongo.tasks.speaker_resolver import MinnaNoNihongoSpeakerResolver
from content_builder.ja.minna_no_nihongo.tasks.vocab_memory import MinnaNoNihongoVocabMemory


class FakeSpeakerAuditProvider:
    def generate_structured_json(self, prompt, file_path=None):
        return {
            "speaker_corrections": [
                {
                    "line_ref": 3,
                    "speaker": "山田",
                    "reason": "line continues Yamada's introduction",
                }
            ]
        }


class FakeSequenceProvider:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def generate_structured_json(self, prompt, file_path=None, file_obj=None):
        self.calls.append({"prompt": prompt, "file_path": file_path, "file_obj": file_obj})
        if not self.responses:
            return {}
        return self.responses.pop(0)


class FakeExplanationProvider:
    def generate_structured_json(self, prompt, file_path=None, file_obj=None):
        return {
            "global_config": {},
            "segments": [
                {
                    "segment_type": "recap",
                    "source": {"kind": "lesson_summary", "indexes": []},
                    "segment_title": "本课总结",
                    "teaching_goal": "回顾重点。",
                    "highlight_words": [
                        {"word": "学生", "pinyin": "がくせい", "translation": "学生"}
                    ],
                    "narration": {"subtitle_zh": "最后回顾 [ja:学生]。"},
                    "estimated_duration_seconds": 18,
                }
            ],
        }


class MinnaNoNihongoPipelineTest(unittest.TestCase):
    def test_pipeline_registry_aliases(self):
        pipeline = get_pipeline("minna_no_nihongo")
        self.assertEqual(pipeline.pipeline_id, "minna_no_nihongo")
        self.assertEqual(pipeline.target_language, "ja")
        self.assertIs(get_pipeline("mnn"), pipeline)

    def test_placeholder_payload_validates(self):
        agent = MinnaNoNihongoAgent(provider=None, memory_dir=Path("tmp"))
        payload = agent.generate_content("lesson001.pdf", lesson_id=1)
        self.assertEqual(payload["pipeline_id"], "minna_no_nihongo")
        self.assertEqual(payload["target_language"], "ja")
        self.assertTrue(payload["course_content"]["sentence_patterns"])
        self.assertTrue(payload["teaching_materials"]["lesson_flow"])
        self.assertTrue(payload["teaching_materials"]["pronunciation_notes"])
        self.assertTrue(payload["video_render_plan"]["explanation"]["segments"])
        self.assertTrue(payload["lesson_audio_assets"]["items"])
        self.assertTrue(payload["course_content"]["sentence_patterns"][0]["reading"])
        self.assertTrue(payload["course_content"]["sentence_patterns"][0]["tokens"])
        self.assertTrue(
            any(
                token["surface"] == "学生" and token["annotation"] == "がくせい"
                for token in payload["course_content"]["sentence_patterns"][0]["tokens"]
            )
        )
        self.assertTrue(payload["database_items"])

    def test_lesson051_uses_intermediate_profile_without_changing_elementary(self):
        elementary = resolve_lesson_profile(50)
        intermediate_profile = resolve_lesson_profile(51)

        self.assertEqual(elementary.pedagogy_profile, "elementary_sentence_pattern_dialogue")
        self.assertEqual(elementary.content_type, "sentence_pattern_dialogue")
        self.assertEqual(intermediate_profile.pedagogy_profile, "intermediate_read_write_speak_listen_grammar")
        self.assertEqual(intermediate_profile.content_type, "integrated_skills_intermediate")
        self.assertEqual(intermediate_profile.source_lesson, 51)
        self.assertEqual(intermediate_profile.source_sections, intermediate.SOURCE_SECTIONS)

    def test_intermediate_placeholder_golden_and_validation_lessons(self):
        agent = MinnaNoNihongoAgent(provider=None, memory_dir=Path("tmp"), render_lesson_audio=False)

        for lesson_id in (51, 52, 63):
            with self.subTest(lesson_id=lesson_id):
                payload = agent.generate_content(f"lesson{lesson_id:03d}.pdf", lesson_id=lesson_id)
                metadata = payload["lesson_metadata"]

                self.assertEqual(metadata["lesson_slug"], f"lesson{lesson_id:03d}")
                self.assertEqual(metadata["title"], f"第{lesson_id}課")
                self.assertEqual(metadata["title_localized"], f"第{lesson_id}课")
                self.assertEqual(metadata["topic_title"], "お願いがあるんですが")
                self.assertTrue(metadata["section_titles"])
                self.assertEqual(metadata["content_type"], "integrated_skills_intermediate")
                self.assertEqual(metadata["source"]["textbook_ja"], "みんなの日本語 中級")
                self.assertEqual(metadata["source"]["source_lesson"], lesson_id)
                self.assertEqual(metadata["source"]["source_sections"], list(intermediate.SOURCE_SECTIONS))
                self.assertTrue(payload["course_content"]["sentence_patterns"])
                self.assertTrue(payload["course_content"]["example_sentences"])
                self.assertTrue(payload["course_content"]["dialogue"]["lines"])

    def test_intermediate_vocabulary_policy_moves_review_words_to_lexical_notes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = MinnaNoNihongoAgent(provider=None, memory_dir=Path(tmpdir), render_lesson_audio=False)
            agent.vocab_memory.save_lesson_vocabulary({
                "lesson_metadata": {"lesson_id": 1, "lesson_slug": "lesson001", "course_id": 201},
                "course_content": {
                    "vocabulary": [
                        {
                            "term": "返す",
                            "annotation": "かえす",
                            "translation": "归还",
                        }
                    ]
                },
            })

            payload = agent.generate_content("lesson051.pdf", lesson_id=51)
            content = payload["course_content"]

            self.assertEqual([item["term"] for item in content["vocabulary"]], ["文章"])
            self.assertEqual(content["lexical_notes"][0]["term"], "返す")
            self.assertEqual(content["lexical_notes"][0]["learning_role"], "context_only")
            self.assertFalse(content["lexical_notes"][0]["quiz_eligible"])
            vocab_quiz_terms = {
                item.get("original_text")
                for item in payload["database_items"]
                if ((item.get("metadata") or {}).get("context") or {}).get("source") == "vocabulary"
            }
            self.assertNotIn("返す", vocab_quiz_terms)
            self.assertIn("文章", vocab_quiz_terms)

    def test_elementary_metadata_keeps_number_and_uses_dialogue_title_as_topic(self):
        payload = MinnaNoNihongoLessonNormalizer().run(
            {
                "lesson_metadata": {
                    "title": "第1課",
                    "title_localized": "第1课",
                },
                "course_content": {
                    "sentence_patterns": [],
                    "example_sentences": [],
                    "dialogue": {
                        "title": "はじめまして",
                        "title_localized": "初次见面",
                        "lines": [
                            {
                                "speaker": "ミラー",
                                "text": "はじめまして。",
                                "reading": "はじめまして。",
                                "translation": "初次见面。",
                            }
                        ],
                    },
                    "vocabulary": [],
                    "display_only_vocabulary": [],
                    "grammar_sections": [],
                },
            },
            lesson_id=1,
            source_pdf=Path("lesson001.pdf"),
            lesson_pdf=Path("lesson001.pdf"),
            course_id=201,
        )
        metadata = payload["lesson_metadata"]

        self.assertEqual(metadata["title"], "第1課")
        self.assertEqual(metadata["topic_title"], "はじめまして")
        self.assertEqual(metadata["topic_title_localized"], "初次见面")
        self.assertIn(
            {"section": "会話", "title": "はじめまして", "title_localized": "初次见面"},
            metadata["section_titles"],
        )

    def test_validator_rejects_missing_sentence_reading(self):
        agent = MinnaNoNihongoAgent(provider=None, memory_dir=Path("tmp"))
        payload = agent.generate_content("lesson001.pdf", lesson_id=1)
        broken_payload = deepcopy(payload)
        broken_payload["course_content"]["sentence_patterns"][0]["reading"] = ""

        with self.assertRaisesRegex(ValueError, "reading missing"):
            agent.validator.validate(broken_payload)

    def test_validator_rejects_incomplete_grammar_section(self):
        agent = MinnaNoNihongoAgent(provider=None, memory_dir=Path("tmp"))
        payload = agent.generate_content("lesson001.pdf", lesson_id=1)
        broken_payload = deepcopy(payload)
        broken_payload["course_content"]["grammar_sections"][0]["explanation"] = ""

        with self.assertRaisesRegex(ValueError, "grammar_sections\\[1\\]\\.explanation missing"):
            agent.validator.validate(broken_payload)

    def test_validator_rejects_simplified_chinese_chars_in_japanese_text(self):
        agent = MinnaNoNihongoAgent(provider=None, memory_dir=Path("tmp"))
        payload = agent.generate_content("lesson001.pdf", lesson_id=1)
        broken_payload = deepcopy(payload)
        broken_payload["course_content"]["dialogue"]["lines"][0]["text"] = "よろしくお愿いします。"

        with self.assertRaisesRegex(ValueError, "simplified Chinese char"):
            agent.validator.validate(broken_payload)

    def test_book1_voice_map_resolves_known_speakers(self):
        renderer = MinnaNoNihongoLessonAudioRenderer()
        self.assertEqual(
            renderer.resolve_voice("マイク・ミラー", source_section="dialogue"),
            "ja-JP-KeitaNeural",
        )
        self.assertEqual(
            renderer.resolve_voice("佐藤さん", source_section="dialogue"),
            "ja-JP-NanamiNeural",
        )
        self.assertEqual(
            renderer.resolve_voice("テレーザ・サントス", source_section="dialogue"),
            "ja-JP-AoiNeural",
        )

    def test_intermediate_voice_map_resolves_lesson051_speakers(self):
        renderer = MinnaNoNihongoLessonAudioRenderer()
        self.assertEqual(
            renderer.resolve_voice("タワポン", source_section="dialogue", lesson_id=51),
            "ja-JP-NaokiNeural",
        )
        self.assertEqual(
            renderer.resolve_voice("佐野さん", source_section="dialogue", lesson_id=51),
            "ja-JP-MayuNeural",
        )
        self.assertEqual(
            renderer.resolve_voice("ナレーション", source_section="dialogue", lesson_id=51),
            "ja-JP-NanamiNeural",
        )
        self.assertEqual(
            renderer.resolve_voice("松本 正", source_section="dialogue", lesson_id=51),
            "ja-JP-DaichiNeural",
        )

    def test_intermediate_unknown_speakers_get_stable_lesson_voice_map(self):
        renderer = MinnaNoNihongoLessonAudioRenderer()
        items = [
            {"source_section": "dialogue", "speaker": "田中"},
            {"source_section": "dialogue", "speaker": "鈴木"},
            {"source_section": "dialogue", "speaker": "田中さん"},
        ]
        voice_map = renderer._lesson_role_voice_map(items, lesson_id=52)

        self.assertEqual(voice_map["田中"], "ja-JP-KeitaNeural")
        self.assertEqual(voice_map["鈴木"], "ja-JP-NanamiNeural")
        self.assertEqual(
            renderer.resolve_voice("田中さん", source_section="dialogue", lesson_id=52, lesson_role_voice_map=voice_map),
            "ja-JP-KeitaNeural",
        )

    def test_render_lesson_audio_cli_parsers(self):
        self.assertEqual(parse_lesson("lesson001"), 1)
        self.assertEqual(parse_lesson("002"), 2)
        self.assertEqual(parse_only(["dialogue_003, pattern_001", "example_002"]), {
            "dialogue_003",
            "pattern_001",
            "example_002",
        })

    def test_speaker_resolver_repairs_leading_addressee(self):
        resolver = MinnaNoNihongoSpeakerResolver()
        payload = {
            "course_content": {
                "dialogue": {
                    "lines": [
                        {"line_ref": 1, "speaker": "佐藤", "text": "おはようございます。"},
                        {"line_ref": 2, "speaker": "山田", "text": "おはようございます。"},
                        {"line_ref": 3, "speaker": "佐藤", "text": "佐藤さん、こちらはマイク・ミラーさんです。"},
                    ]
                }
            }
        }

        repaired = resolver.run(payload)
        self.assertEqual(repaired["course_content"]["dialogue"]["lines"][2]["speaker"], "山田")
        diagnostics = repaired["pipeline_diagnostics"]["speaker_resolution"]
        self.assertTrue(diagnostics["deterministic_corrections"])

    def test_speaker_resolver_applies_llm_audit(self):
        resolver = MinnaNoNihongoSpeakerResolver()
        payload = {
            "course_content": {
                "dialogue": {
                    "lines": [
                        {"line_ref": 1, "speaker": "佐藤", "text": "おはようございます。"},
                        {"line_ref": 2, "speaker": "山田", "text": "おはようございます。"},
                        {"line_ref": 3, "speaker": "佐藤", "text": "こちらはマイク・ミラーさんです。"},
                    ]
                }
            }
        }

        repaired = resolver.run(payload, llm_provider=FakeSpeakerAuditProvider(), lesson_id=1)
        self.assertEqual(repaired["course_content"]["dialogue"]["lines"][2]["speaker"], "山田")
        diagnostics = repaired["pipeline_diagnostics"]["speaker_resolution"]
        self.assertTrue(diagnostics["llm_corrections"])

    def test_content_extractor_splits_task1_and_reuses_pdf_object(self):
        provider = FakeSequenceProvider([
            {
                "lesson_metadata": {"title": "第1課", "title_localized": "第1课"},
                "course_content": {
                    "sentence_patterns": [{"text": "わたしは学生です。", "translation": "我是学生。"}],
                    "example_sentences": [{"text": "あの人は先生です。", "translation": "那个人是老师。"}],
                    "dialogue": {
                        "title": "はじめまして",
                        "title_localized": "初次见面",
                        "lines": [{"speaker": "ミラー", "text": "はじめまして。", "translation": "初次见面。"}],
                    },
                },
            },
            {
                "course_content": {
                    "vocabulary": [{"term": "学生", "annotation": "がくせい", "translation": "学生"}],
                    "display_only_vocabulary": [{"term": "ミラー", "category": "person_name"}],
                }
            },
            {
                "course_content": {
                    "grammar_sections": [{"title": "N1 は N2 です", "explanation": "判断句。"}],
                }
            },
            {
                "course_content": {
                    "practice_source": [{"section": "練習A", "pattern": "N1 は N2 です"}],
                },
                "practice_items": [{"question_type": "CN_TO_JA", "prompt": "我是学生。", "standard_answers": ["わたしは学生です。"]}],
            },
        ])

        payload = MinnaNoNihongoExtractor(provider).run(
            lesson_pdf=Path("lesson001.pdf"),
            source_pdf=Path("lesson001.pdf"),
            lesson_id=1,
            file_obj={"shared": "pdf"},
        )

        self.assertEqual(len(provider.calls), 4)
        self.assertTrue(all(call["file_obj"] == {"shared": "pdf"} for call in provider.calls))
        self.assertTrue(all(call["file_path"] is None for call in provider.calls))
        self.assertEqual(payload["course_content"]["sentence_patterns"][0]["text"], "わたしは学生です。")
        self.assertEqual(payload["course_content"]["vocabulary"][0]["term"], "学生")
        self.assertEqual(payload["course_content"]["grammar_sections"][0]["title"], "N1 は N2 です")
        self.assertEqual(payload["course_content"]["practice_source"][0]["section"], "練習A")
        self.assertTrue(payload["pipeline_diagnostics"]["task1_extraction"]["used_shared_pdf"])

    def test_content_extractor_splits_combined_example_question_answers(self):
        provider = FakeSequenceProvider([
            {
                "course_content": {
                    "sentence_patterns": [],
                    "example_sentences": [
                        {
                            "text": "グプタさんは会社員ですか。……はい、会社員です。カリナさんも会社員ですか。……いいえ。[カリナさんは]学生です。",
                            "translation": "古普塔先生是公司职员吗？是，是公司职员。卡莉娜小姐也是公司职员吗？不是。[卡莉娜小姐]是学生。",
                        }
                    ],
                    "dialogue": {"lines": []},
                }
            },
            {"course_content": {}},
            {"course_content": {}},
            {"course_content": {}},
        ])

        payload = MinnaNoNihongoExtractor(provider).run(
            lesson_pdf=Path("lesson001.pdf"),
            source_pdf=Path("lesson001.pdf"),
            lesson_id=1,
            file_obj={"shared": "pdf"},
        )

        examples = payload["course_content"]["example_sentences"]
        self.assertEqual(
            [item["text"] for item in examples],
            [
                "グプタさんは会社員ですか。",
                "はい、会社員です。",
                "カリナさんも会社員ですか。",
                "いいえ。",
                "[カリナさんは]学生です。",
            ],
        )
        self.assertEqual([item["line_ref"] for item in examples], [1, 2, 3, 4, 5])
        self.assertTrue(all(not item.get("tokens") for item in examples))

    def test_content_extractor_prompt_requires_fine_grained_examples(self):
        extractor = MinnaNoNihongoExtractor(FakeSequenceProvider([]))
        prompt = extractor._build_core_text_prompt(
            lesson_profile=book1.lesson_profile(1),
            support_language="zh",
            course_id=201,
        )

        self.assertIn("每个 example_sentences item 只放一个独立句子或一个短答句", prompt)
        self.assertIn("不要把“问题 + 回答”合并成一条", prompt)

    def test_content_extractor_prompt_uses_intermediate_sections(self):
        extractor = MinnaNoNihongoExtractor(FakeSequenceProvider([]))
        prompt = extractor._build_core_text_prompt(
            lesson_profile=resolve_lesson_profile(51),
            support_language="zh",
            course_id=201,
        )

        self.assertIn("読む・書く", prompt)
        self.assertIn("話す・聞く", prompt)
        self.assertIn("文法・練習", prompt)
        self.assertIn("topic_title", prompt)
        self.assertIn("不要强行寻找旧版「文型」栏", prompt)

    def test_grammar_refiner_discovers_titles_and_repairs_sections(self):
        provider = FakeSequenceProvider([
            {
                "grammar_titles": [
                    {"order": 1, "title": "N1 は N2 です", "source_hint": "文型"}
                ]
            },
            {
                "grammar_sections": [
                    {
                        "title": "N1 は N2 です",
                        "explanation": "身份、职业或属性的判断句。",
                        "patterns": [{"text": "N1 は N2 です", "translation": "N1 是 N2。"}],
                        "examples": [{"text": "わたしは学生です。", "reading": "わたしはがくせいです。"}],
                    }
                ]
            },
        ])
        payload = {
            "course_content": {
                "sentence_patterns": [{"text": "わたしは学生です。"}],
                "grammar_sections": [{"title": "old", "explanation": ""}],
            }
        }

        refined = MinnaNoNihongoGrammarRefiner().run(
            payload,
            llm_provider=provider,
            lesson_pdf=Path("lesson001.pdf"),
            lesson_id=1,
        )

        sections = refined["course_content"]["grammar_sections"]
        self.assertEqual(sections[0]["title"], "N1 は N2 です")
        self.assertEqual(len(provider.calls), 2)
        self.assertTrue(refined["pipeline_diagnostics"]["grammar_refinement"]["used_llm"])

    def test_grammar_refiner_reuses_uploaded_pdf_object(self):
        provider = FakeSequenceProvider([
            {"grammar_titles": [{"order": 1, "title": "N1 は N2 です"}]},
            {
                "grammar_sections": [
                    {
                        "title": "N1 は N2 です",
                        "explanation": "身份、职业或属性的判断句。",
                        "patterns": [{"text": "N1 は N2 です"}],
                        "examples": [{"text": "わたしは学生です。"}],
                    }
                ]
            },
        ])

        MinnaNoNihongoGrammarRefiner().run(
            {"course_content": {"sentence_patterns": [{"text": "わたしは学生です。"}]}},
            llm_provider=provider,
            lesson_pdf=Path("lesson001.pdf"),
            lesson_file_obj={"shared": "pdf"},
            lesson_id=1,
        )

        self.assertEqual(len(provider.calls), 2)
        self.assertTrue(all(call["file_obj"] == {"shared": "pdf"} for call in provider.calls))
        self.assertTrue(all(call["file_path"] is None for call in provider.calls))

    def test_reading_auditor_repairs_particles_deterministically(self):
        payload = {
            "course_content": {
                "vocabulary": [],
                "sentence_patterns": [
                    {
                        "pattern_id": 1,
                        "text": "これは本です。",
                        "reading": "これはほんです。",
                        "tokens": [
                            {"surface": "これ", "annotation": "これ"},
                            {"surface": "は", "annotation": "は"},
                            {"surface": "本", "annotation": ""},
                            {"surface": "です", "annotation": "です"},
                            {"surface": "。", "annotation": ""},
                        ],
                    }
                ],
            }
        }

        audited = MinnaNoNihongoReadingAuditor().run(payload)
        tokens = audited["course_content"]["sentence_patterns"][0]["tokens"]
        self.assertEqual(tokens[1]["annotation"], "わ")
        self.assertTrue(audited["pipeline_diagnostics"]["reading_audit"]["deterministic_corrections"])

    def test_reading_annotator_synthesizes_sentence_reading_from_tokens(self):
        annotator = JapaneseReadingAnnotator()

        lines = annotator.normalize_lines(
            [
                {
                    "text": "これは本です。",
                    "tokens": [
                        {"surface": "これ", "annotation": "これ"},
                        {"surface": "は", "annotation": "わ"},
                        {"surface": "本", "annotation": "ほん"},
                        {"surface": "です", "annotation": "です"},
                        {"surface": "。", "annotation": ""},
                    ],
                }
            ],
            vocabulary=[],
        )

        self.assertEqual(lines[0]["reading"], "これはほんです。")

    def test_reading_annotator_merges_long_vocab_tokens(self):
        annotator = JapaneseReadingAnnotator()

        lines = annotator.normalize_lines(
            [
                {
                    "text": "時計売り場はここです。",
                    "tokens": [
                        {"surface": "時", "annotation": "と"},
                        {"surface": "計", "annotation": "けい"},
                        {"surface": "売り", "annotation": "うり"},
                        {"surface": "場", "annotation": "ば"},
                        {"surface": "は", "annotation": "わ"},
                        {"surface": "ここ", "annotation": "ここ"},
                        {"surface": "です", "annotation": "です"},
                        {"surface": "。", "annotation": ""},
                    ],
                }
            ],
            vocabulary=[
                {"term": "時計", "annotation": "とけい", "translation": "钟表"},
                {"term": "売り場", "annotation": "うりば", "translation": "柜台"},
            ],
        )

        tokens = lines[0]["tokens"]
        self.assertEqual([token["surface"] for token in tokens[:2]], ["時計", "売り場"])
        self.assertEqual(tokens[0]["annotation"], "とけい")
        self.assertTrue(tokens[0]["highlight"])

    def test_reading_annotator_merges_display_only_vocab_without_highlight(self):
        annotator = JapaneseReadingAnnotator()

        lines = annotator.normalize_lines(
            [
                {
                    "text": "ここは新大阪です。",
                    "tokens": [
                        {"surface": "ここ", "annotation": "ここ"},
                        {"surface": "は", "annotation": "わ"},
                        {"surface": "新", "annotation": "しん"},
                        {"surface": "大", "annotation": "おお"},
                        {"surface": "阪", "annotation": "さか"},
                        {"surface": "です", "annotation": "です"},
                        {"surface": "。", "annotation": ""},
                    ],
                }
            ],
            vocabulary=[{"term": "ここ", "annotation": "ここ", "translation": "这里"}],
            merge_vocabulary=[
                {"term": "ここ", "annotation": "ここ", "translation": "这里"},
                {"term": "新大阪", "annotation": "しんおおさか", "category": "place_name"},
            ],
        )

        tokens = lines[0]["tokens"]
        self.assertTrue(any(token["surface"] == "ここ" and token["highlight"] for token in tokens))
        self.assertTrue(
            any(
                token["surface"] == "新大阪"
                and token["annotation"] == "しんおおさか"
                and not token["highlight"]
                for token in tokens
            )
        )

    def test_reading_annotator_merges_vocabulary_reading_alias(self):
        annotator = JapaneseReadingAnnotator()

        lines = annotator.normalize_lines(
            [
                {
                    "text": "わたしは学生です。",
                    "tokens": [
                        {"surface": "わ", "annotation": "わ"},
                        {"surface": "た", "annotation": "た"},
                        {"surface": "し", "annotation": "し"},
                        {"surface": "は", "annotation": "わ"},
                        {"surface": "学生", "annotation": "がくせい"},
                        {"surface": "で", "annotation": "で"},
                        {"surface": "す", "annotation": "す"},
                        {"surface": "。", "annotation": ""},
                    ],
                }
            ],
            vocabulary=[
                {"term": "私", "annotation": "わたし", "translation": "我"},
                {"term": "学生", "annotation": "がくせい", "translation": "学生"},
            ],
        )

        tokens = lines[0]["tokens"]
        self.assertEqual([token["surface"] for token in tokens], ["わたし", "は", "学生", "です", "。"])
        self.assertTrue(tokens[0]["highlight"])
        self.assertFalse(tokens[3]["highlight"])

    def test_reading_annotator_merges_common_kana_expressions(self):
        annotator = JapaneseReadingAnnotator()

        lines = annotator.normalize_lines(
            [
                {
                    "text": "ありません。ください。",
                    "tokens": [
                        {"surface": "あ", "annotation": "あ"},
                        {"surface": "り", "annotation": "り"},
                        {"surface": "ま", "annotation": "ま"},
                        {"surface": "せ", "annotation": "せ"},
                        {"surface": "ん", "annotation": "ん"},
                        {"surface": "。", "annotation": ""},
                        {"surface": "く", "annotation": "く"},
                        {"surface": "だ", "annotation": "だ"},
                        {"surface": "さ", "annotation": "さ"},
                        {"surface": "い", "annotation": "い"},
                        {"surface": "。", "annotation": ""},
                    ],
                }
            ],
            vocabulary=[],
        )

        tokens = lines[0]["tokens"]
        self.assertEqual([token["surface"] for token in tokens], ["ありません", "。", "ください", "。"])
        self.assertFalse(tokens[0]["highlight"])
        self.assertEqual(tokens[2]["annotation"], "ください")

    def test_reading_annotator_merges_basic_contractions_and_polite_expressions(self):
        annotator = JapaneseReadingAnnotator()

        lines = annotator.normalize_lines(
            [
                {
                    "text": "学生じゃありません。こちらこそよろしくお願いします。",
                    "tokens": [
                        {"surface": "学生", "annotation": "がくせい"},
                        {"surface": "じ", "annotation": "じ"},
                        {"surface": "ゃ", "annotation": "ゃ"},
                        {"surface": "ありません", "annotation": "ありません"},
                        {"surface": "。", "annotation": ""},
                        {"surface": "こ", "annotation": "こ"},
                        {"surface": "ち", "annotation": "ち"},
                        {"surface": "ら", "annotation": "ら"},
                        {"surface": "こ", "annotation": "こ"},
                        {"surface": "そ", "annotation": "そ"},
                        {"surface": "よ", "annotation": "よ"},
                        {"surface": "ろ", "annotation": "ろ"},
                        {"surface": "し", "annotation": "し"},
                        {"surface": "く", "annotation": "く"},
                        {"surface": "お", "annotation": "お"},
                        {"surface": "願", "annotation": "ねが"},
                        {"surface": "い", "annotation": "い"},
                        {"surface": "し", "annotation": "し"},
                        {"surface": "ます", "annotation": "ます"},
                        {"surface": "。", "annotation": ""},
                    ],
                }
            ],
            vocabulary=[],
        )

        tokens = lines[0]["tokens"]
        self.assertEqual(
            [token["surface"] for token in tokens],
            ["学生", "じゃ", "ありません", "。", "こちらこそ", "よろしくお願いします", "。"],
        )
        self.assertEqual(tokens[1]["annotation"], "じゃ")
        self.assertEqual(tokens[5]["annotation"], "よろしくおねがいします")

    def test_reading_annotator_merges_vocab_terms_with_spaces_and_tilde(self):
        annotator = JapaneseReadingAnnotator()

        lines = annotator.normalize_lines(
            [
                {
                    "text": "アメリカから来ました。どうぞよろしく。",
                    "tokens": [
                        {"surface": "アメリカ", "annotation": "アメリカ"},
                        {"surface": "か", "annotation": "か"},
                        {"surface": "ら", "annotation": "ら"},
                        {"surface": "来", "annotation": "き"},
                        {"surface": "ました", "annotation": "ました"},
                        {"surface": "。", "annotation": ""},
                        {"surface": "ど", "annotation": "ど"},
                        {"surface": "う", "annotation": "う"},
                        {"surface": "ぞ", "annotation": "ぞ"},
                        {"surface": "よ", "annotation": "よ"},
                        {"surface": "ろ", "annotation": "ろ"},
                        {"surface": "し", "annotation": "し"},
                        {"surface": "く", "annotation": "く"},
                        {"surface": "。", "annotation": ""},
                    ],
                }
            ],
            vocabulary=[
                {"term": "〜から来ました", "annotation": "〜からきました", "translation": "来自……"},
                {"term": "どうぞ よろしく", "annotation": "どうぞよろしく", "translation": "请多关照"},
            ],
        )

        tokens = lines[0]["tokens"]
        self.assertIn("から来ました", [token["surface"] for token in tokens])
        self.assertIn("どうぞよろしく", [token["surface"] for token in tokens])

    def test_reading_annotator_merges_display_names_with_middle_dot(self):
        annotator = JapaneseReadingAnnotator()

        lines = annotator.normalize_lines(
            [
                {
                    "text": "マイク・ミラーです。",
                    "tokens": [
                        {"surface": "マ", "annotation": "マ"},
                        {"surface": "イ", "annotation": "イ"},
                        {"surface": "ク", "annotation": "ク"},
                        {"surface": "・", "annotation": ""},
                        {"surface": "ミラー", "annotation": "ミラー"},
                        {"surface": "です", "annotation": "です"},
                        {"surface": "。", "annotation": ""},
                    ],
                }
            ],
            vocabulary=[],
            merge_vocabulary=[{"term": "マイク・ミラー", "annotation": "マイク・ミラー"}],
        )

        tokens = lines[0]["tokens"]
        self.assertEqual([token["surface"] for token in tokens], ["マイク・ミラー", "です", "。"])
        self.assertFalse(tokens[0]["highlight"])

    def test_reading_annotator_tokenize_merges_across_spaces_and_middle_dot(self):
        annotator = JapaneseReadingAnnotator()

        tokens = annotator.tokenize_text(
            "マイク・ミラーです。どうぞ よろしく。",
            vocabulary=[
                {"term": "どうぞよろしく", "annotation": "どうぞよろしく"},
            ],
            merge_vocabulary=[
                {"term": "マイク・ミラー", "annotation": "マイク・ミラー"},
                {"term": "どうぞ よろしく", "annotation": "どうぞよろしく"},
            ],
        )

        self.assertIn("マイク・ミラー", [token["surface"] for token in tokens])
        self.assertIn("どうぞよろしく", [token["surface"] for token in tokens])

    def test_reading_annotator_uses_morphological_fallback_for_unknown_segments(self):
        annotator = JapaneseReadingAnnotator(
            morphological_tokenizer=lambda text: [
                {"surface": "行って", "annotation": "いって", "pos": "動詞"},
                {"surface": "き", "annotation": "き", "pos": "動詞"},
            ] if text == "行ってき" else []
        )

        tokens = annotator.tokenize_text("行ってきます。", vocabulary=[])

        self.assertEqual([token["surface"] for token in tokens], ["行って", "き", "ます", "。"])
        self.assertEqual(tokens[0]["annotation"], "いって")

    def test_reading_annotator_forces_particle_readings_after_morphology(self):
        annotator = JapaneseReadingAnnotator(
            morphological_tokenizer=lambda text: [
                {"surface": "私", "annotation": "わたし", "pos": "名詞"},
                {"surface": "は", "annotation": "は", "pos": "助詞"},
                {"surface": "学校", "annotation": "がっこう", "pos": "名詞"},
                {"surface": "へ", "annotation": "へ", "pos": "助詞"},
                {"surface": "本", "annotation": "ほん", "pos": "名詞"},
                {"surface": "を", "annotation": "を", "pos": "助詞"},
            ]
        )

        tokens = annotator.tokenize_text("私は学校へ本を", vocabulary=[])
        readings = {token["surface"]: token["annotation"] for token in tokens}

        self.assertEqual(readings["は"], "わ")
        self.assertEqual(readings["へ"], "え")
        self.assertEqual(readings["を"], "お")

    def test_reading_annotator_keeps_vocabulary_longest_match_before_morphology(self):
        annotator = JapaneseReadingAnnotator(
            morphological_tokenizer=lambda text: [
                {"surface": char, "annotation": char}
                for char in text
            ]
        )

        tokens = annotator.tokenize_text(
            "ここは新大阪です。",
            vocabulary=[{"term": "ここ", "annotation": "ここ"}],
            merge_vocabulary=[
                {"term": "ここ", "annotation": "ここ"},
                {"term": "新大阪", "annotation": "しんおおさか"},
            ],
        )

        self.assertIn("新大阪", [token["surface"] for token in tokens])
        self.assertTrue(any(token["surface"] == "ここ" and token["highlight"] for token in tokens))

    def test_reading_annotator_merges_number_counter_tokens(self):
        annotator = JapaneseReadingAnnotator()

        lines = annotator.normalize_lines(
            [
                {
                    "text": "地下1階です。",
                    "tokens": [
                        {"surface": "地下", "annotation": "ちか"},
                        {"surface": "1", "annotation": "いち"},
                        {"surface": "階", "annotation": "かい"},
                        {"surface": "です", "annotation": "です"},
                        {"surface": "。", "annotation": ""},
                    ],
                }
            ],
            vocabulary=[],
        )

        tokens = lines[0]["tokens"]
        self.assertEqual([token["surface"] for token in tokens], ["地下", "1階", "です", "。"])
        self.assertEqual(tokens[1]["annotation"], "いっかい")
        self.assertEqual(lines[0]["reading"], "ちかいっかいです。")

    def test_reading_annotator_merges_number_counter_during_tokenize_fallback(self):
        annotator = JapaneseReadingAnnotator()

        lines = annotator.normalize_lines(
            [{"text": "1階です。"}],
            vocabulary=[],
        )

        tokens = lines[0]["tokens"]
        self.assertEqual(tokens[0]["surface"], "1階")
        self.assertEqual(tokens[0]["annotation"], "いっかい")

    def test_reading_annotator_merges_ordinal_counter_tokens(self):
        annotator = JapaneseReadingAnnotator()

        lines = annotator.normalize_lines(
            [
                {
                    "text": "第3課です。",
                    "tokens": [
                        {"surface": "第", "annotation": "だい"},
                        {"surface": "3", "annotation": "さん"},
                        {"surface": "課", "annotation": "か"},
                        {"surface": "です", "annotation": "です"},
                        {"surface": "。", "annotation": ""},
                    ],
                }
            ],
            vocabulary=[],
        )

        tokens = lines[0]["tokens"]
        self.assertEqual([token["surface"] for token in tokens], ["第3課", "です", "。"])
        self.assertEqual(tokens[0]["annotation"], "だいさんか")

    def test_reading_auditor_synthesizes_missing_sentence_reading(self):
        payload = {
            "course_content": {
                "vocabulary": [{"term": "本", "annotation": "ほん", "translation": "书"}],
                "example_sentences": [
                    {
                        "line_ref": 1,
                        "text": "これは本です。",
                        "reading": "",
                        "tokens": [
                            {"surface": "これ", "annotation": "これ"},
                            {"surface": "は", "annotation": "わ"},
                            {"surface": "本", "annotation": "ほん"},
                            {"surface": "です", "annotation": "です"},
                            {"surface": "。", "annotation": ""},
                        ],
                    }
                ],
            }
        }

        audited = MinnaNoNihongoReadingAuditor().run(payload)

        self.assertEqual(audited["course_content"]["example_sentences"][0]["reading"], "これはほんです。")

    def test_reading_auditor_infers_missing_token_reading_from_sentence_reading(self):
        payload = {
            "course_content": {
                "vocabulary": [],
                "example_sentences": [
                    {
                        "line_ref": 1,
                        "text": "これは辞書です。",
                        "reading": "これはじしょです。",
                        "tokens": [
                            {"surface": "これ", "annotation": "これ"},
                            {"surface": "は", "annotation": "わ"},
                            {"surface": "辞書", "annotation": ""},
                            {"surface": "です", "annotation": "です"},
                            {"surface": "。", "annotation": ""},
                        ],
                    }
                ],
            }
        }

        audited = MinnaNoNihongoReadingAuditor().run(payload)
        tokens = audited["course_content"]["example_sentences"][0]["tokens"]

        self.assertEqual(tokens[2]["annotation"], "じしょ")

    def test_reading_auditor_retokenizes_when_existing_tokens_leave_missing_readings(self):
        payload = {
            "course_content": {
                "vocabulary": [{"term": "辞書", "annotation": "じしょ", "translation": "词典"}],
                "example_sentences": [
                    {
                        "line_ref": 1,
                        "text": "これは辞書です。",
                        "reading": "これはじしょです。",
                        "tokens": [
                            {"surface": "これは辞書です", "annotation": ""},
                            {"surface": "。", "annotation": ""},
                        ],
                    }
                ],
            }
        }

        audited = MinnaNoNihongoReadingAuditor().run(payload)
        tokens = audited["course_content"]["example_sentences"][0]["tokens"]

        self.assertTrue(all(token.get("annotation") for token in tokens if token.get("surface") != "。"))
        self.assertTrue(any(token.get("surface") == "辞書" and token.get("annotation") == "じしょ" for token in tokens))

    def test_reading_auditor_retokenizes_fragmented_tokens_with_local_quality_gate(self):
        annotator = JapaneseReadingAnnotator(
            morphological_tokenizer=lambda text: [
                {"surface": "学生", "annotation": "がくせい", "pos": "名詞"},
                {"surface": "じゃ", "annotation": "じゃ", "pos": "助詞"},
                {"surface": "ありません", "annotation": "ありません", "pos": "表現"},
            ] if text == "学生じゃありません" else []
        )
        payload = {
            "course_content": {
                "vocabulary": [{"term": "学生", "annotation": "がくせい", "translation": "学生"}],
                "sentence_patterns": [
                    {
                        "pattern_id": 1,
                        "text": "学生じゃありません。",
                        "reading": "がくせいじゃありません。",
                        "tokens": [
                            {"surface": "学生", "annotation": "がくせい"},
                            {"surface": "じ", "annotation": "じ"},
                            {"surface": "ゃ", "annotation": "ゃ"},
                            {"surface": "ありません", "annotation": "ありません"},
                            {"surface": "。", "annotation": ""},
                        ],
                    }
                ],
            }
        }

        audited = MinnaNoNihongoReadingAuditor(annotator=annotator).run(payload)
        tokens = audited["course_content"]["sentence_patterns"][0]["tokens"]

        self.assertEqual([token["surface"] for token in tokens], ["学生", "じゃ", "ありません", "。"])
        self.assertTrue(audited["pipeline_diagnostics"]["reading_audit"]["deterministic_corrections"])

    def test_reading_auditor_skips_low_risk_sentences(self):
        provider = FakeSequenceProvider([])
        payload = {
            "course_content": {
                "vocabulary": [{"term": "本", "annotation": "ほん", "translation": "书"}],
                "sentence_patterns": [
                    {
                        "pattern_id": 1,
                        "text": "これは本です。",
                        "reading": "これはほんです。",
                        "tokens": [
                            {"surface": "これ", "annotation": "これ"},
                            {"surface": "は", "annotation": "わ"},
                            {"surface": "本", "annotation": "ほん"},
                            {"surface": "です", "annotation": "です"},
                            {"surface": "。", "annotation": ""},
                        ],
                    }
                ],
            }
        }

        MinnaNoNihongoReadingAuditor().run(payload, llm_provider=provider, lesson_id=1)

        self.assertEqual(len(provider.calls), 0)

    def test_reading_auditor_merges_known_fragmented_tokens_before_llm(self):
        provider = FakeSequenceProvider([])
        payload = {
            "course_content": {
                "vocabulary": [{"term": "私", "annotation": "わたし", "translation": "我"}],
                "sentence_patterns": [
                    {
                        "pattern_id": 1,
                        "text": "わたしです。",
                        "reading": "わたしです。",
                        "tokens": [
                            {"surface": "わ", "annotation": "わ"},
                            {"surface": "た", "annotation": "た"},
                            {"surface": "し", "annotation": "し"},
                            {"surface": "で", "annotation": "で"},
                            {"surface": "す", "annotation": "す"},
                            {"surface": "。", "annotation": ""},
                        ],
                    }
                ],
            }
        }

        audited = MinnaNoNihongoReadingAuditor().run(payload, llm_provider=provider, lesson_id=1)
        tokens = audited["course_content"]["sentence_patterns"][0]["tokens"]

        self.assertEqual([token["surface"] for token in tokens], ["わたし", "です", "。"])
        self.assertEqual(len(provider.calls), 0)
        self.assertTrue(audited["pipeline_diagnostics"]["reading_audit"]["deterministic_corrections"])

    def test_reading_auditor_uses_historical_vocab_for_token_merge(self):
        provider = FakeSequenceProvider([])
        payload = {
            "course_content": {
                "vocabulary": [],
                "sentence_patterns": [
                    {
                        "pattern_id": 1,
                        "text": "わたしです。",
                        "annotation": "わたしです。",
                        "tokens": [
                            {"surface": "わ", "annotation": "わ"},
                            {"surface": "た", "annotation": "た"},
                            {"surface": "し", "annotation": "し"},
                            {"surface": "です", "annotation": "です"},
                            {"surface": "。", "annotation": ""},
                        ],
                    }
                ],
            }
        }

        audited = MinnaNoNihongoReadingAuditor().run(
            payload,
            llm_provider=provider,
            lesson_id=2,
            token_merge_vocabulary=[{"term": "私", "annotation": "わたし", "translation": "我"}],
        )
        tokens = audited["course_content"]["sentence_patterns"][0]["tokens"]

        self.assertEqual([token["surface"] for token in tokens], ["わたし", "です", "。"])
        self.assertEqual(len(provider.calls), 0)

    def test_reading_auditor_sends_fragmented_unknown_kana_to_llm(self):
        provider = FakeSequenceProvider([
            {
                "reading_corrections": [
                    {
                        "source_section": "sentence_patterns",
                        "source_ref": 1,
                        "annotation": "これはあいうえおです。",
                        "tokens": [
                            {"surface": "これ", "annotation": "これ"},
                            {"surface": "は", "annotation": "わ"},
                            {"surface": "あいうえお", "annotation": "あいうえお"},
                            {"surface": "です", "annotation": "です"},
                            {"surface": "。", "annotation": ""},
                        ],
                        "reason": "fragmented kana tokenization",
                    }
                ]
            }
        ])
        payload = {
            "course_content": {
                "vocabulary": [],
                "sentence_patterns": [
                    {
                        "pattern_id": 1,
                        "text": "これはあいうえおです。",
                        "reading": "これはあいうえおです。",
                        "tokens": [
                            {"surface": "これ", "annotation": "これ"},
                            {"surface": "は", "annotation": "わ"},
                            {"surface": "あ", "annotation": "あ"},
                            {"surface": "い", "annotation": "い"},
                            {"surface": "う", "annotation": "う"},
                            {"surface": "え", "annotation": "え"},
                            {"surface": "お", "annotation": "お"},
                            {"surface": "です", "annotation": "です"},
                            {"surface": "。", "annotation": ""},
                        ],
                    }
                ],
            }
        }

        audited = MinnaNoNihongoReadingAuditor().run(payload, llm_provider=provider, lesson_id=1)
        tokens = audited["course_content"]["sentence_patterns"][0]["tokens"]

        self.assertEqual(len(provider.calls), 1)
        self.assertIn("tokenization_quality_issues", provider.calls[0]["prompt"])
        self.assertEqual([token["surface"] for token in tokens], ["これ", "は", "あいうえお", "です", "。"])

    def test_reading_auditor_applies_llm_corrections(self):
        provider = FakeSequenceProvider([
            {
                "reading_corrections": [
                    {
                        "source_section": "sentence_patterns",
                        "source_ref": 1,
                        "reading": "これはほんです。",
                        "romanization": "kore wa hon desu.",
                        "tokens": [
                            {"surface": "これ", "annotation": "これ", "romanization": "kore"},
                            {"surface": "は", "annotation": "わ", "romanization": "wa"},
                            {"surface": "本", "annotation": "ほん", "romanization": "hon"},
                            {"surface": "です", "annotation": "です", "romanization": "desu"},
                            {"surface": "。", "annotation": "", "romanization": ""},
                        ],
                    }
                ]
            }
        ])
        payload = {
            "course_content": {
                "vocabulary": [],
                "sentence_patterns": [
                    {
                        "pattern_id": 1,
                        "text": "これは本です。",
                        "reading": "これはです。",
                        "tokens": [{"surface": "これ", "annotation": "これ"}],
                    }
                ],
            }
        }

        audited = MinnaNoNihongoReadingAuditor().run(payload, llm_provider=provider, lesson_id=1)
        pattern = audited["course_content"]["sentence_patterns"][0]
        self.assertEqual(pattern["reading"], "これはほんです。")
        self.assertEqual(pattern["tokens"][2]["annotation"], "ほん")
        self.assertTrue(audited["pipeline_diagnostics"]["reading_audit"]["llm_corrections"])

    def test_reading_auditor_batches_and_retries_invalid_batch(self):
        provider = FakeSequenceProvider([
            {"reading_corrections": {"bad": "shape"}},
            {"reading_corrections": []},
            {"reading_corrections": []},
        ])
        payload = {
            "course_content": {
                "vocabulary": [],
                "sentence_patterns": [
                    {
                        "pattern_id": index,
                        "text": f"これは本{index}です。",
                        "reading": f"これはほん{index}です。",
                        "tokens": [{"surface": "これ", "annotation": "これ"}],
                    }
                    for index in range(1, 6)
                ],
            }
        }

        MinnaNoNihongoReadingAuditor().run(payload, llm_provider=provider, lesson_id=1)

        self.assertEqual(len(provider.calls), 3)

    def test_practice_generator_hides_conjugation_before_lesson_14(self):
        generator = MinnaNoNihongoPracticeGenerator()
        items = [
            {
                "question_type": "CONJUGATION",
                "prompt": "飲みます -> て形",
                "standard_answers": ["飲んで"],
            },
            {
                "question_type": "CN_TO_JA",
                "prompt": "请喝水。",
                "standard_answers": ["水を飲んでください。"],
            },
        ]

        normalized = generator.normalize_practice_items(items, [], {"lines": []}, lesson_id=13)

        self.assertEqual([item["question_type"] for item in normalized], ["CN_TO_JA"])

    def test_practice_generator_allows_limited_conjugation_from_lesson_14(self):
        generator = MinnaNoNihongoPracticeGenerator()
        items = [
            {
                "question_type": "CONJUGATION",
                "prompt": f"動詞{i} -> て形",
                "standard_answers": [f"答え{i}"],
            }
            for i in range(1, 7)
        ]

        normalized = generator.normalize_practice_items(items, [], {"lines": []}, lesson_id=14)

        self.assertEqual(len(normalized), generator.MAX_VISIBLE_CONJUGATION_ITEMS)
        self.assertTrue(all(item["question_type"] == "CONJUGATION" for item in normalized))
        self.assertTrue(all("conjugation" in item["metadata"]["skill_tags"] for item in normalized))

    def test_vocab_memory_marks_review_words_with_history(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            memory = MinnaNoNihongoVocabMemory(Path(tmp_dir))
            memory.memory_file.parent.mkdir(parents=True, exist_ok=True)
            memory.memory_file.write_text(json.dumps({
                "学生": [
                    {
                        "term": "学生",
                        "annotation": "がくせい",
                        "definition": "学生",
                        "lesson_id": 1,
                        "lesson_slug": "lesson001",
                        "example": {
                            "text": "わたしは学生です。",
                            "reading": "わたしはがくせいです。",
                            "translation": "我是学生。",
                        },
                    }
                ]
            }, ensure_ascii=False), encoding="utf-8")
            memory.global_vocab = memory._load_memory()
            payload = {
                "lesson_metadata": {"lesson_id": 2, "lesson_slug": "lesson002", "course_id": 201},
                "course_content": {
                    "sentence_patterns": [{"text": "あの人は先生です。", "translation": "那个人是老师。"}],
                    "example_sentences": [],
                    "dialogue": {"lines": []},
                    "vocabulary": [
                        {"term": "学生", "annotation": "がくせい", "translation": "学生"},
                        {"term": "先生", "annotation": "せんせい", "translation": "老师"},
                    ],
                },
            }

            annotated = memory.annotate_lesson(payload)
            vocab = annotated["course_content"]["vocabulary"]

            self.assertEqual(vocab[0]["memory_status"], "review")
            self.assertFalse(vocab[0]["is_new_vocabulary"])
            self.assertEqual(vocab[0]["first_seen_lesson_id"], 1)
            self.assertEqual(vocab[0]["historical_examples"][0]["text"], "わたしは学生です。")
            self.assertEqual(vocab[1]["memory_status"], "new")
            self.assertTrue(vocab[1]["is_new_vocabulary"])

    def test_vocab_memory_saves_examples_without_duplicate_same_lesson(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            memory = MinnaNoNihongoVocabMemory(Path(tmp_dir))
            payload = {
                "lesson_metadata": {"lesson_id": 1, "lesson_slug": "lesson001", "course_id": 201},
                "course_content": {
                    "sentence_patterns": [
                        {
                            "pattern_id": 1,
                            "text": "わたしは学生です。",
                            "reading": "わたしはがくせいです。",
                            "translation": "我是学生。",
                        }
                    ],
                    "example_sentences": [],
                    "dialogue": {"lines": []},
                    "vocabulary": [{"term": "学生", "annotation": "がくせい", "translation": "学生"}],
                },
            }

            memory.save_lesson_vocabulary(payload)
            memory.save_lesson_vocabulary(payload)
            stored = json.loads(memory.memory_file.read_text(encoding="utf-8"))

            self.assertEqual(len(stored["学生"]), 1)
            self.assertEqual(stored["学生"][0]["example"]["text"], "わたしは学生です。")

    def test_vocab_memory_updates_same_lesson_usage_on_rerun(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            memory = MinnaNoNihongoVocabMemory(Path(tmp_dir))
            payload = {
                "lesson_metadata": {"lesson_id": 2, "lesson_slug": "lesson002", "course_id": 201},
                "course_content": {
                    "sentence_patterns": [
                        {"pattern_id": 1, "text": "これは辞書です。", "reading": "これはじしょです。"}
                    ],
                    "example_sentences": [],
                    "dialogue": {"lines": []},
                    "vocabulary": [{"term": "辞書", "annotation": "じしょ", "translation": "词典"}],
                },
            }
            updated_payload = deepcopy(payload)
            updated_payload["course_content"]["sentence_patterns"][0]["text"] = "これは辞書です。"
            updated_payload["course_content"]["sentence_patterns"][0]["reading"] = "これはじしょです。"

            memory.save_lesson_vocabulary(payload)
            stored = json.loads(memory.memory_file.read_text(encoding="utf-8"))
            stored["辞書"][0]["example"]["text"] = "これは辞书です。"
            memory.memory_file.write_text(json.dumps(stored, ensure_ascii=False, indent=2), encoding="utf-8")
            memory.save_lesson_vocabulary(updated_payload)
            stored = json.loads(memory.memory_file.read_text(encoding="utf-8"))

            self.assertEqual(len(stored["辞書"]), 1)
            self.assertEqual(stored["辞書"][0]["example"]["text"], "これは辞書です。")

    def test_vocab_memory_exposes_prior_token_merge_vocabulary(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            memory = MinnaNoNihongoVocabMemory(Path(tmp_dir))
            memory.memory_file.parent.mkdir(parents=True, exist_ok=True)
            memory.memory_file.write_text(json.dumps({
                "私": [
                    {
                        "term": "私",
                        "annotation": "わたし",
                        "definition": "我",
                        "lesson_id": 1,
                    }
                ],
                "辞書": [
                    {
                        "term": "辞書",
                        "annotation": "じしょ",
                        "definition": "词典",
                        "lesson_id": 2,
                    }
                ],
                "9": [
                    {
                        "term": "9",
                        "annotation": "きゅう",
                        "definition": "九",
                        "lesson_id": 1,
                    }
                ],
                "歳": [
                    {
                        "term": "歳",
                        "annotation": "さい",
                        "definition": "岁",
                        "lesson_id": 1,
                    }
                ],
                "日": [
                    {
                        "term": "日",
                        "annotation": "にち",
                        "definition": "日",
                        "lesson_id": 1,
                    }
                ],
            }, ensure_ascii=False), encoding="utf-8")
            memory.global_vocab = memory._load_memory()

            lesson2_terms = {item["term"]: item for item in memory.token_merge_vocabulary(lesson_id=2)}
            lesson3_terms = {item["term"]: item for item in memory.token_merge_vocabulary(lesson_id=3)}

            self.assertIn("わたし", lesson2_terms)
            self.assertEqual(lesson2_terms["わたし"]["reading"], "わたし")
            self.assertIn("辞書", lesson3_terms)
            self.assertNotIn("9", lesson2_terms)
            self.assertNotIn("歳", lesson2_terms)
            self.assertNotIn("日", lesson2_terms)
            self.assertNotIn("にち", lesson2_terms)
            self.assertNotIn("辞書", lesson2_terms)

    def test_practice_generator_skips_review_vocabulary(self):
        generator = MinnaNoNihongoPracticeGenerator()
        payload = {
            "lesson_metadata": {"lesson_id": 2, "course_id": 201},
            "course_content": {
                "vocabulary": [
                    {
                        "term": "学生",
                        "annotation": "がくせい",
                        "translation": "学生",
                        "is_new_vocabulary": False,
                        "memory_status": "review",
                    },
                    {
                        "term": "先生",
                        "annotation": "せんせい",
                        "translation": "老师",
                        "is_new_vocabulary": True,
                        "memory_status": "new",
                    },
                ]
            },
            "practice_items": [],
        }

        database_items = generator.build_database_items(payload)

        self.assertEqual(len(database_items), 2)
        self.assertEqual({item["original_text"] for item in database_items}, {"先生", "老师"})

    def test_practice_generator_skips_proper_noun_vocabulary(self):
        generator = MinnaNoNihongoPracticeGenerator()
        payload = {
            "lesson_metadata": {"lesson_id": 1, "course_id": 201},
            "course_content": {
                "vocabulary": [
                    {
                        "term": "マイク・ミラー",
                        "annotation": "マイク・ミラー",
                        "translation": "迈克·米勒",
                        "part_of_speech": "固有名詞",
                        "category": "person_name",
                        "is_new_vocabulary": True,
                    },
                    {
                        "term": "学生",
                        "annotation": "がくせい",
                        "translation": "学生",
                        "is_new_vocabulary": True,
                    },
                ]
            },
            "practice_items": [],
        }

        database_items = generator.build_database_items(payload)

        self.assertEqual(len(database_items), 2)
        self.assertTrue(all("マイク・ミラー" not in item["original_text"] for item in database_items))
        self.assertEqual({item["question_type"] for item in database_items}, {"JA_TO_CN", "CN_TO_JA"})

    def test_practice_generator_normalizes_object_prompt_and_answers(self):
        generator = MinnaNoNihongoPracticeGenerator()

        normalized = generator.normalize_practice_items(
            [
                {
                    "question_type": "CN_TO_JA",
                    "prompt": {"translation": "这是书。"},
                    "standard_answers": [{"text": "これは本です。"}],
                }
            ],
            sentence_patterns=[],
            dialogue={"lines": []},
            lesson_id=2,
        )

        self.assertEqual(normalized[0]["prompt"], "这是书。")
        self.assertEqual(normalized[0]["standard_answers"], ["これは本です。"])

    def test_practice_generator_fallback_builds_task2_style_items(self):
        generator = MinnaNoNihongoPracticeGenerator()
        payload = {
            "lesson_metadata": {"lesson_id": 1, "course_id": 201},
            "course_content": {
                "vocabulary": [
                    {
                        "term": "学生",
                        "annotation": "がくせい",
                        "translation": "学生",
                        "is_new_vocabulary": True,
                    }
                ],
                "sentence_patterns": [
                    {
                        "pattern_id": 1,
                        "text": "わたしは学生です。",
                        "reading": "わたしはがくせいです。",
                        "translation": "我是学生。",
                    }
                ],
                "example_sentences": [],
                "dialogue": {
                    "lines": [
                        {
                            "line_ref": 1,
                            "text": "はじめまして。",
                            "reading": "はじめまして。",
                            "translation": "初次见面。",
                        }
                    ]
                },
                "grammar_sections": [],
            },
            "practice_items": [],
        }

        database_items = generator.build_database_items(payload)
        question_types = {item["question_type"] for item in database_items}

        self.assertIn("JA_TO_CN", question_types)
        self.assertIn("CN_TO_JA", question_types)
        self.assertIn("JA_SPEAK", question_types)
        self.assertIn("JA_LISTEN_WRITE", question_types)

    def test_practice_generator_uses_llm_batches_for_task2_items(self):
        provider = FakeSequenceProvider([
            {
                "database_items": [
                    {
                        "question_type": "CN_TO_JA",
                        "original_text": "学生",
                        "standard_answers": ["学生"],
                    }
                ]
            },
            {
                "database_items": [
                    {
                        "question_type": "CN_TO_JA",
                        "original_text": "我是学生。",
                        "standard_answers": ["わたしは学生です。"],
                    }
                ]
            },
            {
                "database_items": [
                    {
                        "question_type": "JA_SPEAK",
                        "original_text": "我是学生。",
                        "standard_answers": ["わたしは学生です。"],
                        "metadata": {"answer_mode": "speech", "speech_language": "ja"},
                    }
                ]
            },
            {
                "database_items": [
                    {
                        "question_type": "JA_LISTEN_WRITE",
                        "original_text": "我是学生。",
                        "standard_answers": ["わたしは学生です。"],
                    }
                ]
            },
        ])
        generator = MinnaNoNihongoPracticeGenerator()
        payload = {
            "lesson_metadata": {"lesson_id": 1, "course_id": 201},
            "course_content": {
                "vocabulary": [
                    {
                        "term": "学生",
                        "annotation": "がくせい",
                        "translation": "学生",
                        "is_new_vocabulary": True,
                    }
                ],
                "sentence_patterns": [
                    {
                        "pattern_id": 1,
                        "text": "わたしは学生です。",
                        "reading": "わたしはがくせいです。",
                        "translation": "我是学生。",
                    }
                ],
                "example_sentences": [],
                "dialogue": {"lines": []},
                "grammar_sections": [],
            },
            "practice_items": [],
        }

        database_items = generator.build_database_items(payload, llm_provider=provider)

        self.assertEqual(len(provider.calls), 4)
        self.assertTrue(any(item["question_type"] == "JA_LISTEN_WRITE" for item in database_items))
        self.assertTrue(any(item["question_type"] == "JA_SPEAK" for item in database_items))

    def test_practice_generator_allows_conjugation_llm_from_lesson_14(self):
        provider = FakeSequenceProvider([
            {
                "database_items": [
                    {
                        "question_type": "CONJUGATION",
                        "original_text": "飲みます -> て形",
                        "standard_answers": ["飲んで"],
                    }
                ]
            }
        ])
        generator = MinnaNoNihongoPracticeGenerator()
        payload = {
            "lesson_metadata": {"lesson_id": 14, "course_id": 201},
            "course_content": {
                "vocabulary": [],
                "sentence_patterns": [],
                "example_sentences": [],
                "dialogue": {"lines": []},
                "grammar_sections": [{"title": "動詞のて形", "examples": []}],
            },
            "practice_items": [],
        }

        database_items = generator.build_database_items(payload, llm_provider=provider)

        self.assertEqual(len(provider.calls), 1)
        self.assertEqual(database_items[0]["question_type"], "CONJUGATION")
        self.assertIn("conjugation", database_items[0]["metadata"]["skill_tags"])

    def test_render_plan_regenerates_legacy_existing_plan(self):
        builder = MinnaNoNihongoRenderPlanBuilder()
        legacy_plan = {
            "explanation": {
                "segments": [
                    {
                        "segment_type": "line_walkthrough",
                        "template_name": "ja_line_focus",
                        "visual_blocks": [],
                    }
                ],
                "renderer_notes": {"recommended_renderer": "static_teaching_slide_deck"},
            }
        }
        metadata = {"lesson_id": 2, "course_id": 201, "title_localized": "第2课"}
        course_content = {
            "sentence_patterns": [
                {
                    "text": "これは本です。",
                    "reading": "これはほんです。",
                    "translation": "这是书。",
                    "tokens": [
                        {"surface": "これ", "annotation": "これ", "pos": "代名詞", "highlight": True},
                        {"surface": "は", "annotation": "わ", "pos": "助詞"},
                        {"surface": "本", "annotation": "ほん", "pos": "名詞", "highlight": True},
                        {"surface": "です", "annotation": "です", "pos": "助動詞"},
                    ],
                }
            ],
            "example_sentences": [{"text": "それは辞書です。", "reading": "それはじしょです。", "translation": "那是词典。"}],
            "dialogue": {"lines": [{"speaker": "ミラー", "text": "これは何ですか。", "reading": "これはなんですか。", "translation": "这是什么？"}]},
            "vocabulary": [{"term": "本", "annotation": "ほん", "translation": "书", "part_of_speech": "名詞"}],
            "display_only_vocabulary": [],
            "grammar_sections": [{"title": "これ／それ／あれ", "explanation": "指示事物。", "examples": [{"text": "これは本です。"}]}],
            "practice_source": [{"section": "練習A-1", "instruction": "替换名词。", "pattern": "これは [名詞] です。"}],
        }

        plan = builder.run(metadata, course_content, existing_plan=legacy_plan)
        segments = plan["explanation"]["segments"]
        segment_types = {segment["segment_type"] for segment in segments}
        template_names = {segment["template_name"] for segment in segments}

        self.assertEqual(plan["explanation"]["renderer_notes"]["plan_version"], RENDER_PLAN_VERSION)
        self.assertGreater(len(segments), 1)
        self.assertIn("line_walkthrough", segment_types)
        self.assertIn("sentence_focus", segment_types)
        self.assertIn("dialogue_focus", segment_types)
        self.assertIn("vocabulary_focus", segment_types)
        self.assertIn("grammar_focus", segment_types)
        self.assertNotIn("lesson_intro", segment_types)
        self.assertNotIn("practice_prompt", segment_types)
        self.assertNotIn("lesson_recap", segment_types)
        self.assertTrue(template_names <= {"ja_line_focus", "ja_sentence_stack", "ja_vocab_board", "ja_grammar_board"})

    def test_real_lesson_render_plans_match_lesson001_golden_shape(self):
        fixture_dir = (
            BACKEND_DIR
            / "content_builder"
            / "ja"
            / "minna_no_nihongo"
            / "artifacts"
            / "output_json"
            / "zh"
        )
        required_types = {
            "line_walkthrough",
            "sentence_focus",
            "dialogue_focus",
            "vocabulary_focus",
            "grammar_focus",
        }
        allowed_templates = {"ja_line_focus", "ja_sentence_stack", "ja_vocab_board", "ja_grammar_board"}
        builder = MinnaNoNihongoRenderPlanBuilder()

        for lesson_id in (1, 2, 3):
            with self.subTest(lesson_id=lesson_id):
                fixture = fixture_dir / f"lesson{lesson_id:03d}_data.json"
                if not fixture.exists():
                    self.skipTest(f"fixture not present: {fixture}")
                payload = json.loads(fixture.read_text(encoding="utf-8"))
                plan = builder.run(
                    payload["lesson_metadata"],
                    payload["course_content"],
                    existing_plan=None,
                )
                segments = plan["explanation"]["segments"]
                segment_types = {segment.get("segment_type") for segment in segments}
                template_names = {segment.get("template_name") for segment in segments}

                self.assertEqual(plan["explanation"]["renderer_notes"]["plan_version"], RENDER_PLAN_VERSION)
                self.assertGreater(len(segments), 0)
                self.assertTrue(required_types <= segment_types)
                self.assertTrue(template_names <= allowed_templates)
                self.assertEqual(plan["explanation"]["timeline"]["segment_count"], len(segments))
                for segment in segments:
                    self.assertTrue(segment.get("narration_track", {}).get("script"))
                    self.assertTrue(segment.get("visual_blocks"))

    def test_explanation_composer_accepts_llm_directed_segments(self):
        metadata = {"lesson_id": 1, "course_id": 201, "title_localized": "第1课"}
        course_content = {
            "sentence_patterns": [
                {
                    "text": "わたしは学生です。",
                    "reading": "わたしはがくせいです。",
                    "translation": "我是学生。",
                    "tokens": [
                        {"surface": "わたし", "annotation": "わたし", "pos": "代名詞"},
                        {"surface": "は", "annotation": "わ", "pos": "助詞"},
                        {"surface": "学生", "annotation": "がくせい", "pos": "名詞"},
                        {"surface": "です", "annotation": "です", "pos": "助動詞"},
                        {"surface": "。", "annotation": ""},
                    ],
                }
            ],
            "example_sentences": [
                {"text": "これは本です。", "reading": "これはほんです。", "translation": "这是书。", "tokens": []},
                {"text": "それは辞書です。", "reading": "それはじしょです。", "translation": "那是词典。", "tokens": []},
            ],
            "dialogue": {
                "title": "はじめまして",
                "title_localized": "初次见面",
                "lines": [
                    {"speaker": "ミラー", "text": "はじめまして。", "reading": "はじめまして。", "translation": "初次见面。", "tokens": []}
                ],
            },
            "vocabulary": [
                {"term": "わたし", "annotation": "わたし", "translation": "我", "part_of_speech": "代名詞"},
                {
                    "term": "あのひと",
                    "annotation": "あのひと",
                    "translation": "那个人",
                    "part_of_speech": "名詞",
                    "lesson_section": "supplementary",
                },
                {"term": "学生", "annotation": "がくせい", "translation": "学生", "part_of_speech": "名詞"},
            ],
            "display_only_vocabulary": [],
            "grammar_sections": [
                {
                    "title": "N1 は N2 です",
                    "explanation": "判断句。",
                    "patterns": [{"text": "N1 は N2 です。", "translation": "N1 是 N2。"}],
                    "examples": [{"text": "わたしは学生です。", "reading": "わたしはがくせいです。", "translation": "我是学生。"}],
                }
            ],
        }
        explanation = {
            "global_config": {"teaching_style": "LLM directed"},
            "segments": [
                {
                    "segment_type": "line_walkthrough",
                    "source": {"kind": "sentence_patterns", "indexes": [1]},
                    "segment_title": "先看判断句",
                    "teaching_goal": "建立基础句型。",
                    "narration": {"subtitle_zh": "先听 [ja:わたしは学生です]。这句话用来介绍身份。"},
                    "estimated_duration_seconds": 18,
                },
                {
                    "segment_type": "sentence_focus",
                    "source": {"kind": "example_sentences", "indexes": [1, 2]},
                    "segment_title": "例文对比",
                    "teaching_goal": "比较两个指示词句子。",
                    "narration": {"subtitle_zh": "这两句都在练习判断句，只是指代对象不同。"},
                    "estimated_duration_seconds": 16,
                },
                {
                    "segment_type": "vocabulary_focus",
                    "source": {"kind": "vocabulary", "indexes": [3]},
                    "segment_title": "身份词",
                    "teaching_goal": "记住学生这个词。",
                    "narration": {"subtitle_zh": "这里重点看 [ja:学生]，读作 がくせい。"},
                    "estimated_duration_seconds": 12,
                },
                {
                    "segment_type": "grammar_focus",
                    "source": {"kind": "grammar_sections", "indexes": [1]},
                    "segment_title": "语法框架",
                    "teaching_goal": "理解 N1 は N2 です。",
                    "narration": {"subtitle_zh": "这个语法点是名词判断句，用来说明身份或事实。"},
                    "estimated_duration_seconds": 20,
                },
                {
                    "segment_type": "recap",
                    "source": {"kind": "lesson_summary", "indexes": []},
                    "segment_title": "本课总结",
                    "teaching_goal": "回顾本课重点。",
                    "highlight_words": [
                        {"word": "わたしは学生です", "reading": "わたしはがくせいです", "translation": "我是学生"},
                        {"word": "学生", "reading": "がくせい", "translation": "学生"},
                    ],
                    "narration": {"subtitle_zh": "最后回顾一下：[ja:わたしは学生です] 是最基础的判断句。"},
                    "estimated_duration_seconds": 18,
                },
            ],
        }

        plan = MinnaNoNihongoExplanationComposer().run(metadata, course_content, explanation)
        segments = plan["explanation"]["segments"]

        self.assertEqual(plan["explanation"]["renderer_notes"]["plan_version"], DIRECTOR_PLAN_VERSION)
        self.assertEqual(len(segments), 5)
        self.assertEqual(
            [segment["template_name"] for segment in segments],
            ["ja_line_focus", "ja_sentence_stack", "ja_vocab_board", "ja_grammar_board", "lesson_recap"],
        )
        vocab_items = segments[2]["visual_blocks"][0]["content"]["items"]
        self.assertEqual([item["term"] for item in vocab_items], ["学生"])
        self.assertEqual(segments[4]["segment_type"], "recap")
        self.assertEqual(segments[4]["visual_blocks"][0]["block_type"], "recap_summary")
        self.assertEqual(segments[4]["highlight_words"][0]["word"], "わたしは学生です")
        self.assertEqual(segments[0]["narration_track"]["subtitle_zh"], "先听 [ja:わたしは学生です]。这句话用来介绍身份。")

    def test_explanation_composer_adds_recap_when_llm_omits_it(self):
        metadata = {"lesson_id": 1, "course_id": 201, "title_localized": "第1课"}
        course_content = {
            "sentence_patterns": [
                {"text": "わたしは学生です。", "reading": "わたしはがくせいです。", "translation": "我是学生。", "tokens": []}
            ],
            "example_sentences": [],
            "dialogue": {"lines": []},
            "vocabulary": [
                {"term": "学生", "annotation": "がくせい", "translation": "学生", "part_of_speech": "名詞"}
            ],
            "display_only_vocabulary": [],
            "grammar_sections": [
                {"title": "N1 は N2 です", "explanation": "判断句。", "examples": []}
            ],
        }
        explanation = {
            "global_config": {"teaching_style": "LLM directed"},
            "segments": [
                {
                    "segment_type": "line_walkthrough",
                    "source": {"kind": "sentence_patterns", "indexes": [1]},
                    "segment_title": "先看判断句",
                    "teaching_goal": "建立基础句型。",
                    "narration": {"subtitle_zh": "先听 [ja:わたしは学生です]。"},
                    "estimated_duration_seconds": 18,
                }
            ],
        }

        plan = MinnaNoNihongoExplanationComposer().run(metadata, course_content, explanation)
        segments = plan["explanation"]["segments"]

        self.assertEqual(segments[-1]["segment_type"], "recap")
        self.assertEqual(segments[-1]["template_name"], "lesson_recap")
        self.assertTrue(segments[-1]["highlight_words"])

    def test_explanation_writer_sanitizes_old_pinyin_key(self):
        writer = MinnaNoNihongoExplanationWriter(FakeExplanationProvider())
        explanation = writer.run({}, {}, {})
        highlight = explanation["segments"][0]["highlight_words"][0]

        self.assertNotIn("pinyin", highlight)
        self.assertEqual(highlight["reading"], "がくせい")

    def test_render_plan_reuses_legacy_lesson001_golden_plan(self):
        builder = MinnaNoNihongoRenderPlanBuilder()
        golden_segments = [
            {"segment_type": "line_walkthrough", "template_name": "ja_line_focus", "visual_blocks": [{"block_type": "hero_line"}]},
            {"segment_type": "sentence_focus", "template_name": "ja_sentence_stack", "visual_blocks": [{"block_type": "ja_sentence_stack"}]},
        ] * 16
        existing_plan = {
            "explanation": {
                "lesson_id": 1,
                "segments": golden_segments,
                "timeline": {"segment_count": len(golden_segments)},
                "renderer_notes": {"recommended_renderer": "static_teaching_slide_deck"},
            }
        }

        reused = builder.run(
            {"lesson_id": 1, "course_id": 201, "title_localized": "第1课"},
            {
                "sentence_patterns": [],
                "example_sentences": [],
                "dialogue": {"lines": []},
                "vocabulary": [],
                "display_only_vocabulary": [],
                "grammar_sections": [],
            },
            existing_plan=existing_plan,
        )

        self.assertIs(reused, existing_plan)


if __name__ == "__main__":
    unittest.main()

