"""Offline-tester for eval/evaluer.py. Ingen API-kall: klienten er en attrapp."""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluer as ev  # noqa: E402

SANG = """[Verse 1]
Kaffen står og damper på et kjøkken uten lyd
Du har pakka alt du eier, og det er ingen tid
Jeg later som jeg leser mens du teller over pass
Og regnet tegner striper på det skitne vindusglass

[Chorus]
Gå hvis du må
Jeg holder døra på gløtt
Gå hvis du må
Men ikke si at du er trøtt

[Chorus]
Gå hvis du må
Jeg holder døra på gløtt
Gå hvis du må
Men ikke si at du er trøtt
"""

SVAR = f"""Rim: usjekket

Pass to:
```
[Chorus]
Gå hvis du må (4)
Jeg holder døra på gløtt (6)
Gå hvis du må (4)
Men ikke si at du er trøtt (7)
```

Pass tre:
```
{SANG}```
"""


class Tekst(unittest.TestCase):
    def test_systemprompt_er_teksten_under_streken(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "p.md"
            p.write_text("# Tittel\nForklaring\n\n---\n\nDu er en låtskriver.\n", encoding="utf-8")
            self.assertEqual(ev.systemprompt(p), "Du er en låtskriver.")

    def test_ekte_prompt_har_instruksjon(self):
        self.assertTrue(ev.systemprompt(ev.ROOT / "Låtskriver.md").startswith("Du er en profesjonell låtskriver"))

    def test_velger_pass_tre_framfor_pass_to(self):
        tekst = ev.finn_tekst(SVAR)
        self.assertIn("[Verse 1]", tekst)
        self.assertNotIn("(4)", tekst)

    def test_fjerner_telling_nar_bare_pass_to_finnes(self):
        tekst = ev.finn_tekst("```\n[Chorus]\nGå hvis du må (4)\nJeg holder døra på gløtt — 6\n```")
        self.assertEqual(tekst, "[Chorus]\nGå hvis du må\nJeg holder døra på gløtt\n")

    def test_ingen_tekst(self):
        self.assertIsNone(ev.finn_tekst("Bare prat, ingen kodeblokk."))


class Metrikker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rapport = ev.kjor_rim_bm(SANG, "sang")

    def test_rim_og_brudd(self):
        m = ev.metrikker(self.rapport, SANG, {})
        # Refrenget telles én gang: 4 vers + 4 refreng = 8 linjer.
        self.assertEqual(m["linjer"], 8)
        # pass/vindusglass og gløtt/trøtt rimer; lyd/tid og må/må teller ikke.
        self.assertEqual(m["rimandel"], 0.5)
        self.assertFalse(m["ellipse"])
        self.assertEqual(m["nynorsk"], 0)
        self.assertTrue(ev.bestatt(m))

    def test_laste_linjer_og_ingen_vers(self):
        brief = {"laste_linjer": ["Gå hvis du må", "En linje som mangler"], "ingen_vers": True,
                 "fjernes": ["Og regnet tegner striper på det skitne vindusglass"]}
        m = ev.metrikker(self.rapport, SANG, brief)
        self.assertEqual(m["laste_bevart"], 0.5)
        self.assertFalse(m["ingen_vers"])
        self.assertEqual(m["svake_fjernet"], 0.0)
        self.assertFalse(ev.bestatt(m))

    def test_nynorsk_og_ellipse_feiler(self):
        tekst = "[Verse 1]\nEg veit ikkje kva du vil …\n"
        m = ev.metrikker(ev.kjor_rim_bm(tekst, "sang"), tekst, {})
        self.assertEqual(m["nynorsk"], 3)
        self.assertTrue(m["ellipse"])
        self.assertFalse(ev.bestatt(m))


class Kjoring(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rot = Path(self.tmp.name)
        p = mock.patch.object(ev, "RESULTATER", self.rot)
        p.start()
        self.addCleanup(p.stop)

    def kjor(self, *argv):
        with contextlib.redirect_stdout(io.StringIO()) as ut:
            ev.main(list(argv))
        return ut.getvalue()

    def lag(self, navn, svar=SVAR):
        self.kjor("ny", "--navn", navn, "-n", "1")
        for brief in ("pop-lyset", "bare-refreng"):
            (self.rot / navn / "svar" / f"{brief}-1.md").write_text(svar, encoding="utf-8")
        return self.kjor("poeng", "--navn", navn)

    def test_ny_lager_bestillinger(self):
        self.kjor("ny", "--navn", "a", "-n", "2")
        liste = (self.rot / "a" / "BESTILLINGER.md").read_text(encoding="utf-8")
        self.assertIn("pop-lyset-2.md (mangler)", liste)
        self.assertIn("Hun lar lyset stå og går", liste)
        self.assertTrue((self.rot / "a" / "meta.json").exists())

    def test_poeng_sammenlign_og_stemmer(self):
        ut = self.lag("a")
        self.assertIn("Mangler svar", ut)  # bare to av ti briefer har svar
        rader = json.loads((self.rot / "a" / "poeng.json").read_text(encoding="utf-8"))
        self.assertEqual({r["brief"] for r in rader}, {"pop-lyset", "bare-refreng"})
        bare = next(r for r in rader if r["brief"] == "bare-refreng")
        self.assertFalse(bare["bestatt"])  # svaret har vers

        self.lag("b", SVAR.replace("vindusglass", "glass"))
        ut = self.kjor("sammenlign", "a", "b")
        self.assertIn("2 par i blindtesten", ut)

        mappe = self.rot / "a-mot-b"
        nokkel = {p["tekst"]: p for p in json.loads((mappe / "nokkel.json").read_text(encoding="utf-8"))}
        ark = (mappe / "blind-ab.md").read_text(encoding="utf-8")
        ark = ark.replace("Valg: ", "Valg: 2", 1)  # første par: tekst 2
        (mappe / "blind-ab.md").write_text(ark, encoding="utf-8")
        ut = self.kjor("stemmer", "a", "b")
        forste = sorted(nokkel)[0]
        vinner = nokkel[forste]["2"]
        self.assertIn(f"| {forste} | {vinner} |", ut)
        self.assertIn("Ikke besvart: " + sorted(nokkel)[1], ut)


class Briefer(unittest.TestCase):
    def test_briefer_er_gyldige(self):
        briefer = ev.last_briefer(None)
        self.assertGreaterEqual(len(briefer), 10)
        self.assertEqual(len({b["id"] for b in briefer}), len(briefer))
        for b in briefer:
            self.assertIn(b["profil"], {"sang", "rap", "hoggorm"})
            self.assertNotIn("-", b["id"][-2:])  # id-er slutter ikke på «-tall»
        omskriv = next(b for b in briefer if b["id"] == "omskriv-vers-to")
        for linje in omskriv["laste_linjer"] + omskriv["fjernes"]:
            self.assertIn(linje, omskriv["brief"])


if __name__ == "__main__":
    unittest.main()
