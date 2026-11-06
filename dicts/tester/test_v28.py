"""Flowblokker (2.8, portert fra PR #6) med en liten, eksplisitt ordliste, uten nedlasting."""
import importlib.machinery
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader('rim_bm_v28', str(ROOT / 'rim-bm'))
spec = importlib.util.spec_from_loader(loader.name, loader)
rb = importlib.util.module_from_spec(spec)
sys.modules[loader.name] = rb
loader.exec_module(rb)


def linje(n):
    """En linje med n stavelser (sol er én stavelse)."""
    return ' '.join(['sol'] * n)


LAT = '\n'.join([
    '[Verse 1]',
    '{flow A 4}',
    linje(4), linje(4),
    '{flow B}',
    linje(9), linje(9),
    '[Verse 2]',
    '{flow A}',
    linje(4), linje(5),
    '',
])


class Flow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        tmp = Path(cls.tmp.name)
        cls.words = tmp / 'ord.txt'
        cls.words.write_text('sol\nstol\nher\nser\n', encoding='utf-8')
        cls.data = rb.Data(cls.words, tmp / 'uttale', tmp / 'frekvens', False, False, tmp / 'egne')

    def check(self, text, profil='rap'):
        return rb.sjekk_tekst(self.data, text, [], profil)

    def flow(self, text, profil='rap'):
        return [f['melding'] for f in self.check(text, profil) if f['type'] == 'flow']

    def test_marker_parsing(self):
        self.assertEqual(rb.flow_merke('{flow A 10}'), ('A', 10))
        self.assertEqual(rb.flow_merke('{ flyt b }'), ('B', None))
        self.assertEqual(rb.flow_merke('{Flow 2}'), ('2', None))
        self.assertIsNone(rb.flow_merke('{flow}'))
        self.assertIsNone(rb.flow_merke('sol {flow A}'))

    def test_blocks_in_report(self):
        rep = rb.analyse_text(self.data, LAT)
        v1, v2 = rep['seksjoner']
        self.assertEqual(len(v1['linjer']), 4)  # merkene telles ikke som linjer
        self.assertEqual([l['flow'] for l in v1['linjer']], ['A', 'A', 'B', 'B'])
        self.assertEqual(v1['blokker'], [
            {'flow': 'A', 'mal': 4, 'linjer': [1, 2], 'stavelser': [4, 4]},
            {'flow': 'B', 'mal': None, 'linjer': [3, 4], 'stavelser': [9, 9]},
        ])
        self.assertEqual(v2['blokker'][0]['linjer'], [1, 2])

    def test_no_markers_unchanged(self):
        rep = rb.analyse_text(self.data, '[Verse 1]\nsol\n')
        self.assertEqual(rep['seksjoner'][0]['blokker'], [])
        self.assertIsNone(rep['seksjoner'][0]['linjer'][0]['flow'])

    def test_planned_switch_not_flagged(self):
        # Vers to bytter flow på et annet sted enn vers én; det er planlagt, ikke avvik.
        text = '\n'.join(['[Verse 1]', '{flow A}', linje(4), linje(4), '{flow B}', linje(10), linje(10),
                          '[Verse 2]', '{flow B}', linje(10), '{flow A}', linje(4), linje(4)])
        findings = self.check(text)
        self.assertFalse([f for f in findings if f['type'] in ('flow', 'vers')], findings)

    def test_without_markers_old_verse_check(self):
        text = '\n'.join(['[Verse 1]', linje(4), linje(4), '[Verse 2]', linje(10), linje(4)])
        findings = self.check(text)
        self.assertTrue(any(f['type'] == 'vers' and 'linje 1' in f['melding'] for f in findings))
        self.assertFalse(any(f['type'] == 'flow' for f in findings))

    def test_deviation_from_target(self):
        text = '\n'.join(['[Verse 1]', '{flow A 4}', linje(4), linje(8), linje(7)])
        msgs = self.flow(text)
        self.assertEqual(msgs, ['Verse 1 linje 2: 8 stavelser, flow A har 4 (mål)'])

    def test_deviation_across_sections(self):
        text = LAT.replace(linje(5), linje(9))
        self.assertEqual(self.flow(text), ['Verse 2 linje 2: 9 stavelser, flow A har 4 (mål)'])

    def test_deviation_from_most_common(self):
        text = '\n'.join(['[Hook]', '{flow H}', linje(6), linje(6), linje(6), linje(1)])
        self.assertEqual(self.flow(text), ['Hook linje 4: 1 stavelser, flow H har 6 (vanligst)'])

    def test_within_tolerance(self):
        text = '\n'.join(['[Verse 1]', '{flow A 8}', linje(8), linje(11), linje(5)])
        self.assertEqual(self.flow(text), [])

    def test_conflicting_targets(self):
        text = '\n'.join(['[Verse 1]', '{flow A 4}', linje(4), '[Verse 2]', '{flow A 6}', linje(4)])
        self.assertIn('flow A har ulike mål: 4, 6 — det første gjelder', self.flow(text))

    def test_verse_lines_without_marker(self):
        text = '\n'.join(['[Verse 1]', linje(4), '{flow A}', linje(4), '[Verse 2]', linje(4)])
        msgs = self.flow(text)
        self.assertIn('Verse 1: linje 1 mangler flowmerke', msgs)
        self.assertIn('Verse 2: linje 1 mangler flowmerke', msgs)

    def test_markers_are_not_lyrics(self):
        findings = self.check(LAT)
        self.assertFalse(any('flow' in f['melding'] for f in findings if f['type'] != 'flow'), findings)

    def test_unknown_marker_warns(self):
        rep = rb.analyse_text(self.data, '[Verse 1]\n{flw A}\nsol\n')
        self.assertEqual(len(rep['seksjoner'][0]['linjer']), 1)
        self.assertTrue(any('Ukjent merke' in w for w in rep['advarsler']))

    def test_cli_report_and_json(self):
        song = Path(self.tmp.name) / 'lat.txt'
        song.write_text(LAT, encoding='utf-8')
        base = [sys.executable, str(ROOT / 'rim-bm'), '--wordlist', str(self.words), '--ingen-cache', '--tekst', str(song)]
        out = subprocess.run(base + ['--sjekk', '--profil', 'rap'], capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn('Flow: A=4: 4 4 | B: 9 9', out.stdout)
        js = subprocess.run(base + ['--json'], capture_output=True, text=True)
        self.assertEqual(json.loads(js.stdout)['seksjoner'][1]['blokker'][0]['flow'], 'A')



if __name__ == '__main__':
    unittest.main()
