#!/usr/bin/env python3
"""
Weekly digest script:
  • pulls the 10 most-starred Python repos created in the last 7 days
  • writes trending/YYYY-MM-DD.md
  • updates the README snippet with the top 3
"""
from __future__ import annotations
import datetime, os, pathlib
import requests

# 1 – dates -------------------------------------------------------------
today = datetime.date.today()
since = today - datetime.timedelta(days=7)
query  = f"language:python created:>{since.isoformat()}"

# 2 – GitHub Search API -------------------------------------------------
url = (
    "https://api.github.com/search/repositories"
    f"?q={query}&sort=stars&order=desc&per_page=10"
)
resp = requests.get(
    url,
    headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
        "X-GitHub-Api-Version": "2022-11-28",
    },
    timeout=30,
)
resp.raise_for_status()
items = resp.json()["items"]

# 3 – write weekly markdown file ---------------------------------------
out_dir = pathlib.Path("trending")
out_dir.mkdir(exist_ok=True)
md_path = out_dir / f"{today.isoformat()}.md"

with md_path.open("w", encoding="utf-8") as f:
    f.write(f"# Top 10 Python repos – week ending {today}\n\n")
    f.write("| Rank | Repository | ⭐ Stars | Description |\n")
    f.write("| --- | --- | --- | --- |\n")
    for rank, repo in enumerate(items, 1):
        desc = (repo["description"] or "").replace("|", "\\|")
        f.write(
            f"| {rank} "
            f"| [{repo['full_name']}]({repo['html_url']}) "
            f"| {repo['stargazers_count']:,} "
            f"| {desc} |\n"
        )

# 4 – update README snippet --------------------------------------------
readme = pathlib.Path("README.md")
snippet_start = "<!-- trending:start -->"
snippet_end   = "<!-- trending:end -->"

top3 = "\n".join(
    f"{i}. [{r['full_name']}]({r['html_url']}) – ⭐ {r['stargazers_count']:,}"
    for i, r in enumerate(items[:3], 1)
)

if readme.exists():
    content = readme.read_text(encoding="utf-8")
else:
    content = "# Weekly Trending Digest\n\n"

if snippet_start in content and snippet_end in content:
    pre, _, tail = content.partition(snippet_start)
    _, _, post   = tail.partition(snippet_end)
    new = f"{pre}{snippet_start}\n{top3}\n{snippet_end}{post}"
else:
    new = (
        content
        + "\n## Top 3 Python repos this week\n"
        + f"{snippet_start}\n{top3}\n{snippet_end}\n"
    )

readme.write_text(new, encoding="utf-8")
