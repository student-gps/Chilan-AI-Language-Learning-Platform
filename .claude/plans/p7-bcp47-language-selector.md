# BCP 47 标准化语言选择器

## 目标

把界面语言从当前混合的内部代码（如 `zh`、`jp`）迁移到标准 BCP 47 标签（如 `zh-Hans`、`ja`），并用浏览器 `Intl.DisplayNames` 自动生成本地化语言名称和搜索索引。语言选择器不再维护 `Chinese / Chinois / Chinesisch ...` 这种横跨多语言的手工穷举表；仅维护不能从标准名称推出的少量历史/地区快捷别名。

用户选择了**完整迁移**：本地持久化和 API header 都写入标准 BCP 47 标签，同时对已有用户保存的旧值保持兼容。

## 当前问题与影响面

- [frontend/src/utils/languageOptions.js](../../frontend/src/utils/languageOptions.js) 目前将 `jp` 当作日语的 UI 值，并靠大型 `searchAliases` 数组维护翻译名称。
- [frontend/src/components/Navbar.jsx](../../frontend/src/components/Navbar.jsx) 直接查询该数组。
- [frontend/src/i18n.js](../../frontend/src/i18n.js) 的资源键仍以 `zh`、`jp` 为主，另有 `resources.ja = resources.jp` 的兼容赋值；本地存储直接读取、写入原始值。
- [frontend/src/api/apiClient.js](../../frontend/src/api/apiClient.js) 原样将本地存储的语言值放入 `X-Chilan-Interface-Language`。
- [backend/routers/auth.py](../../backend/routers/auth.py) 已能将 `zh-Hans` 和 `ja` 规范成邮件语言，但测试仍覆盖旧的 `jp` header。
- 设置页通过 `UI_LANGUAGE_OPTIONS` 渲染 UI 语言原生 `<select>`，因此也会自动受数据模型影响。

## 实施方案

### 1. 建立唯一语言注册表与兼容函数

重构 [frontend/src/utils/languageOptions.js](../../frontend/src/utils/languageOptions.js)：

- 每项以 `locale` 作为唯一的标准 BCP 47 值：
  - 简体中文 `zh-Hans`；日语 `ja`；其他当前单一变种语言使用主语言标签（`en`、`fr`、`de`、`ko`、`es`、`vi`、`pt`、`ar`、`th`、`ru`、`id`、`ms`、`it`）。
- 保留原生名称、旗帜和少量 `legacyAliases` / `searchAliases`：只收录 `jp`、`cn`、`zh-cn`、`zh-hans-cn`、`ja-jp`、`pt-br` 等非标准或历史/区域输入；删除人工维护的跨语言翻译名称列表。
- 提供集中化函数：
  - `normalizeUiLocale(value)`：处理大小写、下划线、旧 `jp`、`zh`/`zh-cn` 等值，返回支持的规范标签或默认 `zh-Hans`。
  - `getUiLanguageOption(value)`：基于规范标签取得条目。
  - `getUiLanguageDisplayName(locale, displayLocale)`：使用 `Intl.DisplayNames` 输出当前 UI 语言下的名称；无浏览器支持时回退原生名。
  - `getUiLanguageSearchTerms(option, displayLocale)`：组合标准 locale、语言子标签、原生名、**当前界面语言自动生成的名称**和少量快捷别名，并统一去重。
  - `getUiLanguageSelectOptions(displayLocale)`：供设置页生成一致的 option 标签。
- `COURSE_LANGUAGE_OPTIONS` 暂不做数据语义迁移：它描述学习/母语课程元数据，继续保留当前后端使用的语言代码，避免无关的课程筛选与 API 变动。

### 2. 将 i18next 持久化值规范化为 BCP 47

修改 [frontend/src/i18n.js](../../frontend/src/i18n.js)：

- 引入 `normalizeUiLocale`，初始化时将现有 localStorage 的 `zh`、`jp`、`zh-CN` 等值迁移为标准 BCP 47 值并立即写回 `chilan_interface_language`。
- 将 `resources['zh-Hans']` 指向既有 `resources.zh`；保留 `resources.ja = resources.jp`，并继续保留旧资源键作为兼容别名（无需移动大型翻译对象）。
- 初始化 `lng` 使用规范值；配置 `supportedLngs` 为标准语言注册表中的 locale 列表，并启用 `nonExplicitSupportedLngs`，保证 i18next 解析 `zh-Hans`、`ja-JP` 时稳定。
- `languageChanged` 监听器永远写入 `normalizeUiLocale(lng)`，确保之后不会再次产生 `jp` 或非标准大小写形式。
- 由于现有翻译表的中文键为 `zh`、日语键为 `jp`，增加明确的 `fallbackLng` 映射：`zh-Hans → zh`、`ja → jp`（以及全局 `en`），让标准选择值仍复用已存在的翻译资源；验证切换后不出现 fallback 英文或缺失 key。

### 3. 用标准化工具更新调用方

- [frontend/src/components/Navbar.jsx](../../frontend/src/components/Navbar.jsx)
  - 移除局部的手写 Unicode 搜索逻辑与 `searchAliases` 直读，改用 `getUiLanguageSearchTerms`。
  - 查询索引会随着 `i18n.resolvedLanguage` 变化重新生成：在法语 UI 下自动能匹配 `chinois (simplifié)`；在英文 UI 下可匹配 `Chinese (Simplified)`；原生名和 `cn`、`zh-cn` 等快捷输入始终生效。
  - 显示项使用 `Intl.DisplayNames` 的当前界面语言名称，同时保留原生名称和标准 locale（`ZH-HANS`、`JA`），使用户看得懂匹配/选项含义。
  - 调用 `i18n.changeLanguage(item.locale)`，选择结果和 localStorage 都写入规范标签。

- [frontend/src/pages/personalSetting/index.jsx](../../frontend/src/pages/personalSetting/index.jsx)
  - 通过新的 `getUiLanguageSelectOptions(i18n.resolvedLanguage)` 生成设置页 option；value 改为 `locale`。
  - `interfaceLang` state 与 i18next 的规范 locale 同步，设置页切换也写入标准值。

- [frontend/src/api/apiClient.js](../../frontend/src/api/apiClient.js)
  - 调用 `normalizeUiLocale` 再填 `X-Chilan-Interface-Language`，即使 localStorage 被手动改为旧值，API 也会收到标准 BCP 47 标签。

### 4. 后端接受并测试标准 header

- [backend/routers/auth.py](../../backend/routers/auth.py)：复用已存在的 BCP 47 归一化逻辑；补齐明确的标准语言/地区映射（例如 `fr-fr`、`de-de`、`ko-kr`、`pt-pt`、`pt-br` 等）以提高 header 解析的可读性和未来扩展安全性，最终仍转换为邮件模板的主语言键。
- [backend/tests/test_auth_google.py](../../backend/tests/test_auth_google.py)、[backend/tests/test_auth_login.py](../../backend/tests/test_auth_login.py)、[backend/tests/test_auth_password_notifications.py](../../backend/tests/test_auth_password_notifications.py)、[backend/tests/test_auth_verification_code.py](../../backend/tests/test_auth_verification_code.py)：将用于当前 UI 值的 `jp` header 断言/fixture 改为 `ja`，并保留至少一项 `jp` legacy header 兼容测试。
- 为 `normalize_auth_email_lang` / 请求头解析增加针对 `zh-Hans`、`ja`、`pt-BR`、旧 `jp` 的单元测试，证明标准值优先且旧值未破坏。

### 5. 验证

- 前端：检查语言注册表和 Navbar；运行 `npm --prefix frontend run lint`（项目全量如仍有既存 lint 失败，单独 lint 改动文件并列出已有失败）；运行 `npm --prefix frontend run build`。
- 前端行为：验证旧 localStorage 值 `zh`、`jp` 迁移为 `zh-Hans`、`ja`；选中语言后 storage 和 API header 为标准值；在英文、法文、中文 UI 下分别验证自动显示/搜索；验证 `CN`、`Chinese`、`Chinois`、`中文`、`zh-CN`、`jp`、`ja-JP`。
- 后端：运行相关 auth tests 或针对归一化函数的测试子集，验证 BCP 47 header 的邮件语言选择和遗留 `jp` 兼容。

## 兼容性和范围

- **保留读取兼容**：现有用户的 localStorage `zh`、`jp`、`zh-CN`、`ja-JP` 在首次载入即迁移；邮件服务仍接收旧 `jp` header。
- **写入统一规范**：此后 UI 选择、localStorage 与 API header 都输出 `zh-Hans`、`ja` 等 BCP 47 标签。
- 不改动数据库课程语言字段、题目语言逻辑、语音识别的 `language` 参数，也不将课程的 `jp` 代码迁移为 `ja`；这些属于不同的数据域，后续可单独规划。
- 当前未提交的 [frontend/src/components/Navbar.jsx](../../frontend/src/components/Navbar.jsx) 与 [frontend/src/utils/languageOptions.js](../../frontend/src/utils/languageOptions.js) 搜索别名改动将由本方案替换，而非叠加。
