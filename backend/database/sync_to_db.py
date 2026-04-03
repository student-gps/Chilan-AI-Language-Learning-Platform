import os
import json
import psycopg2
import shutil
from psycopg2.extras import Json
from pathlib import Path
from dotenv import load_dotenv
from abc import ABC, abstractmethod
import sys

# 将父目录加入路径以确保能找到 connection
CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
sys.path.append(str(BACKEND_DIR))

# 🌟 引入数据库连接池
try:
    from database.connection import get_connection
except ImportError:
    from connection import get_connection

# ==========================================
# 1. 环境与配置初始化
# ==========================================
load_dotenv(BACKEND_DIR / ".env")

# ==========================================
# 2. Embedding 抽象基类与具体实现
# ==========================================
class BaseEmbeddingProvider(ABC):
    @abstractmethod
    def get_embedding(self, text: str) -> list[float]:
        pass

class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, api_key: str, model_id: str):
        from google import genai
        self.client = genai.Client(api_key=api_key)
        self.model_id = model_id

    def get_embedding(self, text: str) -> list[float]:
        print(f"🧠 [Gemini] 正在生成向量: '{text[:15]}...'")
        response = self.client.models.embed_content(
            model=self.model_id,
            contents=text,
        )
        return response.embeddings[0].values

class DoubaoEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, api_key: str, model_id: str):
        from volcenginesdkarkruntime import Ark
        self.client = Ark(api_key=api_key)
        self.model_id = model_id

    def get_embedding(self, text: str) -> list[float]:
        print(f"🧠 [Doubao] 正在生成向量: '{text[:15]}...'")
        response = self.client.embeddings.create(
            model=self.model_id,
            input=[text]
        )
        return response.data[0].embedding

class EmbeddingFactory:
    @staticmethod
    def create_provider() -> BaseEmbeddingProvider:
        provider_type = os.getenv("EMBED_ACTIVE_PROVIDER", "doubao").lower()
        if provider_type == "gemini":
            api_key = os.getenv("EMBED_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
            model_id = os.getenv("EMBED_GEMINI_MODEL_ID", "gemini-embedding-001")
            return GeminiEmbeddingProvider(api_key, model_id)
        elif provider_type == "doubao":
            api_key = os.getenv("EMBED_DOUBAO_API_KEY")
            model_id = os.getenv("EMBED_DOUBAO_MODEL_ID")
            return DoubaoEmbeddingProvider(api_key, model_id)
        raise ValueError(f"❌ 不支持的 Provider: {provider_type}")


def ensure_vocabulary_knowledge_table(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS vocabulary_knowledge (
            course_id INTEGER NOT NULL,
            lesson_id INTEGER NOT NULL,
            word TEXT NOT NULL,
            pinyin TEXT,
            part_of_speech TEXT,
            definition TEXT NOT NULL,
            example JSONB DEFAULT '{}'::jsonb,
            PRIMARY KEY (course_id, lesson_id, word, definition)
        );
    """)

# ==========================================
# 3. 核心入库逻辑 (已适配新字段)
# ==========================================
def sync_lesson_data(json_file_path: str, provider: BaseEmbeddingProvider) -> bool:
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    lesson_metadata = data.get("lesson_metadata", {})
    course_content = data.get("course_content", {})
    database_items = data.get("database_items", [])
    vocabulary_items = course_content.get("vocabulary", []) if isinstance(course_content, dict) else []
    structured_lesson_payload = {
        "lesson_metadata": lesson_metadata,
        "course_content": course_content,
    }

    course_id = lesson_metadata.get("course_id")
    lesson_id = lesson_metadata.get("lesson_id")
    title = lesson_metadata.get("title")

    conn = None
    cur = None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        ensure_vocabulary_knowledge_table(cur)

        vocab_lookup = {}
        for vocab in vocabulary_items:
            if not isinstance(vocab, dict):
                continue
            word_key = (vocab.get("word") or "").strip()
            if word_key:
                vocab_lookup[word_key] = vocab

        # 1. 同步 lessons 表
        print(f"📦 同步 Lesson {lesson_id} 基础数据...")
        cur.execute("SELECT 1 FROM lessons WHERE course_id = %s AND lesson_id = %s", (course_id, lesson_id))
        
        if cur.fetchone():
            cur.execute("""
                UPDATE lessons SET title = %s, structured_content = %s
                WHERE course_id = %s AND lesson_id = %s
            """, (title, Json(structured_lesson_payload), course_id, lesson_id))
        else:
            cur.execute("""
                INSERT INTO lessons (course_id, lesson_id, title, structured_content)
                VALUES (%s, %s, %s, %s)
            """, (course_id, lesson_id, title, Json(structured_lesson_payload)))

        # 2. 同步 language_items 表
        print(f"🎯 正在处理 {len(database_items)} 道深度解析题目...")
        for item in database_items:
            q_id = item['question_id']
            # 🚀 提取新增字段
            q_pinyin = item.get('original_pinyin', '')
            q_type = item.get('question_type')

            vocab_word = ""
            if q_type == "CN_TO_EN":
                vocab_word = (item.get('original_text') or '').strip()
            elif q_type == "EN_TO_CN":
                standard_answers = item.get('standard_answers') or []
                vocab_word = (standard_answers[0] if standard_answers else '').strip()

            vocab_entry = vocab_lookup.get(vocab_word, {})
            current_example = vocab_entry.get("example_sentence", {}) if isinstance(vocab_entry, dict) else {}
            historical_usages = vocab_entry.get("historical_usages", []) if isinstance(vocab_entry, dict) else []

            history_cards = []
            current_definition = (vocab_entry.get("definition") or "").strip().lower() if isinstance(vocab_entry, dict) else ""
            if isinstance(historical_usages, list):
                for usage in historical_usages:
                    if not isinstance(usage, dict):
                        continue
                    usage_definition = (usage.get("definition") or "").strip()
                    if usage_definition.lower() == current_definition:
                        continue
                    history_cards.append({
                        "definition": usage_definition,
                        "pinyin": usage.get("pinyin"),
                        "part_of_speech": usage.get("part_of_speech"),
                        "example": usage.get("example", {}),
                        "lesson_id": usage.get("lesson_id")
                    })

            q_metadata = {
                "context_examples": item.get('context_examples', []),
                "knowledge": {
                    "word": vocab_word or vocab_entry.get("word", ""),
                    "pinyin": vocab_entry.get("pinyin", q_pinyin),
                    "part_of_speech": vocab_entry.get("part_of_speech", ""),
                    "definition": vocab_entry.get("definition", ""),
                    "example_sentence": current_example,
                    "history": history_cards
                }
            }

            item_metadata = item.get("metadata", {})
            if isinstance(item_metadata, dict):
                q_metadata.update(item_metadata)

            if isinstance(vocab_entry, dict) and (vocab_entry.get("word") or "").strip():
                cur.execute("""
                    INSERT INTO vocabulary_knowledge
                    (course_id, lesson_id, word, pinyin, part_of_speech, definition, example)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (course_id, lesson_id, word, definition)
                    DO UPDATE SET
                        pinyin = EXCLUDED.pinyin,
                        part_of_speech = EXCLUDED.part_of_speech,
                        example = EXCLUDED.example;
                """, (
                    course_id,
                    lesson_id,
                    (vocab_entry.get("word") or "").strip(),
                    vocab_entry.get("pinyin"),
                    vocab_entry.get("part_of_speech"),
                    vocab_entry.get("definition"),
                    Json(vocab_entry.get("example_sentence", {}))
                ))

            # 生成向量 (取第一个答案作为基准)
            embedding = provider.get_embedding(item['standard_answers'][0])
            embedding_str = str(embedding)

            cur.execute("""
                SELECT 1 FROM language_items 
                WHERE course_id = %s AND lesson_id = %s AND question_id = %s
            """, (course_id, lesson_id, q_id))
            
            if cur.fetchone():
                cur.execute("""
                    UPDATE language_items 
                    SET question_type = %s, original_text = %s, original_pinyin = %s, 
                        standard_answers = %s, primary_embedding = %s, metadata = %s
                    WHERE course_id = %s AND lesson_id = %s AND question_id = %s
                """, (item['question_type'], item['original_text'], q_pinyin, 
                      item['standard_answers'], embedding_str, Json(q_metadata), 
                      course_id, lesson_id, q_id))
            else:
                cur.execute("""
                    INSERT INTO language_items 
                    (course_id, lesson_id, question_id, question_type, original_text, 
                     original_pinyin, standard_answers, primary_embedding, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (course_id, lesson_id, q_id, item['question_type'], 
                      item['original_text'], q_pinyin, item['standard_answers'], 
                      embedding_str, Json(q_metadata)))
            
        conn.commit()
        print(f"✅ 入库成功！包含题目拼音与例句上下文。")
        return True

    except Exception as e:
        print(f"❌ 入库失败: {e}")
        if conn: conn.rollback()
        return False
    finally:
        if cur: cur.close()
        if conn: conn.close()

# ==========================================
# 4. 执行入口
# ==========================================
if __name__ == "__main__":
    embed_provider = EmbeddingFactory.create_provider()
    
    # 路径绑定
    content_builder_dir = CURRENT_DIR.parent / "content_builder"
    output_dir = content_builder_dir / "output_json"
    synced_dir = content_builder_dir / "synced_json"
    synced_dir.mkdir(exist_ok=True)
    
    json_files = list(output_dir.glob("*.json"))
    if not json_files:
        print("📭 没有待处理的 JSON 文件。")
    else:
        for target_json in json_files:
            print(f"\n🚀 开始同步: {target_json.name}")
            if sync_lesson_data(str(target_json), embed_provider):
                shutil.move(str(target_json), str(synced_dir / target_json.name))
