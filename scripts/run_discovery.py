"""Orchestrator: run all discovery sources, merge, split catalog vs review queue.
Rule: an item enters catalog only if it has a GitHub repo or a website AND
a non-empty description. Everything else (bare X mentions, meme-rush rows
with no website/github) goes to review_queue.json.
Never invents contract addresses, prices or gains."""
import json, os, sys
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(__file__))
from common import load_json, save_json, merge_items
from discover_github import discover as gh_discover
from discover_official import discover as official_discover
from discover_x import discover as x_discover
from discover_meme_rush import discover as meme_discover

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def catalog_worthy(item):
    # meme-rush / x 只是线索：简介是模板、无可靠官网，永不直接进目录
    if item.get("source") in ("meme-rush", "x"):
        return False
    return bool(item.get("description")) and bool(item.get("github") or item.get("website"))

def main():
    all_items = []
    for name, fn in [("github", gh_discover), ("official", official_discover),
                     ("x", x_discover), ("meme-rush", meme_discover)]:
        try:
            got = fn()
            print(f"[{name}] {len(got)} items")
            all_items.extend(got)
        except Exception as e:
            print(f"[{name}] FAILED: {e}", file=sys.stderr)
    catalog = load_json(os.path.join(ROOT, "data/catalog.json"), {"items": []})
    queue = load_json(os.path.join(ROOT, "data/review_queue.json"), {"items": []})
    now = datetime.now(timezone.utc).isoformat()
    cat_items, cat_added = merge_items(catalog.get("items", []),
                                       [i for i in all_items if catalog_worthy(i)])
    q_items, q_added = merge_items(queue.get("items", []),
                                   [i for i in all_items if not catalog_worthy(i)])
    save_json(os.path.join(ROOT, "data/catalog.json"),
              {"generated_at": now, "items": cat_items})
    save_json(os.path.join(ROOT, "data/review_queue.json"),
              {"generated_at": now, "items": q_items})
    print(f"catalog: +{len(cat_added)} = {len(cat_items)}; queue: +{len(q_added)} = {len(q_items)}")

if __name__ == "__main__":
    main()
