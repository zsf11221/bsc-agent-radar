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

# BNB Chain 官网首页（https://www.bnbchain.org/en，200，2026-11-09 实测）内嵌 JSON
# 里的官方 Agent 示例。描述逐字取自官网 caseDesc，GitHub 路径逐一经
# GitHub API 核实存在。4EVERLAND Hosting MCP 未收：它只标 Greenfield，
# 不在 BSC（56）范围内。
OFFICIAL_EXAMPLES = [
    ("BNB Chain Eliza AgentKit",
     "AI Agent using the BNB Chain Plugin for Eliza AI",
     "https://github.com/bnb-chain/example-hub/tree/main/typescript/eliza-chatbot",
     "https://www.bnbchain.org/en/solutions/ai-agent"),
    ("BNB Chain LangChain AgentKit",
     "Create an AI Agent using the BNB Chain Plugin for LangChain AI",
     "https://github.com/bnb-chain/example-hub/tree/main/python/langchain-chatbot",
     "https://www.bnbchain.org/en/solutions/ai-agent"),
    ("BNBChain MCP - AI-Powered Blockchain Assistant",
     "A ready-to-use template that combines BNB Chain\u2019s MCP with Claude AI, enabling natural language interaction with BNB Smart Chain and Greenfield.",
     "https://github.com/bnb-chain/example-hub/tree/main/typescript/bnbchain-mcp",
     None),
    ("BNB Chain Chatbot with UI (Python)",
     "This project demonstrates how to create a web interface for the BNB Chain LangChain AgentKit Python chatbot, showcasing how to integrate AI agents into decentralized applications (dApps) through API wrappers.",
     "https://github.com/bnb-chain/example-hub/tree/main/python/chatbot-with-ui",
     None),
    ("AI-Powered Reputation NFT Badges on BNB Chain",
     "Forge unique, soulbound ERC-721 NFT reputation badges on the BNB Chain using data analysis and generative AI. This project analyzes wallet activity, generates insightful explanations via LLMs, and mints NFTs with off-chain metadata stored on IPFS.",
     "https://github.com/bnb-chain/example-hub/tree/main/python/ai-wallet-reputation-nft",
     None),
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
    for name, desc, gh_url, website in OFFICIAL_EXAMPLES:
        items.append(make_item(
            name=name, description=desc, source="official",
            source_url=gh_url, github=gh_url, website=website,
        ))
    return items

if __name__ == "__main__":
    print(json.dumps(discover(), ensure_ascii=False, indent=2))
