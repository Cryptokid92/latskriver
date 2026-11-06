# Evaluering av Låtskriver

Svarer på ett spørsmål: ble Låtskriver bedre eller dårligere av en endring?
Testene i `dicts/tester` sjekker at rim-bm regner riktig. Dette sjekker tekstene
som prompten faktisk gir. Ingen API-nøkkel trengs.

## Slik virker det

1. **Faste briefer** (`briefer.json`): ti bestillinger som dekker sang, rap,
   Hoggorm, refreng først, pre-refreng, blandet, norsk/engelsk, bare refreng og
   omskriving med låste linjer. Hver versjon skriver to tekster per brief.
2. **Tall fra rim-bm:** sangteksten (pass tre) hentes ut av svaret og kjøres
   gjennom `rim-bm --tekst --sjekk --json`. Vi måler rimandel, multi og innrim,
   regelbrudd, uttalefunn og nynorskord. Harde krav (ingen «...», ingen tall i
   linjene, ingen nynorsk, låste linjer bevart, ingen vers når bare refrenget er
   bestilt) gir *bestått* eller *ikke bestått*.
3. **Din blindtest:** gammel og ny tekst for samme bestilling står side om side
   i tilfeldig rekkefølge. Du velger, og skriptet teller opp etterpå.

## Gangen

```bash
# 1. Lag mappe og bestillingsliste for versjonen du har nå
python3 eval/evaluer.py ny --navn v2.6
```

Åpne `eval/resultater/v2.6/BESTILLINGER.md`. For hver fil: start en ny samtale i
Claude, lim inn instruksjonen fra `Låtskriver.md` (alt under streken), send
bestillingen og lim hele svaret inn i fila under `svar/`. Bruk samme modell hele
veien.

```bash
# 2. Mål svarene
python3 eval/evaluer.py poeng --navn v2.6

# 3. Gjør det samme etter endringen, så sammenlign
python3 eval/evaluer.py ny --navn v2.7
python3 eval/evaluer.py poeng --navn v2.7
python3 eval/evaluer.py sammenlign v2.6 v2.7

# 4. Fyll inn «Valg:» i blind-ab.md, så tell opp
python3 eval/evaluer.py stemmer v2.6 v2.7
```

Resultatene ligger i `eval/resultater/`. Commit dem, så har du historikken.
Når en versjon først er målt, trenger du bare å lage tekster til den nye.

## Lese resultatet

- Blindtesten er det som teller. Å vinne for eksempel 14 av 20 er et reelt
  løft, mens 11 av 20 ikke er det.
- Rimtallene måler håndverk, ikke kvalitet. Bruk dem til å fange
  tilbakeskritt, som flere regelbrudd eller låste linjer som ikke holdt.
- Svarene varierer fra gang til gang. Derfor er det to tekster per brief.

Tester: `python3 -m unittest discover -s eval`.
