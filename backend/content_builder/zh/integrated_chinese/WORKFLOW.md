# Integrated Chinese 制课流程 v1

默认入口是开发控制台的 **Integrated Chinese**，或下方命令行。所有阶段先在本地完成；默认终点为 `verify`。`publish` 才会上传媒体并写入数据库。

```mermaid
flowchart LR
    A[单课 PDF 与来源指纹] --> B[课文 / 生词 / Language Notes / Grammar]
    B --> C[逐句讲解 / 语法用法 / 题库 / 内容验收]
    C --> D[角色课文语音]
    D --> E[学习者语言本地化]
    E --> F[旁白 TTS / 实测逐句时间]
    F --> G[无字幕静态课件 / 分页音频 / WebP]
    G --> H[完整媒体验收]
    H --> I[显式 publish / 上传成功后入库]
```

## 教材提取范围

| 材料 | 保留内容 | 用途与检查 |
| --- | --- | --- |
| 课文、对话、文章、日记 | 全部正文，原顺序、真实说话人、标点、逐词拼音、逐句翻译 | 每条正文都有对应教学页；课文录音与原句对应。文章按自然句处理，不编造人物 |
| Vocabulary | 简体词形、词性、当前词义、拼音、教材语境例句及例句拼音和翻译 | 按词义区分历史复习与新义；语气词等不强行出孤立翻译题 |
| Language Notes | 每一条说明、用法、礼貌和语境区别 | 用 `note_id` → `source_note_ids` 追踪到讲解页 |
| Grammar | 每个小节的标题、完整说明、结构、例句、使用限制和常见错误 | 用 `grammar_id` → `source_grammar_ids` 追踪；只有标题的空骨架不合格 |
| 教材练习素材 | 与本课知识对应的现有句子和提示 | 听写必须绑定真实课文音频；扩展练习须有明确上下文与参考答案 |

简繁双版只保留一份简体正文。忽略目录、页码、页眉页脚、注脚上标、版权信息和重复的繁体版本。正确保留正文里的真实数字与标点。输入采用明确的单课 PDF；不猜测扫描版本的页码。`source_manifest` 保存原文件位置与 SHA-256，原始 PDF 保留在原位置，便于复查和重跑。

## 教学与题目

- 顺序为课文理解、词语与用法、教材语法、总结。每页围绕一个可解释的教学点；长句由讲稿阶段按自然停顿拆分，各有独立旁白，渲染器不复制整段旁白来凑页数。
- 正文覆盖依据原句与可见教学内容，不能靠旁白提到一句话或填写一个行号替代。
- 新内容必须带语法与 Language Notes 的来源引用。旧 JSON 没有引用时报告“未核实”，不会自动补造已覆盖记录。
- 屏幕文字只放句子、拼音、翻译、结构、对比或简短教学提示。`visual_notes` 是制作备注，不进入教学图片。
- 使用现有题型：识义、中文表达、中文口语、听写。题目需有唯一课号和题号、明确提示、非空参考答案；完全重复题报告复查。
- 听写答案和 `line_ref` 从原始课文素材确定。LLM 提供的错误行号会被纠正；教材中不存在的答案会被拒绝。
- 内容检查通过后才更新词汇记忆和生成媒体。空题库、缺例句拼音、空语法说明、漏正文、未知模板均阻止流程继续。
- 默认不生成当前静态课程未使用的情景演绎分镜。需要演绎资产时，在 `Task3LessonVideoPlanner.run()` 中显式启用 `include_dramatization`。

## 语音、字幕与画面

- 课文使用固定角色音色；同一人保持同一音色。语音文件指纹包含文本、音色、语速、编码等设置，可以复用同一请求的有效录音。
- 英文讲解中的中文发音采用 `[zh:汉字]`。拼音用于视觉阅读，不能用带声调拼音替代中文 TTS。多语版本保留中文发音片段，翻译缺字段会失败。
- 旁白按句生成，记录实测时间。页面时长使用实际语音时长加短尾停顿。字幕起止不得越界、倒序或重叠，文本条数必须与实测时间一致。
- TTS 保留按文本和声音设置缓存的逐句录音。中断后复用成功句子，再完成剩余请求。主音轨成功合成后才原子替换旧文件。
- 幻灯片使用独立静态组件，不从视频动画的某一帧截图。导出边界剔除旁白、字幕和制作备注，模板外层也禁用字幕。字幕留在 JSON，由播放器按时间轴显示。
- 每课只打包一次 Remotion，并复用一个浏览器导出全部页面。正式渲染失败会报错；`--renderer svg` 仅供显式诊断，不通过正式媒体验收。
- 图片输出 1920×1080、WebP q85；交付分页音频为 MP3、单声道、24 kHz、40 kbps。生成时直接编码，避免对同一 MP3 反复有损压缩。
- 图片和分页音频采用内容指纹文件名。修改模板、内容或音轨后得到新 URL，避免浏览器/CDN 仍显示旧课件。旧发布文件保留，不在生成时批量删除。

## 重跑与完成条件

| 变化 | 重算范围 |
| --- | --- |
| PDF、提取提示词、生成模型或历史词义 | 内容生成及受影响下游 |
| 学习者语言 | 本地化、对应旁白、字幕与课件 |
| 旁白、音色、语速或 TTS 实现 | 对应语音、时间轴和分页音频；视觉内容一致时复用图片 |
| 教学内容、模板、静态渲染实现 | 幻灯片图片 |
| 只有视觉样式变化 | `--images-only`；核对原旁白、字幕、时长完全一致后保留录音 |
| 缓存文件丢失或字节内容变化 | 对应阶段重新生成 |

检查点按课号和学习者语言分目录。正文提取、教材笔记、题库与讲解保留独立检查点；完成记录保存输入指纹、结果与产物校验值。失败记录独立保存，不覆盖上一次成功的检查点。每课有进程锁，进程退出后系统释放锁。

`verify` 会实际解码图片、用 ffprobe 检查每条音频，并检查课号、页数、原句录音、字幕、片段顺序、时长和交付编码。不同教学内容意外导出相同画面也会失败；静态渲染配方从 v3 起逐页更新 Remotion 的输入与已解析参数。报告在 `artifacts/reports/<lang>/`。草稿状态是 `draft`，通过完整验收才是 `verified`；二者均不代表已发布。

主旁白是构建中间产物。旧课只有完整分页音频时可以检查和刷新画面，并报告主音轨在本地缺失；修改讲稿后需要重新生成旁白。

`publish` 每次重新验收。必须配置媒体存储；任一文件上传失败或数据库同步失败均返回非零状态，失败课件不会移动为已同步。上传先于数据库写入；上传成功而入库失败时可能留下暂未引用的版本文件，重试采用同样对象键。该过程不宣称跨对象存储与数据库的分布式原子事务。

## 命令

从 `backend/` 执行，使用项目虚拟环境的 Python。

```powershell
# 查看计划，不调用模型、不上传
python -m content_builder.zh.integrated_chinese.workflow plan --lesson 101

# 从单课教材生成并验收；默认复用相同输入的有效产物
python -m content_builder.zh.integrated_chinese.workflow run --lesson 101 --source content_builder/zh/integrated_chinese/artifacts/archive_pdfs/lesson101.pdf

# 先验收教材提取、讲稿和题库
python -m content_builder.zh.integrated_chinese.workflow run --lesson 101 --through content

# 明确采用已完成的英文内容，继续课文 TTS、旁白和课件
python -m content_builder.zh.integrated_chinese.workflow run --lesson 101 --from-stage lesson_audio --input-json content_builder/zh/integrated_chinese/artifacts/synced_json/en/lesson101_data.json

# 视觉更新；不重新调用 LLM 或 TTS
python -m content_builder.zh.integrated_chinese.workflow run --lesson 101 --from-stage slides --images-only

# 生成法语学习者版本，复用共用的英文教材内容与中文课文录音
python -m content_builder.zh.integrated_chinese.workflow run --lesson 101 --lang fr

# 检查全部现有英文课；只读取，不自动重写历史内容
python -m content_builder.zh.integrated_chinese.workflow check --all

# 验收单课的实际媒体
python -m content_builder.zh.integrated_chinese.workflow check --lesson 101 --media --deep

# 内容和媒体已经核对，显式执行发布
python -m content_builder.zh.integrated_chinese.workflow run --lesson 101 --from-stage publish --through publish
```

`--force content` 重做内容任务，`--force narration` 重做旁白主音轨，`--force slides` 重渲图片；文本和声音设置相同的有效逐句 TTS 缓存仍可复用。改变发音策略应修改对应设置，而不是只删除输出 JSON。

自动检查能发现结构、覆盖引用、媒体和时序问题，不能证明翻译、词义与发音在教学上全部正确。新教材版本首次上线仍需抽查原 PDF、试听角色对白和混合语旁白，并检查长句页、语法表和不同学习者语言的可读性。
