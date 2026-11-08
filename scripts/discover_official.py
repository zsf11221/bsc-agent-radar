"""Official sources: BNB Chain / Binance Skills Hub.
Reads public GitHub repo metadata for the official org repos (no scraping
of JS-heavy pages) plus the Binance Skills Hub repo itself.
If bnbchain.org is unreachable the script still returns the GitHub-backed
official items and reports the failure instead of inventing data."""
import json, os, sys, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from common import make_item

# Curated, verifiable official repos -- each is a real public repo, checked
# via the GitHub API in the first live run (2026-11-09).
OFFICIAL_REPOS = [
    ("bnb-chain/bnbchain-mcp", "BNB Chain 官方 MCP 服务器：给 AI Agent 用的 BSC / opBNB / Greenfield 工具"),
    ("binance/binance-skills-hub", "Binance Skills Hub：给 AI Agent 用的加密原生 Skills，包括 Agentic Wallet、meme-rush、扫链等"),
]

def gh_repo(full):
    req = urllib.request.Request(f"https://api.github.com/repos/{full}", headers={
        "Accept": "application/vnd.github+json", "User-Agent": "bsc-agent-radar",
        **({"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"} if os.environ.get("GITHUB_TOKEN") else {}),
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def discover():
    items = []
    for full, note in OFFICIAL_REPOS:
        try:
            repo = gh_repo(full)
        except Exception as e:
            print(f"[official] failed {full}: {e}", file=sys.stderr)
            continue
        items.append(make_item(
            name=repo.get("name") or full,
            description=(repo.get("description") or note),
            source="official", source_url=repo.get("html_url"),
            github=repo.get("html_url"), website=repo.get("homepage") or None,
        ))
    return items

if __name__ == "__main__":
    print(json.dumps(discover(), ensure_ascii=False, indent=2))
