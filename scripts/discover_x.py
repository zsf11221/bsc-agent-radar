"""X discovery (X API v2, recent search).
Requires X_BEARER_TOKEN env / GitHub Secret. Without it the script exits 0
with an empty list and a clear message -- it never fakes X data and never
scrapes x.com HTML.
Queries deliberately do NOT require launch/mint words, so no-token Agent
projects are not filtered out."""
import json, os, sys, urllib.request, urllib.parse
sys.path.insert(0, os.path.dirname(__file__))
from common import make_item

QUERIES = [
    '("AI agent" OR agentic OR DeFAI) (BNB OR BSC OR "BNB Chain") -is:retweet',
    '("Agent ID" OR "Binance Agentic Wallet" OR "Agentic Wallet") agent -is:retweet',
    '(智能体 OR "AI Agent") (币安 OR BNB OR BSC) -is:retweet',
    'from:_mlnbro Agent -is:retweet',
]

def search(query, token, max_results=10):
    url = ("https://api.x.com/2/tweets/search/recent?query=" + urllib.parse.quote(query)
           + f"&max_results={max_results}&tweet.fields=created_at,public_metrics&expansions=author_id")
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "User-Agent": "bsc-agent-radar"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def discover():
    token = os.environ.get("X_BEARER_TOKEN")
    if not token:
        print("[x] X_BEARER_TOKEN not set -- skipping X, no data invented", file=sys.stderr)
        return []
    items = []
    for q in QUERIES:
        try:
            data = search(q, token)
        except Exception as e:
            print(f"[x] query failed {q[:40]!r}: {e}", file=sys.stderr)
            continue
        for tw in data.get("data", []):
            text = tw.get("text", "")
            # Keep only tweets that actually mention an Agent project; a bare
            # mention with no name/link goes to review, not catalog (handled downstream).
            items.append(make_item(
                name=f"X 线索 {tw.get('id')}",
                description=text[:500],
                source="x", source_url=f"https://x.com/i/status/{tw.get('id')}",
                x=f"https://x.com/i/status/{tw.get('id')}",
            ))
    return items

if __name__ == "__main__":
    print(json.dumps(discover(), ensure_ascii=False, indent=2))
