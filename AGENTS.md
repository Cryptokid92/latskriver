# Notat til videre agenter

## Hensikt og prioritering
Brukeren har godkjent forbedringene fra kodegjennomgangen. Første runde retter
kontrollfeil før nye kreative funksjoner: refrenglengde, pre-refreng,
kontrollprofiler og avgrenset omskriving med låste linjer.

## Beslutninger
- `--profil sang|rap|hoggorm` velger kontrollregler. Hoggorm er standard for
  bakoverkompatibilitet. Sang krever ikke rapmerker; bare Hoggorm bruker det
  implisitte favorittarkivet og ad-lib-sammenligningen. Eksplisitt --fasit virker
  i alle profiler. Generelle stemme- og produksjonsregler er foreløpig felles.
- Pre-Chorus/Pre-refreng er egen seksjon, ikke et refreng som må være identisk
  med Chorus. Refrengkontroll sjekker nå også linjeantall.
- Kontroll av refreng sammenligner fortsatt normalisert hovedtekst. Låste
  linjer i omskrivingsarbeidsflyten skal derimot beholdes ordrett. Låsing er en
  promptregel, ikke en implementert automatisk redigeringsmotor.
- Private referansefiler er valgfrie innganger. Ikke finn opp innhold eller
  påstå gjenbrukskontroll mot filer som ikke er tilgjengelige.

- Låtskriver er bare på bokmål. Ingen nynorsk og ingen rim-nn (bestemt av
  brukeren 2026-11-03).
- Eksempellåter ligger i `eksempler.md`, ikke i selve prompten, slik at prompten
  holdes kort og modellen ikke kopierer eksemplene. Kjør `--tekst --sjekk` på
  eksemplene hvis de endres.

## Verifikasjon og miljøbegrensninger
Kjør fra prosjektroten:
`python3 -m unittest discover -s dicts/tester -p test_v26.py -v`
Sju nye tester bestod, inkludert CLI med sangprofil. De bruker en liten
midlertidig ordliste og må ikke tolkes som verifikasjon av norsk uttalekvalitet.

Full suite forsøkt med `python3 -m unittest discover -s dicts/tester -v`.
De eldre testmodulene kunne ikke lastes fordi former-utf8.txt ikke kunne hentes
hit. Den finnes i GitHub-repositoriet; ikke erstatt den med testordlista.
Kjør full suite med originaldata før merge. Ingen Suno-/lydtest er utført.
Direkte Git-kloning feilet på proxyforbindelsen; GitHub-tilkoblingen kunne lese,
men avviste opprettelse av gren med HTTP 403 (Resource not accessible by integration).

## Neste arbeid
1. Kjør full suite med komplett datasett og kontroller bakoverkompatibilitet.
2. Innfør eksplisitte flowblokker før stavelseskontrollen strammes inn.
   Nåværende sammenligning mellom vers er ikke en kontroll av flowblokker.
3. Vurder separate profilfiler og oppdeling av den store prompten uten å miste
   brukerens personlige regler. Dette er ikke gjennomført i første runde.
4. Deretter: alternative kroker, uttalevalg per låt, bedre låtrapport,
   variasjonsarkiv og Suno-eksport. Ikke framstill disse som ferdige funksjoner.
