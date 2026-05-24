from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.langgraph_agents.state import ResearchState


def prd_writer_node(state: ResearchState) -> ResearchState:
    state["current_step"] = "prd_writer_node"
    opportunity = state.get("selected_opportunity", {})
    if not opportunity:
        state["prd_draft"] = {}
        return state

    pain_point = opportunity.get("source_pain_point", {})
    evidence_quotes = pain_point.get("evidence_quotes", [])
    title = f"{opportunity['opportunity_name']} PRD"

    background = (
        f"在当前产品调研数据中，{pain_point.get('evidence_count', 0)} 条反馈与 "
        f"{pain_point.get('topic', 'unknown')} 主题相关，说明该问题已经具备一定用户证据。"
    )
    user_story = (
        f"作为目标用户，我希望{pain_point.get('user_need', '产品能够解决当前痛点')}，"
        "以便更稳定、高效地完成核心任务。"
    )
    requirements = [
        f"识别并优先处理与 {pain_point.get('topic', 'unknown')} 相关的高频问题。",
        "在关键路径中提供更清晰的状态反馈、错误提示和下一步建议。",
        "将问题处理结果沉淀为可追踪的产品指标和复盘材料。",
    ]
    acceptance_criteria = [
        "用户能够理解问题原因和下一步处理方式。",
        "相关反馈可以追溯到原始 GitHub Issue 或 Comment。",
        "上线后可通过 BI 指标观察反馈量和负面反馈变化。",
    ]
    metrics = [
        "相关主题负面反馈占比下降。",
        "同类问题重复反馈数量下降。",
        "PRD 输出证据覆盖率达到 80% 以上。",
    ]
    risks = [
        "规则分析可能误分类部分反馈，需要后续引入人工审核或 LLM 复核。",
        "GitHub 公开反馈不能完全代表所有用户，需要后续补充更多数据源。",
    ]

    prd_markdown = "\n".join(
        [
            f"# {title}",
            "",
            "## 背景",
            background,
            "",
            "## 用户痛点",
            pain_point.get("user_pain", ""),
            "",
            "## 用户故事",
            user_story,
            "",
            "## 功能需求",
            *[f"- {item}" for item in requirements],
            "",
            "## 非功能需求",
            "- 保留原始证据链接，支持后续追溯。",
            "- 输出结构应稳定，便于进入评估和导出流程。",
            "",
            "## 验收标准",
            *[f"- {item}" for item in acceptance_criteria],
            "",
            "## 成功指标",
            *[f"- {item}" for item in metrics],
            "",
            "## 风险与边界",
            *[f"- {item}" for item in risks],
            "",
            "## 证据引用",
            *[f"- {quote}" for quote in evidence_quotes[:5]],
        ]
    )

    state["prd_draft"] = {
        "title": title,
        "opportunity_id": opportunity.get("opportunity_id"),
        "background": background,
        "user_story": user_story,
        "requirements": requirements,
        "acceptance_criteria": acceptance_criteria,
        "metrics": metrics,
        "risks": risks,
        "evidence_refs": evidence_quotes,
        "markdown": prd_markdown,
        "status": "draft",
    }
    return state

