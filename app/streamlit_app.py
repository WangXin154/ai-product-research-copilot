from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "database" / "product_research.db"
WORKFLOW_DIR = PROJECT_ROOT / "outputs" / "workflow"


st.set_page_config(
    page_title="AI Product Research Agent & BI Platform",
    page_icon="📊",
    layout="wide",
)


@st.cache_data(show_spinner=False)
def read_sql(sql: str, params: tuple[Any, ...] = ()) -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame()
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(sql, conn, params=params)


@st.cache_data(show_spinner=False)
def read_text_file(path: str) -> str:
    file_path = Path(path)
    if not file_path.exists():
        return ""
    return file_path.read_text(encoding="utf-8")


@st.cache_data(show_spinner=False)
def read_json_file(path: str) -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        return {}
    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def metric_value(sql: str) -> int | float:
    df = read_sql(sql)
    if df.empty:
        return 0
    return df.iloc[0, 0] or 0


def render_metric_cards(items: list[tuple[str, Any]], columns: int = 4) -> None:
    cols = st.columns(columns)
    for idx, (label, value) in enumerate(items):
        cols[idx % columns].metric(label, value)


def safe_bar(df: pd.DataFrame, x: str, y: str, title: str, color: str | None = None) -> None:
    if df.empty:
        st.info("暂无数据")
        return
    fig = px.bar(df, x=x, y=y, color=color, title=title, text_auto=True)
    fig.update_layout(height=360, margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig, use_container_width=True)


def safe_pie(df: pd.DataFrame, names: str, values: str, title: str) -> None:
    if df.empty:
        st.info("暂无数据")
        return
    fig = px.pie(df, names=names, values=values, title=title, hole=0.35)
    fig.update_layout(height=360, margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig, use_container_width=True)


def sidebar_filters() -> tuple[list[str], list[str]]:
    st.sidebar.title("AI Product Research")
    st.sidebar.caption("Agent + BI Dashboard")
    st.sidebar.write("数据库")
    st.sidebar.code(str(DB_PATH))

    repo_df = read_sql("SELECT DISTINCT repo_name FROM raw_feedback ORDER BY repo_name")
    type_df = read_sql("SELECT DISTINCT feedback_type FROM cleaned_feedback ORDER BY feedback_type")

    repos = repo_df["repo_name"].dropna().tolist() if not repo_df.empty else []
    feedback_types = type_df["feedback_type"].dropna().tolist() if not type_df.empty else []

    selected_repos = st.sidebar.multiselect("仓库", repos, default=repos)
    selected_types = st.sidebar.multiselect("反馈类型", feedback_types, default=feedback_types)

    if st.sidebar.button("刷新数据"):
        st.cache_data.clear()
        st.rerun()

    return selected_repos, selected_types


def repo_filter_clause(selected_repos: list[str], table_alias: str = "") -> tuple[str, tuple[Any, ...]]:
    if not selected_repos:
        return "", ()
    column = f"{table_alias}.repo_name" if table_alias else "repo_name"
    placeholders = ",".join(["?"] * len(selected_repos))
    return f" AND {column} IN ({placeholders})", tuple(selected_repos)


def type_filter_clause(selected_types: list[str], table_alias: str = "") -> tuple[str, tuple[Any, ...]]:
    if not selected_types:
        return "", ()
    column = f"{table_alias}.feedback_type" if table_alias else "feedback_type"
    placeholders = ",".join(["?"] * len(selected_types))
    return f" AND {column} IN ({placeholders})", tuple(selected_types)


def page_overview(selected_repos: list[str], selected_types: list[str]) -> None:
    st.header("Research Overview")

    raw_repo_clause, raw_repo_params = repo_filter_clause(selected_repos)
    clean_repo_clause, clean_repo_params = repo_filter_clause(selected_repos, "rf")
    type_clause, type_params = type_filter_clause(selected_types, "cf")

    raw_count = read_sql(
        f"SELECT COUNT(*) AS c FROM raw_feedback WHERE 1=1{raw_repo_clause}",
        raw_repo_params,
    ).iloc[0]["c"]

    cleaned_count = read_sql(
        f"""
        SELECT COUNT(*) AS c
        FROM cleaned_feedback cf
        JOIN raw_feedback rf ON cf.feedback_id = rf.feedback_id
        WHERE 1=1{clean_repo_clause}{type_clause}
        """,
        clean_repo_params + type_params,
    ).iloc[0]["c"]

    repo_count = read_sql(
        f"SELECT COUNT(DISTINCT repo_name) AS c FROM raw_feedback WHERE 1=1{raw_repo_clause}",
        raw_repo_params,
    ).iloc[0]["c"]

    comment_count = read_sql(
        f"""
        SELECT COUNT(*) AS c
        FROM raw_feedback
        WHERE comment_id IS NOT NULL AND LENGTH(comment_id) > 0{raw_repo_clause}
        """,
        raw_repo_params,
    ).iloc[0]["c"]
    pain_count = metric_value("SELECT COUNT(*) FROM pain_points")
    opp_count = metric_value("SELECT COUNT(*) FROM opportunity_scores")
    prd_count = metric_value("SELECT COUNT(*) FROM prd_drafts")
    eval_count = metric_value("SELECT COUNT(*) FROM ai_evaluation_results")


    render_metric_cards(
        [
            ("原始反馈", int(raw_count)),
            ("清洗反馈", int(cleaned_count)),
            ("覆盖仓库", int(repo_count)),
            ("Comments", int(comment_count)),
            ("痛点", int(pain_count)),
            ("机会点", int(opp_count)),
            ("PRD", int(prd_count)),
            ("AI Eval", int(eval_count)),
        ]
    )

    st.divider()
    left, right = st.columns(2)
    repo_df = read_sql(
        f"""
        SELECT repo_name, COUNT(*) AS feedback_count
        FROM raw_feedback
        WHERE 1=1{raw_repo_clause}
        GROUP BY repo_name
        ORDER BY feedback_count DESC
        """,
        raw_repo_params,
    )
    type_df = read_sql(
        f"""
        SELECT cf.feedback_type, COUNT(*) AS feedback_count
        FROM cleaned_feedback cf
        JOIN raw_feedback rf ON cf.feedback_id = rf.feedback_id
        WHERE 1=1{clean_repo_clause}{type_clause}
        GROUP BY cf.feedback_type
        ORDER BY feedback_count DESC
        """,
        clean_repo_params + type_params,
    )
    with left:
        safe_bar(repo_df, "repo_name", "feedback_count", "各仓库反馈数量")
    with right:
        safe_pie(type_df, "feedback_type", "feedback_count", "反馈类型分布")


def page_feedback(selected_repos: list[str], selected_types: list[str]) -> None:
    st.header("Feedback Intelligence")

    pain_df = read_sql(
        """
        SELECT user_pain, user_need, evidence_count, priority_hint, related_feedback_ids
        FROM pain_points
        ORDER BY evidence_count DESC
        """
    )
    if not pain_df.empty:
        safe_bar(pain_df, "user_pain", "evidence_count", "高频痛点排行", color="priority_hint")
        st.dataframe(pain_df, use_container_width=True, hide_index=True)
    else:
        st.info("暂无痛点数据，请先运行工作流并保存结果。")

    clean_repo_clause, clean_repo_params = repo_filter_clause(selected_repos, "rf")
    type_clause, type_params = type_filter_clause(selected_types, "cf")
    sample_df = read_sql(
        f"""
        SELECT
            rf.repo_name,
            rf.issue_id,
            rf.comment_id,
            cf.feedback_type,
            cf.language,
            cf.cleaned_text,
            rf.url
        FROM cleaned_feedback cf
        JOIN raw_feedback rf ON cf.feedback_id = rf.feedback_id
        WHERE 1=1{clean_repo_clause}{type_clause}
        ORDER BY rf.created_at DESC
        LIMIT 200
        """,
        clean_repo_params + type_params,
    )
    st.subheader("反馈样本")
    st.dataframe(sample_df, use_container_width=True, hide_index=True)


def page_opportunities() -> None:
    st.header("Opportunity Pipeline")
    opp_df = read_sql(
        """
        SELECT
            opportunity_name,
            priority,
            priority_score,
            user_value,
            business_value,
            frequency,
            severity,
            effort,
            risk,
            ai_feasibility,
            evidence_strength
        FROM opportunity_scores
        ORDER BY priority_score DESC
        """
    )
    if opp_df.empty:
        st.info("暂无机会点数据，请先运行工作流并保存结果。")
        return

    priority_df = opp_df.groupby("priority", as_index=False).size().rename(columns={"size": "count"})
    render_metric_cards(
        [
            ("P0", int((opp_df["priority"] == "P0").sum())),
            ("P1", int((opp_df["priority"] == "P1").sum())),
            ("P2", int((opp_df["priority"] == "P2").sum())),
            ("Backlog", int((opp_df["priority"] == "Backlog").sum())),
        ]
    )
    left, right = st.columns(2)
    with left:
        safe_bar(priority_df, "priority", "count", "机会点优先级分布")
    with right:
        fig = px.scatter(
            opp_df,
            x="effort",
            y="user_value",
            size="evidence_strength",
            color="priority",
            hover_name="opportunity_name",
            title="用户价值 vs 实现成本",
        )
        fig.update_layout(height=360, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig, use_container_width=True)

    st.dataframe(opp_df, use_container_width=True, hide_index=True)


def page_evaluation() -> None:
    st.header("AI Evaluation Monitor")
    eval_df = read_sql(
        """
        SELECT
            relevance,
            accuracy,
            actionability,
            evidence_coverage,
            hallucination_risk,
            prd_completeness,
            overall_score,
            created_at
        FROM ai_evaluation_results
        ORDER BY created_at DESC
        """
    )
    if eval_df.empty:
        st.info("暂无 AI Evaluation 数据，请先运行工作流并保存结果。")
        return

    latest = eval_df.iloc[0]
    render_metric_cards(
        [
            ("Overall Score", latest["overall_score"]),
            ("Relevance", latest["relevance"]),
            ("Accuracy", latest["accuracy"]),
            ("Actionability", latest["actionability"]),
            ("Evidence Coverage", latest["evidence_coverage"]),
            ("PRD Completeness", latest["prd_completeness"]),
            ("Hallucination Risk", latest["hallucination_risk"]),
        ],
        columns=4,
    )

    score_df = pd.DataFrame(
        [
            {"metric": "relevance", "score": latest["relevance"]},
            {"metric": "accuracy", "score": latest["accuracy"]},
            {"metric": "actionability", "score": latest["actionability"]},
            {"metric": "prd_completeness", "score": latest["prd_completeness"]},
            {"metric": "overall_score", "score": latest["overall_score"]},
        ]
    )
    risk_df = eval_df.groupby("hallucination_risk", as_index=False).size().rename(columns={"size": "count"})
    left, right = st.columns(2)
    with left:
        safe_bar(score_df, "metric", "score", "最新评估维度")
    with right:
        safe_pie(risk_df, "hallucination_risk", "count", "幻觉风险分布")

    st.dataframe(eval_df, use_container_width=True, hide_index=True)


def page_competitor_intelligence() -> None:
    st.header("Competitor Intelligence")

    competitor_df = read_sql(
        """
        SELECT
            competitor_name,
            feature_name,
            feature_category,
            coverage,
            strength,
            weakness,
            source_url
        FROM competitor_features
        ORDER BY feature_category, competitor_name, feature_name
        """
    )

    workflow_summary = read_json_file(str(WORKFLOW_DIR / "workflow_summary.json"))
    differentiation_opportunities = workflow_summary.get("differentiation_opportunities", [])
    competitor_review_summary = workflow_summary.get("competitor_review_summary", "")

    if competitor_df.empty:
        st.info("暂无竞品数据，请先运行 competitor_loader.py。")
        st.code("python src\\data_ingestion\\competitor_loader.py --file data\\sample_competitors.csv")
        return

    coverage_score = {"high": 3, "medium": 2, "low": 1, "none": 0, "unknown": 0}
    competitor_df["coverage_score"] = competitor_df["coverage"].fillna("unknown").map(coverage_score).fillna(0)

    render_metric_cards(
        [
            ("Competitors", competitor_df["competitor_name"].nunique()),
            ("Feature Categories", competitor_df["feature_category"].nunique()),
            ("Feature Rows", len(competitor_df)),
            ("Diff Opportunities", len(differentiation_opportunities)),
        ]
    )

    if competitor_review_summary:
        st.info(competitor_review_summary)

    st.divider()
    left, right = st.columns(2)
    coverage_df = competitor_df.groupby("coverage", as_index=False).size().rename(columns={"size": "feature_count"})
    category_df = (
        competitor_df.groupby("feature_category", as_index=False)
        .size()
        .rename(columns={"size": "feature_count"})
        .sort_values("feature_count", ascending=False)
    )
    with left:
        safe_pie(coverage_df, "coverage", "feature_count", "Coverage Distribution")
    with right:
        safe_bar(category_df, "feature_category", "feature_count", "Feature Category Distribution")

    st.subheader("Competitor x Capability Heatmap")
    heatmap_df = competitor_df.pivot_table(
        index="competitor_name",
        columns="feature_category",
        values="coverage_score",
        aggfunc="max",
        fill_value=0,
    )
    if heatmap_df.empty:
        st.info("暂无可展示的竞品热力图数据")
    else:
        fig = px.imshow(
            heatmap_df,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="RdYlGn",
            title="Coverage Score: high=3, medium=2, low=1",
        )
        fig.update_layout(height=420, margin=dict(l=20, r=20, t=60, b=20))
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Feature Matrix")
    st.dataframe(
        competitor_df[
            [
                "competitor_name",
                "feature_category",
                "feature_name",
                "coverage",
                "strength",
                "weakness",
                "source_url",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Differentiation Opportunities")
    if differentiation_opportunities:
        opp_df = pd.DataFrame(differentiation_opportunities)
        display_columns = [
            column
            for column in ["category", "opportunity_name", "priority_hint", "rationale", "competitor_gap", "suggested_action"]
            if column in opp_df.columns
        ]
        st.dataframe(opp_df[display_columns], use_container_width=True, hide_index=True)
        for item in differentiation_opportunities[:6]:
            with st.expander(f"{item.get('priority_hint', 'P2')} · {item.get('opportunity_name', '差异化机会')}"):
                st.write(item.get("rationale", ""))
                st.caption("Competitor Gap")
                st.write(item.get("competitor_gap", ""))
                st.caption("Suggested Action")
                st.write(item.get("suggested_action", ""))
    else:
        st.info("暂无差异化机会。请先运行带竞品分析的 Agent 工作流并导出 workflow_summary.json。")
        st.code("python src\\langgraph_agents\\graph.py --repos streamlit/streamlit gradio-app/gradio --limit 30 --save --export")


def page_outputs() -> None:
    st.header("Workflow Output / PRD Preview")
    summary_path = WORKFLOW_DIR / "workflow_summary.md"
    prd_path = WORKFLOW_DIR / "prd_draft.md"
    bi_path = WORKFLOW_DIR / "bi_metrics.json"

    col1, col2, col3 = st.columns(3)
    col1.write("Workflow Summary")
    col1.code(str(summary_path))
    col2.write("PRD Draft")
    col2.code(str(prd_path))
    col3.write("BI Metrics")
    col3.code(str(bi_path))

    summary_text = read_text_file(str(summary_path))
    prd_text = read_text_file(str(prd_path))
    bi_text = read_text_file(str(bi_path))

    tab_summary, tab_prd, tab_bi = st.tabs(["工作流摘要", "PRD 草稿", "BI Metrics JSON"])
    with tab_summary:
        st.markdown(summary_text or "暂无 workflow_summary.md，请先运行工作流导出。")
    with tab_prd:
        st.markdown(prd_text or "暂无 prd_draft.md，请先运行工作流导出。")
    with tab_bi:
        st.code(bi_text or "{}", language="json")

    if summary_text:
        st.download_button("下载 Workflow Summary", summary_text, file_name="workflow_summary.md")
    if prd_text:
        st.download_button("下载 PRD Draft", prd_text, file_name="prd_draft.md")


def main() -> None:
    st.title("AI Product Research Agent & BI Platform")
    st.caption("GitHub Feedback → Agent Workflow → PRD → AI Evaluation → BI Review")

    if not DB_PATH.exists():
        st.error(f"数据库不存在：{DB_PATH}")
        st.stop()

    selected_repos, selected_types = sidebar_filters()
    tabs = st.tabs(
        [
            "Research Overview",
            "Feedback Intelligence",
            "Opportunity Pipeline",
            "AI Evaluation Monitor",
            "Competitor Intelligence",
            "Workflow Output",
        ]
    )
    with tabs[0]:
        page_overview(selected_repos, selected_types)
    with tabs[1]:
        page_feedback(selected_repos, selected_types)
    with tabs[2]:
        page_opportunities()
    with tabs[3]:
        page_evaluation()
    with tabs[4]:
        page_competitor_intelligence()
    with tabs[5]:
        page_outputs()


if __name__ == "__main__":
    main()
