"""Shared helpers for bsc-agent-radar discovery. No network in this module."""
import json, re, hashlib
from datetime import date, datetime, timezone, timedelta
from urllib.parse import urlparse

TOKEN_STATUSES = ("has_token", "no_token", "unknown")
SELF_REPOS = {"zsf11221/bsc-agent-radar"}

def slugify(text):
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s or "unknown"

def dedup_key(item):
    """Dedup by contract first, then github repo, then website domain, then name+source."""
    if item.get("contract_address"):
        return "contract:" + item["contract_address"].lower()
    if item.get("github"):
        return "github:" + item["github"].rstrip("/").lower()
    if item.get("website"):
        try:
            return "domain:" + urlparse(item["website"]).netloc.lower()
        except Exception:
            pass
    return "name:" + slugify(item.get("name"))

def classify_token(text, contract_address=None):
    """Conservative: only has_token with a real 0x contract address.
    no_token only for clear tooling (MCP/SDK/Skills) with no token/mint/$ mention.
    Everything else is unknown -- never invent a token."""
    if contract_address and re.fullmatch(r"0x[0-9a-fA-F]{40}", contract_address):
        return "has_token"
    t = (text or "").lower()
    if re.search(r"\$[a-z]{2,10}\b", t) and ("token" in t or "mint" in t or "coin" in t):
        return "unknown"  # symbol mentioned but no contract verified
    if any(k in t for k in ("mcp server", "mcp", "skills", "sdk", "cli tool")) and not any(
        k in t for k in ("token", "mint", "coin", "$", "airdrop")
    ):
        return "no_token"
    return "unknown"

def make_item(name, description, source, source_url, github=None, website=None,
              x=None, contract_address=None, first_seen=None):
    text = f"{name} {description}"
    return {
        "id": slugify(name) + "-" + hashlib.md5(dedup_key({
            "name": name, "github": github, "website": website,
            "contract_address": contract_address}).encode()).hexdigest()[:6],
        "name": (name or "").strip(),
        "description": (description or "").strip()[:500],
        "source": source,
        "source_url": source_url,
        "website": website,
        "github": github,
        "x": x,
        "contract_address": contract_address,
        "token_status": classify_token(text, contract_address),
        "chain": 56,
        "first_seen": first_seen or datetime.now(timezone(timedelta(hours=8))).date().isoformat(),
        "verified": False,
        "verification": "未核验",
    }

def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")

def merge_items(existing, new_items):
    """Merge by dedup key. Same-name different-contract stays separate
    because contract is part of the key."""
    seen = {dedup_key(it): it for it in existing}
    added = []
    for it in new_items:
        k = dedup_key(it)
        if k in seen:
            continue
        seen[k] = it
        added.append(it)
    return list(seen.values()), added
