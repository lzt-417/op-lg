# AI Writing Patterns — 负面清单

> 本文件列出所有 AI 写作典型指纹。NovAgent 生成 prompt-style-fingerprint 时读取本文件，
> 确保不在 prompt-style-fingerprint 中允许、推荐或配额化这些模式。
> Reviewer Agent 执行 prose-review 时也以此为基准。
> **持续扩展**——每发现一个新 AI 指纹，追加一行。

---

## 禁用句式（禁止出现在 prompt-style-fingerprint 的"允许"或"配额"规则中）

| # | 句式 | 变体/检测模式 | 为什么禁用 | 替代方案 |
|---|------|-------------|-----------|---------|
| 1 | 否定式对比 | `not X but Y` / `not quite X, not quite Y` / `not just X, but also Y` / `not so much X as Y` / `isn't X, it's Y` / `不是…而是…` / `Not X. Y.` 独立成段式（如 "Not knowledge. Not information. Understanding."） / `Not X. Not Y. Z.` 三段式（如 "Not an attack. Not a force. A gentle wave."） / `wasn't X. It was Y.` 分离对比式（如 "The shattering wasn't violent. It was the opposite."） / `Not X — not Y. Z.` 破折号式（如 "Not worse — just final."） | AI 写作第一指纹，先否定再肯定制造伪深刻，读者感受到翻译腔 | 直接陈述"是什么"；用感官/动作替代。例：不说 "It wasn't fear but caution" → "Caution held him back." |
| 2 | "as if" / 仿佛 | `it was as if...` / `as though...` / `like...`（比喻性比较，非动作比较）/ `仿佛…` / `好像…` | AI 用此结构回避直接描写，推给"好像"而非呈现体验 | 去掉"好像"，直接写体验。例：不说 "It was as if the world held its breath" → "The world went quiet." |
| 3 | 过度比喻堆叠 | 同一段内 ≥2 个比喻形容同一事物/场景 | AI 找不到精准表达时堆砌比喻凑感觉 | 只保留最准确的一个比喻 |
| 4 | 总结性反思结尾 | `He realized today had changed him` / `她意识到自己学到了重要的一课` | 说教感，以反思/道德教训结尾是章节失败信号 | 用具体动作/感官细节/未完成悬念收尾 |
| 5 | 空洞评价词 | `beautiful` / `magnificent` / `breathtaking` / `very` / `extremely` / `incredibly` | 空洞的程度修饰，告诉而非展示 | 用具体可感知的细节替代 |

---

## 禁用词（禁止在 style_fingerprint 中推荐或允许）

```
delve, tapestry, myriad, palpable, nuanced, ephemeral, testament, symphony
```

---

## 使用规则

1. **NovAgent（N5 风格生成）：** 生成 style_fingerprint 后必须自检——本清单中的句式/词汇，是否作为"允许规则"、"推荐技巧"、"签名句式"或"配额化项目"出现在 style_fingerprint 中？如果是 → 删除该条，用替代方案重写。

2. **允许作为反面教材：** 可以在 style_fingerprint 中引用本清单内容，但必须明确标注为"禁止"或"反面示例"，绝不可给出"每章最多 N 次"的许可。

3. **Reviewer Agent（Prose Review）：** 审查时以此清单为基准，出现即标记。

4. **更新机制：** COO/PM/Reviewer 每发现新 AI 指纹，追加一行到此文件。
