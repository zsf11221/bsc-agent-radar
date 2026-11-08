"""GitHub discovery: search BSC + Agent repos. No token/contract required.
Uses GITHUB_TOKEN if set, else unauthenticated (lower rate limit).
Excludes this radar repo itself."""
import json, os, sys, time, urllib.request, urllib.parse
sys.path.insert(0, os.path.dirname(__file__))
from common import make_item, SELF_REPOS

QUERIES = [
    "AI agent BNB",
    "agentic BSC",
    "Agent ID BSC",
    "AI agent BNB Smart Chain",
    "MCP BNB Chain",
    "DeFAI BNB",
    "Binance Agentic Wallet agent",
]

def gh_get(url):
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "bsc-agent-radar",
        **({"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"} if os.environ.get("GITHUB_TOKEN") else {}),
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def discover(per_query=10):
    items, seen_repos = [], set()
    for q in QUERIES:
        url = ("https://api.github.com/search/repositories?q=" + urllib.parse.quote(q)
               + f"&sort=updated&order=desc&per_page={per_query}")
        try:
            data = gh_get(url)
        except Exception as e:
            print(f"[github] query failed {q!r}: {e}", file=sys.stderr)
            continue
        for repo in data.get("items", []):
            full = repo.get("full_name", "")
            if full in SELF_REPOS or full in seen_repos:
                continue
            seen_repos.add(full)
            desc = repo.get("description") or ""
            # Must be agent-related and BSC-related (search already narrows, re-check loosely)
            hay = f"{repo.get('name','')} {desc} {' '.join(repo.get('topics') or [])}".lower()
            if "agent" not in hay and "mcp" not in hay and "agentic" not in hay and "defai" not in hay:
                continue
            items.append(make_item(
                name=repo.get("name") or full,
                description=desc or f"GitHub 仓库 {full}",
                source="github", source_url=repo.get("html_url"),
                github=repo.get("html_url"), website=repo.get("homepage") or None,
            ))
        time.sleep(1)  # be polite to rate limits
    return items

if __name__ == "__main__":
    items = discover()
    print(json.dumps(items, ensure_ascii=False, indent=2))
    print(f"# {len(items)} repos", file=sys.stderr)
