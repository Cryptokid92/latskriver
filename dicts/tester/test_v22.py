"""Tester for rettelsene i 2.2: punktum i input, cache-opprydding og generelle trykkregler."""
import os
import tempfile
import time
import unittest
from pathlib import Path

from test_rim_bm import rb, DATA, run


class Punktum(unittest.TestCase):
    def test_tegn_i_input_fjernes(self):
        for word in ("kald.", "kald,", "kald!", "«kald»"):
            self.assertEqual(DATA.info(word).nokkel, "all", word)
        self.assertTrue(rb.check_pair(DATA, "kald.", "skall")["treff"])
        self.assertIn("rim-bm treff", run("--par", "kald.", "skall"))

    def test_punktum_virker_fortsatt_i_uttalefila(self):
        self.assertEqual(DATA.info("protein").stav, 3)
        self.assertEqual(DATA.info("protein").nokkel, "in")


class TrykkHet(unittest.TestCase):
    def test_het_ord_uten_unntak(self):
        cases = {"virkelighet": "irkelighet", "ærlighet": "ærlighet", "hemmelighet": "emmelighet",
                 "evighet": "evighet", "sikkerhet": "ikkerhet", "ensomhet": "ensomhet",
                 "enighet": "enighet", "frihet": "ihet", "nyhet": "yhet"}
        for w, key in cases.items():
            self.assertEqual(DATA.info(w).nokkel, key, w)
            self.assertEqual(DATA.info(w).metode, "heuristikk", w)


class TrykkHiatus(unittest.TestCase):
    def test_ie_io_eo(self):
        cases = {"studio": "udio", "video": "ideo", "familie": "ilie", "familien": "ilien",
                 "familiene": "iliene", "historie": "orie", "studie": "udie", "komedie": "edie"}
        for w, key in cases.items():
            self.assertEqual(DATA.info(w).nokkel, key, w)

    def test_trykk_paa_i_er_uendret(self):
        cases = {"parti": "i", "partiet": "iet", "energien": "ien", "geografien": "ien",
                 "kategorien": "ien", "batteriet": "iet"}
        for w, key in cases.items():
            self.assertEqual(DATA.info(w).nokkel, key, w)


class Cache(unittest.TestCase):
    def test_prune_beholder_tre_nyeste_per_modus(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            now = time.time()
            for n in range(5):
                p = d / f"indeks-uttale-{n:016d}.pkl"
                p.write_bytes(b"x")
                os.utime(p, (now - 100 * n, now - 100 * n))
            other = d / "indeks-skrift-0000000000000000.pkl"
            other.write_bytes(b"x")
            old_tmp, new_tmp = d / "indeks-uttale-a-1.tmp", d / "indeks-uttale-a-2.tmp"
            old_tmp.write_bytes(b"x")
            new_tmp.write_bytes(b"x")
            os.utime(old_tmp, (now - 7200, now - 7200))
            rb.prune_cache(d, "uttale")
            left = sorted(p.name for p in d.glob("indeks-uttale-*.pkl"))
            self.assertEqual(left, [f"indeks-uttale-{n:016d}.pkl" for n in range(3)])
            self.assertTrue(other.exists())
            self.assertFalse(old_tmp.exists())
            self.assertTrue(new_tmp.exists())

    def test_endret_uttalefil_gir_ikke_ubegrenset_vekst(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ord.txt").write_text("kald\nskall\nfall\nvei\n", encoding="utf-8")
            old = rb.CACHE_DIR
            rb.CACHE_DIR = root / "cache"
            try:
                for n in range(6):
                    (root / "uttale.txt").write_text(f"testord{n}  testord{n}\n", encoding="utf-8")
                    rb.Data(root / "ord.txt", root / "uttale.txt", root / "mangler", False, True)
                    time.sleep(0.01)
                self.assertLessEqual(len(list((root / "cache").glob("indeks-uttale-*.pkl"))), rb.CACHE_KEEP)
            finally:
                rb.CACHE_DIR = old


if __name__ == "__main__":
    unittest.main()
