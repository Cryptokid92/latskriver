"""Regresjoner for reviewfunn, med isolerte data uten private referanser."""
import importlib.machinery
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader('rim_bm_v261', str(ROOT / 'rim-bm'))
spec = importlib.util.spec_from_loader(loader.name, loader)
rb = importlib.util.module_from_spec(spec)
sys.modules[loader.name] = rb
loader.exec_module(rb)


class ReviewRegresjoner(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.root = Path(cls.tmp.name)
        cls.words = cls.root / 'ord.txt'
        cls.words.write_text('sol\nstol\nher\nmin\nfin\nvinn\nmynter\nbegynner\npynter\n'
                             'testord\nvariantord\nreserveord\n', encoding='utf-8')
        cls.uttale = cls.root / 'uttale.txt'
        cls.uttale.write_text("testord amp\nvariantord anf | anp | 'anpe\nreserveord amf\n", encoding='utf-8')
        cls.data = rb.Data(cls.words, cls.uttale, cls.root / 'frekvens', False, False, cls.root / 'egne')

    def cli(self, *args):
        result = subprocess.run([sys.executable, str(ROOT / 'rim-bm'), '--wordlist', str(self.words),
                                 '--uttale', str(self.uttale), '--egne', str(self.root / 'egne'),
                                 '--frekvens', str(self.root / 'frekvens'), '--ingen-cache', *args],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def reuse(self, song, reference):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'referanse.txt').write_text(reference, encoding='utf-8')
            return [f for f in rb.sjekk_tekst(self.data, song, [Path(tmp)], 'sang')
                    if f['type'] == 'gjenbruk']

    def test_repeated_reference_hook_does_not_hide_reuse(self):
        phrase = 'Nøkkelen ligger under den røde stolen\n'
        song = '[Chorus]\n' + phrase + '[Verse 1]\nBussen kjører videre\nVinduet står åpent\nKaffen blir kald\n'
        for repeats in (1, 3, 10):
            with self.subTest(repeats=repeats):
                reference = '[Chorus]\n' + phrase * repeats + '[Verse 1]\nHun lukker døra\nHan venter ute\n'
                self.assertTrue(self.reuse(song, reference))

    def test_partial_overlap_is_not_treated_as_same_song(self):
        shared = 'Nøkkelen ligger under den røde stolen\nHun legger jakka på den tomme benken\n'
        self.assertTrue(self.reuse(shared + 'Bussen kjører videre\n', shared + 'Toget kjører videre\n'))

    def test_identical_normalized_song_is_skipped(self):
        song = '[Verse 1]\nNøkkelen ligger under stolen! (ah)\nHun går gjennom døra\n'
        reference = '# Tittel\n[Verse 1 - rap]\nNØKKELEN ligger under stolen. (yeah)\n\nHun går gjennom døra\n'
        self.assertFalse(self.reuse(song, reference))

    def test_reordered_lines_are_not_treated_as_identical_song(self):
        a, b = 'Nøkkelen ligger under stolen\n', 'Hun går gjennom døra\n'
        self.assertTrue(self.reuse(a + b, b + a))

    def test_empty_hooks_at_start_middle_and_end_are_reported(self):
        for song in ('[Chorus]\n[Verse]\nher\n[Chorus]\nsol\nstol\n',
                     '[Chorus]\nsol\nstol\n[Chorus]\n[Verse]\nher\n',
                     '[Chorus]\nsol\nstol\n[Verse]\nher\n[Chorus]\n'):
            with self.subTest(song=song):
                rep = rb.analyse_text(self.data, song)
                self.assertEqual(len(rep['seksjoner']), 3)
                findings = rb.sjekk_tekst(self.data, song, [], 'sang')
                self.assertTrue(any(f['type'] == 'refreng' and 'linjer mot' in f['melding'] for f in findings))

    def test_adlib_only_hook_has_no_main_text(self):
        song = '[Chorus]\nsol\n[Chorus]\n(yeah)\n'
        self.assertTrue(any(f['type'] == 'refreng' and 'mangler hovedtekst' in f['melding']
                            for f in rb.sjekk_tekst(self.data, song, [], 'sang')))

    def test_single_empty_hook_cli(self):
        song = self.root / 'tomt-refreng.txt'
        song.write_text('[Chorus]\n', encoding='utf-8')
        report = json.loads(self.cli('--tekst', str(song), '--sjekk', '--profil', 'sang', '--json'))
        self.assertTrue(any(f['type'] == 'refreng' for f in report['sjekk']))
        self.assertIn('mangler hovedtekst', self.cli('--tekst', str(song), '--sjekk', '--profil', 'sang'))

    def test_blank_text_does_not_create_phantom_section(self):
        self.assertEqual(rb.analyse_text(self.data, '\n  \n')['seksjoner'], [])

    def test_text_and_rhyme_log_use_same_first_variant(self):
        report = rb.analyse_text(self.data, '[Verse]\nmin\nfin\n')
        self.assertEqual(report['seksjoner'][0]['linjer'][1]['type'], 'skjevt')
        pair = report['rimpar'][0]
        self.assertFalse(pair['treff'])
        self.assertTrue(pair['skjevt'])
        self.assertEqual(pair['nokkel'], ['inn', 'in'])
        self.assertEqual(len(pair['varianter'][0]), 2)
        output = io.StringIO()
        with redirect_stdout(output):
            rb.print_text_report(report)
        self.assertNotIn('rim-bm treff', output.getvalue())
        self.assertIn('første uttalevariant brukt', output.getvalue())

    def test_pair_cli_still_considers_all_variants(self):
        pair = json.loads(self.cli('--par', 'min', 'fin', '--json'))[0]
        self.assertTrue(pair['treff'])
        self.assertEqual(pair['nokkel'], ['in', 'in'])

    def test_search_json_modes_and_scores_in_single_and_batch(self):
        for flags, mode in (([], 'rim'), (['--skjevt'], 'skjevt'), (['--assonans'], 'assonans')):
            with self.subTest(mode=mode):
                single = json.loads(self.cli('mynter', *flags, '--json'))
                batch = json.loads(self.cli('--batch', 'mynter', 'sol', *flags, '--json'))
                self.assertEqual(single, batch[0])
                self.assertTrue(all(r['sokemodus'] == mode for r in batch))
                if mode == 'assonans':
                    self.assertEqual(single['assonans_score']['begynner'], 0.92)
                    self.assertNotIn('pynter', single['assonans_score'])
                    self.assertEqual(set(single['assonans_score']),
                                     {w for ws in single['grupper'].values() for w in ws})
                else:
                    self.assertNotIn('assonans_score', single)

    def test_assonance_best_variant_score_respects_filter_and_limit(self):
        report = json.loads(self.cli('testord', '--assonans', '--json', '--stav', '1', '-n', '1'))
        self.assertEqual(report['grupper'], {'1': ['variantord']})
        self.assertEqual(report['assonans_score'], {'variantord': 1.0})
        report = json.loads(self.cli('testord', '--assonans', '--json', '--stav', '2'))
        self.assertEqual(report['assonans_score'], {'variantord': 0.8})

    def test_assonance_text_output_includes_scores(self):
        for args in (('mynter',), ('--batch', 'mynter', 'sol')):
            with self.subTest(args=args):
                output = self.cli(*args, '--assonans')
                self.assertIn('assonans', output)
                self.assertIn('begynner (92 %)', output)

    def test_assonance_empty_results_are_explicit(self):
        report = json.loads(self.cli('sol', '--assonans', '--json', '--stav', '50'))
        self.assertEqual(report['sokemodus'], 'assonans')
        self.assertEqual(report['grupper'], {})
        self.assertEqual(report['assonans_score'], {})
