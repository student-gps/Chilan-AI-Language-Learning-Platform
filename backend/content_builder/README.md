# Content Builder

`content_builder` 现在只负责内容生成，不直接承担数据库发布职责。

## 架构边界

当前目录已经拆成两层：

- `core/`
  放公共基础能力：路径约定、pipeline registry、后续可继续承接 LLM/TTS/ffmpeg/R2 等跨教材复用能力。
- `pipelines/`
  放具体教材流水线。现有中文教材流水线注册为 `integrated_chinese`，它保留当前 Integrated Chinese 风格教材的 prompt、拼音、中文题型、中文课文音频和视频规划逻辑。

后续新增英文教材时，优先新增类似：

```text
pipelines/new_concept_english/
pipelines/cambridge_english/
```

不要按语言直接复制出 `content_builder_en`；教材结构、题型和教学策略才是 pipeline 的主要边界。

## 目录约定

- `generate.py`
  **Stage 1** 主入口。扫描 `artifacts/raw_materials/` 中的 PDF，生成 lesson JSON 和课文对话音频。
- `render_narration.py`
  **Stage 2** 主入口。读取 `artifacts/output_json/` 中的 lesson JSON，渲染母语旁白音轨并写回 JSON。
- `content_agent.py`
  旧导入路径兼容层；真实实现已迁移到 `pipelines/integrated_chinese/agent.py`。
- `core/pipeline.py`
  Pipeline 注册表与统一路径入口；`generate.py`、`render_narration.py`、`localize.py` 都通过它选择流水线。
- `core/llm_providers.py`
  共享 LLM provider、PDF 上传、JSON repair 与 usage/cost 统计。根目录 `llm_providers.py` 仅保留旧导入兼容。
- `pipelines/integrated_chinese/`
  当前中文学习教材流水线定义、agent 和 task 实现，默认复用 legacy artifacts 路径，保证旧命令继续可用。
- `tasks/`
  旧 `tasks.*` 导入路径兼容层；新教材不要在这里新增实现，应放在自己的 `pipelines/<pipeline_id>/tasks/`。
- `llm_providers.py`
  LLM / embedding provider 工厂与适配层。
- `tasks/`
  具体的教材解析、词汇题生成、视频脚本、音频渲染任务实现。
- `scripts/`
  维护脚本、诊断脚本、一次性修复脚本。
- `artifacts/`
  所有运行产物与输入素材目录。

## artifacts

- `artifacts/raw_materials/`
  待处理 PDF。
- `artifacts/output_json/`
  新生成、尚未归档的 lesson JSON。
- `artifacts/synced_json/`
  已确认保留的 lesson JSON 数据。
- `artifacts/output_audio/`
  课文音频、旁白音频等音频产物。
- `artifacts/output_video/`
  渲染得到的视频产物。
- `artifacts/archive_pdfs/`
  已处理完成的 PDF 归档。
- `artifacts/global_vocab_memory.json`
  全局词汇记忆库。
- `artifacts/test_tts_output/`
  TTS 试验脚本输出目录。

## 常用工作流

1. 把教材 PDF 放入 `artifacts/raw_materials/`
2. `python content_builder/generate.py`（Stage 1：生成 lesson JSON + 对话音频，仅本地）
   - 可显式指定：`python content_builder/generate.py --pipeline integrated_chinese`
3. `python content_builder/render_narration.py`（Stage 2：渲染旁白音轨，仅本地）
   - 加 `--render-video` 同时渲染讲解视频（需 Node.js）
   - 加 `--lang fr` 生成法语学习者版本
   - 可显式指定：`python content_builder/render_narration.py --pipeline integrated_chinese --lang fr`
4. 确认 `artifacts/output_json/` 中的数据无误
5. `python database/sync_to_db.py`（Stage 3：上传 R2 + 入库，JSON 移至 `synced_json/`）

## scripts

- `scripts/backfill_vocab_example_pinyin.py`
  回填 vocabulary 例句拼音与 tokens。
- `scripts/reset_pipeline.py`
  清空内容产物、可选清理数据库与 COS。
- `scripts/set_video_urls.py`
  维护讲解视频 URL / COS key。
- `scripts/render_luma_test.py`
  测试 Luma 情景演绎渲染。
- `scripts/check_luma_render.py`
  查询已有 Luma 渲染任务状态。
- `scripts/render_tencent_tts_test.py`
  测试腾讯云逐句课文音频生成。
- `scripts/check_tencent_tts_render.py`
  检查腾讯云逐句音频产物。
- `scripts/test_cosyvoice.py`
  验证 CosyVoice TTS 发音效果。
