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


class FalskKlient:
    """Svarer som API-et, uten nettverk."""

    def __init__(self, svar=SVAR, vinner="1"):
        self.kall = []
        svar_tekst, vinner_ = svar, vinner
        kall = self.kall

        class Strom:
            def __init__(self, **kw):
                kall.append(("stream", kw))

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def get_final_message(self):
                return NS(content=[NS(type="thinking", thinking=""), NS(type="text", text=svar_tekst)],
                          stop_reason="end_turn", model=ev.MODELL, usage=NS(input_tokens=10, output_tokens=20))

        def create(**kw):
            kall.append(("create", kw))
            skjema = kw["output_config"]["format"]["schema"]
            if "vinner" in skjema["properties"]:
                data = {"vinner": vinner_, "begrunnelse": "skarpere bilder"}
            else:
                data = {k: {"poeng": 4, "begrunnelse": "ok"} for k in ev.KRITERIER}
                data["bilder"]["poeng"] = 9  # klemmes til 5
                data["svakeste_linje"] = "Gå hvis du må"
            return NS(content=[NS(type="text", text=json.dumps(data))], stop_reason="end_turn")

        self.beta = NS(messages=NS(stream=Strom, create=create))


class Kjoring(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        p = mock.patch.object(ev, "RESULTATER", Path(self.tmp.name))
        p.start()
        self.addCleanup(p.stop)

    def kjor(self, *argv, klient):
        with mock.patch.object(ev, "_klient", return_value=klient), \
                contextlib.redirect_stdout(io.StringIO()) as ut, contextlib.redirect_stderr(io.StringIO()):
            ev.main(list(argv))
        return ut.getvalue()

    def test_kjor_og_sammenlign(self):
        k = FalskKlient()
        self.kjor("kjor", "--navn", "a", "-n", "1", "--briefer", "pop-lyset", "bare-refreng", klient=k)
        rader = json.loads((Path(self.tmp.name) / "a" / "poeng.json").read_text(encoding="utf-8"))
        self.assertEqual(len(rader), 2)
        self.assertEqual(rader[0]["dommer"]["bilder"]["poeng"], 5)
        self.assertEqual(rader[0]["dommer"]["snitt"], round((5 + 4 * 6) / 7, 2))

        stream_kw = next(kw for t, kw in k.kall if t == "stream")
        self.assertEqual(stream_kw["model"], "claude-opus-5-5")
        self.assertEqual(stream_kw["thinking"], {"type": "adaptive"})
        self.assertEqual(stream_kw["fallbacks"], "default")
        self.assertTrue(stream_kw["system"][0]["text"].startswith("Du er en profesjonell låtskriver"))

        # Ny kjøring gjenbruker eksisterende svar og genererer ikke på nytt.
        k2 = FalskKlient()
        self.kjor("kjor", "--navn", "a", "-n", "1", "--briefer", "pop-lyset", "--uten-dommer", klient=k2)
        self.assertFalse([t for t, _ in k2.kall if t == "stream"])

        self.kjor("kjor", "--navn", "b", "-n", "1", "--briefer", "pop-lyset", "bare-refreng", klient=FalskKlient())
        ut = self.kjor("sammenlign", "a", "b", klient=FalskKlient(vinner="2"))
        self.assertIn("Blind parvis dom", ut)
        mappe = Path(self.tmp.name) / "a-mot-b"
        nokkel = json.loads((mappe / "nokkel.json").read_text(encoding="utf-8"))
        parvis = json.loads((mappe / "parvis.json").read_text(encoding="utf-8"))
        # Vinneren «2» skal oversettes til riktig versjon via nøkkelen.
        for p, d in zip(nokkel, parvis):
            self.assertEqual(d["vinner"], p["2"])
        self.assertIn("Tekst 1", (mappe / "blind-ab.md").read_text(encoding="utf-8"))

    def test_poeng_uten_dommer_beholder_gamle_dommerpoeng(self):
        self.kjor("kjor", "--navn", "a", "-n", "1", "--briefer", "pop-lyset", klient=FalskKlient())
        with mock.patch.object(ev, "_klient", side_effect=AssertionError("ingen API")), \
                contextlib.redirect_stdout(io.StringIO()):
            ev.main(["poeng", "--navn", "a", "--uten-dommer"])
        rader = json.loads((Path(self.tmp.name) / "a" / "poeng.json").read_text(encoding="utf-8"))
        self.assertIn("dommer", rader[0])


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
