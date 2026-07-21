import json
import sys
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

from content_builder.core.llm_providers import LLMFactory, OpenAIProvider


class OpenAICompatibleProviderTests(unittest.TestCase):
    @patch("content_builder.core.llm_providers.OpenAIProvider._render_pdf_pages_to_data_urls")
    @patch("openai.OpenAI")
    def test_openai_provider_passes_base_url_and_reuses_uploaded_pdf_images(self, mock_openai, mock_render_pdf):
        mock_render_pdf.return_value = ["data:image/png;base64,page1", "data:image/png;base64,page2"]

        response = MagicMock()
        response.usage = MagicMock(prompt_tokens=12, completion_tokens=4, total_tokens=16)
        response.choices = [
            MagicMock(message=MagicMock(content='{"ok": true}'))
        ]
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = response
        mock_openai.return_value = mock_client

        with patch.dict(
            "os.environ",
            {
                "LLM_CONTENT_OPENAI_TIMEOUT_SECONDS": "180",
                "LLM_CONTENT_OPENAI_MAX_RETRIES": "6",
            },
            clear=False,
        ):
            provider = OpenAIProvider(
                api_key="cec",
                model_id="azure-gpt-5_4",
                base_url="https://cec-azure-gpt-5-4.dev.fc.chj.cloud/agentops",
            )

            file_obj = provider.upload_pdf("lesson101.pdf")
            result = provider.generate_structured_json("Return JSON", file_obj=file_obj)

        self.assertEqual(result, {"ok": True})
        mock_openai.assert_called_once_with(
            api_key="cec",
            base_url="https://cec-azure-gpt-5-4.dev.fc.chj.cloud/agentops",
            timeout=180.0,
            max_retries=0,
        )
        mock_render_pdf.assert_called_once_with("lesson101.pdf")

        kwargs = mock_client.chat.completions.create.call_args.kwargs
        self.assertEqual(kwargs["model"], "azure-gpt-5_4")
        self.assertEqual(kwargs["temperature"], 0.0)
        self.assertEqual(kwargs["max_tokens"], 32768)
        content = kwargs["messages"][0]["content"]
        self.assertEqual(content[0], {"type": "image_url", "image_url": {"url": "data:image/png;base64,page1"}})
        self.assertEqual(content[1], {"type": "image_url", "image_url": {"url": "data:image/png;base64,page2"}})
        self.assertEqual(content[-1]["type"], "text")
        self.assertIn("Return valid JSON only", content[-1]["text"])

        usage = provider.get_usage_summary()
        self.assertEqual(usage["calls"], 1)
        self.assertEqual(usage["input_tokens"], 12)
        self.assertEqual(usage["output_tokens"], 4)
        self.assertEqual(usage["items"][0]["meta"]["base_url"], "https://cec-azure-gpt-5-4.dev.fc.chj.cloud/agentops")
        self.assertEqual(usage["items"][0]["meta"]["timeout_seconds"], 180)
        self.assertEqual(usage["items"][0]["meta"]["max_retries"], 6)

    @patch.dict(
        "os.environ",
        {
            "LLM_CONTENT_PROVIDER": "openai",
            "LLM_CONTENT_OPENAI_MODEL_ID": "azure-gpt-5_4",
            "LLM_CONTENT_OPENAI_BASE_URL": "https://cec-azure-gpt-5-4.dev.fc.chj.cloud/agentops",
            "LLM_CONTENT_OPENAI_API_KEY": "",
            "LLM_OPENAI_API_KEY": "cec",
            "LLM_CONTENT_OPENAI_TIMEOUT_SECONDS": "180",
            "LLM_CONTENT_OPENAI_MAX_RETRIES": "6",
        },
        clear=False,
    )
    @patch("openai.OpenAI")
    def test_factory_uses_shared_openai_key_fallback(self, mock_openai):
        provider = LLMFactory.create_provider()

        self.assertIsInstance(provider, OpenAIProvider)
        mock_openai.assert_called_once_with(
            api_key="cec",
            base_url="https://cec-azure-gpt-5-4.dev.fc.chj.cloud/agentops",
            timeout=180.0,
            max_retries=0,
        )
        self.assertEqual(provider.model_id, "azure-gpt-5_4")
        self.assertEqual(provider.base_url, "https://cec-azure-gpt-5-4.dev.fc.chj.cloud/agentops")
        self.assertEqual(provider.timeout_seconds, 180)
        self.assertEqual(provider.max_retries, 6)

    @patch("openai.OpenAI")
    def test_openai_provider_parses_list_message_content(self, mock_openai):
        response = MagicMock()
        response.usage = MagicMock(prompt_tokens=3, completion_tokens=2, total_tokens=5)
        response.choices = [
            MagicMock(message=MagicMock(content=[{"type": "output_text", "text": json.dumps({"items": [1, 2]})}]))
        ]
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = response
        mock_openai.return_value = mock_client

        with patch.dict(
            "os.environ",
            {
                "LLM_CONTENT_OPENAI_TIMEOUT_SECONDS": "90",
                "LLM_CONTENT_OPENAI_MAX_RETRIES": "4",
            },
            clear=False,
        ):
            provider = OpenAIProvider(api_key="cec", model_id="azure-gpt-5_4")
            result = provider.generate_structured_json("Return JSON")

        self.assertEqual(result, {"items": [1, 2]})

    @patch("time.sleep")
    @patch("openai.OpenAI")
    def test_openai_provider_retries_on_retryable_errors(self, mock_openai, mock_sleep):
        response = MagicMock()
        response.usage = MagicMock(prompt_tokens=8, completion_tokens=2, total_tokens=10)
        response.choices = [MagicMock(message=MagicMock(content='{"ok": true}'))]

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = [Exception("503 Service Unavailable"), response]
        mock_openai.return_value = mock_client

        with patch.dict(
            "os.environ",
            {
                "LLM_CONTENT_OPENAI_TIMEOUT_SECONDS": "45",
                "LLM_CONTENT_OPENAI_MAX_RETRIES": "2",
            },
            clear=False,
        ):
            provider = OpenAIProvider(api_key="cec", model_id="azure-gpt-5_4")
            result = provider.generate_structured_json("Retry please")

        self.assertEqual(result, {"ok": True})
        self.assertEqual(mock_client.chat.completions.create.call_count, 2)
        mock_sleep.assert_called_once_with(5)


if __name__ == "__main__":
    unittest.main()
