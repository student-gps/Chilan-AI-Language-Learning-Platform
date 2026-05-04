import os
import json
import time
from abc import ABC, abstractmethod
from json_repair import repair_json  # 必须安装: pip install json-repair
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

from config.env import get_env

class BaseLLMProvider(ABC):
    """定义所有模型必须实现的标准接口"""

    def __init__(self):
        self._usage_log = []
    
    @abstractmethod
    def generate_structured_json(self, prompt: str, file_path: str = None, file_obj=None) -> dict:
        """支持直接传入路径或已上传的文件对象"""
        pass

    def upload_pdf(self, file_path: str):
        """预上传 PDF 文件的标准接口（主要为 Gemini 设计）"""
        return None

    def reset_usage_log(self):
        self._usage_log = []

    def get_usage_summary(self) -> dict:
        input_tokens = sum(int(item.get("input_tokens", 0) or 0) for item in self._usage_log)
        output_tokens = sum(int(item.get("output_tokens", 0) or 0) for item in self._usage_log)
        total_tokens = sum(int(item.get("total_tokens", 0) or 0) for item in self._usage_log)
        estimated_cost = sum(float(item.get("estimated_cost_usd", 0.0) or 0.0) for item in self._usage_log)
        return {
            "calls": len(self._usage_log),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": round(estimated_cost, 6),
            "provider": type(self).__name__,
            "items": list(self._usage_log),
        }

    def _record_usage(self, input_tokens=0, output_tokens=0, total_tokens=0, estimated_cost_usd=0.0, meta: dict = None):
        self._usage_log.append({
            "input_tokens": int(input_tokens or 0),
            "output_tokens": int(output_tokens or 0),
            "total_tokens": int(total_tokens or 0),
            "estimated_cost_usd": float(estimated_cost_usd or 0.0),
            "meta": meta or {},
        })

    @staticmethod
    def _to_simplified(obj):
        """递归将 JSON 对象中所有字符串的繁体汉字转换为简体。
        只处理字符串值，不触碰键名、数字、布尔值等。"""
        try:
            import zhconv
        except ImportError:
            return obj  # 未安装时静默跳过，不中断流程

        def _walk(node):
            if isinstance(node, str):
                return zhconv.convert(node, "zh-hans")
            if isinstance(node, dict):
                return {k: _walk(v) for k, v in node.items()}
            if isinstance(node, list):
                return [_walk(item) for item in node]
            return node

        return _walk(obj)

    def _safe_parse_json(self, raw_text: str) -> dict:
        """通用的 JSON 提取与自动修复逻辑"""
        if not raw_text:
            raise ValueError("❌ 收到空的原始文本，无法进行 JSON 解析。")

        # 1. 清理 Markdown 标记
        clean_text = raw_text.strip()
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_text:
            clean_text = clean_text.split("```")[1].split("```")[0].strip()

        # 2. 尝试标准解析
        try:
            return self._to_simplified(json.loads(clean_text))
        except json.JSONDecodeError as parse_error:
            # 3. 如果标准解析失败，启动 json-repair 自动缝补
            try:
                start = max(0, parse_error.pos - 120)
                end = min(len(clean_text), parse_error.pos + 120)
                snippet = clean_text[start:end].replace("\n", "\\n")
                print(
                    "⚠️ 检测到 JSON 语法错误，正在启动自动缝补..."
                    f" ({parse_error.msg} @ line {parse_error.lineno}, col {parse_error.colno}; "
                    f"near: {snippet[:240]})"
                )
                repaired_json_str = repair_json(clean_text)
                return self._to_simplified(json.loads(repaired_json_str))
            except Exception as e:
                # 4. 如果缝补也失败，抛出详细错误
                raise Exception(f"❌ JSON 深度修复失败: {e}\n原始片段: {raw_text[-150:]}")

class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model_id: str, use_vertex: bool = False,
                 vertex_project: str = None, vertex_location: str = "us-central1",
                 vertex_fallback_locations: list = None):
        super().__init__()
        from google import genai
        self.model_id = model_id
        self.use_vertex = use_vertex
        self._vertex_project = vertex_project
        if use_vertex:
            all_locs = [vertex_location]
            for loc in (vertex_fallback_locations or []):
                if loc not in all_locs:
                    all_locs.append(loc)
            self._vertex_locations = all_locs
            self._location_idx = 0
            self.client = self._make_vertex_client(vertex_location)
        else:
            self._vertex_locations = []
            self._location_idx = 0
            self.client = genai.Client(api_key=api_key)

    def _make_vertex_client(self, location: str):
        from google import genai
        return genai.Client(vertexai=True, project=self._vertex_project, location=location)

    def _rotate_region(self) -> bool:
        """Switch to the next region (wraps around). Returns False only when no fallbacks configured."""
        if len(self._vertex_locations) <= 1:
            return False
        self._location_idx = (self._location_idx + 1) % len(self._vertex_locations)
        new_location = self._vertex_locations[self._location_idx]
        print(f"  🔄 区域配额耗尽，自动切换 → {new_location}")
        self.client = self._make_vertex_client(new_location)
        return True

    def _drop_current_region(self) -> bool:
        """Permanently remove the current region (model not available there). Returns False if none left."""
        if not self._vertex_locations:
            return False
        bad = self._vertex_locations[self._location_idx]
        self._vertex_locations.pop(self._location_idx)
        if not self._vertex_locations:
            print(f"  ❌ 区域 {bad} 不支持当前模型，且已无可用备用区域。")
            return False
        self._location_idx = self._location_idx % len(self._vertex_locations)
        new_location = self._vertex_locations[self._location_idx]
        print(f"  ⚠️ 区域 {bad} 不支持当前模型，已永久移除，切换 → {new_location}")
        self.client = self._make_vertex_client(new_location)
        return True

    @staticmethod
    def _pricing_table() -> dict:
        # Paid tier standard pricing, per 1M tokens in USD.
        # Source: Google AI for Developers Gemini Developer API pricing
        # https://ai.google.dev/gemini-api/docs/pricing
        return {
            "gemini-2.0-flash": {"input_per_m": 0.10, "output_per_m": 0.40},
            "gemini-2.0-flash-lite": {"input_per_m": 0.075, "output_per_m": 0.30},
            "gemini-2.5-flash": {"input_per_m": 0.30, "output_per_m": 2.50},
            "gemini-2.5-flash-lite": {"input_per_m": 0.10, "output_per_m": 0.40},
            "gemini-2.5-pro": {"input_per_m": 1.25, "output_per_m": 10.00},
            "gemini-3-flash-preview": {"input_per_m": 0.50, "output_per_m": 3.00},
            "gemini-3.1-flash-lite-preview": {"input_per_m": 0.25, "output_per_m": 1.50},
            "gemini-3.1-pro-preview": {"input_per_m": 2.00, "output_per_m": 12.00},
        }

    def _estimate_cost_usd(self, prompt_tokens: int, completion_tokens: int) -> tuple[float, dict]:
        table = self._pricing_table()
        pricing = table.get(self.model_id)
        if not pricing:
            return 0.0, {
                "pricing_source": "unmapped_model",
                "pricing_mode": "unknown",
            }

        estimated_cost = (
            (prompt_tokens / 1_000_000) * pricing["input_per_m"] +
            (completion_tokens / 1_000_000) * pricing["output_per_m"]
        )
        return estimated_cost, {
            "pricing_source": "https://ai.google.dev/gemini-api/docs/pricing",
            "pricing_mode": "paid_tier_standard",
            "input_price_per_m_tokens_usd": pricing["input_per_m"],
            "output_price_per_m_tokens_usd": pricing["output_per_m"],
        }

    def upload_pdf(self, file_path: str):
        """上传/读取 PDF。Vertex AI 模式下直接 inline bytes，否则走 Gemini Files API。"""
        from google.genai import types
        print(f"📤 正在加载教材: {os.path.basename(file_path)}")
        if self.use_vertex:
            pdf_bytes = Path(file_path).read_bytes()
            print("✅ 文件处理就绪（Vertex AI inline 模式）。")
            return types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf")

        with open(file_path, "rb") as f:
            sample_file = self.client.files.upload(
                file=f,
                config={'mime_type': 'application/pdf'}
            )
        while sample_file.state == "PROCESSING":
            time.sleep(2)
            sample_file = self.client.files.get(name=sample_file.name)
        if sample_file.state == "FAILED":
            raise Exception(f"❌ Gemini 处理文件失败: {file_path}")
        print("✅ 文件处理就绪。")
        return sample_file

    def generate_structured_json(self, prompt: str, file_path: str = None, file_obj=None) -> dict:
        from google.genai import types 
        contents = [prompt]
        
        if file_obj:
            contents.append(file_obj)
        elif file_path:
            file_obj = self.upload_pdf(file_path)
            contents.append(file_obj)

        # 🚀 修正后的安全设置：必须使用 HARM_CATEGORY_ 前缀的全称
        safety_settings = [
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_CIVIC_INTEGRITY", threshold="BLOCK_NONE"),
        ]

        max_retries = 24  # 足够覆盖多区域轮转 + 等待重试
        retry_waits = [5, 10, 20, 30, 45, 60, 90]
        response = None
        wait_attempt = 0        # 等待重试计数（切区域不消耗此计数）
        region_cycle_count = 0  # 连续切区域次数，满一轮就强制等待
        num_regions = max(1, len(self._vertex_locations))
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=contents,
                    config={
                        'response_mime_type': 'application/json',
                        'temperature': 0.0,
                        'max_output_tokens': 32768,
                        'safety_settings': safety_settings
                    }
                )
                break  # 成功则退出重试循环
            except Exception as e:
                err_str = str(e)
                is_quota = "RESOURCE_EXHAUSTED" in err_str or "429" in err_str
                is_model_missing = "NOT_FOUND" in err_str and self.use_vertex
                is_region_unavail = is_quota  # quota = transient, rotate and count
                is_retryable = is_quota or is_model_missing or any(code in err_str for code in ("503", "UNAVAILABLE"))
                if not is_retryable or attempt >= max_retries - 1:
                    raise Exception(f"❌ Gemini API 调用失败: {e}")
                # 404 NOT_FOUND：该区域永久不支持模型，直接移除，不计入轮转计数
                if is_model_missing and self.use_vertex:
                    if not self._drop_current_region():
                        raise Exception(f"❌ Gemini API 调用失败: {e}")
                    num_regions = max(1, len(self._vertex_locations))
                    continue
                # 配额耗尽：轮转区域，但跑完一整圈后强制等待一轮再继续
                if is_region_unavail and self.use_vertex:
                    if region_cycle_count < num_regions:
                        self._rotate_region()
                        region_cycle_count += 1
                        continue  # 立即用新区域重试，不等待
                    else:
                        # 跑完一整圈仍失败，等待后重置计数再轮
                        region_cycle_count = 0
                wait = retry_waits[min(wait_attempt, len(retry_waits) - 1)]
                print(f"  ⏳ Gemini 暂时不可用，{wait}s 后重试 (第 {wait_attempt+1} 次)...")
                time.sleep(wait)
                wait_attempt += 1
        if response is None:
            raise Exception("❌ Gemini API 多次重试后仍未返回结果")
        
        if not response.text:
            candidate = response.candidates[0] if response.candidates else None
            finish_reason = getattr(candidate, 'finish_reason', 'UNKNOWN')
            raise Exception(f"❌ Gemini 返回空。原因: {finish_reason}")

        usage = getattr(response, "usage_metadata", None)
        prompt_tokens = getattr(usage, "prompt_token_count", 0) if usage else 0
        completion_tokens = getattr(usage, "candidates_token_count", 0) if usage else 0
        total_tokens = getattr(usage, "total_token_count", 0) if usage else (prompt_tokens + completion_tokens)
        candidate = response.candidates[0] if getattr(response, "candidates", None) else None
        finish_reason = getattr(candidate, "finish_reason", "UNKNOWN")
        estimated_cost_usd, pricing_meta = self._estimate_cost_usd(prompt_tokens, completion_tokens)
        self._record_usage(
            input_tokens=prompt_tokens,
            output_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=estimated_cost_usd,
            meta={
                "model": self.model_id,
                "finish_reason": str(finish_reason),
                **pricing_meta,
            }
        )
            
        return self._safe_parse_json(response.text)

class ClaudeProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model_id: str):
        super().__init__()
        from anthropic import Anthropic
        self.client = Anthropic(api_key=api_key)
        self.model_id = model_id

    def generate_structured_json(self, prompt: str, file_path: str = None, file_obj=None) -> dict:
        import base64
        content_array = []
        if file_path:
            with open(file_path, "rb") as f:
                pdf_data = base64.b64encode(f.read()).decode("utf-8")
            content_array.append({
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": pdf_data
                }
            })
            
        content_array.append({
            "type": "text",
            "text": f"{prompt}\n\n请严格且仅输出 JSON 格式。"
        })

        response = self.client.messages.create(
            model=self.model_id,
            max_tokens=8192,
            temperature=0.0,
            messages=[{"role": "user", "content": content_array}]
        )
        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "input_tokens", 0) if usage else 0
        output_tokens = getattr(usage, "output_tokens", 0) if usage else 0
        self._record_usage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            estimated_cost_usd=0.0,
            meta={"model": self.model_id}
        )
        return self._safe_parse_json(response.content[0].text)

class DoubaoProvider(BaseLLMProvider):
    def __init__(self, api_key: str, endpoint_id: str):
        super().__init__()
        from volcenginesdkarkruntime import Ark
        self.client = Ark(api_key=api_key)
        self.endpoint_id = endpoint_id

    def generate_structured_json(self, prompt: str, file_path: str = None, file_obj=None) -> dict:
        content_list = []
        if file_path:
            import fitz  
            import base64
            try:
                pdf_document = fitz.open(file_path)
                for page_num in range(len(pdf_document)):
                    page = pdf_document.load_page(page_num)
                    pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
                    img_data = pix.tobytes("png")
                    base64_str = base64.b64encode(img_data).decode("utf-8")
                    content_list.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_str}"}
                    })
            except Exception as e:
                raise Exception(f"本地渲染 PDF 图片失败: {e}")

        content_list.append({"type": "text", "text": prompt})

        response = self.client.chat.completions.create(
            model=self.endpoint_id,
            messages=[{"role": "user", "content": content_list}],
            temperature=0.0,
            max_tokens=8192  
        )
        usage = getattr(response, "usage", None)
        prompt_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
        completion_tokens = getattr(usage, "completion_tokens", 0) if usage else 0
        total_tokens = getattr(usage, "total_tokens", 0) if usage else (prompt_tokens + completion_tokens)
        self._record_usage(
            input_tokens=prompt_tokens,
            output_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=0.0,
            meta={"model": self.endpoint_id}
        )
        return self._safe_parse_json(response.choices[0].message.content)

class LLMFactory:
    """根据配置文件分发具体的模型 Provider"""
    @staticmethod
    def create_provider() -> BaseLLMProvider:
        provider_type = get_env("LLM_CONTENT_PROVIDER", default="gemini").lower()

        if provider_type == "gemini":
            model_id = get_env("LLM_CONTENT_GEMINI_MODEL_ID", default="gemini-2.0-flash")
            use_vertex = get_env("LLM_GEMINI_USE_VERTEX", default="false").lower() == "true"
            if use_vertex:
                project = get_env("VERTEX_AI_PROJECT_ID")
                location = get_env("VERTEX_AI_LOCATION", default="us-central1")
                fallback_raw = get_env("VERTEX_AI_FALLBACK_LOCATIONS", default="")
                fallback_locations = [l.strip() for l in fallback_raw.split(",") if l.strip()]
                sa_key = get_env("GOOGLE_APPLICATION_CREDENTIALS")
                if sa_key:
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = sa_key
                if not project: raise ValueError("❌ Vertex AI 需要配置 VERTEX_AI_PROJECT_ID")
                if fallback_locations:
                    print(f"  ℹ️  Vertex AI 区域轮转已启用: {location} → {' → '.join(fallback_locations)}")
                return GeminiProvider(api_key=None, model_id=model_id,
                                      use_vertex=True, vertex_project=project,
                                      vertex_location=location,
                                      vertex_fallback_locations=fallback_locations)
            api_key = get_env("LLM_CONTENT_GEMINI_API_KEY", "LLM_GEMINI_API_KEY")
            if not api_key: raise ValueError("❌ 未找到 Gemini API Key")
            return GeminiProvider(api_key, model_id)

        elif provider_type == "claude":
            api_key = get_env("LLM_CONTENT_CLAUDE_API_KEY")
            model_id = get_env("LLM_CONTENT_CLAUDE_MODEL_ID", default="claude-3-5-sonnet-latest")
            if not api_key: raise ValueError("❌ 未找到 Claude API Key")
            return ClaudeProvider(api_key, model_id)

        elif provider_type == "doubao":
            api_key = get_env("LLM_CONTENT_DOUBAO_API_KEY")
            endpoint_id = get_env("LLM_CONTENT_DOUBAO_ENDPOINT_ID")
            if not api_key or not endpoint_id: raise ValueError("❌ 未找到 Doubao 配置")
            return DoubaoProvider(api_key, endpoint_id)

        else:
            raise ValueError(f"❌ 不支持的模型类型: {provider_type}")

    @staticmethod
    def create_fallback_provider() -> "BaseLLMProvider | None":
        """返回用于重试的高能力备用 Provider（模型更强但更贵）。

        仅当 LLM_CONTENT_GEMINI_FALLBACK_MODEL_ID 已配置时才返回实例，
        否则返回 None（调用方降级为继续使用主 provider）。
        目前仅支持 Gemini provider 的 model 切换。
        """
        provider_type = get_env("LLM_CONTENT_PROVIDER", default="gemini").lower()
        if provider_type != "gemini":
            return None

        fallback_model = get_env("LLM_CONTENT_GEMINI_FALLBACK_MODEL_ID", default="")
        if not fallback_model:
            return None

        use_vertex = get_env("LLM_GEMINI_USE_VERTEX", default="false").lower() == "true"
        if use_vertex:
            project = get_env("VERTEX_AI_PROJECT_ID")
            location = get_env("VERTEX_AI_LOCATION", default="us-central1")
            fallback_raw = get_env("VERTEX_AI_FALLBACK_LOCATIONS", default="")
            fallback_locations = [l.strip() for l in fallback_raw.split(",") if l.strip()]
            sa_key = get_env("GOOGLE_APPLICATION_CREDENTIALS")
            if sa_key:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = sa_key
            if not project:
                return None
            return GeminiProvider(api_key=None, model_id=fallback_model,
                                  use_vertex=True, vertex_project=project,
                                  vertex_location=location,
                                  vertex_fallback_locations=fallback_locations)

        api_key = get_env("LLM_CONTENT_GEMINI_API_KEY", "LLM_GEMINI_API_KEY")
        if not api_key:
            return None
        return GeminiProvider(api_key, fallback_model)
