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
  promptregel i 2.6. I 2.7 kan --plan/--original kontrollere ordrette låser;
  verktøyet er fortsatt ingen automatisk redigeringsmotor.
- Private referansefiler er valgfrie innganger. Ikke finn opp innhold eller
  påstå gjenbrukskontroll mot filer som ikke er tilgjengelige.

## Verifikasjon og miljøbegrensninger
Kjør fra prosjektroten:
`python3 -m unittest discover -s dicts/tester -p test_v26.py -v`
Sju nye tester bestod, inkludert CLI med sangprofil. De bruker en liten
midlertidig ordliste og må ikke tolkes som verifikasjon av norsk uttalekvalitet.

Full suite er kjørt med `python3 -m unittest discover -s dicts/tester -v`
mot den komplette Norsk ordbank-ordlista (600 400 former i
`dicts/norsk-ordbank-bm/former-utf8.txt`). Resultat: 92 tester, 0 feilet,
0 errors, 0 hoppet over.

- test_rim_bm.py: 27 bestått
- test_v21.py: 16 bestått
- test_v22.py: 7 bestått
- test_v23.py: 13 bestått
- test_v24.py: 14 bestått
- test_v25.py: 8 bestått
- test_v26.py: 7 bestått

Ingen Suno-/lydtest er utført.

## Neste arbeid
1. Kjør full suite med komplett datasett og kontroller bakoverkompatibilitet.
2. Innfør eksplisitte flowblokker før stavelseskontrollen strammes inn.
   Nåværende sammenligning mellom vers er ikke en kontroll av flowblokker.
3. Vurder separate profilfiler og oppdeling av den store prompten uten å miste
   brukerens personlige regler. Dette er ikke gjennomført i første runde.
4. Deretter: alternative kroker, uttalevalg per låt, bedre låtrapport,
   variasjonsarkiv og Suno-eksport. Ikke framstill disse som ferdige funksjoner.


## Overlevering 2.7
PR #3 (2.6) er bekreftet merget. Fulltesten av 2.6 står i avsnittet over:
92 tester, 0 feilet, 0 errors, 0 hoppet over, mot 600 400 former.

2.7 legger til --plan, --original og --streng i rim-bm. JSON-plan versjon 1
beskriver eksplisitte flowblokker og posisjonsbaserte låser. Kontrollen bevarer
rå linjer og tomme seksjoner, i motsetning til den eksisterende rimanalyseringen.
Dette er tilsiktet for å oppdage tomme låste refreng og tegnsettingsendringer.
Planlagte flowblokker erstatter den gamle heuristikken som sammenligner vers;
øvrige sjekker beholdes. Les formatbeskrivelsen i dicts/README.md.

GitHub Actions kjører unittest på Python 3.10 og 3.12 med repoets ordliste.
Workflowen er lagt inn. Actions er ikke kjørt i dette miljøet.
Ingen private låter inngår; eksempelplanen inneholder bare kontrollparametere.
Ordbank-dumpen er ikke committet.

Full suite for 2.7 er kjørt med `python3 -m unittest discover -s dicts/tester -v`
etter `python3 dicts/lag-ordliste.py` mot den komplette Norsk ordbank-ordlista
(600 400 former, samme innhold som `dicts/norsk-ordbank-bm/former-utf8.txt`).
Resultat: 101 tester, 0 feilet, 0 errors, 0 hoppet over.
`Ran 101 tests in 5.098s` / `OK`.

- test_rim_bm.py: 27 bestått
- test_v21.py: 16 bestått
- test_v22.py: 7 bestått
- test_v23.py: 13 bestått
- test_v24.py: 14 bestått
- test_v25.py: 8 bestått
- test_v26.py: 7 bestått
- test_v27.py: 9 bestått
