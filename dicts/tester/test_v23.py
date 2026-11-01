"""Tester for 2.3: assonans-score og egen ordliste (egne-ord.txt)."""
import tempfile
import unittest
from pathlib import Path

from test_rim_bm import rb, DATA, run


class Assonans(unittest.TestCase):
    def test_score_for_rapRim(self):
        self.assertGreaterEqual(rb.assonans("ynter", "ynner"), 0.85)
        self.assertGreaterEqual(rb.assonans("avna", "avnet"), 0.65)
        self.assertEqual(rb.assonans("all", "æi"), 0.0)
        self.assertEqual(rb.assonans("all", "all"), 1.0)

    def test_bare_lik_vokal_er_ikke_nok(self):
        # cash/nær: samme vokal, helt ulike konsonanter — skal ikke merkes i --tekst
        self.assertLess(rb.assonans("æsj", "ær"), rb.ASSONANS_MIN)

    def test_grad(self):
        self.assertEqual(rb.assonans_grad(0.9), "sterk")
        self.assertEqual(rb.assonans_grad(0.7), "middels")
        self.assertEqual(rb.assonans_grad(0.55), "svak")
        self.assertIsNone(rb.assonans_grad(0.3))

    def test_par_viser_assonans_naar_rimet_ikke_treffer(self):
        r = rb.check_pair(DATA, "mynter", "begynner")
        self.assertFalse(r["treff"])
        self.assertEqual(r["assonans_grad"], "sterk")
        self.assertIn("assonans", run("--par", "mynter", "begynner"))
        self.assertNotIn("assonans", run("--par", "kald", "skall"))

    def test_tekst_merker_assonans(self):
        rep = rb.analyse_text(DATA, "[Verse]\nJakka henger tungt, det er ikke mynter\nGutta retter seg når jeg begynner\n")
        last = rep["seksjoner"][0]["linjer"][1]
        self.assertEqual(last["type"], "assonans")
        self.assertEqual(rep["seksjoner"][0]["skjema"], "AB")  # assonans endrer ikke skjemaet
        self.assertEqual(rep["assonanspar"][0]["grad"], "sterk")

    def test_sok_med_assonans(self):
        _, groups = DATA.rhymes("mynter", assonans=True, limit=400)
        words = {w for ws in groups.values() for w in ws}
        self.assertIn("begynner", words)
        self.assertNotIn("pynter", words)  # rent rim, hører til vanlig søk

    def test_assonans_og_skjevt_kan_ikke_kombineres(self):
        with self.assertRaises(SystemExit):
            rb.main(["mynter", "--assonans", "--skjevt"])


class EgneOrd(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        (root / "ord.txt").write_text("kald\nskall\ndash\n", encoding="utf-8")
        (root / "frekvens.txt").write_text("dash 10\nkald 5\n", encoding="utf-8")
        (root / "egne.txt").write_text(
            "# slang og steder\ncash kæsj\nflash flæsj\ndash dæsj\nHorten\nflex\n", encoding="utf-8")
        self.root = root
        self.data = rb.Data(root / "ord.txt", root / "mangler.txt", root / "frekvens.txt",
                            False, False, egne=root / "egne.txt")

    def tearDown(self):
        self.tmp.cleanup()

    def test_egne_ord_er_med_i_indeksen(self):
        self.assertIn("horten", self.data.wordset)
        self.assertIn("flex", self.data.wordset)

    def test_uttale_fra_egne_ord(self):
        self.assertEqual(self.data.info("cash").nokkel, "æsj")

    def test_egne_ord_kommer_forst(self):
        _, groups = self.data.rhymes("cash")
        self.assertEqual(groups[1][:2], ["dash", "flash"])

    def test_egne_ord_teller_som_vanlige(self):
        _, groups = self.data.rhymes("cash", vanlige=True)
        self.assertIn("flash", groups[1])

    def test_uttale_txt_vinner_over_egne(self):
        (self.root / "uttale.txt").write_text("cash kasj\n", encoding="utf-8")
        d = rb.Data(self.root / "ord.txt", self.root / "uttale.txt", self.root / "frekvens.txt",
                    False, False, egne=self.root / "egne.txt")
        self.assertEqual(d.info("cash").nokkel, "asj")

    def test_cache_folger_egne_ord(self):
        old = rb.CACHE_DIR
        rb.CACHE_DIR = self.root / "cache"
        try:
            egne = self.root / "egne.txt"
            rb.Data(self.root / "ord.txt", self.root / "mangler.txt", self.root / "frekvens.txt", False, True, egne=egne)
            egne.write_text(egne.read_text(encoding="utf-8") + "bastø\n", encoding="utf-8")
            d = rb.Data(self.root / "ord.txt", self.root / "mangler.txt", self.root / "frekvens.txt", False, True, egne=egne)
            self.assertIn("bastø", d.wordset)
        finally:
            rb.CACHE_DIR = old


if __name__ == "__main__":
    unittest.main()
