# Evaluering av Låtskriver

Svarer på ett spørsmål: ble Låtskriver bedre eller dårligere av en endring?
Testene i `dicts/tester` sjekker at rim-bm regner riktig. Dette sjekker tekstene
som prompten faktisk gir.

## Slik virker det

1. **Faste briefer** (`briefer.json`): ti bestillinger som dekker sang, rap,
   Hoggorm, refreng først, pre-refreng, blandet, norsk/engelsk, bare refreng og
   omskriving med låste linjer. Hver versjon skriver to tekster per brief.
2. **Automatiske tall:** sangteksten (pass tre) hentes ut av svaret og kjøres
   gjennom `rim-bm --tekst --sjekk --json`. Vi måler rimandel, multi og innrim,
   regelbrudd, uttalefunn og nynorskord. Harde krav (ingen «...», ingen tall i
   linjene, ingen nynorsk, låste linjer bevart, ingen vers når bare refreng er
   bestilt) gir *bestått* eller *ikke bestått*.
3. **LLM-dommer:** gir 1–5 på sju kriterier i `rubrikk.md` (bilder, språk, krok,
   rim, rytme, bestilling, originalitet) og peker ut svakeste linje.
4. **Blind parvis dom:** ved sammenligning får dommeren gammel og ny tekst for
   samme brief i tilfeldig rekkefølge og velger den beste. I tillegg lages
   `blind-ab.md` til deg, med nøkkelen i en egen fil, så du kan stemme selv.

## Kjøre lokalt

```bash
pip install anthropic
export ANTHROPIC_API_KEY=...
python3 eval/evaluer.py kjor --navn v2.6
# endre Låtskriver.md, så:
python3 eval/evaluer.py kjor --navn v2.7
python3 eval/evaluer.py sammenlign v2.6 v2.7
```

Resultatet havner i `eval/resultater/<navn>/` (svar, tekster, `poeng.json`,
`rapport.md`) og `eval/resultater/v2.6-mot-v2.7/rapport.md`. En kjøring som
avbrytes, fortsetter der den slapp. `poeng --navn X --uten-dommer` måler
eksisterende svar på nytt uten API, for eksempel etter en endring i rim-bm.

Nyttige valg: `--briefer rap-skryt rap-nattbuss` for et utvalg, `-n 3` for
flere tekster per brief, `--prompt fil.md` for en annen promptfil.

## Automatisk på GitHub

`.github/workflows/eval.yml` kjører når en PR endrer `Låtskriver.md`, briefene
eller rubrikken. Den evaluerer prompten på PR-ens base og i PR-en, og legger
sammenligningen som kommentar på PR-en. Alle tekster ligger i artefakten
«evaluering». Den kan også startes for hånd under Actions, mot en valgfri ref.

Krever hemmeligheten `ANTHROPIC_API_KEY` under *Settings → Secrets and
variables → Actions*. Uten den hoppes evalueringen over med en advarsel.

## Lese resultatet

- Modellen varierer fra kjøring til kjøring. Se på spredningen (±) ved
  dommersnittet: en endring som er mindre enn den, er trolig støy.
- Den blinde parvise dommen er det tydeligste signalet. Å vinne for eksempel
  14 av 20 er et reelt løft, mens 11 av 20 ikke er det.
- Rim-tallene måler håndverk, ikke kvalitet. Høyere rimandel er ikke bedre hvis
  dommeren samtidig gir lavere poeng på språk.
- Dommeren er en språkmodell med egne vaner. Din egen blindtest i `blind-ab.md`
  er fasiten når de er uenige.

Modellene genererer uten verktøy, så tekstene får `Rim: usjekket`. Det er
likt for alle versjoner og påvirker ikke sammenligningen.

Offline-tester: `python3 -m unittest discover -s eval`.
