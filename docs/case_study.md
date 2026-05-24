# 项目 Case Study: AI 产品调研 Agent 与 BI 决策平台

## 1. 项目简介

本项目是一个面向 AI 产品经理、数据产品经理和产品运营团队的 AI Agent + BI 决策平台。

系统使用 GitHub Issues、用户评论和竞品资料作为真实数据源，通过 LangGraph 编排多 Agent 工作流，并通过 MCP 工具层封装 GitHub、数据库、评估和导出能力，最终完成用户反馈分析、竞品洞察、机会点评分、PRD 生成、AI 输出评估和 BI Dashboard 复盘。

## 2. 项目背景

AI 产品经理在实际工作中需要处理大量分散的用户反馈，包括 GitHub Issues、社区评论、产品建议、Bug报告和竞品更新。

传统方式依赖人工整理，存在效率低、主观性强、难以持续复盘等问题。

同时，通用 AI 工具虽然可以生成总结和 PRD，但缺少真实证据、质量评估和产品工作流闭环，难以直接用于严肃的产品决策。

因此，本项目希望构建一个从真实反馈到产品决策的端到端系统。

## 3. 我解决的问题

本项目重点解决 5 个问题：

1. 用户反馈分散，人工整理成本高。
2. AI 总结缺少证据支撑，容易产生幻觉。
3. 产品机会点缺少量化评分。
4. PRD 生成结果缺少质量评估。
5. 产品调研结果无法通过 BI 持续复盘。

## 4. 我的解决方案

我设计了一个完整的 Agentic Product Research Workflow:

```text
真实数据采集
-> 统一数据 Schema
-> 多 Agent 分析
-> MCP 工具调用
-> 机会点评分
-> PRD生成
-> AI Evaluation
-> BI Dashboard 复盘
```

系统核心模块包括：

- GitHub 数据采集模块
- Product Research Schema
- LangGraph 多 Agent 工作流
- MCP 工具调用层
- 反馈分析与痛点提取
- 机会点评分模型
- PRD 生成模块
- AI Evaluation 模块
- BI Dashboard

## 5. 数据来源

MVP 阶段使用 GitHub Issues / Comments 作为真实用户反馈来源。

目标仓库包括：

- streamlit/streamlit
- gradio-app/gradio
- langchain-ai/langchain
- open-webui/open-webui
- run-llama/llama_index

这些仓库适合作为数据源，因为它们包含大量真实的 Bug、Feature Request、用户抱怨、产品建议和开发者讨论。

## 6. 产品架构

```text
Data Layer
GitHub Issues / Comments / Release Notes / Competitor Docs

MCP Tool Layer
GitHub Tool / Database Tool / Evaluation Tool / Export Tool

LangGraph Agent Layer
Collector / Cleaner / Feedback Analyst / Competitor Analyst / Opportunity Scorer / PRD Writer / Evaluation / BI Insight

Product Workflow Layer
Research Project / Feedback Insights / Opportunity Pipeline / PRD Draft / Human Review

BI & Evaluation Layer
Research Overview / Feedback Intelligence / Opportunity Pipeline / AI Evaluation Monitor

Portfolio Output
PRD / Case Study / Dashboard Screenshots / Resume Bullets
```

## 7. LangGraph 工作流设计

本项目使用 LangGraph 管理多 Agent 状态流转。

核心节点包括：

- Collector Node：采集 GitHub Issues 和 Comments
- Cleaner Node：清洗反馈数据
- Feedback Analyst Node：分析主题、情绪和痛点
- Competitor Analyst Node：生成竞品矩阵
- Opportunity Scorer Node：对机会点排序
- PRD Writer Node：生成 PRD 草稿
- Evaluation Node：评估 AI 输出质量
- Human Review Node：人工审核
- BI Insight Node：生成复盘指标和建议

通过条件路由，系统可以处理数据不足、证据不足、PRD 质量低和幻觉风险高等情况。

## 8. MCP 工具层设计

本项目通过 MCP-style 工具接口封装外部能力：

- GitHub Tool：采集 Issues、Comments、Releases
- Database Tool：查询和写入反馈、痛点、机会点、评估结果
- Evaluation Tool：计算相关性、准确性、证据覆盖率和幻觉风险
- Export Tool：导出 PRD、调研报告和 CSV

MVP 阶段先实现 Python 工具接口，后续可升级为真正 MCP Server。

## 9. AI Evaluation 设计

为避免 AI 输出不可控，本项目设计了 AI Evaluation 体系。

评估维度包括：

- Relevance：是否相关
- Accuracy：是否准确
- Actionability：是否可执行
- Evidence Coverage：证据覆盖率
- Hallucination Risk：幻觉风险
- Human Edit Rate：人工修改率
- PRD Completeness：PRD 完整度

每个 PRD 和产品洞察都需要绑定原始 evidence_quote，保证结论可追溯。

## 10. BI Dashboard 设计

Dashboard 包括以下页面：

1. Research Overview  
   展示反馈总量、仓库数量、正负面比例、Top Pain Points 和 AI 质量评分。

2. Feedback Intelligence  
   展示主题分布、情绪趋势、来源分布、高频关键词和典型证据。

3. Opportunity Pipeline  
   展示 P0/P1/P2 机会点分布、价值-难度矩阵、PRD 状态和人工审核状态。

4. AI Evaluation Monitor  
   展示相关性、准确性、证据覆盖率、幻觉风险和人工修改率。

5. Competitor Intelligence  
   展示竞品功能矩阵、差异化机会和功能差距。

6. Business Impact  
   展示节省时间、报告生成效率、人工修改成本和潜在 ROI。

## 11. 项目成果指标

计划达成以下目标：

- 采集 3-5 个 AI 工具仓库
- 处理 10000+ 条 Issues / Comments
- 构建 20+ BI 指标
- PRD 完整度评分达到 4/5 以上
- AI 输出相关性评分达到 4/5 以上
- 证据覆盖率达到 80% 以上
- 低幻觉风险输出占比达到 85% 以上
- 人工修改率控制在 30% 以下

## 12. 项目亮点

本项目的亮点包括：

1. 使用真实 GitHub 数据，而不是纯演示数据。
2. 通过统一 Product Research Schema 实现全链路追溯。
3. 使用 LangGraph 编排多 Agent 工作流。
4. 通过 MCP 工具层提升 Agent 工具调用稳定性。
5. 引入 AI Evaluation，控制幻觉风险。
6. 将 AI 产品调研结果转化为 BI 决策看板。
7. 最终可沉淀为完整作品集、简历项目和面试案例。

## 13. 简历表达

中文版本：

设计并实现面向 AI 工具产品的 AI 产品调研 Agent 与 BI 决策平台，覆盖真实用户反馈采集、痛点分析、竞品洞察、机会点评分、PRD 生成、AI 输出评估和 BI 复盘。

基于 GitHub API 构建真实反馈数据管道，采集并清洗 AI 工具类开源产品的 Issues / Comments，设计统一 Product Research Schema，实现从原始反馈到 PRD 和评估结果的全链路追踪。

使用 LangGraph 编排多 Agent 工作流，包含 Feedback Analyst、Competitor Analyst、Opportunity Scorer、PRD Writer、Evaluation Agent 和 BI Insight Agent，实现复杂产品调研任务的模块化拆解。

设计 MCP 工具调用层，封装 GitHub 数据采集、数据库查询、AI 输出评估和报告导出能力，提升 Agent 调用外部工具的稳定性和可扩展性。

构建 BI Dashboard 指标体系，监控反馈趋势、需求优先级、竞品差距、PRD 质量、幻觉风险、证据覆盖率、人工修改率和用户满意度，形成 AI 产品从调研到复盘的闭环。

## 14. 总结

这个项目不是一个简单的 AI 文档生成 Demo，而是一个完整的 AI 产品管理工作流系统。

它体现了产品定义、真实数据处理、Agent 工作流设计、MCP 工具调用、AI 质量评估和 BI 数据产品能力，适合作为 AI 产品经理、数据产品经理和 AI 产品运营方向的核心作品集项目。
