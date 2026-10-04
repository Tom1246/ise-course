#!/usr/bin/env python3
"""Count the words of the platform submission summary.

Usage:
    python3 scripts/count_words.py [doc/assignments/a1/A1-summary-en-2026-09-28.md]

The English summary submitted on learn.spaiq.ai must be 150-300 words.  This
script counts the words between the SUMMARY-EN markers in the file, so the
number can be checked and re-checked in one command (the brief requires a
verifiable count, not a guess).
"""
import re, sys, os

START = "<!-- SUMMARY-EN-START -->"
END = "<!-- SUMMARY-EN-END -->"


def count(path="doc/assignments/a1/A1-summary-en-2026-09-28.md"):
    if not os.path.exists(path):
        print(f"[!] not found: {path}")
        return 2
    text = open(path, encoding="utf-8").read()
    if START not in text or END not in text:
        print(f"[!] markers {START} / {END} not found in {path}")
        return 2
    body = text.split(START, 1)[1].split(END, 1)[0]
    words = [w for w in re.findall(r"[A-Za-z0-9][A-Za-z0-9'\-\./,]*", body)]
    n = len(words)
    verdict = "OK (150-300)" if 150 <= n <= 300 else "OUT OF RANGE"
    print(f"file        : {path}")
    print(f"word count  : {n}")
    print(f"requirement : 150-300 words -> {verdict}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        sys.exit(count(*sys.argv[1:]))
    # no argument: check every assignment summary in the repository
    import glob
    paths = sorted(glob.glob("doc/assignments/*/*summary*.md"))
    if not paths:
        print("[!] no summary found under doc/assignments/*/")
        sys.exit(2)
    rc = 0
    for p in paths:
        rc |= count(p)
        print()
    sys.exit(rc)
