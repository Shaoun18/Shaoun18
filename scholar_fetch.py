import os
import requests

# Get SerpAPI key from environment variable
API_KEY = os.environ.get("SERPAPI_KEY")
if not API_KEY:
    raise ValueError("SERPAPI_KEY not set! Add it as a GitHub secret.")

SCHOLAR_ID = "gGfY9toAAAAJ"
PLACEHOLDER = "<!-- PUBLICATIONS_PLACEHOLDER -->"

def fetch_publications(scholar_id, api_key, limit=10):
    """Fetch latest publications from SerpAPI Google Scholar."""
    url = f"https://serpapi.com/search.json?engine=google_scholar_author&author_id={scholar_id}&api_key={api_key}"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

    data = response.json()
    articles = data.get("articles", [])[:limit]

    if not articles:
        return None

    publications_md = ""
    for pub in articles:
        title = pub.get("title", "No Title")
        link = pub.get("link", "#")
        year = pub.get("year", "N/A")
        publications_md += f"- [{title}]({link}) ({year})\n"

    return publications_md

def update_readme(md_content, readme_path="README.md"):
    """Insert publications into README at placeholder."""
    if not md_content:
        print("No publications fetched, README not updated.")
        return

    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            readme = f.read()
    except FileNotFoundError:
        print(f"{readme_path} not found!")
        return

    if PLACEHOLDER not in readme:
        print(f"Placeholder '{PLACEHOLDER}' not found in README.")
        return

    readme = readme.replace(PLACEHOLDER, md_content)
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme)

    print("README.md updated successfully!")

if __name__ == "__main__":
    md_content = fetch_publications(SCHOLAR_ID, API_KEY)
    update_readme(md_content)
