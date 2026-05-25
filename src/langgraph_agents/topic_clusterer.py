from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import OPENAI_API_KEY, OPENAI_CHAT_MODEL, OPENAI_EMBEDDING_MODEL


DEFAULT_MAX_CLUSTERS = 8
DEFAULT_CLUSTER_THRESHOLD = 0.78
MAX_TEXT_CHARS = 1600

FALLBACK_TOPIC_RULES = {
    "Runtime Reliability": ["bug", "error", "crash", "fail", "broken", "exception", "traceback", "cannot"],
    "Performance and Scalability": ["slow", "latency", "performance", "timeout", "memory", "speed", "freeze"],
    "Documentation and Examples": ["doc", "docs", "documentation", "example", "tutorial", "guide", "unclear"],
    "Data and File Workflows": ["upload", "file", "csv", "dataframe", "dataset", "data"],
    "Setup and Compatibility": ["install", "dependency", "version", "environment", "setup", "python"],
    "API and Integrations": ["api", "integration", "connection", "connect", "sql", "database", "token"],
    "User Experience": ["confusing", "difficult", "ux", "ui", "workflow", "experience", "button"],
}

NEGATIVE_TERMS = ["bug", "error", "fail", "failed", "crash", "broken", "cannot", "issue", "problem", "timeout", "exception"]
POSITIVE_TERMS = ["great", "thanks", "thank you", "love", "useful", "helpful", "works", "awesome"]


def stable_id(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]


def clean_for_embedding(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:MAX_TEXT_CHARS]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if not left_norm or not right_norm:
        return 0.0
    return dot / (left_norm * right_norm)


def mean_vector(vectors: list[list[float]]) -> list[float]:
    if not vectors:
        return []
    size = len(vectors[0])
    return [sum(vector[index] for vector in vectors) / len(vectors) for index in range(size)]


def get_openai_client() -> Any | None:
    if not OPENAI_API_KEY:
        return None
    try:
        from openai import OpenAI
    except ImportError:
        return None
    return OpenAI(api_key=OPENAI_API_KEY)


def embed_texts(texts: list[str]) -> tuple[list[list[float]], str]:
    client = get_openai_client()
    if client is None:
        return [], "fallback_no_openai_client"

    embeddings: list[list[float]] = []
    try:
        for start in range(0, len(texts), 64):
            batch = texts[start : start + 64]
            response = client.embeddings.create(model=OPENAI_EMBEDDING_MODEL, input=batch)
            embeddings.extend([item.embedding for item in response.data])
        return embeddings, "openai_embedding"
    except Exception:
        return [], "fallback_embedding_error"


def greedy_cluster_embeddings(
    embeddings: list[list[float]],
    threshold: float = DEFAULT_CLUSTER_THRESHOLD,
    max_clusters: int = DEFAULT_MAX_CLUSTERS,
) -> list[int]:
    clusters: list[list[int]] = []
    centroids: list[list[float]] = []

    for index, embedding in enumerate(embeddings):
        if not clusters:
            clusters.append([index])
            centroids.append(embedding)
            continue

        similarities = [cosine_similarity(embedding, centroid) for centroid in centroids]
        best_cluster = max(range(len(similarities)), key=lambda item: similarities[item])
        best_similarity = similarities[best_cluster]

        if best_similarity >= threshold or len(clusters) >= max_clusters:
            clusters[best_cluster].append(index)
            centroids[best_cluster] = mean_vector([embeddings[item] for item in clusters[best_cluster]])
        else:
            clusters.append([index])
            centroids.append(embedding)

    assignments = [0] * len(embeddings)
    for cluster_index, indexes in enumerate(clusters):
        for index in indexes:
            assignments[index] = cluster_index
    return assignments


def fallback_topic_for_text(text: str, feedback_type: str | None = None) -> tuple[str, list[str], float]:
    lowered = text.lower()
    if feedback_type == "bug":
        return "Runtime Reliability", ["bug", "error", "reliability"], 0.72
    matches: list[tuple[str, list[str]]] = []
    for topic, keywords in FALLBACK_TOPIC_RULES.items():
        hit_keywords = [keyword for keyword in keywords if keyword in lowered]
        if hit_keywords:
            matches.append((topic, hit_keywords))
    if matches:
        topic, keywords = max(matches, key=lambda item: len(item[1]))
        confidence = min(0.86, 0.62 + len(keywords) * 0.06)
        return topic, keywords[:6], confidence
    return "Other Product Feedback", ["feedback"], 0.55


def fallback_assignments(rows: list[dict[str, Any]]) -> list[int]:
    topic_to_cluster: dict[str, int] = {}
    assignments: list[int] = []
    for row in rows:
        topic, _, _ = fallback_topic_for_text(row.get("cleaned_text", ""), row.get("feedback_type"))
        if topic not in topic_to_cluster:
            topic_to_cluster[topic] = len(topic_to_cluster)
        assignments.append(topic_to_cluster[topic])
    return assignments


def infer_sentiment(text: str, feedback_type: str | None = None) -> str:
    lowered = text.lower()
    if feedback_type in {"bug", "complaint"}:
        return "negative"
    if any(term in lowered for term in NEGATIVE_TERMS):
        return "negative"
    if any(term in lowered for term in POSITIVE_TERMS):
        return "positive"
    return "neutral"


def severity_for_feedback(row: dict[str, Any], sentiment: str) -> int:
    feedback_type = row.get("feedback_type")
    text = row.get("cleaned_text", "").lower()
    if feedback_type == "bug" or any(term in text for term in ["crash", "exception", "traceback", "security"]):
        return 4
    if feedback_type == "complaint" or sentiment == "negative":
        return 3
    return 2


def representative_texts(cluster_rows: list[dict[str, Any]], limit: int = 6) -> list[str]:
    sorted_rows = sorted(cluster_rows, key=lambda row: len(row.get("cleaned_text", "")), reverse=True)
    return [row.get("cleaned_text", "")[:700] for row in sorted_rows[:limit] if row.get("cleaned_text")]


def fallback_label_cluster(cluster_rows: list[dict[str, Any]]) -> dict[str, Any]:
    all_text = " ".join(row.get("cleaned_text", "") for row in cluster_rows)
    feedback_types = Counter(row.get("feedback_type", "other") for row in cluster_rows)
    topic, keywords, confidence = fallback_topic_for_text(all_text, feedback_types.most_common(1)[0][0] if feedback_types else None)
    sentiment_counts = Counter(infer_sentiment(row.get("cleaned_text", ""), row.get("feedback_type")) for row in cluster_rows)
    sentiment = sentiment_counts.most_common(1)[0][0] if sentiment_counts else "neutral"
    return {
        "topic": topic,
        "topic_keywords": keywords,
        "topic_summary": f"该主题聚合了 {len(cluster_rows)} 条与 {topic} 相关的用户反馈。",
        "user_need": "用户需要产品团队基于该主题进一步定位问题、明确解决路径，并保留证据链路。",
        "sentiment": sentiment,
        "base_confidence": confidence,
    }


def llm_label_cluster(cluster_rows: list[dict[str, Any]]) -> dict[str, Any]:
    client = get_openai_client()
    if client is None:
        return fallback_label_cluster(cluster_rows)

    samples = representative_texts(cluster_rows)
    if not samples:
        return fallback_label_cluster(cluster_rows)

    prompt = {
        "task": "Name and summarize a product feedback topic cluster.",
        "requirements": [
            "Return strict JSON only.",
            "topic should be concise and product-oriented in English.",
            "topic_keywords should contain 3 to 8 short keywords.",
            "topic_summary should summarize the shared user problem.",
            "user_need should describe what users need from the product team.",
            "sentiment must be one of: positive, neutral, negative.",
        ],
        "feedback_samples": samples,
    }

    try:
        response = client.chat.completions.create(
            model=OPENAI_CHAT_MODEL,
            messages=[
                {"role": "system", "content": "You are a senior AI product research analyst. Return JSON only."},
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        content = response.choices[0].message.content or "{}"
        data = json.loads(content)
        fallback = fallback_label_cluster(cluster_rows)
        return {
            "topic": str(data.get("topic") or fallback["topic"])[:120],
            "topic_keywords": data.get("topic_keywords") if isinstance(data.get("topic_keywords"), list) else fallback["topic_keywords"],
            "topic_summary": str(data.get("topic_summary") or fallback["topic_summary"])[:600],
            "user_need": str(data.get("user_need") or fallback["user_need"])[:600],
            "sentiment": data.get("sentiment") if data.get("sentiment") in {"positive", "neutral", "negative"} else fallback["sentiment"],
            "base_confidence": 0.84,
        }
    except Exception:
        return fallback_label_cluster(cluster_rows)


def build_embedding_topics(feedback_rows: list[dict[str, Any]], max_clusters: int = DEFAULT_MAX_CLUSTERS) -> list[dict[str, Any]]:
    rows = [row for row in feedback_rows if row.get("feedback_id") and row.get("cleaned_text")]
    if not rows:
        return []

    texts = [clean_for_embedding(row.get("cleaned_text", "")) for row in rows]
    embeddings, method = embed_texts(texts)
    assignments = greedy_cluster_embeddings(embeddings, max_clusters=max_clusters) if embeddings and len(embeddings) == len(rows) else fallback_assignments(rows)

    cluster_map: dict[int, list[dict[str, Any]]] = {}
    for row, cluster_id in zip(rows, assignments):
        cluster_map.setdefault(cluster_id, []).append(row)

    cluster_labels = {cluster_id: llm_label_cluster(cluster_rows) for cluster_id, cluster_rows in cluster_map.items()}
    cluster_sizes = {cluster_id: len(cluster_rows) for cluster_id, cluster_rows in cluster_map.items()}

    topics: list[dict[str, Any]] = []
    for row, cluster_id in zip(rows, assignments):
        label = cluster_labels[cluster_id]
        text = row.get("cleaned_text", "")
        row_sentiment = infer_sentiment(text, row.get("feedback_type"))
        sentiment = row_sentiment if row_sentiment != "neutral" else label.get("sentiment", "neutral")
        severity = severity_for_feedback(row, sentiment)
        confidence = round(min(0.95, max(0.45, float(label.get("base_confidence", 0.72)))), 4)
        feedback_id = row.get("feedback_id", "")
        topic_name = str(label.get("topic") or "Other Product Feedback")
        topics.append(
            {
                "topic_id": f"topic_{stable_id(str(cluster_id) + feedback_id)}",
                "feedback_id": feedback_id,
                "repo_name": row.get("repo_name"),
                "topic": topic_name,
                "topic_keywords": json.dumps(label.get("topic_keywords", [])[:8], ensure_ascii=False),
                "topic_summary": label.get("topic_summary", ""),
                "user_need": label.get("user_need", ""),
                "cluster_id": f"cluster_{cluster_id}",
                "evidence_count": cluster_sizes.get(cluster_id, 1),
                "sentiment": sentiment,
                "severity": severity,
                "evidence_quote": text[:280],
                "confidence": confidence,
                "analysis_method": method,
            }
        )
    return topics
