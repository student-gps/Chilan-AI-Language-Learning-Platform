import os
import json
import time
import re
import shutil
from pathlib import Path
from google import genai
from dotenv import load_dotenv

# 1. 自动化路径处理：精准定位到 backend/.env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

class ContentCreatorAgent:
    def __init__(self):
        # 验证 API Key 加载状态
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("❌ 错误：在 .env 文件中未找到 GEMINI_API_KEY。")
        
        # 使用最新的 google-genai SDK
        self.client = genai.Client(api_key=api_key)
        
        # 锁定最稳定且高配的 2.5 Pro 模型
        self.model_id = "gemini-2.5-pro" 

    def parse_textbook(self, file_path: str, lesson_id: int, course_id: int = 1):
        """
        核心逻辑：解析教材 PDF 并生成动态结构化 JSON 数据
        """
        print(f"🚀 正在上传并解析教材: {file_path} (Lesson ID: {lesson_id})")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"❌ 错误：找不到文件 {file_path}")

        # 1. 上传 PDF 文件
        with open(file_path, "rb") as f:
            sample_file = self.client.files.upload(
                file=f,
                config={'mime_type': 'application/pdf'}
            )
        
        # 2. 等待云端处理 PDF
        print("⏳ 系统正在理解教材版式...", end="", flush=True)
        while sample_file.state == "PROCESSING":
            print(".", end="", flush=True)
            time.sleep(2)
            sample_file = self.client.files.get(name=sample_file.name)

        if sample_file.state == "FAILED":
            raise Exception("❌ 教材上传处理失败，请检查 API 状态。")

        # 3. 动态 Prompt 构建 (融入了你最新优化的题库生成规则)
        # 3. 动态 Prompt 构建 (融入了你最新优化的题库生成规则)
        prompt = f"""
        你是一名资深的对外汉语专家和数据工程师。请解析提供的教材 PDF，并严格按照要求提取内容，最终只输出一个合法的 JSON，不要包含任何额外的 Markdown 标记（如 ```json）。

        【核心解析规则】
        1. **lesson_metadata**:
            - course_id: {course_id}（英文学中文固定为1）
            - lesson_id: {lesson_id}
            - title: 这一课程的标题，例如 "Lesson {lesson_id}: 问好" (请根据课文内容生成，标题应该为中文)

        2. **course_content** (前端展示数据):
            - dialogues: 按照原文顺序提取课文内容，包括对话者，对话内容，这些都需要以中文提取，并标注拼音。
            - vocabulary: 提取单词、拼音、词性(Verb/Noun/Adjective等等）、英文定义。同时提取一个例句，必须将例句严格拆分为纯中文 (cn)、纯拼音 (py) 和英文翻译 (en)。

        3. **database_items** (题库数据，严格对齐 PostgreSQL 表结构):
            - 生成用于复习翻译的题目，必须覆盖基础核心词汇和课文重点句子。
            - 你需要将刚刚生成的vocabulary编成简单的中译英、英译中的题目并存到database_items中，请全部生成，也包括一些简单的单字成词的题目。
            - 你还需要生成很重要的句子的翻译，并且这些句子必须是课文中非常核心的句子，不能生成一些无关紧要的题目。
            - 同时你还要对题目进行一定的处理，要保证给用户的题目都是高质量，有普适价值的，比如一些人名相关的题目就可以剔除。
            - 请你按照一定的顺序：先是所有的中译英单词题，再是所有的英译中单词题，再是所有的中译英句子题，最后是所有的英译中句子题。请你务必按照这个顺序来生成题目。
            - course_id 必须为 {course_id}，lesson_id 必须为 {lesson_id}。
            - question_id: 从 1 开始递增的整数。
            - question_type: 严格只能是 "CN_TO_EN" (中译英) 或 "EN_TO_CN" (英译中)。
            - original_text: 题干文本。
            - standard_answers: **必须是数组（List/Array）**，即使只有一个答案也必须包裹在数组中。

        4. **aigc_visual_prompt**: 为本课生成一段 Midjourney 英文提示词，用于生成课程封面。

        【强制输出结构】
        请严格照抄以下 JSON 格式进行输出，绝不允许修改字段名或破坏层级结构：
        {{
        "lesson_metadata": {{
            "course_id": {course_id},
            "lesson_id": {lesson_id},
            "title": "Lesson {lesson_id}: 自动生成的标题"
        }},
        "course_content": {{
            "dialogues": [
            {{
                "lines": [
                {{   
                    "role": "王小明",
                    "english": "Hello, my name is Wang Xiaoming.",
                    "words": [
                    {{"cn": "你", "py": "nǐ"}},
                    {{"cn": "好", "py": "hǎo"}},
                    {{"cn": "，", "py": ""}},
                    {{"cn": "我", "py": "wǒ"}},
                    {{"cn": "叫", "py": "jiào", "highlight": true}}, 
                    {{"cn": "王", "py": "wáng"}},
                    {{"cn": "小", "py": "xiǎo"}},
                    {{"cn": "明", "py": "míng"}},
                    {{"cn": "。", "py": ""}}
                    ]
                }}
                ]
            }}
            ],
            "vocabulary": [
            {{
                "word": "单词",
                "pinyin": "dān cí",
                "part_of_speech": "n",
                "definition": "word",
                "example_sentence": {{
                    "cn": "这是一个例句。",
                    "py": "Zhè shì yí gè lìjù.",
                    "en": "This is an example sentence."
                }}
            }}
            ]
        }},
        "database_items": [
            {{
            "lesson_id": {lesson_id},
            "question_id": 1,
            "course_id": {course_id},
            "question_type": "CN_TO_EN",
            "original_text": "你好",
            "standard_answers": ["Hello", "Hi"]
            }}
        ],
        "aigc_visual_prompt": "..."
        }}
        """

        # 4. 调用模型生成内容
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=[prompt, sample_file],
            config={
                'response_mime_type': 'application/json',
                'temperature': 0.1, # 🌟 强力温控：杜绝格式错乱
                'top_p': 0.8
            }
        )

        try:
            # 5. 解析并返回数据
            structured_data = json.loads(response.text)
            return structured_data
        except Exception as e:
            print(f"\n❌ JSON 解析失败：{e}")
            return None

def main():
    agent = ContentCreatorAgent()
    current_dir = Path(__file__).resolve().parent
    
    # 🌟 标准化流水线目录
    raw_dir = current_dir / "raw_materials"
    output_dir = current_dir / "output_json"
    archive_dir = current_dir / "archive_pdfs"
    
    # 确保目录存在
    for d in [raw_dir, output_dir, archive_dir]:
        d.mkdir(parents=True, exist_ok=True)
    
    # 扫描所有 PDF
    pdf_files = list(raw_dir.glob("*.pdf"))
    
    if not pdf_files:
        print(f"📭 原料库 ({raw_dir.name}) 为空，没有需要处理的 PDF。")
        return

    print(f"📦 发现 {len(pdf_files)} 个新教材准备处理！")

    for pdf_path in pdf_files:
        file_name = pdf_path.stem # 获取去掉后缀的文件名，如 "lesson101"
        print(f"\n=====================================")
        print(f"▶️ 开始处理: {file_name}.pdf")
        
        # 🌟 极简正则：直接从 "lesson101" 中提取出数字 "101"
        numbers = re.findall(r'\d+', file_name)
        if numbers:
            lesson_id = int(numbers[0])
        else:
            print(f"⚠️ 警告：无法从文件名 {file_name} 提取编号，跳过该文件！")
            continue
            
        course_id = 1 # 假设目前的语言课 Course ID 都是 1
        
        # 调用大模型执行解析
        result = agent.parse_textbook(str(pdf_path), lesson_id=lesson_id, course_id=course_id)
        
        if result:
            # 保存输出的 JSON
            output_file = output_dir / f"lesson{lesson_id}_data.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n✅ 成功生成数据: {output_file.name}")
            
            # 🌟 处理完毕，将 PDF 归档
            try:
                archive_path = archive_dir / pdf_path.name
                if archive_path.exists():
                    archive_path = archive_dir / f"{pdf_path.stem}_{int(time.time())}.pdf"
                shutil.move(str(pdf_path), str(archive_path))
                print(f"📁 教材已归档至: archive_pdfs 文件夹，防止重复处理。")
            except Exception as e:
                print(f"⚠️ 归档文件时发生错误: {e}")
        else:
            print(f"❌ {file_name}.pdf 处理失败，保留在 raw_materials 中等待下次重试。")

if __name__ == "__main__":
    main()