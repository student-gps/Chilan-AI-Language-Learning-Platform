import json
import traceback
from pathlib import Path
from llm_providers import BaseLLMProvider
from tasks.task1_extractor import Task1Extractor
from tasks.task2_quiz import Task2QuizGenerator
from tasks.task3_videodirector import Task3VideoGenerator

class ContentCreatorAgent:
    def __init__(self, provider: BaseLLMProvider, memory_dir: Path):
        self.provider = provider
        self.task1 = Task1Extractor(provider)
        self.task2 = Task2QuizGenerator(provider, memory_dir)
        self.task3 = Task3VideoGenerator(provider)

    def parse_textbook(self, file_path: str, lesson_id: int, course_id: int = 1):
        print(f"\n🚀 开始处理流水线: {Path(file_path).name} (Lesson ID: {lesson_id})")
        
        try:
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
                vocabulary=vocab_data, 
                grammar=grammar_data
            )
            
            # 填充视频数据 (匹配导演版新结构)
            if video_data:
                base_data["video_global_config"] = video_data.get("global_config", {})
                base_data["video_scenes"] = video_data.get("video_scenes", [])
            else:
                base_data["video_global_config"] = {}
                base_data["video_scenes"] = []

            # 🎉 【原子化持久化】
            # 🚀 修复点：传入本次提取的新词列表和 lesson_id 以更新“全量动态词典”
            if vocab_data:
                self.task2.save_memory(vocab_data, lesson_id)
                print(f"✨ 动态词典已更新，本课新增 {len(vocab_data)} 个词义记录。")
            
            print(f"✅ 管线任务圆满完成！")
            return base_data

        except Exception as e:
            # 熔断机制：报错则不保存记忆，防止数据污染
            print(f"❌ 流水线执行中断: {e}")
            traceback.print_exc() 
            return None
