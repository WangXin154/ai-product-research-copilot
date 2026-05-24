# Product Research Schema 数据模型设计

## 1. 文档目的

本文档用于定义本项目的统一 Product Research Schema。

该 Schema 用于把原始用户反馈、清洗数据、主题分析、用户痛点、机会点评分、PRD草稿、AI 评估结果和 BI 指标串联起来，形成从数据采集到产品决策的完整链路。

## 2. 设计目标

Product Research Schema 的目标是：

- 原始反馈可追溯
- 清洗过程可复用
- 用户痛点可结构化
- 机会点可评分
- PRD 可关联证据
- AI 输出可评估
- BI 指标可计算

## 3. 核心数据链路

```text
raw_feedback
-> cleaned_feedback
-> feedback_topics
-> pain_points
-> opportunity_scores
-> prd_drafts
-> ai_evaluation_results
-> bi_metrics_daily
```

完整追溯链路：

```text
PRD 结论
-> opportunity_id
-> pain_point_id
-> topic_id
-> feedback_id
-> GitHub Issue / Comment URL
```

## 4. 表结构总览

| 表名 | 作用 |
|---|---|
| raw_feedback | 保存原始 GitHub Issues / Comments |
| cleaned_feedback | 保存清洗后的反馈文本 |
| feedback_topics | 保存主题、情绪、严重程度和证据 |
| pain_points | 保存用户痛点和用户需求 |
| competitor_features | 保存竞品功能信息 |
| opportunity_scores | 保存机会点评分 |
| prd_drafts | 保存 PRD 草稿 |
| ai_evaluation_results | 保存 AI 输出评估结果 |
| bi_metrics_daily | 保存 BI 指标 |

## 5. raw_feedback

### 5.1 表说明

保存从 GitHub、公开评论或其他来源采集的原始用户反馈。

### 5.2 字段设计

| 字段 | 类型 | 说明 |
|---|---|---|
| feedback_id | TEXT | 反馈唯一 ID |
| source | TEXT | 数据来源，如 github |
| repo_name | TEXT | 仓库名称 |
| issue_id | TEXT | GitHub Issue ID |
| comment_id | TEXT | GitHub Comment ID |
| title | TEXT | Issue 标题 |
| body | TEXT | 原始正文 |
| labels | TEXT | 标签，JSON 字符串 |
| state | TEXT | open / closed |
| author | TEXT | 作者 |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |
| comments_count | INTEGER | 评论数 |
| url | TEXT | 原始链接 |

### 5.3 示例

```json
{
  "feedback_id": "fb_001",
  "source": "github",
  "repo_name": "streamlit/streamlit",
  "issue_id": "12345",
  "comment_id": null,
  "title": "App crashes when uploading large files",
  "body": "The app crashes when I upload a CSV larger than 100MB.",
  "labels": "[\"bug\"]",
  "state": "open",
  "author": "example_user",
  "created_at": "2025-01-10T10:00:00Z",
  "updated_at": "2025-01-12T12:00:00Z",
  "comments_count": 8,
  "url": "https://github.com/streamlit/streamlit/issues/12345"
}
```

## 6. cleaned_feedback

### 6.1 表说明

保存清洗、去重、规范化后的反馈文本。

### 6.2 字段设计

| 字段 | 类型 | 说明 |
|---|---|---|
| cleaned_id | TEXT | 清洗记录 ID |
| feedback_id | TEXT | 原始反馈 ID |
| cleaned_text | TEXT | 清洗后的文本 |
| language | TEXT | 语言 |
| feedback_type | TEXT | bug / feature_request / complaint / question / praise / other |
| duplicate_flag | BOOLEAN | 是否重复 |
| noise_flag | BOOLEAN | 是否低质量文本 |
| cleaned_at | TEXT | 清洗时间 |

### 6.3 feedback_type 定义

| 类型 | 说明 |
|---|---|
| bug | Bug 或错误反馈 |
| feature_request | 功能请求 |
| complaint | 抱怨或负面体验 |
| question | 使用问题 |
| praise | 正面反馈 |
| other | 其他 |

## 7. feedback_topics

### 7.1 表说明

保存主题、情绪、严重程度和证据引用。

### 7.2 字段设计

| 字段 | 类型 | 说明 |
|---|---|---|
| topic_id | TEXT | 主题 ID |
| feedback_id | TEXT | 反馈 ID |
| topic | TEXT | 主题名称 |
| sentiment | TEXT | positive / neutral / negative |
| severity | INTEGER | 严重程度 1-5 |
| evidence_quote | TEXT | 关键证据引用 |
| confidence | REAL | 置信度 |

### 7.3 topic 示例

```text
deployment
performance
documentation
integration
onboarding
pricing
error_message
data_upload
```

## 8. pain_points

### 8.1 表说明

保存从用户反馈中抽象出的用户痛点和用户需求。

### 8.2 字段设计

| 字段 | 类型 | 说明 |
|---|---|---|
| pain_point_id | TEXT | 痛点 ID |
| topic_id | TEXT | 主题 ID |
| user_pain | TEXT | 用户痛点 |
| user_need | TEXT | 对应需求 |
| evidence_count | INTEGER | 证据数量 |
| priority_hint | TEXT | 初步优先级提示 |
| related_feedback_ids | TEXT | 关联反馈 ID，JSON 字符串 |
| created_at | TEXT | 创建时间 |

### 8.3 示例

```json
{
  "pain_point_id": "pp_001",
  "topic_id": "topic_deployment",
  "user_pain": "用户在部署应用时经常遇到配置复杂、报错不清晰的问题",
  "user_need": "用户需要更清晰的部署引导和错误提示",
  "evidence_count": 18,
  "priority_hint": "P0",
  "related_feedback_ids": "[\"fb_001\", \"fb_008\", \"fb_021\"]"
}
```

## 9. competitor_features

### 9.1 表说明

保存竞品功能、优势、弱点和来源。

### 9.2 字段设计

| 字段 | 类型 | 说明 |
|---|---|---|
| competitor_id | TEXT | 竞品 ID |
| competitor_name | TEXT | 竞品名称 |
| feature_name | TEXT | 功能名称 |
| feature_category | TEXT | 功能分类 |
| coverage | TEXT | high / medium / low / none |
| strength | TEXT | 优势 |
| weakness | TEXT | 弱点 |
| source_url | TEXT | 来源链接 |

## 10. opportunity_scores

### 10.1 表说明

保存产品机会点和优先级评分结果。

### 10.2 字段设计

| 字段 | 类型 | 说明 |
|---|---|---|
| opportunity_id | TEXT | 机会点 ID |
| pain_point_ids | TEXT | 关联痛点 ID，JSON 字符串 |
| opportunity_name | TEXT | 机会点名称 |
| user_value | REAL | 用户价值 |
| business_value | REAL | 商业价值 |
| frequency | REAL | 出现频率 |
| severity | REAL | 严重程度 |
| effort | REAL | 实现成本 |
| risk | REAL | 风险 |
| ai_feasibility | REAL | AI 可行性 |
| evidence_strength | REAL | 证据强度 |
| priority_score | REAL | 综合分数 |
| priority | TEXT | P0 / P1 / P2 / Backlog |

### 10.3 优先级规则

```text
score >= 4.0：P0
score >= 3.0：P1
score >= 2.0：P2
score < 2.0：Backlog
```

## 11. prd_drafts

### 11.1 表说明

保存 AI 生成和人工审核后的 PRD 草稿。

### 11.2 字段设计

| 字段 | 类型 | 说明 |
|---|---|---|
| prd_id | TEXT | PRD ID |
| opportunity_id | TEXT | 机会点 ID |
| title | TEXT | PRD 标题 |
| background | TEXT | 背景 |
| user_story | TEXT | 用户故事 |
| requirements | TEXT | 功能需求 |
| non_functional_requirements | TEXT | 非功能需求 |
| acceptance_criteria | TEXT | 验收标准 |
| metrics | TEXT | 成功指标 |
| risks | TEXT | 风险 |
| evidence_refs | TEXT | 证据引用，JSON 字符串 |
| status | TEXT | draft / reviewed / approved / rejected |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |

## 12. ai_evaluation_results

### 12.1 表说明

保存 AI 输出质量评估结果。

### 12.2 字段设计

| 字段 | 类型 | 说明 |
|---|---|---|
| evaluation_id | TEXT | 评估 ID |
| output_id | TEXT | 输出对象 ID |
| output_type | TEXT | insight / prd / report |
| relevance | REAL | 相关性 |
| accuracy | REAL | 准确性 |
| actionability | REAL | 可执行性 |
| evidence_coverage | REAL | 证据覆盖率 |
| hallucination_risk | TEXT | low / medium / high |
| human_edit_rate | REAL | 人工修改率 |
| prd_completeness | REAL | PRD 完整度 |
| overall_score | REAL | 总评分 |
| evaluation_notes | TEXT | 评估说明 |
| created_at | TEXT | 创建时间 |

## 13. bi_metrics_daily

### 13.1 表说明

保存每日 BI 指标，用于 Dashboard 展示。

### 13.2 字段设计

| 字段 | 类型 | 说明 |
|---|---|---|
| metric_id | TEXT | 指标 ID |
| date | TEXT | 日期 |
| metric_name | TEXT | 指标名称 |
| metric_value | REAL | 指标值 |
| product_area | TEXT | 产品模块 |
| repo_name | TEXT | 仓库名称 |
| dimension | TEXT | 维度 |
| created_at | TEXT | 创建时间 |

## 14. 建议数据库选择

MVP 阶段建议使用：

```text
SQLite 或 DuckDB
```

原因：

- 本地运行简单
- 不需要复杂部署
- 适合 Streamlit Demo
- 方便导出 CSV
- 足够支持作品集项目

正式版可以扩展为：

```text
PostgreSQL
```

## 15. 数据模型价值

该数据模型可以体现：

- 数据建模能力
- 产品研究结构化能力
- AI 输出证据追溯能力
- BI 指标计算能力
- 从原始反馈到产品决策的闭环设计能力
