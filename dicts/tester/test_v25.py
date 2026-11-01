"""Tester for 2.5: stum d i bøyd rd, multi, flerordsrim og innrim."""
import tempfile
import unittest
from pathlib import Path

from test_rim_bm import rb, DATA, run


class StumD(unittest.TestCase):
    def test_boyde_former_rimer_rent(self):
        par = [
            ("ordet", "sporet"),
            ("bordet", "sporet"),
            ("harde", "klare"),
            ("gjorde", "spore"),
            ("jorden", "moren"),
            ("gjerde", "flere"),
            ("morder", "sporer"),
            ("gården", "åren"),
            ("lærde", "lære"),
        ]
        for a, b in par:
            r = rb.check_pair(DATA, a, b)
            self.assertTrue(r["treff"], f"{a}/{b}: {r['nokkel']}")
            self.assertTrue(r["multi"], f"{a}/{b} skal være multi")

    def test_uttalt_d_blir_ikke_treff(self):
        # verden har d. ferden har ikke. order, herde og byrde beholder d.
        self.assertFalse(rb.check_pair(DATA, "verden", "ferden")["treff"])
        self.assertEqual(DATA.info("ferden").lyd, "feren")
        self.assertEqual(DATA.info("verden").lyd, "verden")
        self.assertEqual(DATA.info("order").lyd, "order")
        self.assertEqual(DATA.info("herde").lyd, "herde")
        self.assertEqual(DATA.info("byrde").lyd, "byrde")
        self.assertEqual(DATA.info("garde").lyd, "garde")

    def test_stavelser_er_uendret(self):
        for w, n in {"ordet": 2, "gjorde": 2, "harde": 2, "gården": 2, "gjerde": 2}.items():
            self.assertEqual(DATA.info(w).stav, n, w)


class Multi(unittest.TestCase):
    def test_par_skiller_multi_fra_enstavelse(self):
        self.assertTrue(rb.check_pair(DATA, "gata", "data")["multi"])
        self.assertTrue(rb.check_pair(DATA, "gatene", "matene")["multi"])
        self.assertTrue(rb.check_pair(DATA, "penger", "henger")["treff"])
        self.assertTrue(rb.check_pair(DATA, "mørket", "tørket")["multi"])
        self.assertFalse(rb.check_pair(DATA, "kald", "skall")["multi"])
        self.assertFalse(rb.check_pair(DATA, "meg", "vei")["multi"])
        self.assertIn("multi", run("--par", "gata", "data"))
        self.assertNotIn("multi", run("--par", "kald", "skall"))

    def test_vokalrim_er_ikke_rent(self):
        for a, b in (("mynter", "begynner"), ("hat", "hatt"), ("hjørnet", "tårnet"), ("her", "ser")):
            r = rb.check_pair(DATA, a, b)
            self.assertFalse(r["treff"], f"{a}/{b}")
            self.assertFalse(r["multi"], f"{a}/{b}")

    def test_flerord_og_innrim_i_tekst(self):
        tekst = "[Verse 1 - rap]\nMørket faller\nTørket kaller\nNatta og katta\n"
        rep = rb.analyse_text(DATA, tekst)
        linjer = rep["seksjoner"][0]["linjer"]
        self.assertEqual(linjer[1].get("flerord"), "Tørket kaller / Mørket faller")
        self.assertIn("Natta", linjer[2]["innrim"])
        p = Path(tempfile.mkdtemp()) / "lat.txt"
        p.write_text(tekst, encoding="utf-8")
        ut = run("--tekst", str(p))
        self.assertIn("flerord", ut)
        self.assertIn("innrim", ut)


class SjekkStemme(unittest.TestCase):
    def test_falsett_og_ellipse(self):
        funn = rb.sjekk_tekst(DATA, "[Bridge - falsetto]\nJa\n", [])
        self.assertTrue(any("falsetto" in f["melding"] for f in funn), funn)
        funn = rb.sjekk_tekst(DATA, "[Chorus - Anthemic]\nJa...\n", [])
        typer = {f["type"] for f in funn}
        self.assertIn("merke", typer)
        self.assertIn("avkorting", typer)
        ren = rb.sjekk_tekst(DATA, "[Chorus - sung hook, chest voice]\nStille vann\n", [])
        self.assertFalse({f["type"] for f in ren} & {"merke", "avkorting"}, ren)

    def test_klisje_fra_latskriver(self):
        funn = rb.sjekk_tekst(DATA, "[Verse 1 - rap]\nByen sover aldri\n", [])
        self.assertTrue(any("byen sover aldri" in f["melding"] for f in funn), funn)


if __name__ == "__main__":
    unittest.main()
