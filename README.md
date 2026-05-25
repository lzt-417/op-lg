# LangGraph Novel Project

将 XFQ-Project 的 AI 网文生成流程迁移到 LangGraph 架构。

## 项目结构

```
qy/
├── src/
│   ├── nodes/             # N1-N10 节点实现
│   │   ├── n1_reader_persona.py
│   │   └── n2_concept.py
│   ├── state/             # 状态定义
│   │   └── planning_state.py
│   ├── adapters/          # 适配层（复用 XFQ-Project 资源）
│   │   ├── template_adapter.py
│   │   └── source_adapter.py
│   ├── utils/
│   │   └── llm_client.py  # LLM 调用封装
│   └── graph_builder.py   # LangGraph 图构建
├── config/
│   └── path_config.yaml   # 路径配置
├── tests/
│   ├── test_n1.py         # N1 测试
│   └── test_n2.py         # N2 测试
├── novels/                # 小说项目目录
├── run_day1.py            # Day 1 运行脚本
└── requirements.txt       # Python 依赖
```

## 迁移进度

### Day 1：规划启动（N1 + N2）✅ 已完成

**已实现：**
- ✅ 项目目录结构
- ✅ PlanningState 状态定义
- ✅ TemplateAdapter（读取 XFQ-Project 模板）
- ✅ SourceDataAdapter（读取 XFQ-Project 源数据）
- ✅ LLMClient（支持 OpenAI 和 Anthropic）
- ✅ N1 节点：读者画像生成
- ✅ N2 节点：概念设计
- ✅ Graph 构建（N1 → N2 线性流）
- ✅ Day 1 验证测试

**测试结果：**
- Adapter 层：[OK] 通过
- N1 节点（dry run）：[OK] 通过

### Day 2：设定 + 大纲 + 风格（N3 + N4 + N5）- 待实现

### Day 3：写作（N6 + N7）- 待实现

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

### 3. 运行 Day 1

```bash
python run_day1.py
```

### 4. 运行测试

```bash
python tests/test_n1.py
python tests/test_n2.py
```

## 下一步

继续 Day 2 的迁移：实现 N3（设定）、N4（大纲）、N5（风格）节点。
