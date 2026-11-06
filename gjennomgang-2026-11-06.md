# Gjennomgang av Låtskriver og rim-bm 2.6

Gjennomgått av Claude (Opus 5.5) · 2026-11-06 · Repo: Cryptokid92/latskriver, commit c76a862

Delbar versjon: https://claude.ai/artifact/HhVCyNGktyx2ZK4ksWoWXz

## Sammendrag

Prosjektet er i god stand, men seks gjenskapte feil i rim-bm rammer vanlig bruk og bør rettes før nye funksjoner. Hele testsuiten består: 92 tester, 0 feil, cirka 6 sekunder mot den komplette ordlista (600 445 former).

Verktøyet er raskt. Et oppslag med cachet indeks tar cirka 0,4 s, en ny indeks bygges på cirka 5 s, og et assonanssøk tar cirka 0,6 s.

Styrker: dokumentasjonen er ærlig om hva verktøyet ikke kan, AGENTS.md er en god beslutningslogg, og 2.6-endringene (profiler, pre-refreng, linjeantall i refreng) har egne regresjonstester.

## Feil i rim-bm

Alle seks er gjenskapt med verktøyet. Linjenumrene gjelder `dicts/rim-bm` på commit c76a862.

| # | Feil | Sted | Symptom | Foreslått retting |
| --- | --- | --- | --- | --- |
| 1 | Apostrof i sammentrekninger leses som trykkmerke | linje 74, 214, 588 | `ska'kke` får nøkkel «e». `ska'kke / gi'kke` gir treff, `ska'kke / hakke` gir ikke treff. Rammer muntlig rap som Hoggorm-profilen ber om. | Fjern apostrof fra ord i sangtekst og fra CLI-ord. Behold apostrof som trykkmerke bare i uttalefilene. |
| 2 | Post-Chorus og Pre-Hook regnes som refreng | linje 768 | `[Post-Chorus]` og `[Pre-Hook]` sammenlignes med første refreng og gir falske «refreng»-funn. Samme type feil som 2.6 rettet for Pre-Chorus. | Gi post-chorus egen type. Utvid pre-mønsteret med pre-hook og tankestrek. |
| 3 | Pre-refreng skjuler ekkosjekken | linje 912 | Sjekken kjører bare når vers står rett før refreng. Med Vers → Pre-Chorus → Chorus hoppes den over. At pre-refrenget siterer kroken, sjekkes heller ikke. | Sjekk vers → pre → refreng, og pre-refreng mot krokens linjer. |
| 4 | Cachen blir utdatert når koden endres | linje 427 | Cache-nøkkelen bygger på versjonsnummer og datafiler, ikke skriptet. Etter endret ld-regel fant `fall` fortsatt `kald` som rim. Testene bruker samme cache (`tester/test_rim_bm.py:31`) og kan bestå mot gammel indeks. | Ta en hash av skriptet med i nøkkelen. La testene bruke en egen midlertidig cache. |
| 5 | «HÅN» flagges som bokstavering | linje 935 | Hoggorm-profilen krever HÅN skrevet slik, men sjekken melder at Suno kan stave det. `egne-ord.txt` kan ikke slå varselet av. | Slå opp i egne ord før sjekken for store bokstaver. |
| 6 | Manglende tekstfil gir traceback | linje 1010 | `--tekst finnes-ikke.txt` krasjer med FileNotFoundError. | Fang feilen og skriv en norsk melding med returkode 2. |

## Feil i prompten (Låtskriver.md)

Promptens norsk/engelsk-eksempler stemmer ikke med verktøyet, og to stemmeregler for Hoggorm ligger fortsatt i de generelle reglene.

- **Norsk/engelsk-eksemplene (linje 181):** `gate / late` gir treff fordi verktøyet leser *late* som norsk. Det er nettopp stavemåte-feilen regelen advarer mot. `meg / way` gir ikke treff, fordi `way` mangler i `egne-ord.txt`. `natt / that` er bare et skjevt rim. `cash / flash` virker og kan stå som eksempel. Vil du beholde `meg / way`, kan `way wæi` legges i `egne-ord.txt`.
- **Stemmeregler (linje 93):** «Alltid full brystrøst» og forbudet mot falsett og belting gjelder også sangprofilen. Eksempelet øverst i fila er «mørk pop, kvinnelig alt». Det går imot profilskillet fra 2.6. Flytt reglene til Hoggorm-profilen, og la `--sjekk` følge samme skille.
- **Versjonshistorikk (linje 19, 166, 170):** v1-sjekken, `--min-key` og «Fra 2.1 er …» er historikk modellen ikke trenger. Flytt det til `dicts/ENDRINGER.md`.
- **Motsigelse om stavelsestall:** linje 152 sier at tallene jevnes ut i seksjonen, mens linje 97 sier at planlagte flowskifter skal beholdes. Skriv «jevnes ut innen hver flowblokk».
- **Overlappende rimtyper:** `meg / vei` står både som rent rim (linje 199) og som lydrim (linje 202). Si at lydrim er et rent rim med ulik stavemåte, eller bruk et annet eksempel.

## Opprydding og dokumentasjon

Ingen av disse påvirker resultatene, men de forvirrer neste person eller agent som leser koden.

- Feilmeldingen ved manglende ordliste ber brukeren kjøre `install.sh`, som ikke finnes (`dicts/rim-bm:1004`). Den bør peke på `python3 dicts/lag-ordliste.py`.
- `RIM_BM_BIN` er dokumentert i `dicts/README.md:103`, men brukes ikke i koden.
- Uten ordliste ved siden av skriptet leter koden i `~/music-projects/dicts` (`dicts/rim-bm:51`), en personlig sti.
- `dicts/uttale-v2.txt` er en ubrukt gammel kopi av standarduttalene.
- Lemma-, paradigme- og bøyingsfilene i `dicts/norsk-ordbank-bm/` (cirka 2 MB) brukes ikke av koden.
- `dicts/ENDRINGER.md` mangler avsnitt for 2.6, selv om README viser dit for testfordelingen.
- Punkt 1 under «Neste arbeid» i AGENTS.md (kjør full suite) er allerede gjort og registrert.
- `--profil` og `--fasit` ignoreres stille uten `--sjekk`, og `--sjekk` uten `--tekst` avvises først etter at indeksen er lastet.
- `rhymes()` bruker `globals()["assonans"]` fordi en parameter skygger funksjonsnavnet. Gi parameteren et annet navn.
- Repoet har ingen CI og ingen lisensfil. En GitHub Action for suiten tar cirka 15 sekunder inkludert indeksbygging. Datakildene er CC BY 4.0 og CC BY-SA 4.0, så en lisensfil bør også si hva som gjelder for koden og promptene.

## Personvern

Repoet er offentlig på GitHub, og Hoggorm-profilen (`Låtskriver.md:243–245`) inneholder personlige opplysninger om familie og arbeidssted. Dette er eierens avgjørelse, ikke en feil.

Hvis opplysningene ikke skal ligge åpent, kan de faktabaserte forbudene flyttes til en privat fil som leses ved bruk, slik `fornoyd/`, `ad-libs.md` og `style-bank.md` allerede gjør. Merk at de også ligger i git-historikken.

## Anbefalt rekkefølge

Rett verktøyfeilene først, fordi prompten viser til resultatene fra verktøyet.

1. Cache-nøkkel med hash av skriptet og egen testcache (feil 4). Da kan resten testes trygt.
2. Apostrof, seksjonstyper og ekko via pre-refreng (feil 1–3), med én regresjonstest per feil.
3. HÅN-varselet og traceback ved manglende fil (feil 5–6).
4. Prompten: bytt norsk/engelsk-eksemplene, flytt stemmereglene til Hoggorm, fjern versjonshistorikk.
5. Opprydding, ENDRINGER.md for 2.6, CI og lisensfil.
6. Avgjør personvernspørsmålet uavhengig av punktene over.

## Metode

Gjennomgangen bygger på lesing av all kode og dokumentasjon, kjøring av testsuiten og målrettede kjøringer av verktøyet.

- Testsuiten: `python3 -m unittest discover -s dicts/tester` med egen cache, 92 tester bestått.
- Promptens rimeksempler kjørt med `rim-bm --par`, blant annet `gate / late`, `meg / way`, `natt / that` og `cash / flash`.
- Sangtekster med Post-Chorus, Pre-Hook, pre-refreng, HÅN og apostrofer kjørt med `--tekst --sjekk`.
- Cachefeilen gjenskapt i en kopi i en midlertidig mappe, ikke i repoet.
- Ingen filer i repoet er endret under gjennomgangen. Ingen lyd- eller Suno-test er gjort, så vurderinger av uttale og rytme er tekstbaserte.

— Claude (Opus 5.5), 6. november 2026
