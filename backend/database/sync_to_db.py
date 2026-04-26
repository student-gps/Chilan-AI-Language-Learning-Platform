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

from config.env import get_env

# 🌟 引入数据库连接池
try:
    from database.connection import get_connection
except ImportError:
    from connection import get_connection

try:
    from services.storage.media_storage import get_media_storage
except ImportError:
    get_media_storage = None

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
        provider_type = get_env("LLM_EMBED_PROVIDER", default="doubao").lower()
        if provider_type == "gemini":
            api_key = get_env("LLM_EMBED_GEMINI_API_KEY", "LLM_GEMINI_API_KEY")
            model_id = get_env("LLM_EMBED_GEMINI_MODEL_ID", default="gemini-embedding-001")
            return GeminiEmbeddingProvider(api_key, model_id)
        elif provider_type == "doubao":
            api_key = get_env("LLM_EMBED_DOUBAO_API_KEY")
            model_id = get_env("LLM_EMBED_DOUBAO_MODEL_ID")
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
# 3. R2 上传（入库前统一执行）
# ==========================================
def upload_assets_to_r2(data: dict) -> dict:
    """
    上传 data 中所有本地音频/视频文件到 R2，并将 object_key 和 audio_url/media_url 写回 data。
    如果 R2 未配置或文件不存在，静默跳过。
    返回更新后的 data（原地修改，同时也返回以便链式调用）。
    """
    if get_media_storage is None:
        return data

    r2 = get_media_storage(optional=True)
    if not r2:
        print("ℹ️ R2 未配置，跳过资源上传（仅本地可用）。")
        return data

    uploaded = 0
    failed = 0

    _artifacts_dir = BACKEND_DIR / "content_builder" / "artifacts"

    def _resolve_path(local_path: str) -> Path:
        """Try absolute path first; fall back to resolving relative to current artifacts dir."""
        p = Path(local_path)
        if p.exists():
            return p
        # Path was generated on a different machine — find 'artifacts' segment and re-root
        parts = p.parts
        try:
            idx = next(i for i, part in enumerate(parts) if part.lower() == "artifacts")
            candidate = _artifacts_dir / Path(*parts[idx + 1:])
            if candidate.exists():
                return candidate
        except StopIteration:
            pass
        return p  # return original (non-existent) path so caller can report it

    def _upload(local_path: str, object_key: str, content_type: str, label: str) -> str:
        """上传单个文件，返回上传成功后的 object_key（失败返回原 object_key）。"""
        nonlocal uploaded, failed
        p = _resolve_path(local_path)
        if not p.exists():
            print(f"  ⚠️ 文件不存在，跳过: {p.name}")
            return object_key
        try:
            result = r2.upload_file(str(p), object_key, content_type=content_type)
            print(f"  ☁️ 已上传 [{label}]: {object_key}")
            uploaded += 1
            return result.get("object_key", object_key)
        except Exception as e:
            print(f"  ⚠️ R2 上传失败 [{label}]: {e}")
            failed += 1
            return object_key

    # ── 1. 课文逐句音频 ──────────────────────────────────────────────────
    lesson_audio = data.get("lesson_audio_assets", {})
    if isinstance(lesson_audio, dict):
        for item in lesson_audio.get("items", []):
            if not isinstance(item, dict):
                continue
            local = (item.get("local_audio_file") or "").strip()
            key   = (item.get("object_key") or "").strip()
            if local and key:
                item["object_key"] = _upload(local, key, "audio/mpeg", f"line {item.get('line_ref', '?')}")

        # ── 2. 整课合并音频 ──────────────────────────────────────────────
        full = lesson_audio.get("full_audio", {})
        if isinstance(full, dict):
            local = (full.get("local_audio_file") or "").strip()
            key   = (full.get("object_key") or "").strip()
            if local and key:
                full["object_key"] = _upload(local, key, "audio/mpeg", "full_audio")

    # ── 3. 讲解视频 ──────────────────────────────────────────────────────
    video_urls = data.get("explanation_video_urls", {})
    if isinstance(video_urls, dict):
        local = (video_urls.get("local_path") or "").strip()
        key   = (video_urls.get("object_key") or "").strip()
        if local and key:
            video_urls["object_key"] = _upload(local, key, "video/mp4", "explanation_video")
            video_urls["media_url"]  = ""   # 由 study router 在请求时生成签名 URL

    print(f"  📊 R2 上传完成：成功 {uploaded} 个，失败 {failed} 个。")
    return data


# ==========================================
# 4. 核心入库逻辑
# ==========================================
def sync_lesson_data(json_file_path: str, provider: BaseEmbeddingProvider) -> bool:
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    lesson_metadata = data.get("lesson_metadata", {})
    course_content = data.get("course_content", {})
    teaching_materials = data.get("teaching_materials", {}) if isinstance(data.get("teaching_materials"), dict) else {}
    database_items = data.get("database_items", [])
    video_plan             = data.get("video_plan", {})             if isinstance(data.get("video_plan"), dict)             else {}
    video_render_plan      = data.get("video_render_plan", {})      if isinstance(data.get("video_render_plan"), dict)      else {}
    lesson_audio_assets    = data.get("lesson_audio_assets", {})    if isinstance(data.get("lesson_audio_assets"), dict)    else {}
    llm_usage              = data.get("llm_usage", {})              if isinstance(data.get("llm_usage"), dict)              else {}
    explanation_video_urls = data.get("explanation_video_urls", {}) if isinstance(data.get("explanation_video_urls"), dict) else {}
    vocabulary_items = course_content.get("vocabulary", []) if isinstance(course_content, dict) else []

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

        col_values = (
            title,
            Json(lesson_metadata),
            Json(course_content),
            Json(teaching_materials),
            Json(video_plan),
            Json(video_render_plan),
            Json(lesson_audio_assets),
            Json(explanation_video_urls),
            Json(llm_usage),
        )

        if cur.fetchone():
            cur.execute("""
                UPDATE lessons SET
                  title                  = %s,
                  lesson_metadata        = %s,
                  course_content         = %s,
                  teaching_materials     = %s,
                  video_plan             = %s,
                  video_render_plan      = %s,
                  lesson_audio_assets    = %s,
                  explanation_video_urls = %s,
                  llm_usage              = %s
                WHERE course_id = %s AND lesson_id = %s
            """, col_values + (course_id, lesson_id))
        else:
            cur.execute("""
                INSERT INTO lessons (
                  course_id, lesson_id, title,
                  lesson_metadata, course_content, teaching_materials,
                  video_plan, video_render_plan, lesson_audio_assets,
                  explanation_video_urls, llm_usage
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (course_id, lesson_id) + col_values)

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
# 5. 执行入口
# ==========================================
if __name__ == "__main__":
    embed_provider = EmbeddingFactory.create_provider()

    # 路径绑定
    content_builder_dir = CURRENT_DIR.parent / "content_builder"
    artifacts_dir = content_builder_dir / "artifacts"
    output_dir = artifacts_dir / "output_json" / "en"
    synced_dir = artifacts_dir / "synced_json" / "en"
    synced_dir.mkdir(parents=True, exist_ok=True)

    json_files = list(output_dir.glob("*_data.json"))
    if not json_files:
        print("📭 没有待处理的 JSON 文件。")
    else:
        for target_json in json_files:
            print(f"\n🚀 开始处理: {target_json.name}")

            with open(target_json, encoding="utf-8") as _f:
                lesson_data = json.load(_f)

            print("☁️ 上传本地资产到 R2...")
            lesson_data = upload_assets_to_r2(lesson_data)

            # 写回更新后的 object_key（供入库使用）
            with open(target_json, "w", encoding="utf-8") as _f:
                json.dump(lesson_data, _f, ensure_ascii=False, indent=2)

            if sync_lesson_data(str(target_json), embed_provider):
                shutil.move(str(target_json), str(synced_dir / target_json.name))
