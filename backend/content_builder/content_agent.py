import json
import traceback
from pathlib import Path
from llm_providers import BaseLLMProvider
from tasks.task1_extractor import Task1Extractor
from tasks.task1b_textbook_notes_extractor import Task1BTextbookNotesExtractor
from tasks.task2_quiz import Task2QuizGenerator
from tasks.task3_videodirector import Task3LessonVideoPlanner
from tasks.task4b_lesson_audio_renderer import Task4BLessonAudioRenderer

class ContentCreatorAgent:
    def __init__(self, provider: BaseLLMProvider, memory_dir: Path):
        self.provider = provider
        self.memory_dir = memory_dir
        self.task1 = Task1Extractor(provider)
        self.task1b = Task1BTextbookNotesExtractor(provider)
        self.task2 = Task2QuizGenerator(provider, memory_dir)
        self.task3 = Task3LessonVideoPlanner(provider)
        self.task4b = Task4BLessonAudioRenderer()

    def parse_textbook(self, file_path: str, lesson_id: int, course_id: int = 1):
        print(f"\n🚀 开始处理流水线: {Path(file_path).name} (Lesson ID: {lesson_id})")
        
        try:
            if hasattr(self.provider, "reset_usage_log"):
                self.provider.reset_usage_log()

            # 🚀 【核心：一次上传，全程复用】
            shared_file = self.task1.llm.upload_pdf(file_path)

            # 🟢 [Task 1] 获取基础数据 (对话与元数据)
            base_data = self.task1.run(
                lesson_id=lesson_id, 
                course_id=course_id, 
                file_path=None, 
                file_obj=shared_file
            )
            
            if not base_data:
                print("❌ Task 1 核心数据提取失败，终止后续管线。")
                return None

            # 🟢 [Task 1B] 提取教材讲解素材 (Language Notes / Grammar)
            teaching_material_result = self.task1b.run(
                lesson_id=lesson_id,
                course_id=course_id,
                file_path=None,
                file_obj=shared_file
            )
            teaching_materials = (
                teaching_material_result.get("teaching_materials", {})
                if isinstance(teaching_material_result, dict)
                else {}
            )
            base_data["teaching_materials"] = teaching_materials

            # 🟢 [Task 2] 提取词汇(含历史记录) + 提取语法 + 生成题库
            # 现在 task2.run 内部包含了对“一词多义”的处理
            task2_result = self.task2.run(
                lesson_id=lesson_id, 
                course_id=course_id, 
                file_path=None, 
                file_obj=shared_file,
                source_dialogues=base_data.get("course_content", {}).get("dialogues", [])
            )
            
            # 合并 Task 2 的官方词汇和题库到最终结果
            vocab_data = []
            grammar_data = []
            if task2_result and isinstance(task2_result, dict):
                vocab_data = task2_result.get("vocabulary", [])
                # 题库数据存入 base_data 以便入库
                base_data["course_content"]["vocabulary"] = vocab_data
                base_data["database_items"] = task2_result.get("database_items", [])
                # 提取练习句，供 Task 3 参考
                grammar_data = task2_result.get("grammar_practice", []) 
            else:
                print("⚠️ Task 2 返回数据异常，填充空列表。")
                base_data["course_content"]["vocabulary"] = []
                base_data["database_items"] = []

            # 🟢 [Task 3] 生成教学视频脚本 (AI 导演模式)
            # 🚀 升级：将 Task 2 得到的词汇和语法也传给导演，让分镜更有教学针对性
            metadata = base_data.get("lesson_metadata", {})
            dialogues = base_data.get("course_content", {}).get("dialogues", [])
            
            video_data = self.task3.run(
                metadata=metadata, 
                dialogues=dialogues, 
                teaching_materials=teaching_materials,
                vocabulary=vocab_data, 
                grammar=grammar_data
            )
            
            # 填充视频脚本数据：保存统一 lesson video plan，供后续渲染层消费
            if video_data and isinstance(video_data, dict):
                base_data["video_plan"] = video_data
            else:
                base_data["video_plan"] = {
                    "lesson_video_plan": {},
                    "dramatization": {
                        "global_config": {},
                        "scenes": []
                    },
                    "explanation": {
                        "global_config": {},
                        "segments": []
                    },
                    "production_notes": {
                        "recommended_workflow": [],
                        "remarks": ""
                    }
                }

            # 🟢 [Task 4B] 生成课文逐句音频资产（腾讯云通用语音合成）
            try:
                audio_output_dir = self.memory_dir / "output_audio" / f"lesson{lesson_id}"
                lesson_audio_assets = self.task4b.render_sentence_audio_assets(
                    lesson_data=base_data,
                    output_dir=audio_output_dir,
                    include_speakers=False,
                    enable_subtitle=False,
                    public_base_url="/media/audio",
                )
                base_data["lesson_audio_assets"] = lesson_audio_assets.get("lesson_audio_assets", {})
                audio_count = len(base_data["lesson_audio_assets"].get("items", []))
                print(f"✨ 课文逐句音频已生成，共 {audio_count} 条。")
            except Exception as audio_error:
                print(f"⚠️ Task 4B 音频生成失败，已跳过本课音频资产: {audio_error}")
                base_data["lesson_audio_assets"] = {
                    "provider": "tencent_tts",
                    "mode": "sentence_audio",
                    "default_voice_type": getattr(self.task4b, "voice_type", None),
                    "role_voice_map": getattr(self.task4b, "role_voice_map", {}),
                    "codec": "mp3",
                    "sample_rate": 16000,
                    "include_speakers": False,
                    "storage_backend": "local",
                    "full_audio": {
                        "status": "missing",
                        "audio_url": "",
                        "object_key": "",
                        "local_audio_file": "",
                        "codec": "mp3",
                    },
                    "items": []
                }

            # 🎉 【原子化持久化】
            # 🚀 修复点：传入本次提取的新词列表和 lesson_id 以更新“全量动态词典”
            if vocab_data:
                self.task2.save_memory(vocab_data, lesson_id)
                print(f"✨ 动态词典已更新，本课新增 {len(vocab_data)} 个词义记录。")

            usage_summary = self.provider.get_usage_summary() if hasattr(self.provider, "get_usage_summary") else {}
            base_data["llm_usage"] = usage_summary
            if usage_summary:
                print(
                    "💰 LLM 用量统计 | "
                    f"调用次数: {usage_summary.get('calls', 0)} | "
                    f"输入 tokens: {usage_summary.get('input_tokens', 0)} | "
                    f"输出 tokens: {usage_summary.get('output_tokens', 0)} | "
                    f"总 tokens: {usage_summary.get('total_tokens', 0)} | "
                    f"估算成本: ${usage_summary.get('estimated_cost_usd', 0.0):.6f}"
                )
            
            print(f"✅ 管线任务圆满完成！")
            return base_data

        except Exception as e:
            # 熔断机制：报错则不保存记忆，防止数据污染
            print(f"❌ 流水线执行中断: {e}")
            traceback.print_exc() 
            return None
