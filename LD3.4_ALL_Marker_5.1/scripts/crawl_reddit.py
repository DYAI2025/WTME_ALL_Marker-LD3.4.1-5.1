#!/usr/bin/env python3
import os
import time
import json
import yaml
import urllib.parse
import urllib.request
from typing import Any, Dict, List

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(REPO_ROOT)
SEEDS = os.path.join(REPO_ROOT, 'crawler', 'seeds.yaml')
OUT_DIR = os.path.join(REPO_ROOT, 'data', 'raw', 'reddit')

UA = 'LD34MarkerBot/1.0 (by u/example)'


def fetch_json(url: str) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode('utf-8'))


def main() -> int:
    with open(SEEDS, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f) or {}
    os.makedirs(OUT_DIR, exist_ok=True)

    red = (cfg.get('reddit') or {})
    subs: List[str] = red.get('subreddits') or []
    listing = red.get('listing', 'new')
    limit = int(red.get('limit', 50))

    results: List[Dict[str, Any]] = []
    for sub in subs:
        url = f"https://www.reddit.com/r/{urllib.parse.quote(sub)}/{listing}.json?limit={limit}"
        try:
            data = fetch_json(url)
        except Exception as e:
            print(f"WARN: {sub}: {e}")
            continue
        children = (((data or {}).get('data') or {}).get('children') or [])
        for ch in children:
            d = (ch or {}).get('data') or {}
            results.append({
                'id': d.get('id'),
                'subreddit': d.get('subreddit'),
                'title': d.get('title'),
                'selftext': d.get('selftext'),
                'created_utc': d.get('created_utc'),
                'permalink': f"https://reddit.com{d.get('permalink')}" if d.get('permalink') else None,
                'score': d.get('score'),
                'num_comments': d.get('num_comments'),
                'over_18': d.get('over_18'),
            })
        time.sleep(1.2)  # Rate‑Limit schonen

    ts = int(time.time())
    out_file = os.path.join(OUT_DIR, f"reddit_{listing}_{ts}.jsonl")
    with open(out_file, 'w', encoding='utf-8') as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"OK: {len(results)} posts → {out_file}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())


