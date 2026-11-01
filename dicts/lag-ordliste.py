#!/usr/bin/env python3
"""Lag former-utf8.txt på nytt fra Norsk ordbank (Språkbanken, CC-BY 4.0).

Bruk:
  python3 lag-ordliste.py                       # laster ned dumpen og bygger lista
  python3 lag-ordliste.py --dump ordbank.tar.gz # bruk en dump du allerede har

Lista får én bøyningsform per linje, med små bokstaver. Disse tas ut:
  - egennavn (tagg «prop»), forkortelser, symboler, prefikser og
    former som bare finnes i sammensetninger («i sms»)
  - former med bindestrek, tall, mellomrom eller andre tegn enn bokstaver
  - enkeltbokstaver
"""
from __future__ import annotations

import argparse
import io
import re
import sys
import tarfile
import urllib.request
from pathlib import Path

URL = "https://www.nb.no/sbfil/leksikalske_databaser/ordbank/20220201_norsk_ordbank_nob_2005.tar.gz"
HERE = Path(__file__).resolve().parent
DEFAULT_OUT = HERE / "norsk-ordbank-bm" / "former-utf8.txt"
SKIP_TAGS = ("prop", "fork", "symb", "i sms", "pref")
OK_WORD = re.compile(r"^[a-zæøåé]{2,}$")


def read_fullform(dump: Path) -> bytes:
    with tarfile.open(dump, "r:gz") as tar:
        for m in tar.getmembers():
            if m.name.endswith("fullformsliste.txt"):
                f = tar.extractfile(m)
                if f is None:
                    break
                return f.read()
    raise SystemExit("Fant ikke fullformsliste.txt i dumpen.")


def build(raw: bytes) -> list[str]:
    keep: set[str] = set()
    text = io.TextIOWrapper(io.BytesIO(raw), encoding="latin-1", newline="")
    next(text)  # overskrift
    for line in text:
        parts = line.rstrip("\r\n").split("\t")
        if len(parts) < 4:
            continue
        word, tag = parts[2].strip().lower(), parts[3]
        if any(t in tag for t in SKIP_TAGS):
            continue
        if OK_WORD.match(word):
            keep.add(word)
    return sorted(keep)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dump", type=Path, help="Sti til ordbank-dumpen (.tar.gz). Uten denne lastes den ned.")
    p.add_argument("--ut", type=Path, default=DEFAULT_OUT, help=f"Hvor lista skrives (standard: {DEFAULT_OUT})")
    args = p.parse_args()

    if args.dump:
        dump = args.dump
    else:
        dump = HERE / "norsk-ordbank-bm" / "ordbank.tar.gz"
        dump.parent.mkdir(parents=True, exist_ok=True)
        print(f"Laster ned {URL}", file=sys.stderr)
        urllib.request.urlretrieve(URL, dump)

    words = build(read_fullform(dump))
    args.ut.parent.mkdir(parents=True, exist_ok=True)
    args.ut.write_text("\n".join(words) + "\n", encoding="utf-8")
    print(f"Skrev {len(words)} former til {args.ut}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
