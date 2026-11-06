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
python3 dicts/rim-bm --krok "Jeg retter én feil om gangen" "Hodet er klart, jeg tar min fart"
```

Profiler: `sang`, `rap`, `hoggorm` (standard). Private låter og referanser følger
ikke med. Rim og stavelser er tekstbaserte anslag, ikke en lydtest.

Arbeidsflyt fra 2.7: kroken velges i et krokverksted med `rim-bm --krok`, og
låter som er klare for Suno, får en lyttelogg fra [maler/lyttelogg.md](maler/lyttelogg.md).
Første versjon har rene seksjonsmerker som `[Verse 1]`; beskrivelser legges til etter lytting.
Et lokalt Hoggorm-arkiv i `artists/Hoggorm/studio/` brukes automatisk i
Hoggorm-profilen. Mappa er ignorert av git og skal ikke committes.

Testene kjøres fra prosjektroten med
`python3 -m unittest discover -s dicts/tester -v`.
[CI-oppsettet](.github/workflows/tests.yml) kjører samme suite på Python 3.10 og 3.14.

Datakilder og deres lisenser står i [datadokumentasjonen](dicts/README.md#data-og-kreditering).
Det er foreløpig ikke valgt en egen lisens for koden og promptene.
