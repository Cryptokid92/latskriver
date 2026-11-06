# Prosjektgjennomgang — Låtskriver / rim-bm

**Dato:** 2025-11-06  
**Omfang:** Kodebase, dokumentasjon, tester (manuell vurdering + kjørt testsuite)

---

## Kort oppsummering

Låtskriver er et fokusert verktøypakke: norsk bokmål-ordliste + `dicts/rim-bm` (~1080 linjer) for rim, tekstanalyse og låtsjekk med profiler (`sang`, `rap`, `hoggorm`). `Låtskriver.md` og `AGENTS.md` støtter arbeidsflyt for språkmodell. Prosjektet fremstår som tydelig scoped, godt dokumentert og med sterk testdekning.

---

## Det som fungerer godt

- **Dokumentasjon:** `README.md`, `dicts/README.md` og `AGENTS.md` forklarer bruk, begrensninger (tekstbasert uttale, ikke lydtest) og videre arbeid tydelig.
- **Tester:** Full kjøring av `python3 -m unittest discover -s dicts/tester -v` (fra prosjektroten) ga **92 tester, alle OK** (~6 s på gjennomgangs­maskinen).
- **Drift:** Lite friksjon — kjørbar uten tung installasjon; miljøvariabler for stier; `.gitignore` holder store nedlastinger unna (f.eks. `dicts/norsk-ordbank-bm/ordbank.tar.gz`).
- **Forventningsstyring:** README og kodekommentarer sier tydelig at løsningen er heuristisk, ikke full uttaleordbok.

---

## Funn og risikoer

### 1. Monolitt (`dicts/rim-bm`)

Én fil samler CLI, indeksering, uttale, rimlogikk og sjekk. Det er enkelt å klone og kjøre, men vanskeligere å navigere og utvide uten modulær oppdeling. `AGENTS.md` peker allerede på oppdeling av prompt og profilfiler som videre arbeid.

### 2. Inkonsistent testkommando i `dicts/README.md`

Under «Tester» står `python3 -m unittest discover -s tester -v`, som forutsetter arbeidskatalog `dicts/`. Fra **prosjektroten** brukes `-s dicts/tester` (som i `README.md` / `AGENTS.md`). Kan forvirre nye brukere.

### 3. `__pycache__`

Lokalt genererte `.pyc` under `dicts/tester/` er dekket av `.gitignore`; pass på at ingenting ved uhell committes.

### 4. Produkt- og metodehull (allerede dokumentert)

- Eksplisitte **flowblokker** før strammere stavelseskontroll — jf. `AGENTS.md`.
- **Suno/lyd** er ikke en del av automatisk verifikasjon — korrekt å ikke fremstille som testet.

---

## Anbefalte neste steg (prioritert)

| Prioritet | Tiltak |
|-----------|--------|
| Høy | Rett eller presiser unittest-stien i `dicts/README.md` (eller skriv eksplisitt «kjør fra `dicts/`-mappa»). |
| Medium | Ved større endringer: vurder å splitte `rim-bm` i moduler (stier, uttale, indeks, rim, sjekk, CLI) med uendret CLI-adferd. |
| Medium | Følg backlog i `AGENTS.md` (flowblokker, profilfiler / promptstruktur). |

---

## Konklusjon

Prosjektet er **klart definert**, **godt forklart** for mennesker og agenter, og **regresjonstestet** med 92 grønne tester. Hovedvedlikeholdsrisiko er **størrelsen på én hovedskriptfil**; dokumentasjons­detalj rundt testkjøring bør rettes for smidig onboarding.

---

*Signert: **Cursor — Composer 2.5** (automatisert kodegjennomgang), 2025-11-06.*
