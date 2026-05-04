# Content Builder

`content_builder` 现在只负责内容生成，不直接承担数据库发布职责。

## 架构边界

当前目录已经拆成两层：

- `core/`
  放公共基础能力：路径约定、pipeline registry、后续可继续承接 LLM/TTS/ffmpeg/R2 等跨教材复用能力。
- `pipelines/`
  放具体教材流水线。当前已注册两个正式 pipeline：
  - `integrated_chinese`：Integrated Chinese 风格中文教材，包含 prompt、拼音、中文题型、中文课文音频和视频规划逻辑。
  - `new_concept_english`：New Concept English Book 1 英语教材，包含原书页码切课、英文课文抽取、中文辅助讲解、练习题和视频规划逻辑。

后续新增教材时，优先新增类似：

```text
pipelines/cambridge_english/
pipelines/another_textbook_family/
```

不要按语言直接复制出 `content_builder_en`；教材结构、题型和教学策略才是 pipeline 的主要边界。

## 目录约定

- `generate.py`
  **Stage 1** 通用主入口。扫描当前 pipeline 的 `raw_materials/` 中的 PDF，生成 lesson JSON 和本地媒体产物；不负责入库。
- `render_narration.py`
  **Stage 2** 主入口。读取当前 pipeline 的 `output_json/<lang>/` 中的 lesson JSON，渲染母语旁白音轨、写回字幕时间轴，并生成静态教学幻灯片 `teaching_slide_deck`。
- `content_agent.py`
  旧导入路径兼容层；真实实现已迁移到 `pipelines/integrated_chinese/agent.py`。
- `core/pipeline.py`
  Pipeline 注册表与统一路径入口；`generate.py`、`render_narration.py`、`localize.py` 都通过它选择流水线。
- `core/llm_providers.py`
  共享 LLM provider、PDF 上传、JSON repair 与 usage/cost 统计。根目录 `llm_providers.py` 仅保留旧导入兼容。
- `pipelines/integrated_chinese/`
  当前中文学习教材流水线定义、agent 和 task 实现；中文听说读写产物归档在 `artifacts/integrated_chinese/`。
- `pipelines/new_concept_english/`
  New Concept English Book 1 流水线定义、agent、book profile、切课脚本和 task 实现；产物归档在 `artifacts/new_concept_english/`。
- `tasks/`
  旧 `tasks.*` 导入路径兼容层；新教材不要在这里新增实现，应放在自己的 `pipelines/<pipeline_id>/tasks/`。
- `llm_providers.py`
  旧导入路径兼容层；共享 LLM provider 实现在 `core/llm_providers.py`。
- `scripts/`
  维护脚本、诊断脚本、一次性修复脚本。
- `artifacts/`
  所有运行产物与输入素材目录。

## artifacts

- `artifacts/integrated_chinese/raw_materials/`
  待处理 PDF。
- `artifacts/integrated_chinese/output_json/`
  新生成、尚未归档的 lesson JSON。
- `artifacts/integrated_chinese/synced_json/`
  已确认保留的 lesson JSON 数据。
- `artifacts/integrated_chinese/output_audio/`
  课文音频、旁白音频等音频产物。
- `artifacts/integrated_chinese/output_video/`
  旧版 mp4 讲解视频产物目录；新工作流不再生成新的 mp4。
- `artifacts/integrated_chinese/output_slides/`
  静态教学幻灯片产物。
- `artifacts/integrated_chinese/archive_pdfs/`
  已处理完成的 PDF 归档。
- `artifacts/integrated_chinese/vocab_memory/global_vocab_memory.json`
  全局词汇记忆库。
- `artifacts/new_concept_english/raw_materials/`
  新概念英语原始整书 PDF 与切出的单课 PDF。
- `artifacts/new_concept_english/output_json/`
  新概念英语新生成、尚未入库归档的 lesson JSON。
- `artifacts/new_concept_english/synced_json/`
  新概念英语已同步入库的 lesson JSON。
- `artifacts/new_concept_english/output_audio/`
  新概念英语旁白等音频产物。
- `artifacts/new_concept_english/output_video/`
  旧版 mp4 讲解视频产物目录；新工作流不再生成新的 mp4。
- `artifacts/new_concept_english/output_slides/`
  新概念英语静态教学幻灯片产物。
- `artifacts/test_tts_output/`
  TTS 试验脚本输出目录。

## 常用工作流

### Integrated Chinese

1. 把教材 PDF 放入 `artifacts/integrated_chinese/raw_materials/`
2. `python content_builder/generate.py --pipeline integrated_chinese`（Stage 1：生成 lesson JSON + 对话音频，仅本地）
3. `python content_builder/render_narration.py --pipeline integrated_chinese --lang en`（Stage 2：渲染旁白音轨 + 生成静态教学幻灯片，仅本地）
   - 加 `--lang fr` 生成法语学习者版本
   - 加 `--force-narration` 重新生成旁白音轨
   - 加 `--force-slides` 重新生成静态幻灯片
4. 确认 `artifacts/integrated_chinese/output_json/<lang>/` 中的数据无误
5. `python database/sync_to_db.py --pipeline integrated_chinese --lang <lang>`（Stage 3：上传 R2 + 入库，JSON 移至 `synced_json/`）

### New Concept English

1. 把 New Concept English Book 1 整书 PDF 放入 `artifacts/new_concept_english/raw_materials/`
2. `python content_builder/pipelines/new_concept_english/build_lesson.py --book 1 --lesson lesson002 --support-lang zh`
   - 加 `--all` 可批量生成 Book 1 app lessons。
   - 加 `--split-only` 只切出单课 PDF，不生成 JSON。
3. `python content_builder/render_narration.py --pipeline new_concept_english --lang zh`
   - 生成旁白音轨、字幕时间轴和静态教学幻灯片。
   - 加 `--force-narration` / `--force-slides` 可强制重生成。
4. 确认 `artifacts/new_concept_english/output_json/zh/` 中的数据无误
5. `python database/sync_to_db.py --pipeline new_concept_english --lang zh`

Stage 2 使用静态 slide deck 替代旧 mp4 讲解视频。Stage 3 由 `database/sync_to_db.py` 统一负责上传音频、slides 并入库。`content_builder/generate.py` 只做本地生成，不再提供自动入库参数。

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
