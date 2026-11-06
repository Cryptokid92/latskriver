# Låtskriver

Norsk låtskriverprompt og rimverktøy for bokmål.

- Bruk [Låtskriver.md](Låtskriver.md) som instruksjon til en språkmodell.
- Se [dicts/README.md](dicts/README.md) for Python-verktøyet og kontrollprofiler.
- Se [AGENTS.md](AGENTS.md) for beslutninger, verifikasjon og videre arbeid.

Krever Python 3.10 eller nyere:

```bash
python3 dicts/rim-bm kald --vanlige -n 12
python3 dicts/rim-bm --tekst lat.txt --sjekk --profil sang
```

Profiler: `sang`, `rap`, `hoggorm` (standard). Private låter og referanser følger
ikke med. Rim og stavelser er tekstbaserte anslag, ikke en lydtest.

Testene kjøres fra prosjektroten med
`python3 -m unittest discover -s dicts/tester -v`.
[CI-oppsettet](.github/workflows/tests.yml) kjører samme suite på Python 3.10 og 3.14.

Datakilder og deres lisenser står i [datadokumentasjonen](dicts/README.md#data-og-kreditering).
Det er foreløpig ikke valgt en egen lisens for koden og promptene.
