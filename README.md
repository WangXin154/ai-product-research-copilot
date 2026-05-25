# AI Product Research Agent & BI Platform

一个面向 AI 产品经理 / 数据产品经理作品集的端到端项目：从真实 GitHub 用户反馈出发，通过数据清洗、Embedding / LLM 主题聚类、LangGraph 多 Agent 工作流、MCP 工具调用、PRD 草稿生成、AI Evaluation、Human Review Gate 和 BI Dashboard，形成可复盘、可审查、可展示的产品调研闭环。

## 项目定位

这个项目不是一个简单的 AI 总结 Demo，而是一个 Agentic Product Research Platform：

```text
GitHub Issues / Comments
-> Data Ingestion
-> Product Research Schema
-> OpenAI Embedding / LLM Topic Discovery
-> LangGraph StateGraph Workflow
-> Pain Points / Competitor Intelligence / Opportunity Scoring
-> PRD Draft
-> AI Evaluation
-> Human Review Gate
-> BI Dashboard
-> Portfolio Case Study
```

它要证明五件事：

1. 能做清晰的产品定义和 PRD。
2. 能处理真实用户反馈数据，而不是只做假数据 Demo。
3. 理解 Agent 工作流和条件路由，不只是调用一次大模型。
4. 知道 AI 输出需要评估、证据约束和人工审核。
5. 能把 AI 能力转化为 BI 决策和业务价值。

## 当前完成状态

截至当前版本，项目已经完成 MVP 到作品集增强版的主体闭环：

- GitHub Issues / Comments 真实数据采集
- SQLite 数据库与统一 Product Research Schema
- 数据清洗与反馈类型识别
- OpenAI Embedding / LLM 主题聚类
- `feedback_topics` 主题结果持久化
- 痛点提取与机会点评分
- 竞品能力矩阵与差异化机会分析
- LangGraph `StateGraph` 多节点工作流
- PRD 草稿生成
- AI Evaluation 质量评估
- Human Review Gate
- BI Dashboard / Streamlit 原型
- 标准 MCP Server
- Workflow 导出
- Smoke Test 健康检查
- Case Study 与 MCP Client 配置文档

当前数据库样例规模：

| 表 | 当前记录数 |
| --- | ---: |
| `raw_feedback` | 541 |
| `cleaned_feedback` | 541 |
| `feedback_topics` | 69 |
| `pain_points` | 19 |
| `competitor_features` | 15 |
| `opportunity_scores` | 19 |
| `prd_drafts` | 3 |
| `ai_evaluation_results` | 8 |
| `bi_metrics_daily` | 18 |

## 核心功能

### 1. 真实反馈采集

项目从 GitHub 开源项目采集真实用户反馈：

- `streamlit/streamlit`
- `gradio-app/gradio`
- `langchain-ai/langchain`
- `open-webui/open-webui`
- `run-llama/llama_index`

采集内容包括：

- Issue title / body
- labels / state / author
- created_at / updated_at
- comments_count
- issue URL / comment URL
- Issue comments

### 2. Product Research Schema

核心数据表包括：

- `raw_feedback`
- `cleaned_feedback`
- `feedback_topics`
- `pain_points`
- `competitor_features`
- `opportunity_scores`
- `prd_drafts`
- `ai_evaluation_results`
- `bi_metrics_daily`

这些表把原始反馈、清洗结果、主题、痛点、机会点、PRD、评估结果和 BI 指标串成一条证据链。

### 3. Embedding / LLM Topic Discovery

主题分析使用 OpenAI Embedding 与 LLM 标签生成：

- Embedding model: `text-embedding-3-small`
- Chat model: `gpt-4o-mini`
- 支持 fallback 规则分类
- 每条 cleaned feedback 可落到 `feedback_topics`
- 保存 topic、keywords、sentiment、confidence、evidence_quote、analysis_method

这让 Dashboard 的 Topic Intelligence 不只是静态规则，而是可以解释的结构化主题聚类结果。

### 4. LangGraph StateGraph 工作流

工作流已经升级为真正的 LangGraph `StateGraph`：

```text
collector
-> feedback_analyst
-> competitor_analyst
-> opportunity_scorer
-> prd_writer
-> evaluation
-> human_review / bi_insight
-> persistence
-> export
```

条件路由包括：

- 数据不足：提前结束或返回采集链路
- 无机会点：跳过 PRD 生成，进入 BI 汇总
- 幻觉风险高：进入 Human Review Gate
- 证据覆盖不足：进入 Human Review Gate
- 输出质量较低：标记为需要人工复核

### 5. 竞品分析

项目支持通过 `data/sample_competitors.csv` 导入竞品能力矩阵，并写入 `competitor_features`。

当前覆盖能力类别包括：

- `agent_workflow`
- `ai_evaluation`
- `bi_dashboard`
- `export`
- `feedback_analysis`
- `human_review`
- `prd_generation`
- `topic_discovery`

Dashboard 中提供 Competitor Intelligence 页面，用于展示：

- 竞品数量
- 能力类别
- Feature rows
- 差异化机会
- 竞品能力矩阵

### 6. PRD 生成

PRD Writer Node 会基于选中的机会点、痛点和证据生成结构化 PRD：

- 背景
- 用户痛点
- 用户故事
- 功能需求
- 非功能需求
- 验收标准
- 成功指标
- 风险与边界
- 证据引用

关键约束：

- PRD 必须引用 pain point 和 evidence quote
- 不允许完全脱离原始反馈凭空生成
- 输出后进入 AI Evaluation
- 高风险结果进入 Human Review

### 7. AI Evaluation

AI Evaluation 评估维度包括：

- Relevance
- Accuracy
- Actionability
- Evidence Coverage
- Hallucination Risk
- PRD Completeness
- Human Edit Rate

评估结果会写入 `ai_evaluation_results`，并同步到 BI 指标。

### 8. Human Review Gate

当满足以下条件时，结果会进入人工审核：

- `hallucination_risk = high`
- `evidence_coverage < 0.60`
- overall score 低于阈值

Human Review 输出包括：

- `needs_review`
- `human_review_status`
- `review_reason`
- `review_notes`

### 9. BI Dashboard

Dashboard 使用 Streamlit + Pandas + Plotly + SQLite。

页面包括：

1. Research Overview
2. Feedback Intelligence
3. Opportunity Pipeline
4. AI Evaluation Monitor
5. Competitor Intelligence
6. Workflow Output

Dashboard 用于展示：

- 反馈总量
- 仓库分布
- 反馈类型分布
- 主题分布
- 情绪分布
- Top Pain Points
- P0 / P1 / P2 机会点
- AI 质量评分
- Human Review 状态
- 竞品能力矩阵
- Workflow 导出结果

### 10. 标准 MCP Server

项目已经提供标准 MCP Server：

```text
src/mcp_server/server.py
```

可被 Claude Desktop、Cursor、Codex MCP 配置等 MCP Client 调用。

MCP Server 暴露的能力包括：

- 查询数据库统计
- 查询 repo summary
- 查询 topic summary / samples
- 查询 competitor summary / matrix
- 查询 opportunity / PRD / evaluation
- 调用 GitHub feedback 工具
- 调用 evaluation tool
- 调用 export tool

MCP Client 配置说明见：

```text
docs/mcp_client_setup.md
```

## 技术栈

- Python 3.13
- SQLite
- Pandas
- Plotly
- Streamlit
- LangGraph
- OpenAI API
- MCP / FastMCP
- GitHub REST API

## 目录结构

```text
ai-product-research-copilot/
├── README.md
├── requirements.txt
├── .env.example
├── docs/
│   ├── PRD.md
│   ├── langgraph_workflow.md
│   ├── mcp_tool_design.md
│   ├── mcp_client_setup.md
│   ├── metrics_framework.md
│   ├── data_schema.md
│   └── case_study.md
├── database/
│   ├── schema.sql
│   └── product_research.db
├── data/
│   └── sample_competitors.csv
├── scripts/
│   └── smoke_test.py
├── src/
│   ├── data_ingestion/
│   │   ├── github_api.py
│   │   ├── cleaner.py
│   │   ├── validate_collection.py
│   │   └── competitor_loader.py
│   ├── langgraph_agents/
│   │   ├── graph.py
│   │   ├── state.py
│   │   ├── collector_node.py
│   │   ├── feedback_analyst_node.py
│   │   ├── topic_clusterer.py
│   │   ├── competitor_analyst_node.py
│   │   ├── opportunity_scorer_node.py
│   │   ├── prd_writer_node.py
│   │   ├── evaluation_node.py
│   │   ├── human_review_node.py
│   │   ├── bi_insight_node.py
│   │   └── persistence.py
│   ├── mcp_tools/
│   │   ├── github_tool.py
│   │   ├── database_tool.py
│   │   ├── evaluation_tool.py
│   │   └── export_tool.py
│   ├── mcp_server/
│   │   └── server.py
│   └── utils/
│       └── config.py
├── app/
│   └── streamlit_app.py
└── outputs/
    ├── workflow/
    ├── exports/
    └── dashboard_screenshots/
```

## 环境配置

### 1. 安装依赖

```powershell
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`：

```powershell
Copy-Item .env.example .env
```

`.env` 示例：

```text
GITHUB_TOKEN=
GITHUB_API_BASE=https://api.github.com
OPENAI_API_KEY=
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4o-mini
DATABASE_PATH=database/product_research.db
```

说明：

- `GITHUB_TOKEN` 可选，但建议配置，用于提高 GitHub API rate limit。
- `OPENAI_API_KEY` 用于 Embedding / LLM 主题聚类。
- `.env` 不应提交到 Git。

## 运行方式

### 1. 初始化数据库

```powershell
python database\init_db.py
```

### 2. 采集 GitHub 数据

```powershell
python src\data_ingestion\github_api.py --repos streamlit/streamlit gradio-app/gradio --max-issues 50 --include-comments
```

### 3. 清洗反馈

```powershell
python src\data_ingestion\cleaner.py
```

### 4. 验证采集结果

```powershell
python src\data_ingestion\validate_collection.py --sample-limit 5
```

### 5. 导入竞品样例数据

```powershell
python src\data_ingestion\competitor_loader.py --file data\sample_competitors.csv
```

### 6. 运行 LangGraph Agent 工作流

```powershell
python src\langgraph_agents\graph.py --repos streamlit/streamlit gradio-app/gradio --limit 30 --save --export
```

常用参数：

- `--repos`: 选择分析仓库
- `--limit`: 每个仓库读取多少条 cleaned feedback
- `--save`: 写入数据库
- `--export`: 导出 workflow summary、PRD、BI metrics

### 7. 启动 Dashboard

```powershell
streamlit run app\streamlit_app.py
```

默认访问：

```text
http://localhost:8501
```

### 8. 启动 MCP Server

```powershell
python src\mcp_server\server.py
```

终端停在运行状态、没有报错，就是 MCP Server 已经在等待 MCP Client 通过 stdio 调用。MCP Server 默认不是网页服务，因此不会自动打开浏览器页面。

### 9. 运行 Smoke Test

```powershell
python scripts\smoke_test.py
```

Smoke Test 会检查：

- 数据库是否存在
- 核心表是否存在
- 核心表是否有数据
- 必要文件是否存在
- workflow outputs 是否存在
- requirements 是否完整
- 关键模块是否可 import

期望输出：

```json
{
  "success": true
}
```

## MCP Client 配置

项目的 MCP Server 可以被支持 MCP 的客户端调用。

详细配置见：

```text
docs/mcp_client_setup.md
```

典型启动命令：

```powershell
python src\mcp_server\server.py
```

常见 MCP Client：

- Claude Desktop
- Cursor
- Codex MCP 配置

## 示例输出

工作流导出目录：

```text
outputs/workflow/
```

包含：

- `workflow_summary.json`
- `workflow_summary.md`
- `prd_draft.md`
- `bi_metrics.json`

导出示例：

```powershell
python src\mcp_tools\export_tool.py --repo-summary --markdown --cleaned-csv
```

导出目录：

```text
outputs/exports/
```

## 项目文档

- `docs/PRD.md`: 产品定义与需求边界
- `docs/langgraph_workflow.md`: Agent 工作流与条件路由
- `docs/mcp_tool_design.md`: MCP 工具设计
- `docs/mcp_client_setup.md`: MCP Client 连接说明
- `docs/metrics_framework.md`: 指标体系
- `docs/data_schema.md`: 数据库 Schema 说明
- `docs/case_study.md`: 作品集案例复盘

## 作品集亮点

这个项目适合作为 AI 产品经理 / 数据产品经理作品集项目，亮点包括：

- 使用真实 GitHub Issues / Comments 作为用户反馈来源
- 设计统一 Product Research Schema
- 使用 OpenAI Embedding / LLM 做主题聚类与用户需求抽取
- 使用 LangGraph `StateGraph` 编排多 Agent 工作流
- 通过 MCP Server 标准化工具调用
- 把用户痛点、竞品差距、机会点评分、PRD 和 AI Evaluation 串成闭环
- 通过 Human Review Gate 控制 AI 输出风险
- 通过 BI Dashboard 支持产品复盘和数据驱动决策

## 简历表达示例

可用于简历 / 面试的表达：

- Designed and implemented an Agentic Product Research Platform that converts real GitHub Issues and Comments into structured product insights, opportunity scores, PRD drafts, AI evaluation reports, and BI dashboards.
- Built a LangGraph StateGraph workflow with topic discovery, pain point extraction, competitor intelligence, opportunity scoring, PRD generation, AI evaluation, and human review routing.
- Implemented a Product Research Schema in SQLite to persist raw feedback, cleaned feedback, topics, pain points, competitor features, opportunity scores, PRDs, evaluation results, and BI metrics.
- Integrated OpenAI embeddings and LLM-based topic labeling to cluster feedback and produce evidence-backed user needs.
- Built a standard MCP Server to expose GitHub, database, evaluation, and export tools to MCP-compatible clients.
- Created a Streamlit BI dashboard for feedback intelligence, opportunity pipeline review, AI quality monitoring, competitor intelligence, and workflow outputs.

## 当前限制与下一步

建议继续优化：

- 补充 Dashboard 截图到 `outputs/dashboard_screenshots/`
- 扩大数据规模到 3,000 到 5,000 条反馈
- 提升 PRD Evaluation 的 claim-level evidence matching
- 增加更多 MCP Client 实测截图
- 增加单元测试与 CI
- 进一步优化中英文混合 PRD 文案
- 增加 Dashboard 的 Export / Case Study 页面

## 安全说明

- 不要提交 `.env`
- 不要提交真实 API Key
- 如需公开项目，建议不要提交本地 SQLite 数据库，或只提交脱敏样例数据
- GitHub Token 和 OpenAI API Key 应通过环境变量读取

