"""Kontrollregresjoner med en liten, eksplisitt ordliste, uten nedlasting."""
import importlib.machinery
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader('rim_bm_v26', str(ROOT / 'rim-bm'))
spec = importlib.util.spec_from_loader(loader.name, loader)
rb = importlib.util.module_from_spec(spec)
sys.modules[loader.name] = rb
loader.exec_module(rb)


class Kontroll(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.words = Path(cls.tmp.name) / 'ord.txt'
        cls.words.write_text('sol\nstol\nher\nser\njeg\ndeg\n', encoding='utf-8')
        cls.data = rb.Data(cls.words, Path(cls.tmp.name) / 'uttale', Path(cls.tmp.name) / 'frekvens', False, False, Path(cls.tmp.name) / 'egne')

    def check(self, text, profil='sang'):
        return rb.sjekk_tekst(self.data, text, [], profil)

    def test_prechorus_is_not_hook(self):
        for label in ('Pre-Chorus', 'Pre Chorus', 'Pre-refreng', 'Førrefreng'):
            with self.subTest(label=label):
                text = f'[{label}]\nher\n[Chorus]\nsol\nstol\n[Chorus]\nsol\nstol\n'
                self.assertFalse(any(f['type'] == 'refreng' for f in self.check(text)))

    def test_shorter_and_longer_hook(self):
        for second in ('sol', 'sol\nstol\nher'):
            with self.subTest(second=second):
                findings = self.check('[Chorus]\nsol\nstol\n[Chorus]\n' + second)
                self.assertTrue(any(f['type'] == 'refreng' and 'linjer mot' in f['melding'] for f in findings))

    def test_changed_hook(self):
        self.assertTrue(any(f['type'] == 'refreng' for f in self.check('[Chorus]\nsol\n[Chorus]\nstol')))

    def test_identical_hook(self):
        self.assertFalse(any(f['type'] == 'refreng' for f in self.check('[Chorus]\nsol\n[Chorus]\nsol')))

    def test_profiles(self):
        # Fra 2.7.0 godtas rene versmerker; rapkravet gjelder beskrevne versmerker.
        text = '[Verse 1 - cold flow]\nsol\n'
        self.assertFalse(any('sier ikke rap' in f['melding'] for f in self.check(text)))
        for profile in ('rap', 'hoggorm'):
            self.assertTrue(any('sier ikke rap' in f['melding'] for f in self.check(text, profile)))
        self.assertEqual(rb.sjekk_tekst(self.data, text, []), self.check(text, 'hoggorm'))

    def test_cli_profile(self):
        song = Path(self.tmp.name) / 'lat.txt'
        song.write_text('[Verse 1]\nsol\n', encoding='utf-8')
        result = subprocess.run([sys.executable, str(ROOT / 'rim-bm'), '--wordlist', str(self.words), '--ingen-cache', '--tekst', str(song), '--sjekk', '--profil', 'sang', '--json'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(any('sier ikke rap' in f['melding'] for f in json.loads(result.stdout)['sjekk']))

    def test_invalid_profile(self):
        with self.assertRaises(ValueError):
            self.check('sol', 'ukjent')
