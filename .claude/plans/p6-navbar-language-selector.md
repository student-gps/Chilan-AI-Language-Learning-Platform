# 导航栏语言选择器优化

## 背景

导航栏当前在 [frontend/src/components/Navbar.jsx](../../frontend/src/components/Navbar.jsx) 中直接渲染 15 个语言按钮。菜单高度超过常见桌面视口、没有筛选能力，并且打开/关闭仅支持鼠标，移动端和键盘导航的体验有限。语言清单来自 [frontend/src/utils/languageOptions.js](../../frontend/src/utils/languageOptions.js)，选择语言仍应继续通过 `i18n.changeLanguage` 持久化到本地存储。

用户希望合理优化该下拉框；搜索语言在当前静态小型列表中实现成本低，因此纳入本次改动。

## 方案

仅修改 [frontend/src/components/Navbar.jsx](../../frontend/src/components/Navbar.jsx)，不增加第三方依赖，也不改变 [frontend/src/utils/languageOptions.js](../../frontend/src/utils/languageOptions.js) 的数据格式或 i18n 逻辑。

1. **状态和派生列表**
   - 加入搜索关键词状态和输入框 ref。
   - 使用 `useMemo` 按语言的英文名称、原生名称与语言代码进行大小写无关过滤（Unicode 字符串直接匹配，覆盖中文、日文、阿拉伯文等原生名称）。
   - 打开菜单时清空上一轮关键词并自动聚焦搜索框；关闭、切换语言或路由变化时也清空关键词，避免下一次打开处于不可预期的筛选状态。

2. **重构下拉层视觉与布局**
   - 将现有单列 `w-48` 长列表替换为更宽的自适应菜单：顶部为简洁标题和带 `Search` 图标的搜索框，底部为限高、可滚动的语言列表。
   - 每个语言项保留旗帜、原生名、英文名和当前语言勾选状态；当前语言即使不匹配关键词，也会跟随筛选规则展示，避免用户在搜索时失去当前选择的上下文。
   - 空搜索结果显示清晰的空状态和当前检索词（纯展示，不改变语言）。
   - 对小屏维持安全宽度和最大宽度，列表内部滚动而不超出页面可视区域。

3. **交互与可访问性**
   - 为触发器和菜单补充 `aria-haspopup`、`aria-expanded`、关联 ID、`aria-label` 等语义。
   - 支持 Escape 关闭并将焦点返回触发器；触发器上的 Enter/Space 保持原生按钮行为。
   - 下拉菜单内语言项为按钮，保留点击选择；搜索框可正常输入，不会被导航栏 3 秒自动关闭计时器误伤（在下拉容器内活动会重置计时器）。
   - 不额外实现箭头键高亮选择：该模式需要 roving tabindex/焦点管理，复杂度高且不是当前 15 种语言搜索选择的核心需求；浏览器原生 Tab 导航、搜索、点击、Escape 都完整可用。

4. **验证**
   - 运行 `npm run lint`，确保 hooks 依赖、未使用导入及 JSX 规则均通过。
   - 运行 `npm run build`，验证生产构建通过。
   - 手工验证：打开后搜索英文名、原生名与代码；空结果；切换语言；点击外部关闭；Escape 关闭；窄屏下列表滚动。

## 不在范围内

- 不修改设置页的原生 `<select>`（它是独立的表单控件，改成自定义可搜索组件会扩大本次范围）。
- 不增加或删除任何支持的 UI 语言。
- 不修改用户已有的 [frontend/src/i18n.js](../../frontend/src/i18n.js) 和 [frontend/src/pages/TypingIntroPage.jsx](../../frontend/src/pages/TypingIntroPage.jsx) 未提交改动。
