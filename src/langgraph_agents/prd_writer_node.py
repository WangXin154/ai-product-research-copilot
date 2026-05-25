from __future__ import annotations

import re
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.langgraph_agents.state import ResearchState


TOPIC_TITLE_MAP = {
    "Performance and Usability Issues": "性能与可用性问题优化 PRD",
    "Runtime Reliability": "运行稳定性与错误处理优化 PRD",
    "Language Support Enhancement": "多语言支持能力优化 PRD",
    "Feature Prioritization": "用户反馈优先级机制优化 PRD",
    "Search Functionality Improvement": "反馈搜索与重复问题识别优化 PRD",
}


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def readable_topic(topic: str) -> str:
    if not topic:
        return "核心用户问题"
    known = {
        "Performance and Usability Issues": "性能与可用性问题",
        "Runtime Reliability": "运行稳定性问题",
        "Language Support Enhancement": "多语言支持需求",
        "Feature Prioritization": "功能优先级反馈",
        "Search Functionality Improvement": "搜索与重复反馈识别问题",
    }
    return known.get(topic, topic.replace("_", " "))


def build_title(opportunity_name: str, topic: str) -> str:
    if topic in TOPIC_TITLE_MAP:
        return TOPIC_TITLE_MAP[topic]
    topic_text = readable_topic(topic)
    return f"{topic_text}优化 PRD"


def infer_user_persona(topic: str) -> str:
    if topic in {"Performance and Usability Issues", "Runtime Reliability"}:
        return "数据应用开发者"
    if topic == "Language Support Enhancement":
        return "非英语地区用户"
    if topic == "Feature Prioritization":
        return "活跃社区用户"
    return "目标用户"


def build_background(pain_point: dict) -> str:
    evidence_count = pain_point.get("evidence_count", 0)
    topic = readable_topic(pain_point.get("topic", ""))
    user_pain = normalize_space(pain_point.get("user_pain", ""))
    if user_pain.startswith("用户围绕"):
        user_pain = user_pain.split("集中反馈：", 1)[-1]
    return (
        f"本次调研从 GitHub Issues / Comments 中识别出 {evidence_count} 条与{topic}相关的反馈。"
        f"这些反馈集中反映出：{user_pain or '用户在关键流程中存在可被产品优化的阻碍。'}"
        " 该问题已经具备明确的用户证据，适合作为下一阶段产品优化机会进入 PRD 设计。"
    )


def build_user_story(pain_point: dict) -> str:
    topic = pain_point.get("topic", "")
    persona = infer_user_persona(topic)
    topic_text = readable_topic(topic)
    user_need = normalize_space(pain_point.get("user_need", ""))

    if topic in {"Performance and Usability Issues", "Runtime Reliability"}:
        goal = "在遇到性能下降、组件异常或运行错误时，能够快速理解问题原因并获得明确的处理建议"
    elif topic == "Language Support Enhancement":
        goal = "能够使用符合本地语言习惯的界面与提示"
    elif topic == "Feature Prioritization":
        goal = "能够清楚表达需求优先级，并看到反馈如何影响产品排期"
    elif topic == "Search Functionality Improvement":
        goal = "能够快速找到已有问题、解决方案和相关讨论，减少重复提交"
    elif user_need:
        goal = user_need.rstrip("。.")
    else:
        goal = f"能够更顺畅地完成与{topic_text}相关的核心任务"

    return f"作为{persona}，我希望{goal}，以便更稳定、高效地完成核心工作流。"


def build_requirements(pain_point: dict) -> list[str]:
    topic = pain_point.get("topic", "")
    topic_text = readable_topic(topic)
    common = [
        f"建立{topic_text}的高频反馈识别机制，支持按反馈数量、严重程度和证据强度排序。",
        "在关键路径中提供用户可理解的状态反馈、错误提示和下一步处理建议。",
        "在 PRD 输出中保留对应的 Issue / Comment 证据，支持后续追溯和人工复核。",
    ]
    topic_specific = {
        "Performance and Usability Issues": [
            "识别性能回归、组件刷新异常、导航交互失败等高影响问题，并形成可排期的问题清单。",
            "为高频性能问题增加复现条件、影响范围和优先级说明。",
        ],
        "Runtime Reliability": [
            "将运行异常、崩溃、报错和不可用场景按影响范围进行归类。",
            "为关键异常提供更清晰的错误说明、日志定位线索和用户侧解决建议。",
        ],
        "Language Support Enhancement": [
            "梳理用户请求的语言覆盖范围，并明确首批支持语言的优先级。",
            "建立翻译内容审核流程，避免界面术语不一致影响理解。",
        ],
        "Feature Prioritization": [
            "建立社区反馈投票和优先级解释机制，让用户理解需求排期依据。",
            "将高频需求与产品机会点评分体系关联，形成可复盘的决策链路。",
        ],
        "Search Functionality Improvement": [
            "优化历史 Issue / Comment 搜索结果的召回和排序，减少重复反馈。",
            "在用户提交反馈前提示相似问题和已有解决方案。",
        ],
    }
    return topic_specific.get(topic, []) + common


def build_acceptance_criteria(pain_point: dict) -> list[str]:
    topic_text = readable_topic(pain_point.get("topic", ""))
    return [
        f"用户能够理解{topic_text}的主要问题原因、影响范围和下一步处理方式。",
        "每个关键结论至少关联一条原始 GitHub Issue 或 Comment 证据。",
        "产品团队能够在 Dashboard 中查看该主题的反馈数量、情绪、证据覆盖率和后续状态。",
        "当 AI Evaluation 判断证据覆盖不足或幻觉风险较高时，结果会进入 Human Review Gate。",
    ]


def build_metrics(pain_point: dict) -> list[str]:
    topic_text = readable_topic(pain_point.get("topic", ""))
    return [
        f"{topic_text}相关负面反馈占比下降。",
        "同类问题重复反馈数量下降。",
        "PRD 输出证据覆盖率达到 80% 以上。",
        "进入 Human Review 的高风险输出比例下降。",
    ]


def build_risks() -> list[str]:
    return [
        "GitHub 公开反馈存在样本偏差，不能完全代表所有用户群体。",
        "Embedding / LLM 聚类可能存在误归类，需要保留人工复核机制。",
        "部分问题的真实修复成本需要结合工程复杂度、版本兼容性和产品优先级进一步评估。",
        "AI 生成 PRD 只能作为草稿，最终上线范围需要由产品、设计和工程共同确认。",
    ]


def format_evidence(evidence_quotes: list[str]) -> list[str]:
    formatted = []
    for index, quote in enumerate(evidence_quotes[:5], start=1):
        text = normalize_space(quote)
        if text:
            formatted.append(f"Evidence {index}: {text}")
    return formatted or ["Evidence 1: 暂无可用证据引用，请补充原始反馈。"]


def prd_writer_node(state: ResearchState) -> ResearchState:
    state["current_step"] = "prd_writer_node"
    opportunity = state.get("selected_opportunity", {})
    if not opportunity:
        state["prd_draft"] = {}
        return state

    pain_point = opportunity.get("source_pain_point", {})
    evidence_quotes = pain_point.get("evidence_quotes", [])
    topic = pain_point.get("topic", "")
    title = build_title(opportunity.get("opportunity_name", ""), topic)
    background = build_background(pain_point)
    user_story = build_user_story(pain_point)
    requirements = build_requirements(pain_point)
    acceptance_criteria = build_acceptance_criteria(pain_point)
    metrics = build_metrics(pain_point)
    risks = build_risks()
    evidence_refs = format_evidence(evidence_quotes)

    prd_markdown = "\n".join(
        [
            f"# {title}",
            "",
            "## 背景",
            background,
            "",
            "## 用户痛点",
            normalize_space(pain_point.get("user_pain", "")),
            "",
            "## 用户故事",
            user_story,
            "",
            "## 功能需求",
            *[f"- {item}" for item in requirements],
            "",
            "## 非功能需求",
            "- 保留原始证据链接，支持后续追溯。",
            "- 输出结构应稳定，便于进入 AI Evaluation、Human Review 和 Dashboard 复盘流程。",
            "- 对高风险结论标记审核状态，避免未经验证的 AI 结论直接进入产品决策。",
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
            *[f"- {item}" for item in evidence_refs],
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
        "evidence_refs": evidence_refs,
        "markdown": prd_markdown,
        "status": "draft",
    }
    return state
