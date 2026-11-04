#!/usr/bin/env python3
"""Evaluering av Låtskriver: blir tekstene bedre eller dårligere mellom versjoner?

Tre lag:
  1. Faste briefer (eval/briefer.json), samme for hver versjon.
  2. Automatiske tall fra rim-bm (--sjekk --json) og enkle regelkontroller.
  3. En LLM-dommer med fast rubrikk (eval/rubrikk.md), og blind parvis
     sammenligning mellom to versjoner.

Bruk (fra prosjektroten):
  python3 eval/evaluer.py kjor --navn v2.6                 # generer, mål og bedøm
  python3 eval/evaluer.py kjor --navn ny --prompt annen.md  # en annen promptfil
  python3 eval/evaluer.py poeng --navn v2.6 --uten-dommer   # mål på nytt, uten API
  python3 eval/evaluer.py sammenlign v2.6 ny                # tabell + parvis dommer

Generering og dommer krever ANTHROPIC_API_KEY (pip install anthropic).
Tallene fra rim-bm og regelkontrollene virker uten nøkkel.
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
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "eval"
RIM_BM = ROOT / "dicts" / "rim-bm"
RESULTATER = EVAL / "resultater"

MODELL = "claude-opus-5-5"
DOMMER_MODELL = "claude-opus-5-5"
FALLBACK_BETA = "server-side-fallback-2026-07-01"

KRITERIER = ["bilder", "sprak", "krok", "rim", "rytme", "bestilling", "originalitet"]
# Funn fra rim-bm --sjekk som teller som regelbrudd. Uttale og merker er
# veiledende og varierer med profil, så de rapporteres hver for seg.
BRUDD = {"gjentakelse", "vers", "refreng", "avkorting", "gjenbruk", "ekko"}
NYNORSK = {"ikkje", "eg", "kva", "korleis", "berre", "heime", "kvifor", "noko", "dykk",
           "ho", "me", "frå", "eit", "ein", "mykje", "veit ikkje", "saman", "fekk"}
# «ho» og «me» kan forekomme i talemål; de teller med, men vær obs.
NYNORSK.discard("ho")
NYNORSK.discard("me")

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


# ---------------------------------------------------------------- API

def _klient():
    try:
        import anthropic
    except ImportError:
        sys.exit("Mangler pakken anthropic: pip install anthropic")
    return anthropic.Anthropic()


def generer(klient, system: str, brief: str, modell: str) -> dict:
    with klient.beta.messages.stream(
        model=modell,
        max_tokens=64000,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": brief}],
        thinking={"type": "adaptive"},
        output_config={"effort": "high"},
        betas=[FALLBACK_BETA],
        fallbacks="default",
    ) as stream:
        msg = stream.get_final_message()
    tekst = "".join(b.text for b in msg.content if b.type == "text")
    return {"svar": tekst, "stop": msg.stop_reason, "modell": msg.model,
            "inn": msg.usage.input_tokens, "ut": msg.usage.output_tokens}


def _json_kall(klient, system: str, bruker: str, skjema: dict, modell: str) -> dict | None:
    msg = klient.beta.messages.create(
        model=modell,
        max_tokens=16000,
        system=system,
        messages=[{"role": "user", "content": bruker}],
        thinking={"type": "adaptive"},
        output_config={"effort": "high", "format": {"type": "json_schema", "schema": skjema}},
        betas=[FALLBACK_BETA],
        fallbacks="default",
    )
    if msg.stop_reason in ("refusal", "max_tokens"):
        return None
    tekst = next((b.text for b in msg.content if b.type == "text"), None)
    return json.loads(tekst) if tekst else None


def _rubrikk_skjema() -> dict:
    kriterium = {
        "type": "object",
        "properties": {"poeng": {"type": "integer"}, "begrunnelse": {"type": "string"}},
        "required": ["poeng", "begrunnelse"],
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {
            **{k: kriterium for k in KRITERIER},
            "svakeste_linje": {"type": "string"},
        },
        "required": [*KRITERIER, "svakeste_linje"],
        "additionalProperties": False,
    }


def bedom(klient, brief: str, tekst: str, modell: str) -> dict | None:
    rubrikk = (EVAL / "rubrikk.md").read_text(encoding="utf-8")
    bruker = f"<bestilling>\n{brief}\n</bestilling>\n\n<tekst>\n{tekst}</tekst>"
    svar = _json_kall(klient, rubrikk, bruker, _rubrikk_skjema(), modell)
    if svar is None:
        return None
    for k in KRITERIER:
        svar[k]["poeng"] = max(1, min(5, int(svar[k]["poeng"])))
    svar["snitt"] = round(statistics.mean(svar[k]["poeng"] for k in KRITERIER), 2)
    return svar


PARVIS = """Du er en streng norsk låtskriver. Du får én bestilling og to sangtekster på bokmål, merket 1 og 2.
Rekkefølgen er tilfeldig. Velg teksten du helst ville gitt videre til en artist, ut fra bilder,
naturlig bokmål, krok, rim, rytme, hvor godt bestillingen følges og originalitet. Lengde er ikke en fordel i seg selv.
Velg «uavgjort» bare når du virkelig ikke kan skille dem. Svar bare med JSON etter skjemaet."""

PARVIS_SKJEMA = {
    "type": "object",
    "properties": {
        "vinner": {"type": "string", "enum": ["1", "2", "uavgjort"]},
        "begrunnelse": {"type": "string"},
    },
    "required": ["vinner", "begrunnelse"],
    "additionalProperties": False,
}


def parvis(klient, brief: str, t1: str, t2: str, modell: str) -> dict | None:
    bruker = f"<bestilling>\n{brief}\n</bestilling>\n\n<tekst_1>\n{t1}</tekst_1>\n\n<tekst_2>\n{t2}</tekst_2>"
    return _json_kall(klient, PARVIS, bruker, PARVIS_SKJEMA, modell)


# ---------------------------------------------------------------- kommandoer

def last_briefer(ider: list[str] | None) -> list[dict]:
    alle = json.loads((EVAL / "briefer.json").read_text(encoding="utf-8"))
    if ider:
        ukjente = set(ider) - {b["id"] for b in alle}
        if ukjente:
            sys.exit(f"Ukjente briefer: {', '.join(sorted(ukjente))}")
        alle = [b for b in alle if b["id"] in ider]
    return alle


def _poeng_for(mappe: Path, briefer: list[dict], klient, dommer_modell: str | None,
               parallelt: int, gamle: dict | None = None) -> list[dict]:
    jobber = []
    for b in briefer:
        for svarfil in sorted((mappe / "svar").glob(f"{b['id']}-*.md")):
            jobber.append((b, svarfil))

    def en(jobb):
        b, svarfil = jobb
        i = int(svarfil.stem.rsplit("-", 1)[1])
        svar = svarfil.read_text(encoding="utf-8")
        tekst = finn_tekst(svar)
        rad = {"brief": b["id"], "i": i, "tekst_funnet": tekst is not None}
        if tekst is None:
            return rad
        (mappe / "tekster").mkdir(exist_ok=True)
        (mappe / "tekster" / f"{b['id']}-{i}.txt").write_text(tekst, encoding="utf-8")
        m = metrikker(kjor_rim_bm(tekst, b["profil"]), tekst, b)
        rad["metrikker"] = m
        rad["bestatt"] = bestatt(m)
        forrige = (gamle or {}).get((b["id"], i))
        if klient is not None and dommer_modell:
            rad["dommer"] = bedom(klient, b["brief"], tekst, dommer_modell)
        elif forrige and forrige.get("dommer"):
            rad["dommer"] = forrige["dommer"]
        return rad

    with ThreadPoolExecutor(max_workers=parallelt) as ex:
        return list(ex.map(en, jobber))


def kjor(args) -> None:
    prompt = Path(args.prompt).resolve()
    system = systemprompt(prompt)
    briefer = last_briefer(args.briefer)
    mappe = RESULTATER / args.navn
    (mappe / "svar").mkdir(parents=True, exist_ok=True)
    klient = _klient()

    jobber = [(b, i) for b in briefer for i in range(1, args.n + 1)
              if not (mappe / "svar" / f"{b['id']}-{i}.md").exists()]
    forbruk = {"inn": 0, "ut": 0, "avvist": 0}
    las = threading.Lock()

    def en(jobb):
        b, i = jobb
        r = generer(klient, system, b["brief"], args.modell)
        if r["stop"] == "refusal":
            with las:
                forbruk["avvist"] += 1
            print(f"  {b['id']}-{i}: avvist av modellen", file=sys.stderr)
            return
        (mappe / "svar" / f"{b['id']}-{i}.md").write_text(r["svar"], encoding="utf-8")
        with las:
            forbruk["inn"] += r["inn"]
            forbruk["ut"] += r["ut"]
        print(f"  {b['id']}-{i}: {r['ut']} tokens ut", file=sys.stderr)

    print(f"Genererer {len(jobber)} tekster med {args.modell} …", file=sys.stderr)
    with ThreadPoolExecutor(max_workers=args.parallelt) as ex:
        list(ex.map(en, jobber))

    meta = {
        "navn": args.navn,
        "prompt": str(prompt.relative_to(ROOT)) if prompt.is_relative_to(ROOT) else str(prompt),
        "prompt_sha256": hashlib.sha256(system.encode()).hexdigest()[:12],
        "modell": args.modell,
        "dommer_modell": None if args.uten_dommer else args.dommer_modell,
        "n": args.n,
        "dato": dt.date.today().isoformat(),
        "tokens": forbruk,
    }
    (mappe / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _skriv_poeng(mappe, briefer, None if args.uten_dommer else klient, args.dommer_modell, args.parallelt)


def poeng(args) -> None:
    mappe = RESULTATER / args.navn
    if not (mappe / "svar").is_dir():
        sys.exit(f"Fant ikke {mappe / 'svar'}")
    klient = None if args.uten_dommer else _klient()
    _skriv_poeng(mappe, last_briefer(args.briefer), klient, args.dommer_modell, args.parallelt)


def _skriv_poeng(mappe: Path, briefer: list[dict], klient, dommer_modell: str, parallelt: int) -> None:
    gamle = {}
    if (mappe / "poeng.json").exists():
        for r in json.loads((mappe / "poeng.json").read_text(encoding="utf-8")):
            gamle[(r["brief"], r["i"])] = r
    rader = _poeng_for(mappe, briefer, klient, dommer_modell if klient else None, parallelt, gamle)
    (mappe / "poeng.json").write_text(json.dumps(rader, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (mappe / "rapport.md").write_text(rapport(mappe.name, rader), encoding="utf-8")
    print(rapport(mappe.name, rader))


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
    dommer = [r["dommer"] for r in ok if r.get("dommer")]
    if dommer:
        s["dommer_snitt"] = round(statistics.mean(d["snitt"] for d in dommer), 2)
        s["dommer_sd"] = round(statistics.stdev(d["snitt"] for d in dommer), 2) if len(dommer) > 1 else 0.0
        for k in KRITERIER:
            s[f"dommer_{k}"] = round(statistics.mean(d[k]["poeng"] for d in dommer), 2)
    return s


def rapport(navn: str, rader: list[dict]) -> str:
    s = sammendrag(rader)
    ut = [f"# Evaluering: {navn}", "",
          f"{s['tekster']} tekster, {s['bestatt']} besto de harde kravene, {s['uten_tekst']} uten funnet sangtekst.", "",
          "| Mål | Verdi |", "|---|---|"]
    for k, vis, _ in TALL:
        ut.append(f"| {vis} | {s[k]} |")
    if "dommer_snitt" in s:
        ut.append(f"| **Dommer, snitt (1–5)** | **{s['dommer_snitt']}** ± {s['dommer_sd']} |")
        for k in KRITERIER:
            ut.append(f"| Dommer: {k} | {s[f'dommer_{k}']} |")
    ut += ["", "## Per tekst", "", "| Tekst | Bestått | Rimandel | Brudd | Dommer | Svakeste linje |", "|---|---|---|---|---|---|"]
    for r in sorted(rader, key=lambda r: (r["brief"], r["i"])):
        if not r.get("tekst_funnet"):
            ut.append(f"| {r['brief']}-{r['i']} | – | – | – | – | fant ingen sangtekst |")
            continue
        m, d = r["metrikker"], r.get("dommer") or {}
        svak = (d.get("svakeste_linje") or "").replace("|", "/").replace("\n", " ")
        ut.append(f"| {r['brief']}-{r['i']} | {'ja' if r['bestatt'] else '**nei**'} | {m['rimandel']} "
                  f"| {m['regelbrudd']} | {d.get('snitt', '–')} | {svak} |")
    return "\n".join(ut) + "\n"


def sammenlign(args) -> None:
    a_mappe, b_mappe = RESULTATER / args.a, RESULTATER / args.b
    ra = json.loads((a_mappe / "poeng.json").read_text(encoding="utf-8"))
    rb = json.loads((b_mappe / "poeng.json").read_text(encoding="utf-8"))
    sa, sb = sammendrag(ra), sammendrag(rb)
    ut_mappe = RESULTATER / f"{args.a}-mot-{args.b}"
    ut_mappe.mkdir(parents=True, exist_ok=True)

    linjer = [f"# {args.a} mot {args.b}", "", f"| Mål | {args.a} | {args.b} | Endring |", "|---|---|---|---|"]

    def rad(vis, ka, hoy):
        va, vb = sa.get(ka), sb.get(ka)
        if va is None or vb is None:
            return
        diff = round(vb - va, 3)
        tegn = "" if diff == 0 else ("bedre" if (diff > 0) == hoy else "dårligere")
        linjer.append(f"| {vis} | {va} | {vb} | {diff:+} {tegn} |")

    rad("Besto harde krav", "bestatt", True)
    for k, vis, hoy in TALL:
        rad(vis, k, hoy)
    rad("**Dommer, snitt**", "dommer_snitt", True)
    for k in KRITERIER:
        rad(f"Dommer: {k}", f"dommer_{k}", True)
    if "dommer_sd" in sa:
        linjer += ["", f"Spredning i dommersnitt: ±{sa['dommer_sd']} og ±{sb['dommer_sd']}. "
                   "En endring mindre enn dette er trolig støy."]

    # Blind parvis: samme brief og nummer, tilfeldig rekkefølge.
    tekster = {}
    for navn, mappe in ((args.a, a_mappe), (args.b, b_mappe)):
        for f in (mappe / "tekster").glob("*.txt"):
            tekster[(navn, f.stem)] = f.read_text(encoding="utf-8")
    felles = sorted({k for (n, k) in tekster if n == args.a} & {k for (n, k) in tekster if n == args.b})
    briefer = {b["id"]: b for b in last_briefer(None)}
    rng = random.Random(args.frø)
    par = []
    for stem in felles:
        snu = rng.random() < 0.5
        forst, sist = (args.b, args.a) if snu else (args.a, args.b)
        par.append({"tekst": stem, "1": forst, "2": sist})

    # Ark for menneskelig blindtest + nøkkel.
    ark = ["# Blind A/B", "", "Les begge og noter 1, 2 eller uavgjort per bestilling. Nøkkelen ligger i `nokkel.json`.", ""]
    for p in par:
        brief = briefer[p["tekst"].rsplit("-", 1)[0]]["brief"]
        ark += [f"## {p['tekst']}", "", "> " + brief.replace("\n", "\n> "), "",
                "### Tekst 1", "```", tekster[(p["1"], p["tekst"])].rstrip(), "```", "",
                "### Tekst 2", "```", tekster[(p["2"], p["tekst"])].rstrip(), "```", "", "Valg: ", ""]
    (ut_mappe / "blind-ab.md").write_text("\n".join(ark), encoding="utf-8")
    (ut_mappe / "nokkel.json").write_text(json.dumps(par, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if not args.uten_dommer and par:
        klient = _klient()

        def en(p):
            brief = briefer[p["tekst"].rsplit("-", 1)[0]]["brief"]
            r = parvis(klient, brief, tekster[(p["1"], p["tekst"])], tekster[(p["2"], p["tekst"])], args.dommer_modell)
            if r is None:
                return None
            return {"tekst": p["tekst"], "vinner": p[r["vinner"]] if r["vinner"] in ("1", "2") else "uavgjort",
                    "begrunnelse": r["begrunnelse"]}

        with ThreadPoolExecutor(max_workers=args.parallelt) as ex:
            dommer = [d for d in ex.map(en, par) if d]
        seire = {args.a: 0, args.b: 0, "uavgjort": 0}
        for d in dommer:
            seire[d["vinner"]] += 1
        linjer += ["", "## Blind parvis dom", "",
                   f"{args.b} vant {seire[args.b]}, {args.a} vant {seire[args.a]}, uavgjort {seire['uavgjort']} "
                   f"(av {len(dommer)}).", "", "| Tekst | Vinner | Hvorfor |", "|---|---|---|"]
        for d in sorted(dommer, key=lambda d: d["tekst"]):
            linjer.append(f"| {d['tekst']} | {d['vinner']} | {d['begrunnelse'].replace('|', '/').replace(chr(10), ' ')} |")
        (ut_mappe / "parvis.json").write_text(json.dumps(dommer, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    ark_sti = ut_mappe / "blind-ab.md"
    vis = ark_sti.relative_to(ROOT) if ark_sti.is_relative_to(ROOT) else ark_sti
    linjer += ["", f"Blindtest for deg selv: `{vis}`."]
    tekst = "\n".join(linjer) + "\n"
    (ut_mappe / "rapport.md").write_text(tekst, encoding="utf-8")
    print(tekst)


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="kommando", required=True)

    k = sub.add_parser("kjor", help="generer tekster, mål og bedøm")
    k.add_argument("--navn", required=True, help="navn på kjøringen, for eksempel v2.6")
    k.add_argument("--prompt", default=str(ROOT / "Låtskriver.md"))
    k.add_argument("-n", type=int, default=2, help="tekster per brief (standard 2)")
    k.add_argument("--briefer", nargs="*", help="bare disse brief-id-ene")
    k.add_argument("--modell", default=MODELL)
    k.add_argument("--dommer-modell", default=DOMMER_MODELL)
    k.add_argument("--uten-dommer", action="store_true")
    k.add_argument("--parallelt", type=int, default=4)
    k.set_defaults(fn=kjor)

    q = sub.add_parser("poeng", help="mål eksisterende svar på nytt")
    q.add_argument("--navn", required=True)
    q.add_argument("--briefer", nargs="*")
    q.add_argument("--dommer-modell", default=DOMMER_MODELL)
    q.add_argument("--uten-dommer", action="store_true", help="behold tidligere dommerpoeng, ingen API")
    q.add_argument("--parallelt", type=int, default=4)
    q.set_defaults(fn=poeng)

    s = sub.add_parser("sammenlign", help="sammenlign to kjøringer")
    s.add_argument("a", help="gammel versjon")
    s.add_argument("b", help="ny versjon")
    s.add_argument("--dommer-modell", default=DOMMER_MODELL)
    s.add_argument("--uten-dommer", action="store_true")
    s.add_argument("--frø", type=int, default=1, help="frø for tilfeldig rekkefølge")
    s.add_argument("--parallelt", type=int, default=4)
    s.set_defaults(fn=sammenlign)

    args = p.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
