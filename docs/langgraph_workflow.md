# LangGraph 多 Agent 工作流设计

## 1. 文档目的

本文档用于说明本项目中 LangGraph 多 Agent 工作流的设计方案，包括状态结构、节点指责、节点之间的数据流转、条件路由、失败重试和人工审核机制。

本文件应作为项目设计文档保存在：

```text
docs/langgraph_workflow.md
```
## 2. LangGraph 在项目中的作用

LangGraph 是本项目的 Agent 工作流编排层。

它的作用是把“AI 产品调研”这个复杂任务拆分成多个可控节点，并管理节点之间的状态传递和条件分支。

本项目中的 LangGraph 主要解决以下问题：

- 如何把数据采集、反馈分析、竞品分析、机会点评分、PRD 生成和 AI 评估串成完整流程。
- 如何让每个 Agent 只负责一个清晰任务
- 如何在数据不足、证据不足或输出质量低自动回退
- 如何在高风险输出时进入人工审核
- 如何保证 AI 生成内容可以被追溯和评估

## 3. 总体工作流

```text
Collector Node
-> Cleaner Node
-> Feedback Analyst Node
-> Competitor Analyst Node
-> Opportunity Scorer Node
-> PRD Writer Node
-> Evaluation Node
-> Human Review Node
-> BI Insight Node
-> Export
```

简化理解：

```text
采集数据
-> 清洗数据
-> 分析反馈
-> 分析竞品
-> 识别机会点
-> 生成 PRD
-> 评估输出质量
-> 人工审核
-> BI 复盘
-> 导出结果
```

## 4. 核心状态设计：ResearchState

LangGraph 中所有节点共享并更新同一个状态对象： `ResearchState`.

定义结构如下：

```python
ResearchState = {
    "project_id": str,
    "project_name": str,
    "selected_repos": list[str],
    "data_range": dict,
    "max_items": int,
    "raw_feedback": list[dict],
    "cleaned_feedback": list[dict],
    "topics": list[dict],
    "pain_points": list[dict],
    "competitor_docs": list[dict],
    "competitor_matrix": list[dict],
    "opportunities": list[dict],
    "selected_opportunity": dict,
    "prd_draft": dict,
    "evaluation_report": dict,
    "bi_metrics": dict,
    "product_review_summary": str,
    "human_review_status": str,
    "revision_request": str,
    "errors": list[dict],
    "current_step": str
}
```

## 5. 状态字段说明

| 字段 | 说明 |
|---|---|
| project_id | 当前调研项目 ID |
| project_name | 当前调研项目名称 |
| selected_repos | 用户选择的 GitHub 仓库 |
| date_range | 数据采集时间范围 |
| max_items | 最大采集数量 |
| raw_feedback | 原始 Issues / Comments 数据 |
| cleaned_feedback | 清洗后的反馈数据 |
| topics | 反馈主题分析结果 |
| pain_points | 用户痛点与需求 |
| competitor_docs | 竞品资料 |
| competitor_matrix | 竞品功能矩阵 |
| opportunities | 产品机会点列表 |
| selected_opportunity | 被选中用于生成 PRD 的机会点 |
| prd_draft | PRD 草稿 |
| evaluation_report | AI 输出评估报告 |
| bi_metrics | BI 指标结果 |
| product_review_summary | 产品复盘总结 |
| human_review_status | 人工审核状态 |
| revision_request | 人工修改意见 |
| errors | 工作流错误记录 |
| current_step | 当前执行节点 |

## 6. 字节设计

### 6.1 Collector Node

作用：采集真实用户反馈数据。

输入：

```text
selected_repos
data_range
max_items
labels
```

处理逻辑：

- 调用 GitHub Tool
- 获取 Issues
- 获取 Issue Comments
- 获取 Labels
- 记录数据来源和 URL
- 保留原始反馈

输出：

```text
raw_feedback
```

失败场景：

- 记录错误到 `errors`
- 重试有限次数
- 如果数据仍不足，提示用户更换仓库或扩大时间范围

### 6.2 Cleaner Node

作用：清洗原始反馈数据，并转化为统一格式。

输入：

```text
raw_feedback
```

处理逻辑：

- 清洗 Markdown
- 移除代码块
- 移除无效链接
- 合并 Issue 和 Commnents
- 去重
- 识别语言
- 判断反馈类型

输出：

```text
cleaned_feedback
```

反馈类型：

```text
bug
feature_request
complaint
question
praise
other
```

### 6.3 Feedback Analyst Node

作用：从清洗后的反馈中提取主题、情绪、痛点和需求。

输入：

```text
cleaned_feedback
```

处理逻辑：

- 识别高频主题
- 进行情绪分析
- 判断问题严重程度
- 提取用户痛点
- 转化为用户需求
- 为每个结论绑定 evidence_quote

输出：

```text
topics
pain_points
```

输出示例：

```json
{
  "pain_point_id": "pp_001",
  "user_pain": "用户在部署应用时经常遇到配置复杂、报错不清晰的问题",
  "user_need": "用户需要更清晰的部署引导和错误提示",
  "evidence_count": 18,
  "evidence_quotes": [
    "I cannot figure out why deployment keeps failing."
  ],
  "severity": 4
}
```

### 6.4 Competitor Analyst Node

作用：分析竞品功能和差异化机会

输入：

```text
competitor_docs
pain_points
```

处理逻辑：

- 整理竞品功能列表
- 构建功能覆盖矩阵
- 分析竞品优势
- 分析竞品弱点
- 结合用户痛点识别差异化机会

输出：

```text
competitor_matrix
feature_gap
```

### 6.5 Opportunity Scorer Node

作用：对产品机会点进行优先级评分。

输入：

```text
pain_points
competitor_matrix
feedback_frequency
```

评分维度:

```text
user_value
business_value
frequency
severity
effort
risk
ai_feasibility
evidence_strength
```

推荐公式：

```text
priority_score =
user_value * 0.25
+ business_value * 0.20
+ frequency * 0.15
+ severity * 0.15
+ ai_feasibility * 0.10
+ evidence_strength * 0.15
- effort * 0.15
- risk * 0.10
```
输出：

```text
opportunities
```

优先级规则：

```text
score >= 4.0：P0
score >= 3.0：P1
score < 3.0：P2 / Backlog
```

### 6.6 PRD Writer Node

作用：基于选定机会点生成结构化 PRD 草稿。

输入：

```text
selected_opportunity
pain_points
evidence_quotes
```

PRD 输出结构：

```text
背景
目标用户
用户痛点
用户故事
功能需求
非功能需求
验收标准
成功指标
风险与边界
证据引用
```

输出：

```text
prd_draft
```

### 6.7 Evaluation Node

作用： 评估 AI 生成的洞察、机会点和 PRD 质量。

输入：

```text
prd_draft
pain_points
evidence_quotes
```

评估维度：

```text
relevance
accuracy
actionability
evidence_coverage
hallucination_risk
prd_completeness
human_edit_rate
```

输出：

```text
evaluation_report
```

输出示例：

```json
{
  "relevance": 4.5,
  "accuracy": 4.0,
  "actionability": 4.2,
  "evidence_coverage": 0.86,
  "hallucination_risk": "low",
  "prd_completeness": 4.3,
  "overall_score": 4.2,
  "need_human_review": false
}
```

### 6.8 Human Review Node

作用：对高风险或重要输出进行人工审核。

触发条件：

```text
hallucination_risk = high
evidence_coverage < 0.8
prd_completeness < 4.0
priority = P0
```

输入：

```text
prd_draft
evaluation_report
```

人工操作：

```text
approve
revise
reject
```

输出：

```text
human_review_status
revision_request
approved_prd
```

### 6.9 BI Insight Node

作用：基于分析结果生成 BI 指标和产品复盘建议。

输入：

```text
topics
pain_points
opportunities
evaluation_report
human_review_status
```

输出：

```text
bi_metrics
product_review_summary
```

指标示例：

```text
反馈总数
负面反馈占比
Top Pain Points
P0/P1/P2 机会点数量
平均 PRD 完整度
平均证据覆盖率
高幻觉风险输出占比
人工修改率
```
## 7. 条件路由设计

### 7.1 数据不足

条件：

```text
len(raw_feedback) < minimum_feedback_count
```

路由：

```text
Collector Node → Collector Node
```

处理方式：

- 扩大时间范围
- 增加仓库
- 提示用户补充数据

### 7.2 清洗后有效数据不足

条件：

```text
len(cleaned_feedback) < minimum_cleaned_count
```

路由：

```text
Cleaner Node → Collector Node
```

### 7.3 证据覆盖不足

条件：

```text
evidence_coverage < 0.8
```

路由：

```text
Evaluation Node → Feedback Analyst Node
```

处理方式：

- 重新检索证据
- 删除无证据结论
- 降低结论置信度

### 7.4 PRD 完整度不足

条件：

```text
prd_completeness < 4.0
```

路由：

```text
Evaluation Node → PRD Writer Node
```

### 7.5 幻觉风险高

条件：

```text
hallucination_risk = "high"
```

路由：

```text
Evaluation Node → Human Review Node
```

### 7.6 机会点评分低

条件：

```text
priority = "P2" or priority = "Backlog"
```

路由：

```text
Opportunity Scorer Node → BI Insight Node
```

处理方式：

- 不生成 PRD
- 进入 Backlog
- 在 BI Dashboard 中展示

## 8. 失败重试机制

每个节点应支持基础错误处理：

```text
try:
    执行节点逻辑
except Exception as error:
    写入 errors
    判断是否可重试
```

建议策略：

| 节点 | 重试策略 |
|---|---|
| Collector Node | API 失败最多重试 3 次 |
| Cleaner Node | 清洗失败跳过异常样本 |
| Feedback Analyst Node | LLM 失败最多重试 2 次 |
| PRD Writer Node | 输出格式错误时重新生成 |
| Evaluation Node | 评分失败时使用默认风险标记 |
| Export Node | 导出失败时返回错误信息 |

## 9. Human-in-the-loop 设计

人工审核不应该只作为形式，而应该参与关键决策。

需要人工审核的情况：

- P0 机会点
- 高幻觉风险输出
- 证据覆盖率不足
- PRD 完整度不足
- 用户主动要求修改
- 输出将用于作品集或正式展示

人工审核结果：

```text
approved：通过
revision_required：需要修改
rejected：拒绝
```

## 10. MVP 版本建议

MVP 阶段可以先实现简化流程：

```text
Collector
→ Cleaner
→ Feedback Analyst
→ Opportunity Scorer
→ PRD Writer
→ Evaluation
→ BI Insight
```

暂时弱化：

```text
Competitor Analyst
Human Review
复杂失败重试
真正 MCP Server
```

这样可以先跑通端到端链路，再逐步增强。

## 11. 最终交付结果

完成后，系统应该能够做到：

1. 用户选择 GitHub 仓库。
2. 系统采集真实 Issues / Comments。
3. 系统清洗并分析反馈。
4. 系统提取用户痛点。
5. 系统生成产品机会点并排序。
6. 系统基于高优机会点生成 PRD。
7. 系统评估 PRD 的质量和幻觉风险。
8. 系统在 BI Dashboard 中展示结果。
9. 用户可以导出 PRD，调研报告和作品集材料。

## 12. 作品集表达价值

这个工作流可以体现：

- Agent Workflow 设计能力
- LangGraph 状态管理能力
- 产品调研任务拆解能力
- AI 产品质量控制能力
- Human-in-the-loop 设计能力
- 数据驱动产品决策能力
