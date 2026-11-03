# Endringer fra 2.6 til 2.7

- Eksplisitte flowblokker: `{flow A}` eller `{flow A 10}` på egen linje starter en blokk med navn og valgfritt stavelsesmål (`{flyt A}` godtas). Blokka varer til neste flowmerke eller seksjonsmerke. Merkene telles ikke som tekst og er usynlige for gjenbruk-, klisjé- og uttalesjekken. Ukjente `{...}`-merker gir en advarsel.
- `--tekst` skriver `Flow:` per seksjon. JSON har `blokker` (flow, mål, linjenumre, stavelser) per seksjon og `flow` per linje.
- `--sjekk` sammenligner linjer med samme flownavn på tvers av seksjoner, mot målet eller det vanligste tallet. Melder avvik over tre, ulike mål for samme flow og verslinjer uten flowmerke. Et planlagt flowskifte på ulike steder i versene gir ikke lenger falske vers-funn.
- Uten flowmerker er sjekken uendret (vers én mot vers to, linje for linje, ±3).
- 15 nye tester, til sammen 107.

# Endringer fra 2.4 til 2.5

- Stum d i vanlige bøyde rd-ord: `ordet` rimer på `sporet`, `gjorde` på `spore`, `harde` på `klare`, `gjerde` på `flere`. Lydformene ligger i `uttale-standard.txt`. `verden`, `order`, `herde`, `byrde` og `garde` beholder uttalt d, så `verden` / `ferden` ikke lenger er treff.
- `--par` merker `· multi` når et rent treff har to eller flere vokalkjerner i nøkkelen (`gata / data`). Enstavelsesrim som `kald / skall` merkes ikke.
- `--tekst` merker multi, flerordsrim (de to siste ordene rimer parvis) og innrim mot sluttordet. Rimskjemaet er uendret.
- `--sjekk` melder `...` i teksten, og falsett, belting, Anthemic og produksjonsord i `[]`. Tre klisjeer lagt til fra Låtskriver.md.
- Dokumentert assonans-eksempel for mynter/begynner er 92 %, som verktøyet skriver ut.
- 8 nye tester, til sammen 85.

# Endringer fra 2.3 til 2.4

- `--tekst lat.txt --sjekk`: låtsjekk. Melder gjenbruk (fire ord eller mer på rad som står i en tidligere låt), gjentatte ord i versene, versmerker uten «rap», instrumenter i merkene, ad-libs i versene mot favorittene, hook som avviker fra første gang, stavelser i vers to mot vers én (mer enn tre i avvik), vers som slutter på samme ord som starten av hooken, klisjeer fra Låtskriver.md, og uttalevarsler for Suno (enkeltbokstaver, ord i store bokstaver, ord som ikke finnes i ordbanken eller egne-ord).
- Tidligere låter hentes fra `artists/Hoggorm/studio/fornoyd` og `tekster` (kodeblokker i .md, hele .txt). Andre mapper: `--fasit DIR` (kan gjentas) eller `RIM_BM_FASIT` (kolon-separert). En fasitfil der over halvparten av linjene er like, regnes som samme låt og hoppes over.
- Lydregler: skj → sj, og hj-, hv-, gj- i starten av ord → j, v, j (skjønner → sjønner, hjem → jem). Rimnøkler er uendret.
- Assonans: konsonanttype teller 40 % (var 30 %), så lik vokal med helt ulike konsonanter (cash/nær) blir «svak».
- 14 nye tester, til sammen 77.

# Endringer fra 2.2 til 2.3

- Assonans (vokalklang) for rap. `--par` viser «assonans 94 % (sterk)» når rimet ikke treffer, for eksempel mynter/begynner. Scoren sammenligner vokalene fra trykket og ut (trykkvokalen teller dobbelt, nære vokalpar som e/æ og o/å teller halvt) og konsonanttype (40 %). Grader: sterk ≥ 85 %, middels ≥ 65 %, svak ≥ 50 %.
- `rim-bm ord --assonans`: søk etter vokalklang, sortert etter score. Kan ikke kombineres med `--skjevt`.
- `--tekst` merker assonans mot de to forrige linjene og lister dem under «Assonans». Rimskjemaet endres ikke; bokstavene gjelder fortsatt bare rene og skjeve rim.
- Egen ordliste `egne-ord.txt` (eller `--egne FIL` / `RIM_BM_EGNE`): slang, engelske ord og stedsnavn. Valgfri lydform per ord. Egne ord rangeres først og teller som vanlige. `uttale.txt` går foran egne-ord.txt. Cachen bygges på nytt når fila endres.
- 12 nye tester, til sammen 62.

# Endringer fra 2.1 til 2.2

- Tegn i ord du skriver inn fjernes igjen: `--par kald. skall` gir treff, som i 2.0. Punktum som stavelsesskille gjelder nå bare lydformer i uttalefila.
- Cachen ryddes: de tre sist brukte indeksene per modus beholdes, eldre slettes. En indeks som brukes, merkes som nylig brukt. Gamle midlertidige filer slettes etter en time. I 2.1 ga hver endring i uttale.txt en ny indeks på cirka 15 MB som aldri ble slettet.
- Generell trykkregel for -het: h-en regnes til suffikset. Virkelighet, ærlighet, hemmelighet, evighet, sikkerhet, ensomhet og enighet får trykk på første stavelse uten unntak i uttalefila.
- Generell trykkregel for hiatus: i eller e rett foran trykklett e eller o, og o etter i eller e, er trykklette i ord som ender på -ie, -io eller -eo, også bøyd (familien, familiene, radioen). Studio, video, familie, historie, studie og komedie får riktig nøkkel. Ord med trykk på -i (parti, partiet, energien, geografien) er uendret.
- 7 nye tester, til sammen 50.

# Endringer fra 2.0 til 2.1

- Flere eksplisitte uttalevarianter med `|`; alle indekseres og vurderes ved søk og parsjekk.
- Punktum kan skille vokalkjerner i uttalefila. Protein og koffein har tre stavelser uten å ødelegge ekte diftonger i stein og vei.
- Eksplisitte trykkrettelser for radio, mulighet, kjærlighet, planet og komet; to lesninger av finere.
- Fred/sted finner hverandre. Min/fin kan treffe under den registrerte lange uttalen; den korte varianten beholdes.
- `--batch` og flere vanlige søkeord gir separate resultater med én datainnlasting.
- JSON viser metode, variantliste og at resultatet er et anslag. Tekstrapporten varsler når den bruker første av flere uttaler.
- Positive argumentverdier valideres, og moduser som ikke kan brukes sammen avvises.
- Unicode normaliseres til NFC. Ordlista dedupliseres ved indeksering.
- Standarduttaler skilles fra egne uttaler. Oppgradering fra 2.0 tar sikkerhetskopi og bevarer egne endringer.
- Unike temporære cachefiler; ingen automatisk sletting av andres datasettcacher.
- 16 nye tester, i tillegg til de 27 eksisterende. De konkrete ordeksemplene er unntaksdata, ikke en påstand om generell fonetisk fullstendighet.
