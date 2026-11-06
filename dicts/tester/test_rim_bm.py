"""Tester for rim-bm v2. Kjør: python3 -m unittest discover -s tester -v  (fra pakkemappa)."""
from __future__ import annotations

import importlib.machinery
import atexit
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SCRIPT = Path(os.environ.get("RIM_BM_SCRIPT", ROOT / "rim-bm"))

loader = importlib.machinery.SourceFileLoader("rim_bm", str(SCRIPT))
spec = importlib.util.spec_from_loader("rim_bm", loader)
rb = importlib.util.module_from_spec(spec)
sys.modules["rim_bm"] = rb
loader.exec_module(rb)

WORDLIST = Path(os.environ.get("RIM_BM_WORDLIST", rb.WORDLIST))
UTTALE = Path(os.environ.get("RIM_BM_UTTALE", rb.UTTALE))
FREKVENS = Path(os.environ.get("RIM_BM_FREKVENS", rb.FREKVENS))
# Testene bruker ikke den personlige egne-ord.txt, så nye ord der ikke endrer fasiten.
rb.EGNE = HERE / "ingen-egne-ord.txt"
_TEST_CACHE = tempfile.TemporaryDirectory(prefix="rim-bm-tests-")
atexit.register(_TEST_CACHE.cleanup)
rb.CACHE_DIR = Path(_TEST_CACHE.name)
DATA = rb.Data(WORDLIST, UTTALE, FREKVENS, skrift=False)


def run(*argv: str) -> str:
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = rb.main(list(argv))
    assert code == 0, f"exit {code} for {argv}"
    return buf.getvalue()


class Stavelser(unittest.TestCase):
    def test_vokalpar_som_ikke_er_diftonger(self):
        for w, n in {"sjøen": 2, "snøen": 2, "skoa": 2, "mye": 2, "noe": 2, "noen": 2, "sier": 2}.items():
            self.assertEqual(DATA.info(w).stav, n, w)

    def test_diftonger(self):
        for w, n in {"vei": 1, "høyt": 1, "sau": 1, "meg": 1, "deilig": 2}.items():
            self.assertEqual(DATA.info(w).stav, n, w)

    def test_aksent(self):
        self.assertEqual(DATA.info("idé").stav, 2)
        self.assertEqual(DATA.info("én").stav, 1)

    def test_vanlige_ord(self):
        for w, n in {"gatene": 3, "bowlinga": 3, "kald": 1, "hennessy": 3, "horten": 2}.items():
            self.assertEqual(DATA.info(w).stav, n, w)

    def test_stav_filter_finner_tostavelsesord(self):
        _, groups = DATA.rhymes("snøen", stav=2)
        self.assertIn("sjøen", groups.get(2, []))


class Trykk(unittest.TestCase):
    def test_flere_trykklette_stavelser(self):
        cases = {"gatene": "atene", "tellinga": "ellinga", "bowlinga": "owlinga",
                 "løpende": "øpende", "bevegelse": "egelse"}
        for w, key in cases.items():
            self.assertEqual(DATA.info(w).nokkel, key, w)

    def test_trykk_paa_slutten(self):
        cases = {"igjen": "enn", "idé": "e", "universitet": "et", "normal": "al",
                 "konsekvens": "ens", "bilalarm": "arm"}
        for w, key in cases.items():
            self.assertEqual(DATA.info(w).nokkel, key, w)

    def test_prefiks(self):
        self.assertEqual(DATA.info("betale").nokkel, "ale")
        self.assertEqual(DATA.info("fortelle").nokkel, "elle")
        self.assertEqual(DATA.info("fortjene").nokkel, "ene")
        self.assertEqual(DATA.info("bedre").nokkel, "edre")
        self.assertEqual(DATA.info("begge").nokkel, "egge")
        self.assertEqual(DATA.info("fordel").nokkel, "ordel")

    def test_ere_verb_og_genitiv(self):
        self.assertEqual(DATA.info("studere").nokkel, "ere")
        self.assertEqual(DATA.info("mannens").nokkel, "annens")


class Uttale(unittest.TestCase):
    def pair(self, a, b):
        return rb.check_pair(DATA, a, b)

    def test_rene_rim_som_staves_ulikt(self):
        for a, b in [("kald", "skall"), ("her", "nær"), ("meg", "vei"), ("jeg", "lei"),
                     ("land", "mann"), ("sagt", "takt"), ("rødt", "støtt"), ("ord", "bor"),
                     ("kveld", "selv"), ("blod", "no"), ("godt", "flott"), ("igjen", "venn"),
                     ("gjelder", "kvelder")]:
            r = self.pair(a, b)
            self.assertTrue(r["treff"], f"{a}/{b}: {r}")

    def test_svake_rim_gir_ikke_treff(self):
        for a, b in [("her", "ser"), ("var", "normal"), ("kald", "vei")]:
            self.assertFalse(self.pair(a, b)["treff"], f"{a}/{b}")

    def test_skjeve_rim(self):
        self.assertTrue(self.pair("tjener", "slenger")["skjevt"])
        self.assertTrue(self.pair("baby", "lady")["skjevt"])

    def test_samme_ord(self):
        r = self.pair("kald", "kald")
        self.assertTrue(r["samme_ord"])
        self.assertFalse(r["treff"])

    def test_skrift_modus_som_v1(self):
        self.assertFalse(self.pair("kald", "skall")["skrift_treff"])
        self.assertTrue(self.pair("her", "ser")["skrift_treff"])


class Stoy(unittest.TestCase):
    def test_ingen_egennavn_eller_bindestrek(self):
        for w in ("harald", "ronald", "a-ene", "ann"):
            self.assertNotIn(w, DATA.wordset, w)

    def test_ingen_sammensetninger_med_sokeordet(self):
        _, groups = DATA.rhymes("kald", limit=10000)
        flat = [w for ws in groups.values() for w in ws]
        self.assertNotIn("iskald", flat)
        self.assertNotIn("vinterkald", flat)
        _, groups_all = DATA.rhymes("kald", limit=10000, filt=False)
        self.assertIn("iskald", [w for ws in groups_all.values() for w in ws])

    def test_vanlige_ord_forst(self):
        first = DATA.rhymes("kald", limit=12)[1][1]
        for w in ("all", "fall", "skall"):
            self.assertIn(w, first, w)
        self.assertNotIn("fald", first)


class Kommandoer(unittest.TestCase):
    def test_par(self):
        out = run("--par", "kald", "skall")
        self.assertIn("kald / skall — oppslag: rim-bm treff", out)

    def test_par_json(self):
        res = json.loads(run("--par", "her", "nær", "ser", "--json"))
        self.assertEqual([r["treff"] for r in res], [True, False])

    def test_info(self):
        out = run("--info", "gatene")
        self.assertIn("nøkkel «atene»", out)

    def test_liste(self):
        out = run("kald", "-n", "6")
        self.assertIn("nøkkel «all»", out)
        self.assertIn("skall", run("kald"))

    def test_skjevt_liste(self):
        out = run("tjener", "--skjevt", "--stav", "2")
        self.assertIn("penger", out)


class Laat(unittest.TestCase):
    """Regresjon: «Disse gatene gjorde meg kald»."""

    @classmethod
    def setUpClass(cls):
        cls.rep = rb.analyse_text(DATA, (HERE / "disse-gatene.txt").read_text(encoding="utf-8"))
        cls.sec = {s["navn"]: s for s in cls.rep["seksjoner"]}

    def test_hook(self):
        hook = self.sec["[Hook]"]
        self.assertEqual(hook["skjema"], "ABABAA")
        self.assertEqual(hook["stavelser"], [9, 8, 9, 7, 6, 9])

    def test_vers_stavelser(self):
        self.assertEqual(self.sec["[Verse 1]"]["stavelser"],
                         [13, 13, 14, 14, 12, 12, 13, 12, 7, 7, 7, 8, 13, 12, 15, 13])
        self.assertEqual(self.sec["[Verse 2]"]["stavelser"],
                         [13, 14, 13, 14, 13, 13, 15, 14, 14, 14, 13, 14])

    def test_vers_skjema(self):
        self.assertEqual(self.sec["[Verse 1]"]["skjema"], "AABBCCDDEEEEFFGG")
        self.assertEqual(self.sec["[Verse 2]"]["skjema"], "AABBCCDDEEFF")

    def test_alle_rimpar_treffer(self):
        bad = [r for r in self.rep["rimpar"] if not r["treff"]]
        self.assertEqual(bad, [])
        self.assertGreaterEqual(len(self.rep["rimpar"]), 15)

    def test_tall_gir_advarsel(self):
        rep = rb.analyse_text(DATA, "[Verse]\nTjente 1 mill\nbak bowlinga hver kveld\n")
        self.assertTrue(rep["advarsler"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
