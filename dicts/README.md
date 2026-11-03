# rim-bm 2.6

Tekstbaserte rimkandidater for norsk bokmål. Bygger videre på den innsendte 2.0-pakken. Bruker uttaleregler, eksplisitte unntak og estimert trykkplassering; det er fortsatt ikke en full norsk uttaleordbok eller en lydtest.

## Installer

Krever Python 3.10 eller nyere. Fra en utsjekking av repositoriet:

```bash
python3 dicts/rim-bm --versjon
python3 dicts/rim-bm kald --vanlige -n 12
python3 dicts/rim-bm --tekst lat.txt --sjekk --profil sang
```

Ingen installasjonsskript er nødvendig. Data finnes relativt til skriptet.
`uttale.txt` er egne uttaleoverstyringer; behold denne ved oppgraderinger.

## Kontrollprofiler (2.6)

`--profil sang` krever ikke rap i versmerkene. `--profil rap` krever rapmerker.
`--profil hoggorm` er standard for bakoverkompatibilitet og bruker dessuten
favorittarkivet til ad-lib-sammenligning. Generelle kontroller for rim, refreng,
klisjeer og stemmemerker beholdes i alle profiler.

Bare Hoggorm søker standardarkivet under `artists/Hoggorm/studio` relativt til
foreldremappa til datamappa. Bruk `--fasit /sti/til/tekster` (kan gjentas) for
å velge arkiv eksplisitt i alle profiler. Manglende arkiv gir ingen gjenbrukssjekk
mot tidligere låter; «ingen funn» er derfor ikke bevis på originalitet.

Pre-refreng regnes som egen seksjon. Gjentatte refreng må ha samme antall
linjer og samme normaliserte hovedtekst; ad-libs, tegnsetting og store/små
bokstaver sammenlignes fortsatt ikke. Låste linjer i omskrivingsprompten har
strengere krav og skal sammenlignes ordrett.

## Kommandoer

```bash
rim-bm kald --vanlige -n 12
rim-bm --batch sol kald protein --json
rim-bm sol kald                 # også batch; ingen ord ignoreres
rim-bm --info protein radio min --json
rim-bm --par min fin            # viser hvilken variant som traff
rim-bm --par kald skall vei     # kald/skall og kald/vei
rim-bm --tekst lat.txt --json
rim-bm snøen --stav 2
rim-bm tjener --skjevt
rim-bm mynter --assonans --vanlige   # vokalklang for rap, med score
rim-bm kald --skrift
```

`--batch` laster data én gang. `--json` beholder norske tegn og inneholder `metode`, `usikker` og tilgjengelige `varianter` i ordanalysene. Alle vurderinger merkes usikre i betydningen tekstbaserte anslag; det er ikke en kalibrert sannsynlighet. Metoden angir `uttalefil`, `heuristikk` eller `skrift`, ikke en ekstern kildebekreftelse.

Vanlige søk og `--par` undersøker alle registrerte varianter. `--par` viser første eksakte samsvar, ellers første grove skjeve samsvar. Et treff er mulig under den viste uttalen, ikke nødvendigvis i enhver setning. `--tekst` bruker første variant og gir beskjed ved ord med flere varianter; den kan ikke velge uttale ut fra musikalsk kontekst.

`--tekst` ignorerer seksjonsmerker og ad-libs i parentes i hovedtellinga. Den varsler om sifre. Rimskjemaet kan samle gjentatte ord og grove skjeve rim under samme bokstav; se parets type. Ingen musikalsk kvalitet er automatisk godkjent.

`--stav` og `-n` må være positive. `--info`, `--par`, `--tekst` og `--batch` kan ikke kombineres med hverandre. `--alle` beholder sammensetninger av søkeordet; `--vanlige` betyr at ordet finnes i den medfølgende frekvenslista. `--skrift` deaktiverer uttaleomskrivingene, men gjenskaper ikke alle detaljer i v1.

## Låtsjekk

`rim-bm --tekst lat.txt --sjekk` kjører rapporten og en sjekkliste: gjenbruk fra tidligere låter, gjentatte ord i versene, versmerker uten «rap», instrumenter i merkene, ad-libs mot favorittene, hook som avviker, vers to mot vers én, ekko mellom vers og hook, klisjeer og uttalevarsler for Suno. Tidligere låter leses fra `artists/Hoggorm/studio/fornoyd` og `tekster`; bruk `--fasit DIR` eller `RIM_BM_FASIT` for andre mapper. Funnene er forslag, ikke dom.

## Assonans

Rap lever på vokalklang, men assonans er ikke et rent rim. `--par` viser assonans-score når rimet ikke treffer (`mynter / begynner — ikke treff · assonans 92 % (sterk)`). `--assonans` søker etter ord med samme vokaler fra trykket og ut. `--tekst` merker assonans mot de to forrige linjene, men endrer ikke rimskjemaet. Grader: sterk ≥ 85 %, middels ≥ 65 %, svak ≥ 50 %. Scoren er en tekstbasert vurdering, ikke en lydtest.

Et rent treff med to eller flere vokalkjerner i nøkkelen merkes `· multi` (`gata / data`). `--tekst` merker også flerordsrim og innrim mot sluttordet.

## Egne ord

`egne-ord.txt` holder slang, engelske ord og stedsnavn som ikke finnes i ordbanken (Horten, Bastø, cash, flex). Ett ord per linje, eventuelt med lydform etter: `cash kæsj`. Egne ord rangeres først i søk og teller som vanlige. `uttale.txt` går foran. Annen fil: `--egne FIL` eller `RIM_BM_EGNE`.

## Egen uttale

Format i `uttale.txt`:

```text
# Flere varianter skilles med |. Første brukes av --tekst.
min minn | min
finere f'inere | fin'ere
# Punktum tvinger separate vokalkjerner; apostrof angir trykk.
protein prote.'in
koffein koffe.'in
# Navn kan legges inn eksplisitt.
pepper p'epper
```

En oppføring erstatter standardens varianter for det ordet. Apostrofen angir trykk før en vokalkjerne. Punktum skiller stavelser, men fjernes fra lydstrengen og rimnøkkelen. Uttalefilens verdier behandles som allerede omskrevne lydformer: de kjøres ikke gjennom de generelle uttalereglene igjen. `--info` viser telle- og trykkresultatet. Dette er verktøyets egen lydnotasjon, ikke IPA.

Standardfila har konkrete rettelser for protein, koffein, radio, mulighet, kjærlighet, fred, planet og komet. Min/din/sin har kort og lang variant. Finere har to trykkvarianter. Fra 2.2 dekker generelle regler i koden også resten av ordtypene: alle -het-ord (virkelighet, ærlighet, sikkerhet, ensomhet) og ord med -ie, -io og -eo (familie, historie, studio, video), med bøyningsformer. Ord med trykk på -i (parti, energien, geografien) beholder trykket på i. Bøyningsformer av andre unntak trenger eventuelt egne oppføringer.

## Cache og datastier

Data ligger relativt til skriptet. Følgende miljøvariabler kan overstyre:

| Variabel | Bruk |
|---|---|
| RIM_BM_HOME | Mappe med ordliste, frekvens og brukeruttaler |
| RIM_BM_WORDLIST | Egen ordliste |
| RIM_BM_UTTALE | Egne uttaleoverstyringer |
| RIM_BM_FREKVENS | Egen rangeringsliste |
| RIM_BM_CACHE | Cachemappe, normalt `~/.cache/rim-bm` |
| RIM_BM_BIN | Installasjonsmappe for kommandolenken |

De leverte standarduttalene følger alltid skriptet. `--wordlist`, `--uttale` og `--frekvens` kan også overstyre stier. `--ingen-cache` hopper over cache. Indeksen avhenger av programversjon, datastien, filstørrelse og endringstid for ordliste og begge uttalefiler. Frekvenslista lastes separat. De tre sist brukte indeksene per modus beholdes, og eldre slettes. Hver endring i uttale.txt gir en ny indeks på cirka 15 MB, så uten opprydding vokser cachen for hver endring. Bruker du flere datasett om hverandre, holdes de tre sist brukte. Midlertidige cachefiler har unike navn og slettes etter en time hvis en prosess har stoppet underveis.

## Tester

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tester -v
```

85 tester. Fordelingen per versjon står i `ENDRINGER.md`. Testene gjelder standardpakken. En brukeruttale kan med vilje gi andre resultater; installerens standardtester bruker den tomme brukerfila fra distribusjonen.

## Gjenværende begrensninger

Trykk, stumme konsonanter, vokallengde og lånord er fortsatt delvis heuristiske. Treff skal vurderes mot den faktisk planlagte uttalen. `--skjevt` er en grov idéfunksjon. Frekvens er fra undertekster og avgjør ikke hva som passer en bestemt låt. Flerordsrim og kontekstavhengig uttale velges ikke automatisk. En fast testtekst er en regresjonstest, ikke et representativt mål på all norsk.

## Data og kreditering

Ordlista og frekvenslista er uendret fra den innsendte v2-pakken (600 400 ordformer). Kildefilene er beholdt:

- Norsk ordbank bokmål 2005, dump 2022-02-01, Nasjonalbiblioteket / Språkbanken / UiB. CC BY 4.0. https://www.nb.no/sprakbanken/ressurskatalog/oai-nb-no-sbr-5/
- FrequencyWords av Hermit Dave, OpenSubtitles 2018. CC BY-SA 4.0, som oppgitt i `frekvens/KILDE.md`.

`lag-ordliste.py --dump fil.tar.gz` kan bygge ordlista fra en lokal originaldump. Uten `--dump` laster skriptet ned Norsk ordbank-dumpen til `norsk-ordbank-bm/ordbank.tar.gz` og skriver `norsk-ordbank-bm/former-utf8.txt` på nytt. Dumpen er oppført i `.gitignore` og skal ikke committes; kjør `python3 lag-ordliste.py` for å hente og bygge den lokalt. Endringene i 2.1 og 2.2 gjelder program, uttaledata, dokumentasjon og tester; de store datalistene er ikke bygget på nytt i de versjonene.

