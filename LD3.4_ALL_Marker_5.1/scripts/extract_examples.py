#!/usr/bin/env python3
import os
import json
import re
from typing import Dict, Any, List

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, 'data', 'raw', 'reddit')
OUT = os.path.join(REPO, 'Review-ccrawler.md')

KEYS = [
    (r'\bhappy\b|\bjoy\b|\bjoyful\b', 'ATO_JOY_EXPRESSION'),
    (r"\bi like\b|\bi love\b|\bprefer\w*\b", 'ATO_POSITIVE_PREFERENCE'),
    (r"\bproud of\b|\bsatisfied\b|\bfeel good\b", 'ATO_SATISFACTION_STATE'),
    (r"\boptimistic\b|\bhopeful\b|\bconfident\b", 'ATO_POSITIVE_OUTLOOK_CUE'),
    (r"\bhug\w*\b|\bkiss\w*\b|\bpraise\b|\bcompliment\w*\b|\baffection\b", 'ATO_REWARD_RESPONSE'),
    (r"\bsmil\w*\b|\blaugh\w*\b", 'ATO_NONVERBAL_JOY_VERB'),
    (r"\bhappy\b\s*[,;]?\s*when\b", 'SEM_STATE_OF_HAPPINESS'),
    (r"\bi like\b.*\b(run|play|cook|read|learn|work|train|hike|swim)\b|\b(run|play|cook|read|learn|work|train|hike|swim)\b.*\bi like\b", 'SEM_ACTIVE_ENJOYMENT'),
    (r"\bproud of\b|\bsatisfied with\b", 'SEM_EXPRESSED_SATISFACTION'),
    (r"\bpositive outlook\b|\boptimistic\b|\blooking forward\b|\bhopeful\b", 'SEM_POSITIVE_OUTLOOK'),
    (r"\b(smile|smiled|laugh|laughed)\b", 'SEM_REPORTED_NONVERBAL_JOY'),
    (r"\b(cheer myself up|make myself feel better|cultivat\w* gratitude|regulat\w* my emotions)\b", 'SEM_POSITIVE_EMOTION_REGULATION'),
]


def iter_jsonl(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue


def main() -> int:
    files = sorted([os.path.join(SRC, f) for f in os.listdir(SRC) if f.endswith('.jsonl')])
    if not files:
        print('No reddit jsonl found')
        return 1
    latest = files[-1]
    picks: List[Dict[str, Any]] = []
    seen_texts = set()
    for row in iter_jsonl(latest):
        text = ' '.join([(row.get('title') or ''), (row.get('selftext') or '')]).strip()
        text = re.sub(r'\s+', ' ', text)
        if not text or len(text) < 30:
            continue
        low = text.lower()
        for pat, marker in KEYS:
            if re.search(pat, low):
                key = (marker, low[:200])
                if key in seen_texts:
                    continue
                seen_texts.add(key)
                picks.append({
                    'marker': marker,
                    'text': text[:500] + ('…' if len(text) > 500 else ''),
                    'link': row.get('permalink') or ''
                })
                break
        if len(picks) >= 40:
            break

    lines: List[str] = []
    lines.append('## Kuratierte Beispiele aus dem Crawler (Reddit)')
    lines.append('')
    lines.append('- Hinweise: echte Nutzertexte, leicht gekürzt; Zuordnung zum vorgesehenen Marker steht jeweils voran.')
    lines.append('')
    for i, p in enumerate(picks, 1):
        link = p['link'] if p['link'] else ''
        lines.append(f"{i}. [{p['marker']}] {p['text']}")
        if link:
            lines.append(f"   - Link: {link}")
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"OK: {len(picks)} Beispiele → {OUT}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())


