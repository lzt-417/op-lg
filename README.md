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
│   │   ├── n7_chapter_writing.py
│   │   ├── n8_review.py
│   │   └── n9_merge_fix.py
│   ├── guides/            # 审查指南
│   │   ├── logic_review_guide.md
│   │   ├── adversarial_edit_guide.md
│   │   ├── prose_review_guide.md
│   │   ├── merge_rules.md
│   │   └── ai_patterns_blacklist.md
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
├── run_day4.py            # Day 4 运行脚本（N1-N9）
└── requirements.txt       # Python 依赖
```


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
# 运行完整 N1-N9 流程（Day 1-4，写作 + 审改）
python run_day4.py

# 或仅运行 N1-N7（Day 1-3，写作）
python run_day3.py

# 或仅运行 N1-N5（Day 1-2，设定 + 大纲）
python run_day2.py

# 或仅运行 N1-N2（Day 1，规划启动）
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
