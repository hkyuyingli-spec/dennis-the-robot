import os
import re
from typing import List, Dict, Any
import requests

RECENCY_PATTERNS = [
    r"\blatest\b",
    r"\brecent\b",
    r"\brecently\b",
    r"\bnew\s+research\b",
    r"\bnew\s+stud(?:y|ies)\b",
    r"\bcurrent\s+research\b",
    r"\bupdate\b",
    r"\bupdates\b",
    r"\bupdated\b",
    r"\bnews\b",
    r"\bbreakthrough\b",
    r"\bbreakthroughs\b",
    r"\b202[4-9]\b",
    r"\btoday\b",
    # Indonesian
    r"\bterbaru\b",
    r"\bterkini\b",
    r"\bpenelitian\s+baru\b",
    r"\bstudi\s+baru\b",
    r"\briset\s+baru\b",
    r"\bpembaruan\b",
    r"\bberita\b",
    # Chinese
    r"最新",
    r"近期",
    r"新研究",
    r"新发现",
    r"更新",
    r"近况",
]


def is_recency_query(query: str) -> bool:
    """
    Checks if the user's query contains recency-indicating language in English,
    Indonesian, or Chinese (e.g. 'latest', 'recent', 'new research', current year).
    """
    if not query:
        return False
    q_lower = query.lower()
    for pattern in RECENCY_PATTERNS:
        if re.search(pattern, q_lower):
            return True
    return False


def live_search_unavailable_message(lang: str = "en") -> str:
    """Returns a clear, user-facing message when the live search service is unavailable."""
    messages = {
        "en": "⚠️ Live web search is unavailable because TAVILY_API_KEY is not configured. Add the key to enable current research references.",
        "id": "⚠️ Pencarian web terbaru tidak tersedia karena TAVILY_API_KEY belum dikonfigurasi. Tambahkan kunci tersebut untuk mengaktifkan referensi riset terkini.",
        "zh": "⚠️ 直播网页搜索当前不可用，因为未配置 TAVILY_API_KEY。请添加该密钥以启用最新研究参考。",
    }
    return messages.get(lang, messages["en"])


def format_live_search_rag_block(results: List[Dict[str, Any]]) -> str:
    """
    Formats web search results into a standardized RAG reference block,
    matching the convention used by constitution, herb, and cancer education blocks.
    """
    if not results:
        return ""

    blocks = [
        "=== REFERENCE: LIVE WEB SEARCH (CURRENT RESEARCH) ===",
        "The following live web search results were retrieved for recent context:\n",
    ]
    for r in results:
        title = r.get("title", "Online Source")
        url = r.get("url", "")
        content = r.get("content", "").strip()
        blocks.append(f"--- Source: {title} ({url}) ---\nSummary: {content}\n")
    blocks.append("=== END OF LIVE WEB SEARCH REFERENCE DATA ===")
    return "\n".join(blocks)


def search_live_tcm(query: str, lang: str = "en", max_results: int = 3) -> str:
    """
    Calls the Tavily Search API if TAVILY_API_KEY is configured in the environment.
    If the key is missing or an error occurs, this function returns a clear, user-facing
    notice instead of silently failing.
    Returns the formatted RAG block string on success.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "TAVILY_API_KEY" in st.secrets:
                api_key = st.secrets["TAVILY_API_KEY"]
        except Exception:
            pass
    if not api_key:
        return live_search_unavailable_message(lang)

    q_lower = query.lower()
    if not any(term in q_lower for term in ["tcm", "chinese medicine", "herbal", "草药", "中医", "herba"]):
        search_query = f"{query} TCM Traditional Chinese Medicine"
    else:
        search_query = query

    endpoint = "https://api.tavily.com/search"
    payload = {
        "api_key": api_key,
        "query": search_query,
        "search_depth": "basic",
        "max_results": max_results,
        "include_answer": False,
    }

    try:
        resp = requests.post(endpoint, json=payload, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            return format_live_search_rag_block(results)
        else:
            print(f"[LiveSearch] Tavily API returned status code {resp.status_code}")
            return live_search_unavailable_message(lang)
    except Exception as e:
        print(f"[LiveSearch] Error during search request: {e}")
        return live_search_unavailable_message(lang)
