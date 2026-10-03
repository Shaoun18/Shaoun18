"""Sync Google Scholar publications and metrics into README.md via SerpAPI.

README.md must contain these marker pairs (content between them is replaced):
  <!-- PUBLICATIONS:START --> ... <!-- PUBLICATIONS:END -->
  <!-- METRICS:START -->      ... <!-- METRICS:END -->
"""
import os
import re
import sys

import requests

SCHOLAR_ID = "gGfY9toAAAAJ"
README_PATH = "README.md"
LIMIT = 10
API_URL = "https://serpapi.com/search.json"


def fetch_author(api_key: str) -> dict | None:
    params = {
        "engine": "google_scholar_author",
        "author_id": SCHOLAR_ID,
        "sort": "pubdate",
        "num": 100,
        "api_key": api_key,
    }
    try:
        resp = requests.get(API_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as exc:
        print(f"::error::Failed to fetch Scholar data: {exc}")
        return None
    if data.get("error"):
        print(f"::error::SerpAPI error: {data['error']}")
        return None
    return data


def build_publications(articles: list) -> str:
    lines = []
    for art in articles[:LIMIT]:
        title = (art.get("title") or "Untitled").replace("[", "(").replace("]", ")")
        link = art.get("link") or f"https://scholar.google.com/citations?user={SCHOLAR_ID}"
        year = art.get("year") or "n/a"
        cited = (art.get("cited_by") or {}).get("value")
        suffix = f" · 🔍 {cited} citations" if cited else ""
        lines.append(f"- [{title}]({link}) ({year}){suffix}")
    return "\n".join(lines)


def build_metrics(data: dict, pub_count: int) -> str:
    citations = h_index = i10 = None
    for row in (data.get("cited_by") or {}).get("table", []):
        if "citations" in row:
            citations = row["citations"].get("all")
        elif "h_index" in row:
            h_index = row["h_index"].get("all")
        elif "i10_index" in row:
            i10 = row["i10_index"].get("all")
    rows = [("📄 Publications", pub_count), ("🔍 Citations", citations),
            ("📈 h-index", h_index), ("🧪 i10-index", i10)]
    out = ["| Metric | Count |", "|--------|:-----:|"]
    out += [f"| {name} | **{val}** |" for name, val in rows if val is not None]
    return "\n".join(out)


def replace_block(text: str, tag: str, content: str) -> tuple[str, bool]:
    pattern = re.compile(
        rf"(<!-- {tag}:START -->)(.*?)(<!-- {tag}:END -->)", re.DOTALL
    )
    if not pattern.search(text):
        print(f"::warning::Marker <!-- {tag}:START/END --> not found in README")
        return text, False
    return pattern.sub(lambda m: f"{m.group(1)}\n{content}\n{m.group(3)}", text), True


def main() -> int:
    api_key = os.environ.get("SERPAPI_KEY")
    if not api_key:
        print("::warning::SERPAPI_KEY secret not set. Skipping update.")
        return 0

    data = fetch_author(api_key)
    if not data:
        return 1
    articles = data.get("articles") or []
    if not articles:
        print("::warning::No publications returned. README left unchanged.")
        return 0

    with open(README_PATH, "r", encoding="utf-8") as fh:
        readme = fh.read()

    readme, _ = replace_block(readme, "PUBLICATIONS", build_publications(articles))
    readme, _ = replace_block(readme, "METRICS", build_metrics(data, len(articles)))

    with open(README_PATH, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(readme)
    print("README.md updated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
