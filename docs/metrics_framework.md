# 指标体系与 AI Evaluation 框架

## 1. 文档目的

本文档用于定义本项目的 BI 指标体系和 AI 输出评估体系。

本项目不是单纯的 AI 文档生成工具，也是一个包含真实数据、 Agent 工作流、 AI Evaluation 和 BI Dashboard 的产品决策系统。

因此，指标体系需要同时回答两个问题：

1. 产品调研是否有效？
2. AI 生成结果是否可靠？

## 2. 指标体系总览

本项目指标分为 5 类：

| 指标类别 | 说明 |
|---|---|
| 数据采集指标 | 衡量真实反馈数据规模和覆盖范围 |
| 用户反馈指标 | 衡量用户痛点、主题、情绪和问题严重度 |
| 机会点评分指标 | 衡量产品机会点的优先级和可执行性 |
| AI Evaluation 指标 | 衡量 AI 输出质量、证据覆盖率和幻觉风险 |
| BI 复盘指标 | 衡量流程效率、产出质量和业务价值 |


## 3. Dashboard 页面设计

```text
Research Overview
Feedback Intelligence
Competitor Intelligence
Opportunity Pipeline
AI Evaluation Monitor
Business Impact / ROI Simulation
```

## 4. Research  Overview 指标

Research Overview 用于展示调研项目整体状态

| 指标 | 定义 | 计算方式 | 产品价值 |
|---|---|---|---|
| feedback_count | 反馈总数 | raw_feedback 总记录数 | 判断数据规模 |
| repo_count | 覆盖仓库数量 | distinct repo_name | 判断调研范围 |
| issue_count | Issue 数量 | raw_feedback 中 issue 记录数 | 衡量核心反馈量 |
| comment_count | Comment 数量 | raw_feedback 中 comment 记录数 | 衡量讨论深度 |
| open_issue_ratio | Open Issue 占比 | open issues / total issues | 判断问题积压 |
| negative_feedback_ratio | 负面反馈占比 | negative feedback / total feedback | 判断用户不满程度 |
| avg_ai_quality_score | 平均 AI 输出质量分 | evaluation overall_score 平均值 | 判断 AI 生成质量 |
| latest_update_time | 最近更新时间 | max(updated_at) | 判断数据新鲜度 |

## 5. Feedback Intelligence 用于分析用户反馈中的主题、情绪和痛点

| 指标 | 定义 | 计算方式 | 产品价值 |
|---|---|---|---|
| topic_count | 主题数量 | distinct topic | 判断问题覆盖面 |
| top_topics | 高频主题 | 按 topic 频次排序 | 找到核心问题 |
| sentiment_distribution | 情绪分布 | positive / neutral / negative 占比 | 判断用户态度 |
| severity_distribution | 严重程度分布 | severity 1-5 分布 | 判断问题紧急度 |
| bug_ratio | Bug 类反馈占比 | bug feedback / total feedback | 判断产品稳定性 |
| feature_request_ratio | 功能请求占比 | feature request / total feedback | 判断新增需求强度 |
| complaint_ratio | 抱怨类反馈占比 | complaint / total feedback | 判断体验问题 |
| evidence_count_per_pain_point | 每个痛点证据数 | evidence_count 平均值 | 判断洞察可信度 |

## 6. Competitor Intelligence 指标

Competitor Intelligence 用于支持竞品分析和差异化机会识别。

| 指标 | 定义 | 计算方式 | 产品价值 |
|---|---|---|---|
| competitor_count | 竞品数量 | distinct competitor_name | 判断竞品覆盖范围 |
| feature_count | 功能条目数 | competitor_features 总数 | 判断分析深度 |
| feature_coverage_rate | 功能覆盖率 | 已覆盖功能 / 功能总数 | 判断产品竞争力 |
| feature_gap_count | 功能差距数量 | uncovered or weak features | 识别差异化机会 |
| competitor_strength_count | 竞品优势数量 | strength 字段统计 | 了解竞品强项 |
| competitor_weakness_count | 竞品弱点数量 | weakness 字段统计 | 找到切入点 |

## 7. Opportunity Pipeline 指标

Opportunity Pipeline 用于支持需求优先级判断。

| 指标 | 定义 | 计算方式 | 产品价值 |
|---|---|---|---|
| opportunity_count | 机会点总数 | opportunity_scores 总数 | 判断需求池规模 |
| p0_count | P0 机会点数量 | priority = P0 | 判断高优先级需求 |
| p1_count | P1 机会点数量 | priority = P1 | 判断近期可做需求 |
| p2_count | P2 机会点数量 | priority = P2 | 判断待观察需求 |
| backlog_count | Backlog 数量 | priority = Backlog | 管理低优需求 |
| avg_priority_score | 平均优先级分数 | priority_score 平均值 | 判断机会质量 |
| avg_user_value | 平均用户价值 | user_value 平均值 | 判断用户收益 |
| avg_business_value | 平均商业价值 | business_value 平均值 | 判断商业收益 |
| avg_effort | 平均实现成本 | effort 平均值 | 判断研发压力 |
| prd_generated_count | 已生成 PRD 数量 | prd_drafts 总数 | 衡量产出效率 |

## 8. AI Evaluation Monitor 指标

AI Evaluation Monitor 是本项目最重要的质量控制页面。

| 指标 | 定义 | 目标值 |
|---|---|---|
| relevance_score | 输出是否围绕任务和输入数据 | >= 4/5 |
| accuracy_score | 是否准确理解原始反馈 | >= 4/5 |
| actionability_score | 是否可转化为产品行动 | >= 4/5 |
| evidence_coverage | 有证据支撑的结论比例 | >= 80% |
| hallucination_risk_rate | 高幻觉风险输出占比 | <= 15% |
| human_edit_rate | 人工修改比例 | <= 30% |
| prd_completeness_score | PRD 结构完整度 | >= 4/5 |
| overall_ai_score | AI 输出综合评分 | >= 4/5 |

## 9. Business Impact 指标

Business Impact 用于展示项目的业务价值和作品集价值。

| 指标 | 定义 | 计算方式 | 产品价值 |
|---|---|---|---|
| report_generation_time | 报告生成耗时 | 生成报告结束时间 - 开始时间 | 衡量效率 |
| manual_time_saved | 节省人工时间 | 预估人工耗时 - 系统耗时 | 展示效率提升 |
| workflow_completion_rate | 完整流程完成率 | 完成导出用户数 / 启动流程用户数 | 判断可用性 |
| export_count | 导出次数 | 导出文件数量 | 衡量交付价值 |
| prd_acceptance_rate | PRD 审核通过率 | approved PRD / total PRD | 判断 PRD 可用性 |
| average_review_rounds | 平均审核轮次 | review rounds 平均值 | 判断输出稳定性 |

## 10. AI Evaluation 维度定义

### 10.1 Relevance 相关性

定义：

AI 输出是否回答了当前任务，是否围绕输入数据、用户痛点和选定机会点展开。

评分标准：

| 分数 | 标准 |
|---|---|
| 5 | 完全相关，紧扣输入数据和任务 |
| 4 | 基本相关，存在少量泛化内容 |
| 3 | 部分相关，但存在偏题 |
| 2 | 大部分内容偏离任务 |
| 1 | 几乎无关 |

### 10.2 Accuracy 准确性

定义：

AI 输出是否准确理解原始反馈、用户痛点和证据内容。

检查方式：

- 是否误解用户反馈
- 是否夸大问题严重程度
- 是否错误归纳用户需求
- 是否和 evidence_quote 一致

目标：

```text
>= 4/5
```

### 10.3 Actionability 可执行性

定义：

AI 输出是否能够转化为明确的产品行动。

检查项：

- 是否有明确目标
- 是否有用户故事
- 是否有功能需求
- 是否有验收标准
- 是否有成功指标
- 是否有风险说明
- 是否能进入产品排期讨论

目标：

```text
>= 4/5
```

### 10.4 Evidence Coverage 证据覆盖

定义：

AI 输出中的关键结论，有多少比例可以追溯到原始用户反馈证据。

计算方式：

```text
evidence_coverage = 有证据支撑的结论数 / 总结论数
```

目标：

```text
>= 80%
```

示例：

```text
如果 PRD 中有 10 个关键结论，其中 8 个有 evidence_quote 支撑，则 evidence_coverage = 80%。
```
### 10.5 Hallucination Risk 幻觉风险

定义：

AI 是否生成了没有证据支撑、无法追溯或明显编造的信息。

风险等级：

| 等级 | 判断标准 |
|---|---|
| low | 关键结论基本都有证据支撑 |
| medium | 存在少量弱证据结论 |
| high | 存在明显无证据断言或编造内容 |

目标：

```text
低幻觉风险输出占比 >= 85%
```

### 10.6 Human Edit Rate 人工修改率

定义：

人工修改内容占 AI 原始输出的比例。

计算方式：

```text
human_edit_rate = 修改字符数 / AI 原始输出字符数
```

目标：

```text
<= 30%
```

意义：

人工修改率越低，说明 AI 输出越接近可用交付物。

### 10.7 PRD Completeness PRD 完整度

定义：

AI 生成的PRD 是否包含完整的产品需求文档结构。

检查项：

- 背景
- 目标用户
- 用户痛点
- 用户故事
- 功能需求
- 非功能需求
- 验收标准
- 成功指标
- 风险与边界
- 证据引用

评分方式：

```text
prd_completeness = 已包含模块数 / 应包含模块数 * 5
```

目标：

```text
>= 4/5
```

## 11. 机会点评分模型
机会点评分用于决定哪些需求进入 PRD 生成流程。

### 11.1 评分维度

| 维度 | 含义 | 分数范围 |
|---|---|---|
| user_value | 用户价值 | 1-5 |
| business_value | 商业价值 | 1-5 |
| frequency | 出现频率 | 1-5 |
| severity | 严重程度 | 1-5 |
| effort | 实现成本 | 1-5 |
| risk | 实施风险 | 1-5 |
| ai_feasibility | AI 可实现性 | 1-5 |
| evidence_strength | 证据强度 | 1-5 |

### 11.2 推荐公式

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

### 11.3 优先级规则

| 分数 | 优先级 | 说明 |
|---|---|---|
| score >= 4.0 | P0 | 高优先级，建议进入 PRD |
| 3.0 <= score < 4.0 | P1 | 中高优先级，可进入排期 |
| 2.0 <= score < 3.0 | P2 | 观察，暂不优先 |
| score < 2.0 | Backlog | 暂不处理 |

## 12. 指标落库建议

建议将指标写入 `bi_metrics_daily` 表。

核心字段：

| 字段 | 说明 |
|---|---|
| metric_id | 指标 ID |
| date | 日期 |
| metric_name | 指标名称 |
| metric_value | 指标值 |
| product_area | 产品模块 |
| repo_name | 仓库名称 |
| dimension | 维度 |
| created_at | 创建时间 |

## 13. MVP 阶段指标范围

MVP 阶段优先完成以下指标：

```text
feedback_count
repo_count
negative_feedback_ratio
top_topics
sentiment_distribution
pain_point_count
opportunity_count
p0_count
p1_count
p2_count
avg_priority_score
prd_generated_count
relevance_score
evidence_coverage
hallucination_risk_rate
prd_completeness_score
```

先完成这些核心指标，就可以支撑第一版 Dashboard。

## 14. 作品集表达价值

本指标体系可以体现以下能力：

- 数据产品指标设计能力
- AI 产品质量评估能力
- BI Dashboard 规划能力
- 产品运营复盘能力
- AI 输出风控意识
- 从数据到产品决策的闭环设计能力