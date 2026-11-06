#!/usr/bin/env python3
"""Evaluering av Låtskriver: blir tekstene bedre eller dårligere mellom versjoner?

Ingen API og ingen nøkkel. Tekstene lager du i Claude som vanlig, og
skriptet måler dem og lager en blindtest.

  python3 eval/evaluer.py ny --navn v2.6          # lag mappe og bestillingsliste
  (lim inn Låtskriver.md + hver brief i Claude, lagre svarene i svar/)
  python3 eval/evaluer.py poeng --navn v2.6       # rim-bm-tall og harde krav
  python3 eval/evaluer.py sammenlign v2.6 v2.7    # tabell + blind-ab.md
  python3 eval/evaluer.py stemmer v2.6 v2.7       # tell stemmene dine fra blind-ab.md
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import random
import re
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "eval"
RIM_BM = ROOT / "dicts" / "rim-bm"
RESULTATER = EVAL / "resultater"

# Funn fra rim-bm --sjekk som teller som regelbrudd. Uttale og merker er
# veiledende og varierer med profil, så de rapporteres hver for seg.
BRUDD = {"gjentakelse", "vers", "refreng", "avkorting", "gjenbruk", "ekko"}
# «ho» og «me» finnes også i bokmålstalemål, så de er ikke med.
NYNORSK = {"ikkje", "eg", "kva", "korleis", "berre", "heime", "kvifor", "noko", "dykk",
           "frå", "eit", "ein", "mykje", "saman", "fekk"}

SEKSJON = re.compile(r"^\s*\[[^\]]+\]\s*$")
TELLING = re.compile(r"[\s(—–-]+\d{1,2}\)?\s*$")
ORD = re.compile(r"[A-Za-zÆØÅæøåÉéÜü']+")


# ---------------------------------------------------------------- tekst

def systemprompt(path: Path) -> str:
    """Instruksjonen er teksten under første linje som bare er «---»."""
    text = path.read_text(encoding="utf-8")
    deler = re.split(r"^---\s*$", text, maxsplit=1, flags=re.M)
    return (deler[1] if len(deler) == 2 else text).strip()


def kodeblokker(svar: str) -> list[str]:
    return re.findall(r"```[^\n]*\n(.*?)```", svar, flags=re.S)


def _har_telling(blokk: str) -> bool:
    linjer = [l for l in blokk.splitlines() if l.strip() and not SEKSJON.match(l)]
    return bool(linjer) and sum(bool(TELLING.search(l)) for l in linjer) > len(linjer) / 2


def finn_tekst(svar: str) -> str | None:
    """Plukk ut sangteksten (pass tre) fra et fullt svar.

    Velger den lengste kodeblokka med seksjonsmerker og uten stavelsestall.
    Finnes bare blokker med telling (for eksempel «bare refreng»), fjernes
    tellingen fra den lengste.
    """
    blokker = [b for b in kodeblokker(svar) if any(SEKSJON.match(l) for l in b.splitlines())]
    if not blokker:
        return None
    rene = [b for b in blokker if not _har_telling(b)]
    if rene:
        valgt = max(rene, key=lambda b: len(b.splitlines()))
    else:
        valgt = max(blokker, key=lambda b: len(b.splitlines()))
        valgt = "\n".join(TELLING.sub("", l) for l in valgt.splitlines())
    return valgt.strip() + "\n"


def _norm(linje: str) -> str:
    return " ".join(linje.strip().split())


# ---------------------------------------------------------------- rim-bm

def kjor_rim_bm(tekst: str, profil: str) -> dict:
    with tempfile.NamedTemporaryFile("w", suffix=".txt", encoding="utf-8", delete=False) as f:
        f.write(tekst)
        sti = f.name
    try:
        res = subprocess.run(
            [sys.executable, str(RIM_BM), "--tekst", sti, "--sjekk", "--profil", profil, "--json"],
            capture_output=True, text=True, encoding="utf-8", cwd=ROOT,
        )
    finally:
        os.unlink(sti)
    if res.returncode != 0:
        raise RuntimeError(f"rim-bm feilet: {res.stderr.strip()}")
    return json.loads(res.stdout)


def metrikker(rapport: dict, tekst: str, brief: dict) -> dict:
    """Tall fra én tekst. Ren funksjon, testbar uten nettverk."""
    # Gjentatte refreng teller én gang, så de ikke blåser opp rimandelen.
    seksjoner, sett = [], set()
    for sek in rapport.get("seksjoner", []):
        nokkel = tuple(_norm(l["tekst"]) for l in sek["linjer"])
        if nokkel in sett:
            continue
        sett.add(nokkel)
        seksjoner.append(sek)

    linjer = rimet = multi = innrim = assonans = 0
    for sek in seksjoner:
        rimbokstaver = {l["bokstav"] for l in sek["linjer"] if l.get("type") == "treff"}
        for l in sek["linjer"]:
            linjer += 1
            rimet += l["bokstav"] in rimbokstaver
            multi += bool(l.get("multi") or l.get("flerord"))
            innrim += bool(l.get("innrim"))
            assonans += l.get("type") == "assonans"

    funn: dict[str, int] = {}
    for f in rapport.get("sjekk", []):
        funn[f["type"]] = funn.get(f["type"], 0) + 1

    ord_ = [w.lower() for w in ORD.findall(tekst)]
    m = {
        "linjer": linjer,
        "rimandel": round(rimet / linjer, 3) if linjer else 0.0,
        "multi_innrim_per_4": round(4 * (multi + innrim) / linjer, 3) if linjer else 0.0,
        "assonansandel": round(assonans / linjer, 3) if linjer else 0.0,
        "regelbrudd": sum(n for t, n in funn.items() if t in BRUDD),
        "uttalefunn": funn.get("uttale", 0),
        "funn": funn,
        "tall_i_linje": sum("Tall i linja" in w for w in rapport.get("advarsler", [])),
        "nynorsk": sum(w in NYNORSK for w in ord_),
        "ellipse": bool(re.search(r"\.\.\.|…|\bosv\b", tekst)),
    }
    linjesett = {_norm(l) for l in tekst.splitlines()}
    if brief.get("laste_linjer"):
        bevart = sum(_norm(l) in linjesett for l in brief["laste_linjer"])
        m["laste_bevart"] = round(bevart / len(brief["laste_linjer"]), 3)
    if brief.get("fjernes"):
        m["svake_fjernet"] = round(sum(_norm(l) not in linjesett for l in brief["fjernes"]) / len(brief["fjernes"]), 3)
    if brief.get("ingen_vers"):
        m["ingen_vers"] = not re.search(r"^\s*\[(verse|vers)", tekst, flags=re.I | re.M)
    return m


def bestatt(m: dict) -> bool:
    """Harde krav: brudd her er feil uansett smak."""
    ok = not m["ellipse"] and m["nynorsk"] == 0 and m["tall_i_linje"] == 0
    ok = ok and m.get("laste_bevart", 1.0) == 1.0 and m.get("ingen_vers", True)
    return ok


# ---------------------------------------------------------------- kommandoer

def last_briefer(ider: list[str] | None = None) -> list[dict]:
    alle = json.loads((EVAL / "briefer.json").read_text(encoding="utf-8"))
    if ider:
        ukjente = set(ider) - {b["id"] for b in alle}
        if ukjente:
            sys.exit(f"Ukjente briefer: {', '.join(sorted(ukjente))}")
        alle = [b for b in alle if b["id"] in ider]
    return alle


def _vis(sti: Path) -> str:
    return str(sti.relative_to(ROOT)) if sti.is_relative_to(ROOT) else str(sti)


def ny(args) -> None:
    prompt = Path(args.prompt).resolve()
    mappe = RESULTATER / args.navn
    svar = mappe / "svar"
    svar.mkdir(parents=True, exist_ok=True)
    meta = {
        "navn": args.navn,
        "prompt": _vis(prompt),
        "prompt_sha256": hashlib.sha256(systemprompt(prompt).encode()).hexdigest()[:12],
        "n": args.n,
        "dato": dt.date.today().isoformat(),
        "modell": args.modell,
    }
    (mappe / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    ut = [f"# Bestillinger for {args.navn}", "",
          f"Prompt: `{meta['prompt']}` (sha {meta['prompt_sha256']}).", "",
          "For hver fil under: start en **ny** samtale i Claude, lim inn instruksjonen fra "
          f"`{meta['prompt']}` (alt under streken), og send bestillingen som neste melding. "
          f"Lim hele svaret inn i fila i `{_vis(svar)}/`. Bruk samme modell for alle tekstene.", ""]
    for b in last_briefer():
        for i in range(1, args.n + 1):
            fil = svar / f"{b['id']}-{i}.md"
            status = "ferdig" if fil.exists() and fil.read_text(encoding="utf-8").strip() else "mangler"
            ut += [f"## {fil.name} ({status})", "", "```", b["brief"], "```", ""]
    (mappe / "BESTILLINGER.md").write_text("\n".join(ut), encoding="utf-8")
    print(f"Lagde {_vis(mappe / 'BESTILLINGER.md')}")


def poeng(args) -> None:
    mappe = RESULTATER / args.navn
    if not (mappe / "svar").is_dir():
        sys.exit(f"Fant ikke {_vis(mappe / 'svar')}. Kjør «ny --navn {args.navn}» først.")
    rader, mangler = [], []
    for b in last_briefer():
        filer = sorted((mappe / "svar").glob(f"{b['id']}-*.md"))
        if not filer:
            mangler.append(b["id"])
        for svarfil in filer:
            svar = svarfil.read_text(encoding="utf-8")
            if not svar.strip():
                mangler.append(svarfil.stem)
                continue
            i = int(svarfil.stem.rsplit("-", 1)[1])
            tekst = finn_tekst(svar)
            rad = {"brief": b["id"], "i": i, "tekst_funnet": tekst is not None}
            if tekst is not None:
                (mappe / "tekster").mkdir(exist_ok=True)
                (mappe / "tekster" / f"{b['id']}-{i}.txt").write_text(tekst, encoding="utf-8")
                m = metrikker(kjor_rim_bm(tekst, b["profil"]), tekst, b)
                rad["metrikker"] = m
                rad["bestatt"] = bestatt(m)
            rader.append(rad)
    (mappe / "poeng.json").write_text(json.dumps(rader, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tekst = rapport(args.navn, rader, mangler)
    (mappe / "rapport.md").write_text(tekst, encoding="utf-8")
    print(tekst)


# ---------------------------------------------------------------- rapport

TALL = [  # (nøkkel, visningsnavn, høyere er bedre)
    ("rimandel", "Rimandel", True),
    ("multi_innrim_per_4", "Multi/innrim per 4 linjer", True),
    ("regelbrudd", "Regelbrudd (rim-bm)", False),
    ("uttalefunn", "Uttalefunn", False),
    ("nynorsk", "Nynorskord", False),
]


def sammendrag(rader: list[dict]) -> dict:
    ok = [r for r in rader if r.get("tekst_funnet")]
    s = {"tekster": len(rader), "uten_tekst": len(rader) - len(ok),
         "bestatt": sum(bool(r.get("bestatt")) for r in ok)}
    for k, _, _ in TALL:
        verdier = [r["metrikker"][k] for r in ok]
        s[k] = round(statistics.mean(verdier), 3) if verdier else None
    return s


def rapport(navn: str, rader: list[dict], mangler: list[str] | None = None) -> str:
    s = sammendrag(rader)
    ut = [f"# Evaluering: {navn}", "",
          f"{s['tekster']} tekster, {s['bestatt']} besto de harde kravene, {s['uten_tekst']} uten funnet sangtekst.", ""]
    if mangler:
        ut += [f"Mangler svar: {', '.join(mangler)}.", ""]
    ut += ["| Mål | Verdi |", "|---|---|"]
    for k, vis, _ in TALL:
        ut.append(f"| {vis} | {s[k]} |")
    ut += ["", "## Per tekst", "", "| Tekst | Bestått | Rimandel | Brudd | Merknad |", "|---|---|---|---|---|"]
    for r in sorted(rader, key=lambda r: (r["brief"], r["i"])):
        if not r.get("tekst_funnet"):
            ut.append(f"| {r['brief']}-{r['i']} | – | – | – | fant ingen sangtekst |")
            continue
        m = r["metrikker"]
        merk = []
        if m["ellipse"]:
            merk.append("«...»")
        if m["nynorsk"]:
            merk.append(f"{m['nynorsk']} nynorskord")
        if m["tall_i_linje"]:
            merk.append("tall i linje")
        if m.get("laste_bevart", 1.0) < 1.0:
            merk.append(f"låste linjer bevart {m['laste_bevart']}")
        if m.get("ingen_vers") is False:
            merk.append("skrev vers")
        ut.append(f"| {r['brief']}-{r['i']} | {'ja' if r['bestatt'] else '**nei**'} | {m['rimandel']} "
                  f"| {m['regelbrudd']} | {', '.join(merk)} |")
    return "\n".join(ut) + "\n"


def _sammenligningsmappe(a: str, b: str) -> Path:
    return RESULTATER / f"{a}-mot-{b}"


def sammenlign(args) -> None:
    a_mappe, b_mappe = RESULTATER / args.a, RESULTATER / args.b
    for m in (a_mappe, b_mappe):
        if not (m / "poeng.json").exists():
            sys.exit(f"Fant ikke {_vis(m / 'poeng.json')}. Kjør «poeng --navn {m.name}» først.")
    sa = sammendrag(json.loads((a_mappe / "poeng.json").read_text(encoding="utf-8")))
    sb = sammendrag(json.loads((b_mappe / "poeng.json").read_text(encoding="utf-8")))
    ut_mappe = _sammenligningsmappe(args.a, args.b)
    ut_mappe.mkdir(parents=True, exist_ok=True)

    linjer = [f"# {args.a} mot {args.b}", "", f"| Mål | {args.a} | {args.b} | Endring |", "|---|---|---|---|"]

    def rad(vis, k, hoy):
        va, vb = sa.get(k), sb.get(k)
        if va is None or vb is None:
            return
        diff = round(vb - va, 3)
        tegn = "" if diff == 0 else ("bedre" if (diff > 0) == hoy else "dårligere")
        linjer.append(f"| {vis} | {va} | {vb} | {diff:+} {tegn} |")

    rad("Besto harde krav", "bestatt", True)
    for k, vis, hoy in TALL:
        rad(vis, k, hoy)

    # Blindtest: samme brief og nummer, tilfeldig rekkefølge, nøkkel i egen fil.
    tekster = {}
    for navn, mappe in ((args.a, a_mappe), (args.b, b_mappe)):
        for f in (mappe / "tekster").glob("*.txt"):
            tekster[(navn, f.stem)] = f.read_text(encoding="utf-8")
    felles = sorted({k for (n, k) in tekster if n == args.a} & {k for (n, k) in tekster if n == args.b})
    briefer = {b["id"]: b for b in last_briefer()}
    rng = random.Random(args.frø)
    par = []
    for stem in felles:
        forst, sist = (args.b, args.a) if rng.random() < 0.5 else (args.a, args.b)
        par.append({"tekst": stem, "1": forst, "2": sist})

    ark = ["# Blindtest", "",
           "Les begge tekstene for hver bestilling og skriv 1, 2 eller = bak «Valg:». "
           "Se `eval/rubrikk.md` for hva du kan se etter. Ikke åpne `nokkel.json` før du er ferdig. "
           f"Tell opp med `python3 eval/evaluer.py stemmer {args.a} {args.b}`.", ""]
    for p in par:
        brief = briefer[p["tekst"].rsplit("-", 1)[0]]["brief"]
        ark += [f"## {p['tekst']}", "", "> " + brief.replace("\n", "\n> "), "",
                "### Tekst 1", "```", tekster[(p["1"], p["tekst"])].rstrip(), "```", "",
                "### Tekst 2", "```", tekster[(p["2"], p["tekst"])].rstrip(), "```", "", "Valg: ", ""]
    (ut_mappe / "blind-ab.md").write_text("\n".join(ark), encoding="utf-8")
    (ut_mappe / "nokkel.json").write_text(json.dumps(par, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    linjer += ["", f"{len(par)} par i blindtesten: `{_vis(ut_mappe / 'blind-ab.md')}`."]
    tekst = "\n".join(linjer) + "\n"
    (ut_mappe / "rapport.md").write_text(tekst, encoding="utf-8")
    print(tekst)


VALG = re.compile(r"^## (\S+)\s*$|^Valg:\s*(\S*)", re.M)


def stemmer(args) -> None:
    mappe = _sammenligningsmappe(args.a, args.b)
    nokkel = {p["tekst"]: p for p in json.loads((mappe / "nokkel.json").read_text(encoding="utf-8"))}
    ark = (mappe / "blind-ab.md").read_text(encoding="utf-8")
    telling = {args.a: 0, args.b: 0, "uavgjort": 0}
    ubesvart, per_tekst, gjeldende = [], [], None
    for overskrift, valg in VALG.findall(ark):
        if overskrift:
            gjeldende = overskrift
            continue
        if gjeldende not in nokkel:
            continue
        v = valg.strip().rstrip(".")
        if v in ("1", "2"):
            vinner = nokkel[gjeldende][v]
        elif v in ("=", "uavgjort", "u"):
            vinner = "uavgjort"
        else:
            ubesvart.append(gjeldende)
            continue
        telling[vinner] += 1
        per_tekst.append((gjeldende, vinner))
    svart = len(per_tekst)
    ut = [f"# Dine stemmer: {args.a} mot {args.b}", "",
          f"{args.b} vant {telling[args.b]}, {args.a} vant {telling[args.a]}, uavgjort {telling['uavgjort']} (av {svart}).", ""]
    if ubesvart:
        ut += [f"Ikke besvart: {', '.join(ubesvart)}.", ""]
    ut += ["| Tekst | Vinner |", "|---|---|"] + [f"| {t} | {v} |" for t, v in per_tekst]
    tekst = "\n".join(ut) + "\n"
    (mappe / "stemmer.md").write_text(tekst, encoding="utf-8")
    print(tekst)


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="kommando", required=True)

    k = sub.add_parser("ny", help="lag mappe og bestillingsliste for en versjon")
    k.add_argument("--navn", required=True, help="navn på versjonen, for eksempel v2.6")
    k.add_argument("--prompt", default=str(ROOT / "Låtskriver.md"))
    k.add_argument("-n", type=int, default=2, help="tekster per brief (standard 2)")
    k.add_argument("--modell", default="", help="hvilken Claude-modell du bruker, for notatet")
    k.set_defaults(fn=ny)

    q = sub.add_parser("poeng", help="mål svarene med rim-bm og harde krav")
    q.add_argument("--navn", required=True)
    q.set_defaults(fn=poeng)

    s = sub.add_parser("sammenlign", help="sammenlign to versjoner og lag blindtest")
    s.add_argument("a", help="gammel versjon")
    s.add_argument("b", help="ny versjon")
    s.add_argument("--frø", type=int, default=1, help="frø for tilfeldig rekkefølge")
    s.set_defaults(fn=sammenlign)

    t = sub.add_parser("stemmer", help="tell stemmene dine fra blind-ab.md")
    t.add_argument("a")
    t.add_argument("b")
    t.set_defaults(fn=stemmer)

    args = p.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
