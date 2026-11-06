# Notat til videre agenter

## Hensikt og prioritering
Brukeren har godkjent forbedringene fra kodegjennomgangen. Første runde retter
kontrollfeil før nye kreative funksjoner: refrenglengde, pre-refreng,
kontrollprofiler og avgrenset omskriving med låste linjer.

## Beslutninger
- `--profil sang|rap|hoggorm` velger kontrollregler. Hoggorm er standard for
  bakoverkompatibilitet. Sang krever ikke rapmerker; bare Hoggorm bruker det
  implisitte favorittarkivet og ad-lib-sammenligningen. Eksplisitt --fasit virker
  i alle profiler. Merkeregelen er felles fra 2.7.0: rene merker først,
  beskrivelser etter lytting.
- Pre-Chorus/Pre-refreng er egen seksjon, ikke et refreng som må være identisk
  med Chorus. Refrengkontroll sjekker nå også linjeantall.
- Kontroll av refreng sammenligner fortsatt normalisert hovedtekst. Låste
  linjer i omskrivingsarbeidsflyten skal derimot beholdes ordrett. Låsing er en
  promptregel, ikke en implementert automatisk redigeringsmotor.
- Private referansefiler er valgfrie innganger. Ikke finn opp innhold eller
  påstå gjenbrukskontroll mot filer som ikke er tilgjengelige.
- I 2.6.1 hoppes en referanse bare over ved identisk normalisert hovedtekst
  i samme linjerekkefølge. Delvis overlapp, også fra tidligere versjoner av
  samme låt, varsles som gjenbruk og må vurderes.
- Tomme, navngitte seksjoner beholdes; refreng uten hovedtekst varsles.
  Rimloggen i `--tekst` bruker første uttalevariant, som linjeanalysen.
  `--par` undersøker fortsatt alle varianter.
- Søke-JSON beholder eksisterende felt og legger til `sokemodus`.
  Assonanssøk har `assonans_score` per returnert kandidat (0–1).
- Prompten utjevner bare stavelser mellom linjer som deler flow eller melodi.
  Automatisk flowblokkkontroll er fortsatt ikke implementert.
- I 2.6.2 inkluderer cachen skriptets innholdshash og absolutte datastier.
  Fullsuite-testene bruker en egen midlertidig cache, ikke brukercachen.
- Apostrofer i tekst/CLI-ord er ikke trykkmerker; trykknotasjonen er for
  lydformer i uttalefilene. Pre-Hook og post-refreng er egne seksjonstyper,
  også med tankestrek. Rapmerking krever ordet `rap`, ikke delstrengen i `trap`.
- Ekkokontroll går via pre-refreng. Vers sammenlignes mot første refreng,
  eller det følgende refrenget hvis det første er tomt. Pre-refreng varsles
  ved en hel normalisert kroklinje; delvis sitat og bilder vurderes manuelt.
  Stavelsessammenligning bruker første vers med hovedtekst.
- Markdown-referanser behandles per kodeblokk. Bare en identisk blokk
  hoppes over; andre blokker i samme fil sammenlignes fortsatt.
- `HÅN` er et eksplisitt unntak fra bokstaveringsvarsel bare i Hoggorm.
  Egne ord gir ikke generelt fritak. Felles stemmeregler er beholdt.
- `--profil` og `--fasit` krever `--sjekk` (som krever `--tekst`) eller
  `--krok`. Uleselig tekst og ugyldige flagg avvises før indeksen lastes.
- 2.7.0 innfører krokverkstedet: `--krok` vurderer kandidater side om side
  (stavelser, sluttrim, rimtall, multi, klisjé, brukt før). «Brukt før» følger
  samme arkivregel som `--sjekk` og er ordrett etter normalisering; omskrevne
  kroker og gjenbrukte bilder må vurderes manuelt. Prompten krever ti til
  femten kandidater og leverer valgt krok med to reserver.
- Lyttelogg er en promptregel og en mal (`maler/lyttelogg.md`), ikke kode.
  Den fylles bare etter faktisk lytting. Malen har bevisst ingen kodeblokker,
  så den ikke blandes inn i gjenbrukssjekken når den ligger i en låtfil.
- Brukerens Hoggorm-arkiv (PDF levert 2026-11-06) er gjenskapt lokalt i
  `artists/Hoggorm/studio/` (47 filer) og ignorert av git. Blanklinjer gikk tapt
  i PDF-en; brutte seksjonsmerker og stilprompter er satt sammen igjen.
  Originalfilene er fortsatt kilden. Ikke commit arkivet uten eierens beskjed.
- Arkivet viser gjentatte grep: «Hodet er klart, jeg tar min fart» er
  refrenglinje i åtte låter, klart/fart står i sytten filer, og broen
  «Ikke … (nah) / Ikke … (ey)» i sju. Dette er lagt inn i Hoggorm-profilens
  variasjonsregel.
- Eierbeslutning 2026-11-06: første versjon av en låt har rene seksjonsmerker
  (`[Verse 1]`, `[Chorus]`). Beskrivelser som rap, falsett, harmonier eller sax
  legges til etter lytting, én om gangen, og føres i lytteloggen. Favorittene i
  `fornoyd/` brukte slike beskrivelser; de er ikke lenger forbudt, men heller
  ikke standard. Rapkravet i rap/Hoggorm gjelder bare beskrevne versmerker, og
  merkevarsler for stemme, instrumenter og produksjon er påminnelser.

## Verifikasjon og miljøbegrensninger
Kjør fra prosjektroten:
`python3 -m unittest discover -s dicts/tester -p test_v26.py -v`
og for reviewrettelsene:
`python3 -m unittest discover -s dicts/tester -p test_v261.py -v`
og for Claude/Grok-rettelsene:
`python3 -m unittest discover -s dicts/tester -p test_v262.py -v`
og for krokverkstedet:
`python3 -m unittest discover -s dicts/tester -p test_v27.py -v`
Disse har henholdsvis sju, fjorten, tjueén og femten tester med små,
midlertidige datasett og må ikke tolkes som verifikasjon av norsk uttalekvalitet.

Full suite er kjørt med `python3 -m unittest discover -s dicts/tester -v`
mot den komplette Norsk ordbank-ordlista (600 400 former i
`dicts/norsk-ordbank-bm/former-utf8.txt`). Resultat for 2.7.0: 142 tester, 0 feilet,
0 errors, 0 hoppet over.

- test_rim_bm.py: 27 bestått
- test_v21.py: 16 bestått
- test_v22.py: 7 bestått
- test_v23.py: 13 bestått
- test_v24.py: 14 bestått
- test_v25.py: 8 bestått
- test_v26.py: 7 bestått
- test_v261.py: 14 bestått
- test_v262.py: 21 bestått
- test_v27.py: 15 bestått

Kjørt lokalt med Python 3.14.8. Python 3.10-syntaks og workflow-YAML er
kontrollert. CI er konfigurert for 3.10 og 3.14 i `.github/workflows/tests.yml`,
men GitHub-kjøring er ikke utført her. Ingen Suno-/lydtest er utført.

## Evaluering
Før en endring i `Låtskriver.md` regnes som en forbedring: lag tekster til de
faste briefene med gammel og ny versjon, kjør `poeng` og `sammenlign`, og la
brukeren ta blindtesten (se `eval/README.md`). Ingen API-nøkkel: brukeren har
valgt bort automatisk generering og LLM-dommer. Testene ligger i
`eval/test_evaluer.py` og kjøres i samme CI-jobb som rim-bm
(`.github/workflows/tests.yml`, Python 3.10 og 3.14).

## Neste arbeid
1. Behold full suite med komplett datasett som regresjonskontroll ved nye endringer.
2. Innfør eksplisitte flowblokker før stavelseskontrollen strammes inn.
   Nåværende sammenligning mellom vers er ikke en kontroll av flowblokker.
3. Vurder separate profilfiler og oppdeling av den store prompten uten å miste
   brukerens personlige regler. Dette er ikke gjennomført i første runde.
4. Deretter: uttalevalg per låt, bedre låtrapport, variasjonsarkiv for bilder
   og fortellinger (ikke bare ordrette kroklinjer) og Suno-eksport. Ikke
   framstill disse som ferdige funksjoner. Krokverkstedet finnes fra 2.7.0.
5. Fyll lyttelogger for låtene som er «klar for Suno» før nye regler skrives;
   reglene bør bygge på det som faktisk ble hørt.
6. Valg av lisens for kode/prompt og eventuell flytting av personlige regler
   til private filer er eierbeslutninger. Ingen lisens er valgt, og de
   personlige reglene er ikke flyttet i reviewrettelsene.
