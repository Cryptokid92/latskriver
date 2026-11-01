"""Tester for 2.4: låtsjekk (--sjekk) og uttale-varsler."""
import tempfile
import unittest
from pathlib import Path

from test_rim_bm import rb, DATA, run

LAT = """[Hook]
Stille vann (stille vann)
Ingen veit hva jeg kan

[Verse 1 - sax solo]
Baby, jeg make it rain for alle gutta i byen
Kompis, kompis, sa jeg, neon over HÅN
Kompis sa B er her, og hjertet slår fort
Ingen veit hva jeg kan

[Hook]
Stille vann (stille vann)
Ingen veit hva jeg vil

[Verse 2 - rap]
Kort linje her
Dette er en mye lengre linje med mange flere ord i seg
"""

FASIT = """# Lemonade

```
Hu er sur, men hu er søt (ah)
Baby, jeg make it rain (yeah, yeah)
Sitron og is (ah)
```
"""


def types(funn):
    return {f["type"] for f in funn}


class Sjekk(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        d = Path(cls.tmp.name) / "fornoyd"
        d.mkdir()
        (d / "lemonade.md").write_text(FASIT, encoding="utf-8")
        cls.fasit = [d]
        cls.funn = rb.sjekk_tekst(DATA, LAT, cls.fasit)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def msgs(self, kind):
        return " | ".join(f["melding"] for f in self.funn if f["type"] == kind)

    def test_gjenbruk_fra_fasit(self):
        self.assertIn("make it rain", self.msgs("gjenbruk"))
        self.assertIn("lemonade.md", self.msgs("gjenbruk"))

    def test_gjentatte_ord_utenfor_hook(self):
        self.assertIn("kompis ×3", self.msgs("gjentakelse"))

    def test_klisje_i_merke_teller_ikke(self):
        funn = rb.sjekk_tekst(DATA, "[Outro - fading vocals]\nYeah (yeah)\n", [])
        self.assertNotIn("klisjé", types(funn))
        self.assertTrue(any("fading" in f["melding"] for f in funn), funn)

    def test_merker(self):
        m = self.msgs("merke")
        self.assertIn("Verse 1", m)
        self.assertIn("rap", m)
        self.assertIn("sax", m)
        self.assertNotIn("Verse 2", m)

    def test_hook_ulik(self):
        self.assertIn("vil", self.msgs("refreng"))

    def test_vers_mot_vers(self):
        self.assertIn("linje 2", self.msgs("vers"))

    def test_ekko_vers_hook(self):
        self.assertIn("kan", self.msgs("ekko"))

    def test_klisje(self):
        self.assertIn("neon", self.msgs("klisjé"))

    def test_adlibs(self):
        self.assertIn("ad-libs", self.msgs("ad-libs"))

    def test_uttale(self):
        m = self.msgs("uttale")
        self.assertIn("HÅN", m)
        self.assertIn("«B»", m)
        self.assertIn("rain", m)  # «make» finnes i ordbanken (en make)

    def test_ren_tekst_gir_faa_funn(self):
        ren = "[Hook]\nStille vann (ah)\nIngen veit hva jeg kan (shh)\n\n[Verse 1 - rap]\nHun går forbi (ah)\nJeg står igjen (yeah)\n"
        funn = rb.sjekk_tekst(DATA, ren, [])
        self.assertFalse({"gjenbruk", "merke", "refreng", "klisjé", "uttale"} & types(funn), funn)

    def test_cli(self):
        p = Path(self.tmp.name) / "lat.txt"
        p.write_text(LAT, encoding="utf-8")
        out = run("--tekst", str(p), "--sjekk", "--fasit", str(self.fasit[0]))
        self.assertIn("Sjekk", out)
        self.assertIn("make it rain", out)


class Lydregler(unittest.TestCase):
    def test_skj_hj_hv_gj(self):
        self.assertEqual(DATA.info("skjønner").lyd, "sjønner")
        self.assertEqual(DATA.info("hjem").lyd, "jem")
        self.assertEqual(DATA.info("hva").lyd, "va")
        self.assertEqual(DATA.info("gjeng").lyd, "jeng")

    def test_rim_er_uendret(self):
        self.assertEqual(DATA.info("skjønner").nokkel, "ønner")
        self.assertEqual(DATA.info("hjem").nokkel, "em")


if __name__ == "__main__":
    unittest.main()
