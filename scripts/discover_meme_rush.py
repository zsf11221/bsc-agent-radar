"""Binance meme-rush supplement (Four.meme on BSC, chain 56).
Public bapi endpoint, no key. Only token launches -- supplementary only,
never the main discovery source. Keyword filter keeps only agent-related
tokens; everything else is dropped, not stored."""
import json, sys, urllib.request
sys.path.insert(0, __import__("os").path.dirname(__file__))
from common import make_item

URL = "https://web3.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/market/token/pulse/rank/list/ai"
import re
KEYWORD_RE = re.compile(r"\b(agent|agentic|defai|mcp|ai agent)\b", re.I)
def _agent_like(symbol, name, hay):
    low = hay.lower()
    if KEYWORD_RE.search(hay):
        return True
    if re.search(r"\bai\b", low):
        return True
    # 名字以 AI 结尾且长度>4，如 TerafabAI；Mai（3 字母）不算
    for tok in (symbol or "", name or ""):
        if len(tok.strip()) > 4 and tok.strip().lower().endswith("ai"):
            return True
    return False

def fetch(rank_type=10, limit=20):
    payload = json.dumps({"chainId": "56", "rankType": rank_type, "limit": limit}).encode()
    req = urllib.request.Request(URL, data=payload, headers={
        "Content-Type": "application/json", "User-Agent": "bsc-agent-radar"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def discover():
    items = []
    for rank_type in (10, 20, 30):  # new / finalizing / migrated
        try:
            data = fetch(rank_type)
        except Exception as e:
            print(f"[meme-rush] rankType {rank_type} failed: {e}", file=sys.stderr)
            continue
        for t in data.get("data") or []:
            hay = f"{t.get('symbol','')} {t.get('name','')} {(t.get('narrativeText') or {}).get('en','')}"
            if not _agent_like(t.get('symbol'), t.get('name'), hay):
                continue  # Mai 这种含 ai 子串的不算；TerafabAI 这种以 AI 结尾的算
            contract = t.get("contractAddress")
            if not contract:
                continue
            socials = t.get("socials") or {}
            items.append(make_item(
                name=t.get("symbol") or t.get("name") or contract[:10],
                description=(t.get("name") or "") + " — meme-rush 新币（补充源，仅看币）",
                source="meme-rush", source_url=f"https://www.bnbchain.org/en",
                website=(socials.get("website") or None),
                x=(socials.get("twitter") or None),
                contract_address=contract,
            ))
    return items

if __name__ == "__main__":
    print(json.dumps(discover(), ensure_ascii=False, indent=2))
