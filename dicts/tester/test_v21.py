"""Uavhengige feileksempler og CLI-kontrakter for 2.1."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from test_rim_bm import rb, DATA, run


class NewRegressions(unittest.TestCase):
    def test_three_syllable_hiatus(self):
        for word in ('protein', 'koffein'):
            self.assertEqual(DATA.info(word).stav, 3)
            self.assertEqual(DATA.info(word).trykk, 3)

    def test_actual_diphthongs_unchanged(self):
        for word in ('stein', 'vei', 'sau', 'høy'):
            self.assertEqual(DATA.info(word).stav, 1)

    def test_review_stress_examples(self):
        for word in ('radio', 'mulighet', 'kjærlighet'):
            self.assertEqual(DATA.info(word).trykk, 1)
        for word in ('planet', 'komet'):
            self.assertEqual(DATA.info(word).trykk, 2)

    def test_new_pair_and_negative_controls(self):
        self.assertTrue(rb.check_pair(DATA, 'fred', 'sted')['treff'])
        for a, b in [('fred', 'fryd'), ('her', 'ser'), ('min', 'måne')]:
            self.assertFalse(rb.check_pair(DATA, a, b)['treff'])

    def test_variants_preserve_short_and_long(self):
        for a, b in [('min', 'fin'), ('min', 'vinn'), ('din', 'fin'), ('sin', 'fin')]:
            r = rb.check_pair(DATA, a, b)
            self.assertTrue(r['treff'])
            self.assertEqual(len(r['varianter'][0]), 2)
        self.assertIn('variantavhengig', run('--par', 'min', 'fin'))

    def test_variants_indexed_in_both_directions(self):
        for a, b in [('min', 'fin'), ('fin', 'min')]:
            groups = DATA.rhymes(a, limit=10000)[1]
            self.assertIn(b, [w for ws in groups.values() for w in ws])

    def test_batch_order_and_separate_queries(self):
        result = json.loads(run('--batch', 'sol', 'kald', '--json', '-n', '4'))
        self.assertEqual([r['ord']['ord'] for r in result], ['sol', 'kald'])
        self.assertIn('stol', result[0]['grupper']['1'])
        self.assertIn('all', result[1]['grupper']['1'])
        self.assertEqual(result, json.loads(run('sol', 'kald', '--json', '-n', '4')))

    def test_batch_reuses_data(self):
        from unittest.mock import patch
        with patch.object(rb, 'Data', wraps=rb.Data) as ctor:
            run('--batch', 'sol', 'kald', '--json', '-n', '1')
            self.assertEqual(ctor.call_count, 1)

    def test_json_exposes_method_and_variants(self):
        result = json.loads(run('--info', 'min', 'radio', 'stol', '--json'))
        self.assertEqual(len(result[0]['varianter']), 2)
        self.assertEqual(result[1]['metode'], 'uttalefil')
        self.assertEqual(result[2]['metode'], 'heuristikk')
        self.assertTrue(all(r['usikker'] for r in result))

    def test_bad_numeric_options_rejected(self):
        for args in [('sol', '-n', '-1'), ('sol', '-n', '0'), ('sol', '--stav', '0')]:
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as err:
                rb.main(list(args))
            self.assertEqual(err.exception.code, 2)

    def test_exclusive_modes(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            rb.main(['--info', '--par', 'min', 'fin'])

    def test_unicode_normalization(self):
        self.assertEqual(DATA.info('idé').nokkel, DATA.info('ide\u0301').nokkel)
        self.assertEqual(DATA.info('idé').stav, DATA.info('ide\u0301').stav)

    def test_dot_is_boundary_not_part_of_key(self):
        info = rb.analyse('prøveord', {'prøveord': "prote.'in"}, DATA.wordset)
        self.assertEqual((info.stav, info.trykk, info.nokkel), (3, 3, 'in'))

    def test_custom_file_overrides_bundled_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'ord.txt').write_text('min\nfin\n')
            (root/'uttale.txt').write_text('min minn\n')
            d = rb.Data(root/'ord.txt', root/'uttale.txt', root/'missing', False, False)
            self.assertFalse(rb.check_pair(d, 'min', 'fin')['treff'])
            self.assertEqual(len(d.infos('min')), 1)

    def test_text_reports_variant_ambiguity(self):
        rep = rb.analyse_text(DATA, '[Verse]\nBilen er min\nProtein og koffein\n')
        self.assertEqual(rep['seksjoner'][0]['stavelser'], [4, 7])
        self.assertTrue(any('første variant' in s for s in rep['advarsler']))

    def test_homograph_both_stresses(self):
        self.assertEqual([i.trykk for i in DATA.infos('finere')], [1, 2])


if __name__ == '__main__':
    unittest.main()
