# LangGraph Novel Project

将 XFQ-Project 的 AI 网文生成流程迁移到 LangGraph 架构。

## 项目结构

```
qy/
├── src/
│   ├── nodes/             # N1-N10 节点实现
│   │   ├── n1_reader_persona.py
│   │   ├── n2_concept.py
│   │   ├── n3_setting.py
│   │   ├── n4_outline.py
│   │   ├── n5_style.py
│   │   ├── n6_chapter_outline.py
│   │   └── n7_chapter_writing.py
│   ├── state/             # 状态定义
│   │   └── planning_state.py
│   ├── adapters/          # 适配层（复用XFQ-Project资源）        
│   │   │
│   │   ├── template_adapter.py
│   │   └── source_adapter.py
│   ├── utils/
│   │   ├── llm_client.py  # LLM 调用封装
│   │   └── validators.py  # 输出验证工具
│   └── graph_builder.py   # LangGraph 图构建
├── tests/
│   ├── test_n1.py         # N1 测试
│   ├── test_n2.py         # N2 测试
│   ├── test_n3.py         # N3 测试
│   ├── test_n4.py         # N4 测试
│   ├── test_n5.py         # N5 测试
│   └── test_day1_integration.py  # 集成测试
├── novels/                # 小说项目目录
├── run_day1.py            # Day 1 运行脚本（N1-N2）
├── run_day2.py            # Day 2 运行脚本（N1-N5）
├── run_day3.py            # Day 3 运行脚本（N1-N7）
└── requirements.txt       # Python 依赖
```

## 迁移进度

### Day 1：规划启动（N1 + N2）

**已实现：**
- 项目目录结构
- PlanningState 状态定义
- TemplateAdapter（读取 XFQ-Project 模板）
- SourceDataAdapter（读取 XFQ-Project 源数据）
- LLMClient（支持 OpenAI 和 Anthropic）
- N1 节点：读者画像生成
- N2 节点：概念设计
- Graph 构建（N1 → N2 线性流）
- Day 1 验证测试

**测试结果：**
- Adapter 层：[OK] 通过
- N1 节点（dry run）：[OK] 通过

### Day 2：设定 + 大纲 + 风格（N3 + N4 + N5）

**已实现：**
- N3 节点：世界观 + 角色设定 + 剧情关系图（2 次 LLM 调用）
- N4 节点：全书大纲（逐 Arc 生成，支持 Hook Arc + Arc 1-N）
- N5 节点：风格指纹（10 维度，含 AI 负面清单）
- Graph 构建（N1 → N2 → N3 → N4 → N5 线性流）
- Day 2 验证测试

**测试结果：**
- N3 产出（worldbuilding/characters/story_graph）：[OK] 通过
- N4 产出（5 个 Arc 大纲，含 Logline + 章节标注）：[OK] 通过
- N5 产出（style_fingerprint，含 POV + 禁用词表）：[OK] 通过

### Day 3：写作（N6 + N7）

**已实现：**
- N6 节点：章纲生成（逐 Arc 提取章节，支持 max_chapters 限制）
- N7 节点：正文写作（逐章生成，≥2200 字/章，支持 max_chapters 限制）
- 输出验证（validators.py：大小、关键词、占位符检测）
- 重试机制（retry_on_failure，最多 2 次重试）
- Graph 构建（N1 → N2 → N3 → N4 → N5 → N6 → N7 线性流）

**测试结果：**

### Day 4：审改（N8 + N9）- 待实现

### Day 5：交付 + 验证（N10）- 待实现

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 设置 API Key

选择一个 LLM provider：

```bash
# OpenAI
export OPENAI_API_KEY='your-key'

# 或 Anthropic
export ANTHROPIC_API_KEY='your-key'
```

### 3. 运行

```bash
# 运行完整 N1-N7 流程（Day 1 + Day 2 + Day 3）
python run_day3.py

# 或仅运行 N1-N5（Day 1 + Day 2）
python run_day2.py

# 或仅运行 N1-N2（Day 1）
python run_day1.py
```

### 4. 运行测试

```bash
python tests/test_n1.py
python tests/test_n2.py
python tests/test_n3.py
python tests/test_n4.py
python tests/test_n5.py
python tests/test_day1_integration.py
```
