# Case Study: AI 产品调研 Agent 与 BI 决策平台

## 1. 项目概述

本项目是一个面向 AI 产品经理 / 数据产品经理的 **Agentic Product Research & BI Decision Platform**。

系统基于真实 GitHub Issues / Comments 数据，完成从用户反馈采集、数据清洗、Embedding 主题聚类、痛点提取、竞品洞察、机会点评分、PRD 草稿生成、AI Evaluation、Human Review Gate 到 Streamlit BI Dashboard 复盘的完整闭环。

项目不是单次 AI 总结 Demo，而是一个可运行、可验证、可展示的 AI 产品调研工作流系统。

核心闭环：

```text
真实用户反馈采集
-> 数据清洗与统一 Schema
-> OpenAI Embedding / LLM Topic Discovery
-> LangGraph StateGraph 多 Agent 分析
-> 标准 MCP Server 工具调用
-> 用户痛点 / 竞品洞察 / 机会点评分
-> PRD 草稿生成
-> AI Evaluation
-> Human Review Gate
-> BI Dashboard 复盘
-> 作品集展示
```

## 2. 项目背景

AI 产品经理在做产品调研时，需要从大量真实反馈中识别用户痛点、机会点和产品优先级。但传统流程存在几个问题：

- 用户反馈分散在 GitHub Issues、Comments、Release Notes 和社区讨论中
- 手工阅读大量反馈成本高，难以持续复盘
- AI 生成 PRD 容易缺少证据支撑，存在幻觉风险
- 产品机会点缺少统一评分体系
- 竞品分析、用户反馈和 PRD 输出经常割裂
- 调研结果难以转化为 BI 指标和作品集材料

因此，我设计并实现了一个 AI 产品调研 Agent 平台，将真实用户反馈转化为结构化洞察、机会点、PRD 草稿和 BI 决策面板。

## 3. 当前真实数据规模

截至当前版本，项目已经完成第一版真实数据闭环。

| 指标 | 当前数量 |
|---|---:|
| Raw Feedback | 541 |
| Cleaned Feedback | 541 |
| Feedback Topics | 69 |
| Pain Points | 19 |
| Competitor Features | 15 |
| Opportunity Scores | 19 |
| PRD Drafts | 3 |
| AI Evaluation Results | 8 |
| BI Metrics | 18 |

第一批真实数据来源：

- `streamlit/streamlit`
- `gradio-app/gradio`
- `langchain-ai/langchain`
- `open-webui/open-webui`
- `run-llama/llama_index`

当前版本已达到 MVP 第一阶段目标：采集并处理 300-1000 条真实 Issues / Comments。

## 4. 系统架构

```text
Data Sources
GitHub Issues / Comments / Competitor Feature Matrix

Data Layer
SQLite / raw_feedback / cleaned_feedback / feedback_topics / pain_points / competitor_features / opportunity_scores / prd_drafts / ai_evaluation_results / bi_metrics_daily

MCP Layer
Standard MCP Server / GitHub Tools / Database Tools / Evaluation Tools / Export Tools

Agent Workflow Layer
LangGraph StateGraph / Collector / Feedback Analyst / Competitor Analyst / Opportunity Scorer / PRD Writer / Evaluation / Human Review / BI Insight

BI & Portfolio Layer
Streamlit Dashboard / Workflow Export / PRD Draft / Research Summary / Case Study
```

## 5. 数据层设计

项目使用 SQLite 作为轻量数据层，支持本地运行和作品集展示。

核心表包括：

| 表名 | 作用 |
|---|---|
| `raw_feedback` | 保存 GitHub Issues / Comments 原始反馈 |
| `cleaned_feedback` | 保存清洗后的反馈文本、语言和反馈类型 |
| `feedback_topics` | 保存 Embedding / LLM 识别出的主题、情绪、置信度和证据 |
| `pain_points` | 保存用户痛点、用户需求、证据数量和优先级提示 |
| `competitor_features` | 保存竞品功能矩阵和功能覆盖情况 |
| `opportunity_scores` | 保存机会点评分和优先级 |
| `prd_drafts` | 保存结构化 PRD 草稿 |
| `ai_evaluation_results` | 保存 AI 输出质量评估结果 |
| `bi_metrics_daily` | 保存 BI 指标和复盘数据 |

数据层保证每条结论都可以追溯到原始 GitHub Issue / Comment。

## 6. GitHub 数据采集

数据采集模块位于：

```text
src/data_ingestion/github_api.py
src/data_ingestion/cleaner.py
src/data_ingestion/validate_collection.py
```

能力包括：

- 调用 GitHub Issues API
- 获取 title / body / labels / state / author / created_at / comments_count
- 获取 Issue Comments
- 支持 GitHub Token
- 支持分页、限流提示和失败重试
- 写入 SQLite 数据库
- 清洗原始反馈并生成统一 Product Research Schema
- 验证数据完整性、comments 数量、字段缺失和清洗覆盖率

## 7. OpenAI Embedding / LLM Topic Discovery

项目使用 OpenAI Embedding 对清洗后的用户反馈进行相似度聚类，并通过 LLM 对主题进行命名和总结。

相关模块：

```text
src/langgraph_agents/topic_clusterer.py
src/langgraph_agents/feedback_analyst_node.py
```

输出到：

```text
feedback_topics
```

每条 topic 记录包含：

- topic
- topic_keywords
- topic_summary
- user_need
- sentiment
- confidence
- evidence_quote
- analysis_method

当前已验证真实 OpenAI Embedding 调用：

```text
analysis_method = openai_embedding
```

这使项目不只是规则分类，而是具备基于语义相似度的主题发现能力。

## 8. 竞品分析模块

竞品分析模块用于把用户反馈洞察与市场竞品能力进行对照。

相关模块：

```text
src/data_ingestion/competitor_loader.py
src/langgraph_agents/competitor_analyst_node.py
```

数据表：

```text
competitor_features
```

当前竞品能力矩阵覆盖：

- Dovetail
- Productboard
- LangSmith
- LangChain
- LlamaIndex
- Open WebUI
- Streamlit
- Gradio
- Notion AI
- Airtable
- Jira Product Discovery

Dashboard 中已经实现：

```text
Competitor Intelligence
```

展示能力包括：

- 竞品数量
- 功能类别数量
- Feature Rows
- 差异化机会数量
- Coverage Distribution
- Feature Category Distribution
- Competitor x Capability Heatmap
- Feature Matrix
- Differentiation Opportunities

## 9. LangGraph StateGraph 工作流

项目已经从普通顺序 Pipeline 升级为真正的 LangGraph StateGraph。

核心文件：

```text
src/langgraph_agents/graph.py
src/langgraph_agents/state.py
```

节点包括：

- Collector Node
- Feedback Analyst Node
- Competitor Analyst Node
- Opportunity Scorer Node
- PRD Writer Node
- Evaluation Node
- Human Review Node
- BI Insight Node

当前工作流：

```text
collector
-> feedback_analyst
-> competitor_analyst
-> opportunity_scorer
-> prd_writer
-> evaluation
-> conditional routing
   -> human_review
   -> bi_insight
-> END
```

条件路由包括：

- 数据不足：结束流程并记录错误
- 无机会点：跳过 PRD 生成，进入 BI Insight
- 幻觉风险高：进入 Human Review
- 证据覆盖率低：进入 Human Review
- 总评分过低：进入 Human Review

这证明项目不是简单调用一次 LLM，而是具备多节点、状态驱动、带质量闸门的 Agent 工作流。

## 10. 标准 MCP Server

项目已经从 MCP-style Python 工具接口升级为标准 MCP Server。

核心文件：

```text
src/mcp_server/server.py
```

使用：

```python
from mcp.server.fastmcp import FastMCP
```

暴露的标准 MCP tools 包括：

- `database_stats`
- `database_repo_summary`
- `database_query_raw_feedback`
- `database_query_cleaned_feedback`
- `database_topic_summary`
- `database_topic_samples`
- `database_competitor_summary`
- `database_competitor_matrix`
- `database_opportunity_summary`
- `database_latest_prd`
- `database_latest_evaluation`
- `github_fetch_repo_issues`
- `github_fetch_issue_comments`
- `github_fetch_repo_feedback_tool`
- `github_fetch_release_notes`
- `evaluation_score_output`
- `export_cleaned_feedback`
- `export_repo_summary`
- `export_research_summary`

MCP Server 的作用是让 Agent 通过标准协议稳定调用 GitHub、数据库、评估和导出能力。

## 11. 机会点评分体系

机会点评分模块位于：

```text
src/langgraph_agents/opportunity_scorer_node.py
```

评分维度包括：

- User Value
- Business Value
- Frequency
- Severity
- Effort
- Risk
- AI Feasibility
- Evidence Strength

输出优先级：

- P0：必须优先解决
- P1：重要但可排期
- P2：观察 / Backlog

这些结果会写入：

```text
opportunity_scores
```

并进入 Dashboard 的 Opportunity Pipeline 页面。

## 12. PRD 生成模块

PRD Writer Node 位于：

```text
src/langgraph_agents/prd_writer_node.py
```

当前已经优化为更接近真实产品经理写作方式，输出包括：

- 背景
- 用户痛点
- 用户故事
- 功能需求
- 非功能需求
- 验收标准
- 成功指标
- 风险与边界
- 证据引用

示例输出：

```text
# 运行稳定性与错误处理优化 PRD

作为数据应用开发者，我希望在遇到性能下降、组件异常或运行错误时，能够快速理解问题原因并获得明确的处理建议，以便更稳定、高效地完成核心工作流。
```

每个 PRD 草稿都绑定 evidence quote，并经过 Evaluation Node 和 Human Review Gate。

## 13. AI Evaluation 与 Human Review Gate

AI Evaluation 模块位于：

```text
src/langgraph_agents/evaluation_node.py
src/mcp_tools/evaluation_tool.py
```

评估维度包括：

- Relevance
- Accuracy
- Actionability
- Evidence Coverage
- Hallucination Risk
- PRD Completeness
- Human Edit Rate

Human Review 模块位于：

```text
src/langgraph_agents/human_review_node.py
```

当满足以下条件时进入人工审核：

- `hallucination_risk = high`
- `evidence_coverage < 0.6`
- `overall_score < 4.0`

当前真实运行结果示例：

```text
needs_review: true
human_review_status: needs_review
review_reason: AI 输出存在高风险或证据覆盖不足，需要人工复核。
```

这体现了 AI 产品质量闭环，而不是单纯生成内容。

## 14. BI Dashboard

Dashboard 使用：

```text
Streamlit + Plotly + Pandas + SQLite
```

核心文件：

```text
app/streamlit_app.py
```

页面包括：

1. Research Overview
2. Feedback Intelligence
3. Opportunity Pipeline
4. AI Evaluation Monitor
5. Competitor Intelligence
6. Workflow Output

Dashboard 当前可以展示：

- 反馈总量
- 仓库覆盖数
- Comments 数量
- 反馈类型分布
- 高频痛点
- 机会点优先级
- AI Evaluation 结果
- Human Review 状态
- 竞品能力矩阵
- 差异化机会
- Workflow 输出与 PRD 草稿

## 15. 导出结果

项目会生成以下作品集材料：

```text
outputs/workflow/workflow_summary.json
outputs/workflow/workflow_summary.md
outputs/workflow/prd_draft.md
outputs/workflow/bi_metrics.json
outputs/exports/cleaned_feedback.csv
outputs/exports/repo_summary.json
outputs/exports/research_summary.md
```

这些文件可用于 README、作品集页面、面试讲解和简历补充材料。

## 16. 项目亮点

本项目亮点包括：

1. 使用真实 GitHub Issues / Comments，而不是纯模拟数据。
2. 建立统一 Product Research Schema，实现原始反馈、清洗反馈、主题、痛点、机会点、PRD 和评估结果的追溯。
3. 使用 OpenAI Embedding + LLM 进行语义主题发现。
4. 使用 LangGraph StateGraph 编排多 Agent 工作流和条件路由。
5. 使用标准 MCP Server 封装 GitHub、数据库、评估和导出工具。
6. 引入 AI Evaluation 和 Human Review Gate，控制幻觉风险和证据不足问题。
7. 将竞品能力矩阵与用户反馈分析结合，识别差异化机会。
8. 使用 Streamlit BI Dashboard 支持产品复盘和数据驱动决策。
9. 最终输出 PRD、调研报告、CSV、JSON 和作品集 Case Study。

## 17. 当前不足与后续计划

当前项目已经完成 MVP 主链路，但仍有可优化空间：

- 增加 `.env.example` 并完善配置说明
- 补充 Dashboard 截图并放入 `outputs/dashboard_screenshots/`
- 增加 `scripts/smoke_test.py` 或 `tests/`，减少手动验证成本
- 将 Dashboard SQL 抽离到 `src/analytics/bi_queries.py`
- 优化 fallback topic summary，让 PRD 背景更加自然
- 增加更严格的 Evidence Claim Matching
- 补充部署说明和 MCP Client 配置示例
- 扩大数据规模到 3000-5000 条反馈

## 18. 简历表达

中文版本：

- 设计并实现 AI 产品调研 Agent 与 BI 决策平台，基于真实 GitHub Issues / Comments 构建从用户反馈采集、语义主题聚类、痛点提取、机会点评分、PRD 生成、AI 评估到 BI Dashboard 复盘的端到端闭环。
- 使用 OpenAI Embedding 与 LLM 对 500+ 条真实用户反馈进行主题发现和产品洞察提取，并将主题、痛点、证据和机会点沉淀到统一 Product Research Schema。
- 基于 LangGraph StateGraph 编排 Collector、Feedback Analyst、Competitor Analyst、Opportunity Scorer、PRD Writer、Evaluation、Human Review 和 BI Insight 等节点，实现带条件路由的多 Agent 工作流。
- 设计标准 MCP Server，封装 GitHub 数据采集、数据库查询、AI Evaluation 和导出能力，使 Agent 能通过统一工具协议稳定调用外部能力。
- 构建 AI Evaluation 与 Human Review Gate，监控相关性、准确性、证据覆盖率、幻觉风险和 PRD 完整度，形成 AI 输出质量闭环。
- 使用 Streamlit + Plotly 构建 BI Dashboard，展示反馈分析、机会点优先级、竞品能力矩阵、差异化机会、AI 评估和工作流输出。

English version:

- Designed and built an Agentic Product Research Platform that transforms real GitHub Issues and Comments into structured topics, pain points, opportunity scores, PRD drafts, AI evaluation results, and BI insights.
- Implemented an OpenAI embedding-based topic discovery pipeline with LLM-generated topic labels, user needs, sentiment, confidence scores, and evidence tracking.
- Built a LangGraph StateGraph workflow with Collector, Feedback Analyst, Competitor Analyst, Opportunity Scorer, PRD Writer, Evaluation, Human Review, and BI Insight nodes.
- Implemented a standard MCP Server exposing GitHub, database, evaluation, and export tools for stable Agent tool usage.
- Designed an AI Evaluation and Human Review framework covering relevance, accuracy, actionability, evidence coverage, hallucination risk, and PRD completeness.
- Created a Streamlit BI Dashboard to visualize research overview, feedback intelligence, opportunity pipeline, AI evaluation, competitor intelligence, and workflow outputs.

## 19. 总结

这个项目证明了 5 件事：

1. 我能够进行产品定义、PRD 设计和作品集表达。
2. 我能够处理真实数据，而不是只做假 Demo。
3. 我理解 Agent 工作流和 LangGraph 状态编排。
4. 我知道 AI 输出需要评估、证据约束和人工审核。
5. 我能够把 AI 能力转化为 BI 决策和业务价值。

本项目适合作为 AI 产品经理、数据产品经理、AI 应用产品经理和 Agentic Workflow 产品方向的核心作品集项目。
