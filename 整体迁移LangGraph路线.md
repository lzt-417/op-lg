# 整体迁移到 LangGraph 路线图

> **目标：** 将 XFQ-Project 迁移到 LangGraph 架构
> **策略：** 边迁移边测试，2 周完成


---

## 时间总览

```
第1周：迁移 + 跑通测试（Day 1-5）
    ↓
第2周：优化完善（Day 6-10）
```

---

## 第1周：迁移 + 跑通测试

### Day 1：规划阶段（N1 + N2）
- N1 读者画像 → reader-persona.md
- N2 概念设计 → concept.md

### Day 2：设定 + 大纲 + 风格（N3 + N4 + N5）
- N3 世界观与角色设定 → worldbuilding.md + characters.md + story_graph.md
- N4 全书大纲 → outline-hook_arc.md + outline-arc_1~4.md
- N5 风格指纹 → style_fingerprint.md

### Day 3：写作（N6 + N7）
- N6 章纲生成 → ch01~03-outline.md
- N7 正文写作 → ch01~03-draft.md（每章 ≥2200 字）
- 输出验证 + 重试机制

### Day 4：审改（N8 + N9）
- N8 三路审查（先串行）
- N9 合并修复

### Day 5：编译 + 验证（N10）
- N10 编译输出
- 端到端测试
- 性能统计

---

## 第2周：优化完善

### Day 6-7：性能优化
- 状态持久化（SQLite Checkpointer）
- 中断/恢复功能

### Day 8-9：并行审查
- Send API 真并行
- 审查结果自动合并

### Day 10：人机协同 + 最终测试
- 关键断点设置
- 端到端测试（10+ 章）


---

## API 配置

- **Provider：** 阿里云百炼（OpenAI 兼容）
- **Base URL：** https://dashscope.aliyuncs.com/compatible-mode/v1
- **Model：** qwen-long

> **周期：** 2 周
