# Låtskriver

Norsk låtskriverprompt og rimverktøy for bokmål.

- Bruk [Låtskriver.md](Låtskriver.md) som instruksjon til en språkmodell.
- Se [dicts/README.md](dicts/README.md) for Python-verktøyet og kontrollprofiler.
- Se [eval/README.md](eval/README.md) for å måle om en endring gjør tekstene bedre.
- Se [AGENTS.md](AGENTS.md) for beslutninger, verifikasjon og videre arbeid.

Krever Python 3.10 eller nyere:

```bash
python3 dicts/rim-bm kald --vanlige -n 12
python3 dicts/rim-bm --tekst lat.txt --sjekk --profil sang
```

Profiler: `sang`, `rap`, `hoggorm` (standard). Private låter og referanser følger
ikke med. Rim og stavelser er tekstbaserte anslag, ikke en lydtest.
