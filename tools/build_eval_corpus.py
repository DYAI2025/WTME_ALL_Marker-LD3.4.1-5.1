#!/usr/bin/env python3
"""
build_eval_corpus.py — Build anonymized eval corpus from WhatsApp exports.

Sources:
  1. GitHub repo DYAI2025/RelationshipZB19-25 (German chunks, ~1609 files)
  2. Same repo ready_chunks/ (English chunks, 63 files)
  3. Same repo Email_austausch_ZB.md (German emails)

Output:
  eval/gold_corpus.jsonl  — one JSON object per chunk with parsed messages
  eval/gold_emails.jsonl  — one JSON object per email

Usage:
  python3 tools/build_eval_corpus.py                          # Dry run (stats only)
  python3 tools/build_eval_corpus.py --build                  # Clone repo + build corpus
  python3 tools/build_eval_corpus.py --build --repo-path /path/to/repo  # Use local clone
  python3 tools/build_eval_corpus.py --build --skip-clone     # Reuse /tmp clone
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EVAL_DIR = REPO / "eval"
OUTPUT_CORPUS = EVAL_DIR / "gold_corpus.jsonl"
OUTPUT_EMAILS = EVAL_DIR / "gold_emails.jsonl"

GITHUB_REPO = "DYAI2025/RelationshipZB19-25"
DEFAULT_CLONE_PATH = Path("/tmp/RelationshipZB19-25")

# ---------------------------------------------------------------------------
# Anonymization Map
# ---------------------------------------------------------------------------
# Order matters: longer names first to avoid partial replacement
NAME_MAP = [
    # Full names first (longest match first)
    ("Zoe Leandra Nagel", "Person_B"),
    ("Zoe Leandra", "Person_B"),
    ("Ben Poersch", "Person_A"),
    ("Daniel De Cock", "Person_C"),
    # Surnames alone
    ("Poersch", "Person_A"),
    ("Nagel", "Person_B"),
    ("De Cock", "Person_C"),
    # First names / variants
    ("Zoé", "Person_B"),
    ("Zoe", "Person_B"),
    ("Ben", "Person_A"),
    ("Benny", "Person_A"),
    ("Daniel", "Person_C"),
]

# Third-party names (discovered from data — add more as found)
THIRD_PARTY_NAMES = [
    ("Jobst", "Person_D"),
    ("Dagmar", "Person_E"),
    ("Stefan", "Person_F"),
    ("Nick", "Person_G"),
]

# Regex patterns for PII
PII_PATTERNS = [
    # Email addresses
    (re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+'), '[EMAIL]'),
    # Phone numbers (German/international formats)
    (re.compile(r'(?:\+\d{1,3}[\s-]?)?\(?\d{2,5}\)?[\s.-]?\d{3,}[\s.-]?\d{2,}'), '[PHONE]'),
    # Google Maps URLs
    (re.compile(r'https?://maps\.google\.com/\S+'), '[LOCATION_URL]'),
    (re.compile(r'https?://goo\.gl/maps/\S+'), '[LOCATION_URL]'),
    # WhatsApp location shares
    (re.compile(r'Standort: https?://\S+'), 'Standort: [LOCATION_URL]'),
]

# WhatsApp system messages to strip
SYSTEM_PATTERNS = [
    re.compile(r'.*Nachrichten und Anrufe sind Ende-zu-Ende-verschlüsselt.*'),
    re.compile(r'.*hat diese Gruppe erstellt.*'),
    re.compile(r'.*hat das Gruppenbild geändert.*'),
    re.compile(r'.*wurde hinzugefügt.*'),
    re.compile(r'.*hat die Gruppe verlassen.*'),
    re.compile(r'.*Sicherheitsnummer.*geändert.*'),
]

# WhatsApp media placeholders
MEDIA_PATTERN = re.compile(
    r'‎?(Bild|Video|Audio|GIF|Sticker|Dokument) weggelassen'
    r'|‎?<Anhang: [^>]+>'
    r'|‎?Sprachanruf\..*'
    r'|‎?Videoanruf\..*'
    r'|‎?Verpasster Sprachanruf.*'
    r'|‎?Verpasster Videoanruf.*'
    r'|‎?Du hast diese Nachricht gelöscht.*'
    r'|‎?Diese Nachricht wurde gelöscht.*'
)


def anonymize_text(text: str) -> str:
    """Replace all PII in text with anonymous placeholders."""
    # Names — two passes: first compound-safe (no word boundary), then word-boundary
    # Pass 1: Always replace surnames and long names (case-insensitive for email/compound matches)
    for name, replacement in NAME_MAP + THIRD_PARTY_NAMES:
        if len(name) >= 5:
            text = re.sub(re.escape(name), replacement, text, flags=re.IGNORECASE)
    # Pass 2: Short names with word boundary to avoid substring matches (case-sensitive)
    for name, replacement in NAME_MAP + THIRD_PARTY_NAMES:
        if len(name) < 5:
            text = re.sub(rf'\b{re.escape(name)}\b', replacement, text)

    # PII regex patterns
    for pattern, replacement in PII_PATTERNS:
        text = pattern.sub(replacement, text)

    return text


def anonymize_speaker(speaker: str) -> str:
    """Anonymize speaker name."""
    for name, replacement in NAME_MAP:
        if name in speaker:
            return replacement
    return speaker


def is_system_message(text: str) -> bool:
    """Check if message is a WhatsApp system message."""
    for pat in SYSTEM_PATTERNS:
        if pat.match(text):
            return True
    return False


def is_media_only(text: str) -> bool:
    """Check if message is only a media placeholder."""
    stripped = text.strip()
    if not stripped:
        return True
    return bool(MEDIA_PATTERN.fullmatch(stripped))


# ---------------------------------------------------------------------------
# WhatsApp Chunk Parser
# ---------------------------------------------------------------------------
# Format: [[DD.MM.YY, HH]\nMM:SS] Speaker: message
# Continuation lines don't start with MM:SS]

# Matches the start of a new timestamp block
BLOCK_START = re.compile(r'^\[\[(\d{2}\.\d{2}\.\d{2}),\s*(\d{1,2})\]$')
# Matches a message line within a block
MSG_LINE = re.compile(r'^(\d{2}:\d{2})\]\s*(.+?):\s*(.*)$')
# Matches single-line timestamp format (original exports)
SINGLE_LINE = re.compile(r'^\[?‎?\[?(\d{2}\.\d{2}\.\d{2}),\s*(\d{1,2}:\d{2}:\d{2})\]\s*(.+?):\s*(.*)$')


def parse_whatsapp_chunk(text: str) -> list[dict]:
    """Parse a WhatsApp chunk into structured messages."""
    messages = []
    lines = text.split('\n')
    i = 0
    current_hour = None
    current_date = None

    while i < len(lines):
        line = lines[i].rstrip()

        # Check for block start: [[DD.MM.YY, HH]
        block_match = BLOCK_START.match(line)
        if block_match:
            current_date = block_match.group(1)
            current_hour = block_match.group(2)
            i += 1
            continue

        # Check for message line: MM:SS] Speaker: text
        msg_match = MSG_LINE.match(line)
        if msg_match and current_date and current_hour:
            min_sec = msg_match.group(1)
            speaker = msg_match.group(2).strip()
            text_content = msg_match.group(3)

            # Collect continuation lines
            i += 1
            while i < len(lines):
                next_line = lines[i].rstrip()
                if not next_line:
                    i += 1
                    continue
                # Stop if next line is a new message or block start
                if MSG_LINE.match(next_line) or BLOCK_START.match(next_line):
                    break
                # Stop if it's a single-line format
                if SINGLE_LINE.match(next_line):
                    break
                text_content += '\n' + next_line
                i += 1

            # Clean up
            text_content = text_content.strip()
            # Remove left-to-right mark
            text_content = text_content.replace('\u200e', '')
            speaker = speaker.replace('\u200e', '')

            if is_system_message(text_content):
                continue
            if is_media_only(text_content):
                continue

            timestamp = f"{current_date} {current_hour}:{min_sec}"
            messages.append({
                "speaker": anonymize_speaker(speaker),
                "text": anonymize_text(text_content),
                "timestamp": timestamp,
            })
            continue

        # Check for single-line format: [DD.MM.YY, HH:MM:SS] Speaker: text
        single_match = SINGLE_LINE.match(line)
        if single_match:
            date = single_match.group(1)
            time = single_match.group(2)
            speaker = single_match.group(3).strip()
            text_content = single_match.group(4)

            i += 1
            while i < len(lines):
                next_line = lines[i].rstrip()
                if not next_line:
                    i += 1
                    continue
                if SINGLE_LINE.match(next_line) or BLOCK_START.match(next_line) or MSG_LINE.match(next_line):
                    break
                text_content += '\n' + next_line
                i += 1

            text_content = text_content.strip().replace('\u200e', '')
            speaker = speaker.replace('\u200e', '')

            if is_system_message(text_content):
                continue
            if is_media_only(text_content):
                continue

            messages.append({
                "speaker": anonymize_speaker(speaker),
                "text": anonymize_text(text_content),
                "timestamp": f"{date} {time}",
            })
            continue

        i += 1

    return messages


# ---------------------------------------------------------------------------
# Email Parser
# ---------------------------------------------------------------------------
def parse_emails(text: str) -> list[dict]:
    """Parse email markdown into structured email entries."""
    emails = []
    # Split on email header patterns
    # Headers look like: "zl. <email>\nFr., 8. Aug., 00:22\nan mich"
    # or "B. P. <email>\nSa., 9. Aug., 01:09\nan Z."
    sections = re.split(r'\n(?=[A-Za-zÀ-ÿ][\w. ]*<[\w.@]+>)', text)

    for section in sections:
        section = section.strip()
        if len(section) < 50:
            continue

        # Try to extract sender from header
        header_match = re.match(r'(.+?)<[\w.@]+>', section)
        sender = "unknown"
        if header_match:
            raw_sender = header_match.group(1).strip()
            sender = anonymize_speaker(raw_sender) if raw_sender else "unknown"
            # For initials like "B." or "B. P."
            if re.match(r'^[A-Z]\.(\s*[A-Z]\.)*$', raw_sender):
                if 'B' in raw_sender:
                    sender = "Person_A"
                elif 'Z' in raw_sender or 'z' in raw_sender:
                    sender = "Person_B"

        # Get body (after "an mich" or "an ..." line)
        body_match = re.search(r'\nan\s+\w+.*?\n\n(.+)', section, re.DOTALL)
        body = body_match.group(1).strip() if body_match else section

        body = anonymize_text(body)

        if len(body) > 20:
            emails.append({
                "sender": sender,
                "text": body,
                "type": "email",
            })

    return emails


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def clone_repo(clone_path: Path) -> bool:
    """Clone the GitHub repo if not already present."""
    if clone_path.exists() and (clone_path / ".git").exists():
        print(f"  Repo already cloned at {clone_path}", file=sys.stderr)
        subprocess.run(["git", "-C", str(clone_path), "pull", "-q"], check=False)
        return True

    print(f"  Cloning {GITHUB_REPO} to {clone_path}...", file=sys.stderr)
    result = subprocess.run(
        ["gh", "repo", "clone", GITHUB_REPO, str(clone_path)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"  ERROR: Clone failed: {result.stderr}", file=sys.stderr)
        return False
    return True


def collect_chunks(repo_path: Path) -> list[tuple[str, str, str]]:
    """Collect all chunk files. Returns [(filepath, chunk_id, lang), ...]"""
    chunks = []
    chunk_dirs = ["01-249", "250-499", "500-699", "700-899", "900-1102", "1003-1199", "1200-end"]

    # German chunks
    for dir_name in chunk_dirs:
        dir_path = repo_path / dir_name
        if not dir_path.exists():
            continue
        for f in sorted(dir_path.glob("_chat_ch*.txt")):
            # Extract chunk number
            match = re.search(r'ch(\d+)', f.name)
            chunk_id = f"de_{match.group(1).zfill(4)}" if match else f"de_{f.stem}"
            chunks.append((str(f), chunk_id, "de"))

    # English chunks (ready_chunks/)
    ready_dir = repo_path / "ready_chunks"
    if ready_dir.exists():
        for f in sorted(ready_dir.glob("_chat_merged_ch*.txt")):
            match = re.search(r'ch(\d+)', f.name)
            chunk_id = f"en_{match.group(1).zfill(4)}" if match else f"en_{f.stem}"
            chunks.append((str(f), chunk_id, "en"))

    return chunks


def main():
    parser = argparse.ArgumentParser(description="Build anonymized eval corpus")
    parser.add_argument("--build", action="store_true", help="Actually build the corpus (default: dry run)")
    parser.add_argument("--repo-path", type=str, help="Path to local repo clone")
    parser.add_argument("--skip-clone", action="store_true", help="Skip cloning, use /tmp clone")
    args = parser.parse_args()

    repo_path = Path(args.repo_path) if args.repo_path else DEFAULT_CLONE_PATH

    # Step 1: Get repo
    if not args.skip_clone and not args.repo_path:
        if not args.build:
            print("DRY RUN — use --build to actually build the corpus\n", file=sys.stderr)
            repo_path = DEFAULT_CLONE_PATH
            if not repo_path.exists():
                print(f"  Repo not found at {repo_path}. Run with --build to clone.", file=sys.stderr)
                return
        else:
            if not clone_repo(repo_path):
                return

    if not repo_path.exists():
        print(f"ERROR: Repo path {repo_path} does not exist", file=sys.stderr)
        return

    # Step 2: Collect chunks
    chunks = collect_chunks(repo_path)
    print(f"\n{'='*55}")
    print(f"  EVAL CORPUS BUILDER")
    print(f"{'='*55}\n")
    print(f"  Source: {repo_path}")
    print(f"  Chunks found: {len(chunks)}")

    de_chunks = [c for c in chunks if c[2] == "de"]
    en_chunks = [c for c in chunks if c[2] == "en"]
    print(f"    German: {len(de_chunks)}")
    print(f"    English: {len(en_chunks)}")

    # Step 3: Parse and anonymize
    total_messages = 0
    total_chars = 0
    empty_chunks = 0
    corpus_entries = []

    for filepath, chunk_id, lang in chunks:
        with open(filepath, 'r', encoding='utf-8') as f:
            raw_text = f.read()

        messages = parse_whatsapp_chunk(raw_text)

        if not messages:
            empty_chunks += 1
            continue

        msg_count = len(messages)
        char_count = sum(len(m["text"]) for m in messages)
        total_messages += msg_count
        total_chars += char_count

        entry = {
            "id": chunk_id,
            "lang": lang,
            "message_count": msg_count,
            "messages": messages,
        }
        corpus_entries.append(entry)

    print(f"\n  Parsed chunks: {len(corpus_entries)}")
    print(f"  Empty/media-only chunks: {empty_chunks}")
    print(f"  Total messages: {total_messages:,}")
    print(f"  Total characters: {total_chars:,}")
    print(f"  Avg messages/chunk: {total_messages / max(len(corpus_entries), 1):.1f}")

    # Step 4: Parse emails
    email_path = repo_path / "Email_austausch_ZB.md"
    email_entries = []
    if email_path.exists():
        with open(email_path, 'r', encoding='utf-8') as f:
            email_text = f.read()
        email_entries = parse_emails(email_text)
        email_chars = sum(len(e["text"]) for e in email_entries)
        print(f"\n  Emails parsed: {len(email_entries)}")
        print(f"  Email characters: {email_chars:,}")

    # Step 5: Check anonymization quality
    print(f"\n  --- Anonymization Check ---")
    leak_count = 0
    leak_names = set()
    for entry in corpus_entries:
        for msg in entry["messages"]:
            full_text = msg["speaker"] + " " + msg["text"]
            for name, _ in NAME_MAP:
                if len(name) > 3 and name in full_text:
                    leak_count += 1
                    leak_names.add(name)
    if leak_count == 0:
        print(f"  OK: No PII name leaks detected in corpus")
    else:
        print(f"  WARNING: {leak_count} potential name leaks: {leak_names}")

    # Step 6: Write output
    if args.build:
        EVAL_DIR.mkdir(parents=True, exist_ok=True)

        with open(OUTPUT_CORPUS, 'w', encoding='utf-8') as f:
            for entry in corpus_entries:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        print(f"\n  Written: {OUTPUT_CORPUS} ({len(corpus_entries)} entries)")

        if email_entries:
            with open(OUTPUT_EMAILS, 'w', encoding='utf-8') as f:
                for entry in email_entries:
                    f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            print(f"  Written: {OUTPUT_EMAILS} ({len(email_entries)} entries)")

        print(f"\n  Corpus ready for evaluation.")
        print(f"  Run: python3 -m uvicorn api.main:app --port 8420")
        print(f"  Then: python3 tools/eval_corpus.py")
    else:
        print(f"\n  DRY RUN complete. Use --build to write files.")


if __name__ == "__main__":
    main()
