"""Offline tests for discovery helpers. No network, no secrets."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from common import make_item, dedup_key, merge_items, classify_token

def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    assert cond, name

# token classification: no contract -> never has_token
check("no contract => not has_token", classify_token("My $TOKEN mint now") == "unknown")
check("real contract => has_token", classify_token("x", "0x" + "ab" * 20) == "has_token")
check("mcp tool, no token words => no_token", classify_token("MCP server for BNB Chain") == "no_token")
check("plain agent project => unknown", classify_token("AI agent for BSC trading") == "unknown")

# dedup: same name, different contract stays separate
a = make_item("Foo", "agent", "chain", "https://example.com/a", contract_address="0x" + "11" * 20)
b = make_item("Foo", "agent", "chain", "https://example.com/b", contract_address="0x" + "22" * 20)
check("same name diff contract = different keys", dedup_key(a) != dedup_key(b))
merged, added = merge_items([a], [a, b])
check("merge keeps both diff-contract items", len(merged) == 2 and len(added) == 1)
merged2, added2 = merge_items([a], [dict(a)])
check("merge drops exact duplicate", len(merged2) == 1 and len(added2) == 0)

# catalog-worthy rule lives in run_discovery
sys.path.insert(0, os.path.dirname(__file__))
from run_discovery import catalog_worthy
check("github + desc => catalog", catalog_worthy(make_item("X", "desc", "github", "u", github="https://github.com/a/b")))
check("bare x mention => review only", not catalog_worthy(make_item("X 线索 1", "hi", "x", "u", x="https://x.com/i/status/1")))
check("no desc => review only", not catalog_worthy({"description": "", "github": "https://github.com/a/b"}))

print("all offline tests passed")
