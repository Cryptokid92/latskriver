# rim-bm 2.7.0

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

Pre-refreng og post-refreng regnes som egne seksjonstyper, også `Pre-Hook`,
`Post-Chorus` og navn med tankestrek. Gjentatte refreng må ha samme antall
linjer og samme normaliserte hovedtekst; ad-libs, tegnsetting og store/små
bokstaver sammenlignes fortsatt ikke. Låste linjer i omskrivingsprompten har
strengere krav og skal sammenlignes ordrett. Tomme refreng beholdes i rapporten
og varsles av `--sjekk`, også når de bare inneholder ad-libs.

Fra 2.7.0 godtas rene versmerker som `[Verse 1]` i alle profiler; første versjon av en låt skal ha rene merker, og beskrivelser legges til etter lytting. Har et versmerke en beskrivelse, krever rap- og Hoggorm-profilen ordet `rap`; `trap` og `drap` oppfyller ikke kravet.
Den eksplisitt tillatte skrivemåten `HÅN` gir ikke bokstaveringsvarsel i
Hoggorm-profilen. Andre ord med store bokstaver vurderes som før, også i egne
ord. Dette sier ikke hvordan Suno faktisk vil uttale dem.

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
rim-bm --krok "Jeg retter én feil om gangen" "Hodet er klart, jeg tar min fart"
```

`--batch` laster data én gang. `--json` beholder norske tegn og inneholder `metode`, `usikker` og tilgjengelige `varianter` i ordanalysene. Alle vurderinger merkes usikre i betydningen tekstbaserte anslag; det er ikke en kalibrert sannsynlighet. Metoden angir `uttalefil`, `heuristikk` eller `skrift`, ikke en ekstern kildebekreftelse.

Søkeresultater i JSON har `sokemodus`: `rim`, `skjevt` eller `assonans`, også i batch. `grupper` beholder stavelsesgrupper med ordlister. Assonanssøk har dessuten `assonans_score`, et objekt fra kandidatord til score mellom 0 og 1, bare for returnerte kandidater. Scoren er den beste blant variantene som oppfyller søkets stavelsesfilter; den er ikke en sannsynlighet eller et bevis på rent rim. Tomme assonanssøk gir tomme objekter for både `grupper` og `assonans_score`. Skriftmetoden framgår fortsatt av `ord.metode`.

Vanlige søk og `--par` undersøker alle registrerte varianter. `--par` viser første eksakte samsvar, ellers første grove skjeve samsvar. Et treff er mulig under den viste uttalen, ikke nødvendigvis i enhver setning. `--tekst` bruker første variant både i linjeanalysen og rimloggen, og gir beskjed ved ord med flere varianter; den kan ikke velge uttale ut fra musikalsk kontekst. JSON-rimpar angir `uttalevalg: "forste"` for tekstrapporten og `"alle"` for `--par`; `varianter` viser fortsatt alle tilgjengelige varianter.

`--tekst` ignorerer seksjonsmerker og ad-libs i parentes i hovedtellinga. Den varsler om sifre. Rimskjemaet kan samle gjentatte ord og grove skjeve rim under samme bokstav; se parets type. Ingen musikalsk kvalitet er automatisk godkjent.

`--stav` og `-n` må være positive. `--info`, `--par`, `--tekst`, `--batch` og `--krok` kan ikke kombineres med hverandre. `--alle` beholder sammensetninger av søkeordet; `--vanlige` betyr at ordet finnes i den medfølgende frekvenslista. `--skrift` deaktiverer uttaleomskrivingene, men gjenskaper ikke alle detaljer i v1.

## Låtsjekk

`rim-bm --tekst lat.txt --sjekk` kjører rapporten og en sjekkliste: gjenbruk fra tidligere låter, gjentatte ord i versene, beskrevne versmerker uten «rap», instrumenter og stemmebeskrivelser i merkene (som påminnelser), ad-libs mot favorittene, hook som avviker, vers to mot første vers med hovedtekst, ekko mellom vers og hook, klisjeer og uttalevarsler for Suno. Bare Hoggorm leser standardarkivet `artists/Hoggorm/studio/fornoyd` og `tekster`, eller mapper valgt med `RIM_BM_FASIT`. Bruk `--fasit DIR` for eksplisitte mapper i alle profiler; flagget går foran miljøvariabelen. Funnene er forslag, ikke dom.

En referanse hoppes bare over når hele den normaliserte hovedteksten er identisk i samme linjerekkefølge, uten hensyn til merker, ad-libs, tegnsetting eller store/små bokstaver. I Markdown behandles hver kodeblokk separat, så en stilprompt i en annen blokk ikke gjør låta ulik seg selv. Andre blokker i samme fil sammenlignes fortsatt. Delvis overlapp, også med en tidligere versjon av samme låt, gir gjenbruksfunn som må vurderes. Gjentatte kroklinjer i arkivet gjør ikke en annen låt til «samme låt».

Ekkokontrollen av versslutten virker også når ett eller flere pre-refreng står før hooken. Den sammenligner mot starten av første refreng med mindre dette er tomt; da brukes refrenget som følger verset. Pre-refreng varsles når en normalisert linje siterer en hel linje fra det følgende refrenget. Delvis sitering, signaturbilder og tittelgjenbruk krever fortsatt manuell vurdering.

`--profil` og `--fasit` krever `--sjekk` (som igjen krever `--tekst`) eller `--krok`. Ugyldige kombinasjoner og uleselige tekstfiler gir feilmelding og returkode 2 før indeksen lastes.

## Krokverksted (2.7)

`rim-bm --krok "linje" "linje"` vurderer krokkandidater side om side. Hver kandidat står i egne anførselstegn. For hver linje vises stavelser i hovedteksten (ad-libs i parentes telles ikke), om tallet ligger innenfor fem–ni, sluttordets rimnøkkel, `multi` når nøkkelen har to eller flere vokalkjerner, antall rene rim i ordlista (og hvor mange av dem som er vanlige), klisjeer fra forbudt-lista og hvilke tidligere låter linja står i.

«Brukt før» sjekkes mot samme arkiv som `--sjekk`: bare Hoggorm leser standardarkivet `fornoyd/` og `tekster/`, og `--fasit DIR` velger mapper i alle profiler. `--fasit artists/Hoggorm/studio` tar med alle undermapper, også utkast. En kandidat merkes når den står inni en tidligere linje (minst tre ord, ikke bare småord), når en tidligere linje står inni kandidaten, eller når de deler fire ord på rad. Sammenligningen er ordrett etter normalisering; en omskrevet krok med samme bilde eller rimpar må vurderes manuelt. En kandidat fra en låt som allerede ligger i arkivet, merkes mot seg selv.

Antall rene rim er et mål på hvor lett sluttordet er å rime på, ikke på hvor godt rimet passer. `--json` gir én post per kandidat med `tekst`, `stav`, `innenfor`, `sluttord`, `nokkel`, `multi`, `rim`, `rim_vanlige`, `klisje` og `brukt_for`.

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

Apostrof er bare et trykkmerke i lydformer fra uttalefilene. I CLI-ord og sangtekst behandles `ska'kke` og `ska’kke` som `skakke` under uttaleanalysen. Tekst og skrivemåte i rapporten bevares. `gjennom` har ferdig omskrevet standardlydform `j'ennom`.

Standardfila har konkrete rettelser for protein, koffein, radio, mulighet, kjærlighet, fred, planet og komet. Min/din/sin har kort og lang variant. Finere har to trykkvarianter. Fra 2.2 dekker generelle regler i koden også resten av ordtypene: alle -het-ord (virkelighet, ærlighet, sikkerhet, ensomhet) og ord med -ie, -io og -eo (familie, historie, studio, video), med bøyningsformer. Ord med trykk på -i (parti, energien, geografien) beholder trykket på i. Bøyningsformer av andre unntak trenger eventuelt egne oppføringer.

## Cache og datastier

Data ligger relativt til skriptet. Følgende miljøvariabler kan overstyre:

| Variabel | Bruk |
|---|---|
| RIM_BM_HOME | Mappe med ordliste, frekvens og brukeruttaler |
| RIM_BM_WORDLIST | Egen ordliste |
| RIM_BM_UTTALE | Egne uttaleoverstyringer |
| RIM_BM_EGNE | Egne ord og valgfrie lydformer |
| RIM_BM_FASIT | Kolonseparerte referansemapper, bare implisitt i Hoggorm-profilen |
| RIM_BM_FREKVENS | Egen rangeringsliste |
| RIM_BM_CACHE | Cachemappe, normalt `~/.cache/rim-bm` |

De leverte standarduttalene følger alltid skriptet. Standard datamappe er skriptets mappe, også når ordlista mangler; ingen personlig reservesti brukes. `--wordlist`, `--uttale`, `--egne` og `--frekvens` kan også overstyre stier. `--ingen-cache` hopper over cache. Indeksen avhenger av programversjon, en SHA-256-hash av skriptet, absolutte datastier, filstørrelse og endringstid for ordliste, begge uttalefiler og egne ord. Kodeendringer gir derfor ny indeks uten at versjonsnummeret må endres. Frekvenslista lastes separat. De tre sist brukte indeksene per modus beholdes, og eldre slettes. Hver endring i uttale.txt gir en ny indeks på cirka 15 MB, så uten opprydding vokser cachen for hver endring. Bruker du flere datasett om hverandre, holdes de tre sist brukte. Midlertidige cachefiler har unike navn og slettes etter en time hvis en prosess har stoppet underveis.

## Tester

Kjør fra prosjektroten:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dicts/tester -v
```

142 tester. Fordelingen per testfil står i `../AGENTS.md`. Testene gjelder standardpakken; kontrolltestene for 2.6, 2.6.1, 2.6.2 og 2.7 bruker små, midlertidige datasett. Fullsuite-testene oppretter en egen midlertidig indekscache som slettes etter kjøring; de leser eller rydder ikke brukercachen. En brukeruttale kan med vilje gi andre resultater; standardpakken leveres med en tom brukerfil.

`.github/workflows/tests.yml` kjører suiten med medfølgende ordliste på Python 3.10 og 3.14 ved push og pull request. Arbeidsflyten bruker [checkout](https://github.com/actions/checkout) og [setup-python](https://github.com/actions/setup-python). En lokal testkjøring er ikke en bekreftelse på at GitHub-kjøringen er gjennomført.

## Gjenværende begrensninger

Trykk, stumme konsonanter, vokallengde og lånord er fortsatt delvis heuristiske. Treff skal vurderes mot den faktisk planlagte uttalen. `--skjevt` er en grov idéfunksjon. Frekvens er fra undertekster og avgjør ikke hva som passer en bestemt låt. Flerordsrim og kontekstavhengig uttale velges ikke automatisk. En fast testtekst er en regresjonstest, ikke et representativt mål på all norsk.

## Data og kreditering

Ordlista og frekvenslista er uendret fra den innsendte v2-pakken (600 400 ordformer). Kildefilene er beholdt:

`uttale-v2.txt` er en historisk kopi som ikke leses av programmet. Lemma-, paradigme- og bøyingsfilene i `norsk-ordbank-bm/` er medfølgende kildedata; runtime bruker `former-utf8.txt`. Egne uttaleendringer skal legges i `uttale.txt`.

- Norsk ordbank bokmål 2005, dump 2022-02-01, Nasjonalbiblioteket / Språkbanken / UiB. CC BY 4.0. https://www.nb.no/sprakbanken/ressurskatalog/oai-nb-no-sbr-5/
- FrequencyWords av Hermit Dave, OpenSubtitles 2018. CC BY-SA 4.0, som oppgitt i `frekvens/KILDE.md`.

`lag-ordliste.py --dump fil.tar.gz` kan bygge ordlista fra en lokal originaldump. Uten `--dump` laster skriptet ned Norsk ordbank-dumpen til `norsk-ordbank-bm/ordbank.tar.gz` og skriver `norsk-ordbank-bm/former-utf8.txt` på nytt. Dumpen er oppført i `.gitignore` og skal ikke committes; kjør `python3 lag-ordliste.py` for å hente og bygge den lokalt. Endringene i 2.1 og 2.2 gjelder program, uttaledata, dokumentasjon og tester; de store datalistene er ikke bygget på nytt i de versjonene.

