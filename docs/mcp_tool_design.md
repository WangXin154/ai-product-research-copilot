# MCP 工具调用层设计

## 1. 文档目的

本文档用于说明本项目中 MCP 工具调用层的设计方案，包括工具层定位、核心工具列表、输入输出结构、Agent 调用关系和 MCP 实现建议。

MCP 在本项目中的作用是为 LangGraph Agent 提供标准化、可复用、可追踪的工具调用能力。

本项目中的 MCP 不只是技术包装，而是用于解决以下问题：

- Agent 如何稳定调用 GitHub 数据源
- Agent 如何查询和写入数据库
- Agent 如何执行 AI 输出评估
- Agent 如何导出 PRD 报告和 BI 数据
- Agent 如何把外部系统能力纳入统一工作流

## 2. MCP 在项目中的定位

本项目整体架构如下：

```text
Data Layer
GitHub Issues / Comments / Release Notes / Competitor Docs

MCP Tool Layer
GitHub Tool / Database Tool / Evaluation Tool / Export Tool

LangGraph Agent Layer
Collector / Feedback Analyst / Competitor Analyst / Opportunity Scorer / PRD Writer / Evaluation / BI Insight

Product Workflow Layer
Research Project / Feedback Insights / Opportunity Pipeline / PRD Draft / Human Review

BI & Evaluation Layer
Research Overview / Feedback Intelligence / Opportunity pipeline / AI Evaluation Monitor
```

MCP Tool Layer 位于数据层和 Agent 层之间。

它的职责是把外部能力封装成稳定接口，让 Agent 不直接处理复杂外部系统细节。

## 3. 设计原理

### 3.1 工具指责单一

每个工具只负责一类清晰任务，例如：

- GitHub Tool 只负责 GitHub 数据采集
- Database Tool 只负责数据库读写
- Evaluation Tool 只负责 AI 输出评估
- Export Tool 只负责文件导出

### 3.2 输入输出结构化

所有工具都应该使用结构化输入和结构化输出，避免 Agent 直接处理不可控文本。

### 3.3 结果可追溯

工具返回的数据必须包含来源信息，例如：

- GitHub Issue URL
- Comment ID
- Repo Name
- Evidence Quote
- Created Time

### 3.4 错误可处理

工具调用失败时，不应该直接中断整个工作流，而应该返回结构化错误信息。

### 3.5 MVP 先做 MCP-style 接口

MVP 阶段可以先用 Python 函数或类实现 MVP 风格接口。等住流程跑通后，再升级为真正 MCP Server。

## 4. MCP 工具总览

| 工具 | 主要能力 | 调用方 | 核心产出 |
|---|---|---|---|
| GitHub Tool | 采集 Issues、Comments、Labels、Releases | Collector Node | raw_feedback |
| Database Tool | 查询和写入数据库 | 所有 Agent | 结构化数据 |
| Competitor Tool | 读取竞品资料和功能矩阵 | Competitor Analyst Node | competitor_matrix |
| Evaluation Tool | 评估 AI 输出质量 | Evaluation Node | ai_evaluation_results |
| Export Tool | 导出 PRD、报告、CSV | PRD Writer Node / BI Insight Node | 输出文件 |

## 5. GitHub Tool 设计

GitHub Tool 用于采集真实用户反馈数据，是本项目最重要的数据来源工具。

### 5.1 github.fetch_issues

用途：从指定 GitHub 仓库采集 Issues.

输入：

```json
{
  "owner": "streamlit",
  "repo": "streamlit",
  "state": "all",
  "labels": ["bug", "enhancement"],
  "since": "2025-01-01",
  "per_page": 100,
  "max_pages": 5
}
```

输出：

```json
{
  "success": true,
  "data": [
    {
      "issue_id": 12345,
      "repo_name": "streamlit/streamlit",
      "title": "App crashes when uploading large files",
      "body": "The app crashes when I upload a CSV larger than 100MB.",
      "labels": ["bug"],
      "state": "open",
      "author": "example_user",
      "created_at": "2025-01-10T10:00:00Z",
      "updated_at": "2025-01-12T12:00:00Z",
      "comments_count": 8,
      "url": "https://github.com/streamlit/streamlit/issues/12345"
    }
  ],
  "meta": {
    "repo_name": "streamlit/streamlit",
    "fetched_count": 1,
    "page_count": 1
  }
}
```

错误输出：

```json
{
  "success": false,
  "error": {
    "code": "GITHUB_RATE_LIMIT",
    "message": "GitHub API rate limit exceeded"
  }
}
```

### 5.2 github.fetch_comments

用途：采集指定 Issue 下的评论。

输入：

```json
{
  "owner": "streamlit",
  "repo": "streamlit",
  "issue_id": 12345
}
```

输出：

```json
{
  "success": true,
  "data": [
    {
      "comment_id": 98765,
      "issue_id": 12345,
      "repo_name": "streamlit/streamlit",
      "body": "I have the same issue with large file uploads.",
      "author": "another_user",
      "created_at": "2025-01-11T09:00:00Z",
      "url": "https://github.com/streamlit/streamlit/issues/12345#issuecomment-98765"
    }
  ]
}
```

### 5.3 github.fetch_releases

用途：采集仓库 Release Notes，用于分析产品版本变化和竞品动态。

输入：

```json
{
  "owner": "streamlit",
  "repo": "streamlit",
  "max_items": 20
}
```

输出：

```json
{
  "success": true,
  "data": [
    {
      "release_id": 111,
      "repo_name": "streamlit/streamlit",
      "tag_name": "v1.40.0",
      "title": "Streamlit 1.40.0",
      "body": "Release notes content",
      "published_at": "2025-01-01T00:00:00Z",
      "url": "https://github.com/streamlit/streamlit/releases/tag/v1.40.0"
    }
  ]
}
```

## 6. Database Tool 设计

Database Tool 用于统一管理项目数据读写。

MVP 阶段建议使用 SQLite 或 DuckDB。

### 6.1 database.insert_records

用途：向指定数据表批量写入记录。

输入：

```json
{
  "table": "raw_feedback",
  "records": [
    {
      "feedback_id": "fb_001",
      "source": "github",
      "repo_name": "streamlit/streamlit",
      "issue_id": "12345",
      "title": "App crashes when uploading large files",
      "body": "The app crashes when I upload a CSV larger than 100MB."
    }
  ]
}
```

输出：

```json
{
  "success": true,
  "inserted_count": 1,
  "failed_count": 0
}
```

### 6.2 database.query

用途：执行结构化 SQL 查询。

输入：

```json
{
  "sql_query": "SELECT * FROM pain_points ORDER BY evidence_count DESC LIMIT 10"
}
```

输出：

```json
{
  "success": true,
  "data": [
    {
      "pain_point_id": "pp_001",
      "user_pain": "用户上传大文件时经常遇到崩溃问题",
      "evidence_count": 18,
      "priority_hint": "P0"
    }
  ]
}
```

### 6.3 database.query_metrics

用途：查询 BI Dashboard 所需指标。

输入：

```json
{
  "metric_name": "negative_feedback_ratio",
  "date_range": {
    "start": "2025-01-01",
    "end": "2025-01-31"
  },
  "dimension": "repo_name"
}
```

输出：

```json
{
  "success": true,
  "data": [
    {
      "date": "2025-01-01",
      "repo_name": "streamlit/streamlit",
      "metric_name": "negative_feedback_ratio",
      "metric_value": 0.32
    }
  ]
}
```

## 7. Competitor Tool 设计

Competitor Tool 用于读取和整理竞品资料。

MVP 阶段可以先使用人工维护的 CSV 或 Markdown 文件。

### 7.1 competitor.load_features

用途：读取竞品功能资料。

输入：

```json
{
  "source_path": "data/sample_competitors.csv"
}
```

输出：

```json
{
  "success": true,
  "data": [
    {
      "competitor_name": "Gradio",
      "feature_name": "快速构建 AI Demo",
      "feature_category": "App Builder",
      "coverage": "high",
      "strength": "上手快，适合模型展示",
      "weakness": "复杂 BI 分析能力较弱"
    }
  ]
}
```

### 7.2 competitor.compare_features

用途：根据用户痛点和竞品功能，生成差异化机会。

输入：

```json
{
  "pain_points": [],
  "competitor_features": []
}
```

输出：

```json
{
  "success": true,
  "data": [
    {
      "feature_gap": "缺少面向产品经理的 AI 输出评估看板",
      "related_pain_points": ["pp_001", "pp_002"],
      "opportunity_hint": "构建 AI Evaluation Monitor"
    }
  ]
}
```

## 8. Evaluation Tool 设计

Evaluation Tool 用于评估 AI 生成内容质量。

### 8.1 evaluation.score_output

用途：对 AI 输出进行综合评分。

输入：

```json
{
  "output_id": "prd_001",
  "output_type": "prd",
  "output_text": "Generated PRD content",
  "evidence_texts": [
    "I cannot figure out why deployment keeps failing.",
    "The error message is not clear enough."
  ],
  "rubric": "prd_quality"
}
```

输出：

```json
{
  "success": true,
  "data": {
    "output_id": "prd_001",
    "relevance": 4.5,
    "accuracy": 4.0,
    "actionability": 4.2,
    "evidence_coverage": 0.86,
    "hallucination_risk": "low",
    "prd_completeness": 4.3,
    "overall_score": 4.2,
    "need_human_review": false
  }
}
```

### 8.2 evaluation.check_evidence

用途：检查 AI 输出中的结论是否有证据支撑。

输入：

```json
{
  "claims": [
    "用户需要更清晰的部署失败提示",
    "用户希望系统自动生成优化建议"
  ],
  "evidence_texts": [
    {
      "feedback_id": "fb_001",
      "text": "The deployment failed but I do not know why."
    }
  ]
}
```

输出：

```json
{
  "success": true,
  "data": [
    {
      "claim": "用户需要更清晰的部署失败提示",
      "supported": true,
      "evidence_ids": ["fb_001"]
    },
    {
      "claim": "用户希望系统自动生成优化建议",
      "supported": false,
      "evidence_ids": []
    }
  ]
}
```

## 9. Export Tool 设计

Export Tool 用于导出 PRD、调研报告、CSV 和作品集材料。

### 9.1 export.prd_markdown

用途：导出 PRD Markdown 文件。

输入：

```json
{
  "prd_id": "prd_001",
  "format": "markdown"
}
```

输出：

```json
{
  "success": true,
  "file_path": "outputs/prd_examples/prd_001.md"
}
```

### 9.2 export.research_report

用途：导出调研报告。

输入：

```json
{
  "project_id": "project_001",
  "sections": [
    "summary",
    "data_sources",
    "pain_points",
    "opportunities",
    "prd",
    "evaluation"
  ]
}
```

输出：

```json
{
  "success": true,
  "file_path": "outputs/evaluation_reports/project_001_report.md"
}
```

### 9.3 export.metrics_csv

用途：导出 BI 指标数据。

输入：

```json
{
  "project_id": "project_001",
  "metric_group": "ai_evaluation"
}
```

输出：

```json
{
  "success": true,
  "file_path": "outputs/metrics/ai_evaluation_metrics.csv"
}
```

## 10. Agent 与 MCP 工具调用关系

| LangGraph 节点 | 调用工具 | 调用目的 |
|---|---|---|
| Collector Node | GitHub Tool | 采集 Issues / Comments |
| Cleaner Node | Database Tool | 读取原始反馈、写入清洗结果 |
| Feedback Analyst Node | Database Tool | 读取清洗反馈、写入主题和痛点 |
| Competitor Analyst Node | Competitor Tool | 读取竞品资料、生成竞品矩阵 |
| Opportunity Scorer Node | Database Tool | 读取痛点和竞品信息、写入机会点评分 |
| PRD Writer Node | Database Tool / Export Tool | 读取机会点、写入 PRD、导出文档 |
| Evaluation Node | Evaluation Tool / Database Tool | 评估 AI 输出并写入结果 |
| BI Insight Node | Database Tool / Export Tool | 查询指标、导出报告 |

## 11. 错误处理规范

所有工具调用失败时，都应返回统一错误结构：

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Readable error message",
    "detail": {}
  }
}
```

常见错误类型：

| 错误码 | 说明 |
|---|---|
| GITHUB_RATE_LIMIT | GitHub API 限流 |
| GITHUB_NOT_FOUND | 仓库或 Issue 不存在 |
| DATABASE_QUERY_FAILED | SQL 查询失败 |
| DATABASE_INSERT_FAILED | 数据写入失败 |
| EVALUATION_FAILED | AI 输出评估失败 |
| EXPORT_FAILED | 文件导出失败 |
| INVALID_INPUT | 输入参数不合法 |

## 12. MVP 实现建议

MVP 阶段建议先实现以下文件：

```text
src/mcp_tools/github_tool.py
src/mcp_tools/database_tool.py
src/mcp_tools/evaluation_tool.py
src/mcp_tools/export_tool.py
```

每个文件先实现普通 Python 函数，保持 MCP 风格输入输出。

第一阶段目标：

```text
让 LangGraph Agent 能通过这些工具完成端到端流程。
```

第二阶段目标：

```text
将工具封装为真正 MCP Server。
```

## 13. 项目表达价值

MCP 工具层可以体现以下能力：

- Agent 工具调用设计能力
- 外部系统集成能力
- 数据接口设计能力
- 结构化输入输出设计能力
- AI 工作流工程化能力
- 从 Demo 到可扩展系统的架构思维
