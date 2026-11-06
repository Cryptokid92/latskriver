"""Regresjoner fra Claude/Grok-review, uten private data eller brukercache."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_v261 import rb

ROOT = Path(__file__).resolve().parents[1]


class ReviewRegresjoner(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.words = self.root / 'ord.txt'
        self.words.write_text('fall\nkald\nhakke\nskakke\ngikke\nsol\nstol\nher\nmin\nfin\n', encoding='utf-8')
        self.egne = self.root / 'egne.txt'
        self.egne.write_text('hån\nabc\n', encoding='utf-8')
        self.uttale = self.root / 'uttale.txt'
        self.data = rb.Data(self.words, self.uttale, self.root / 'frekvens', False, False, self.egne)

    def cli(self, *args, script=None, wordlist=None):
        return subprocess.run([sys.executable, str(script or ROOT / 'rim-bm'),
                               '--wordlist', str(wordlist or self.words),
                               '--uttale', str(self.uttale), '--egne', str(self.egne),
                               '--frekvens', str(self.root / 'frekvens'), *args],
                              env=dict(os.environ, RIM_BM_CACHE=str(self.root / 'cache')),
                              capture_output=True, text=True)

    def findings(self, text, kind, profile='sang'):
        return [f['melding'] for f in rb.sjekk_tekst(self.data, text, [], profile) if f['type'] == kind]

    def test_code_change_invalidates_cache_even_with_same_size_and_mtime(self):
        script = self.root / 'rim-bm'
        source = (ROOT / 'rim-bm').read_text(encoding='utf-8')
        script.write_text(source, encoding='utf-8')
        before = self.cli('fall', '--json', script=script)
        self.assertEqual(before.returncode, 0, before.stderr)
        self.assertIn('kald', json.loads(before.stdout)['grupper']['1'])
        stat = script.stat()
        old = '("ld", re.compile(r"ld(?=" + INFL + ")"), "ll")'
        new = '("ld", re.compile(r"ld(?=" + INFL + ")"), "ld")'
        self.assertIn(old, source)
        script.write_text(source.replace(old, new), encoding='utf-8')
        os.utime(script, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        after = self.cli('fall', '--json', script=script)
        uncached = self.cli('fall', '--json', '--ingen-cache', script=script)
        self.assertEqual(after.returncode, 0, after.stderr)
        self.assertEqual(uncached.returncode, 0, uncached.stderr)
        self.assertEqual(json.loads(after.stdout)['grupper'], {})
        self.assertEqual(json.loads(after.stdout), json.loads(uncached.stdout))
        self.assertEqual(len(list((self.root / 'cache').glob('*.pkl'))), 2)

    def test_contractions_are_not_stress_marks(self):
        for apostrophe in ("'", '’', '‘', 'ʼ'):
            with self.subTest(apostrophe=apostrophe):
                a, b = 'ska' + apostrophe + 'kke', 'gi' + apostrophe + 'kke'
                self.assertEqual(self.data.info(a).nokkel, 'akke')
                self.assertEqual(self.data.info(a).stav, 2)
                self.assertFalse(rb.check_pair(self.data, a, b)['treff'])
                self.assertTrue(rb.check_pair(self.data, a, 'hakke')['treff'])
                result = self.cli('--par', a, 'hakke', '--json')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(json.loads(result.stdout)[0]['treff'])

    def test_text_contractions_and_quote_marks(self):
        report = rb.analyse_text(self.data, "[Verse]\n'ska’kke'\nhakke\n'\n")
        self.assertEqual(report['seksjoner'][0]['stavelser'], [2, 2])
        self.assertEqual(report['seksjoner'][0]['linjer'][1]['type'], 'treff')
        self.assertTrue(report['rimpar'][0]['treff'])

    def test_stress_notation_still_works_in_pronunciation_file(self):
        self.uttale.write_text("ska'kke skakk'e\n", encoding='utf-8')
        data = rb.Data(self.words, self.uttale, self.root / 'missing', False, False, self.egne)
        self.assertEqual(data.info('ska’kke').nokkel, 'e')
        self.assertEqual(data.info('ska’kke').metode, 'uttalefil')
        self.assertEqual(data.info('protein').stav, 3)
        self.assertEqual(data.info('protein').trykk, 3)

    def test_pre_and_post_sections_are_not_hooks(self):
        for label in ('Post-Chorus', 'Post Hook', 'Post–Refreng', 'Etterrefreng',
                      'Pre-Hook', 'Pre–Chorus', 'Pre—Hook', 'Pre‑refreng', 'Førrefreng'):
            with self.subTest(label=label):
                text = f'[Chorus]\nsol\n[{label}]\nstol\n[Chorus]\nsol\n'
                self.assertFalse(self.findings(text, 'refreng'))

    def test_section_type_comes_from_label_not_voice_description(self):
        self.assertEqual(rb._seksjon_type('[Verse 1 - rap, hook-like voice]'), 'verse')
        self.assertEqual(rb._seksjon_type('[Bridge - sung hook]'), 'annet')
        self.assertEqual(rb._seksjon_type('[Verse2 - rap]'), 'verse')

    def test_verse_echo_survives_prechorus(self):
        for pre in ('', '[Pre-Chorus]\nVinduet står åpent\n', '[Pre-Hook]\nVinduet står åpent\n'):
            with self.subTest(pre=pre):
                text = '[Verse 1]\nJeg ser en sol\n' + pre + '[Chorus]\nJeg ser en sol\n'
                self.assertTrue(any('Verse 1' in f for f in self.findings(text, 'ekko')))

    def test_prechorus_quotes_hook_but_shared_endword_is_not_a_quote(self):
        song = '[Pre-Chorus]\nJEG SER EN SOL! (ah)\n[Chorus]\nJeg ser en sol\n'
        self.assertTrue(any('siterer kroklinja' in f for f in self.findings(song, 'ekko')))
        song = '[Pre-Chorus]\nHun venter på sol\n[Chorus]\nJeg ser en sol\n'
        self.assertFalse(self.findings(song, 'ekko'))

    def test_echo_does_not_cross_bridge_or_postchorus(self):
        for label in ('Bridge', 'Post-Chorus'):
            with self.subTest(label=label):
                song = f'[Verse]\nsol\n[{label}]\nher\n[Chorus]\nsol\n'
                self.assertFalse(self.findings(song, 'ekko'))

    def test_empty_first_verse_does_not_disable_syllable_check(self):
        song = '[Verse 1]\n[Verse 2]\nsol\n[Verse 3]\nsol sol sol sol sol sol sol sol\n'
        self.assertTrue(any('Verse 3' in f and 'Verse 2' in f for f in self.findings(song, 'vers')))

    def test_echo_uses_following_hook_even_if_first_hook_is_empty(self):
        song = '[Chorus]\n[Verse 1]\nsol\n[Chorus]\nsol\n'
        self.assertTrue(self.findings(song, 'ekko'))
        self.assertTrue(self.findings(song, 'refreng'))

    def test_rap_marker_requires_a_word(self):
        for profile in ('rap', 'hoggorm'):
            for label in ('trap', 'drap', 'rapporter'):
                with self.subTest(profile=profile, label=label):
                    self.assertTrue(self.findings(f'[Verse 1 - {label}]\nsol\n', 'merke', profile))
            self.assertFalse(self.findings('[Verse 1 - cold RAP, chest voice]\nsol\n', 'merke', profile))
        self.assertFalse(self.findings('[Verse 1]\nsol\n', 'merke', 'sang'))

    def test_han_exception_is_profile_specific_and_not_all_custom_words(self):
        for profile in ('hoggorm', 'rap', 'sang'):
            findings = '\n'.join(self.findings('[Verse 1 - rap]\nHÅN ABC B\n', 'uttale', profile))
            self.assertEqual('HÅN' in findings, profile != 'hoggorm')
            self.assertIn('ABC', findings)
            self.assertIn('«B»', findings)

    def test_stemme_rules_remain_shared(self):
        for profile in ('sang', 'rap', 'hoggorm'):
            self.assertTrue(self.findings('[Chorus - falsetto]\nsol\n', 'merke', profile))

    def test_missing_unreadable_and_invalid_text_fail_before_indexing(self):
        invalid = self.root / 'invalid.txt'
        invalid.write_bytes(b'\xff')
        for path in (self.root / 'absent.txt', self.root, invalid):
            with self.subTest(path=path):
                result = self.cli('--tekst', str(path), wordlist=self.root / 'missing-words')
                self.assertEqual(result.returncode, 2)
                self.assertIn('Kan ikke lese tekstfila', result.stderr)
                self.assertNotIn('Traceback', result.stderr)
                self.assertEqual(result.stdout, '')
        self.assertFalse((self.root / 'cache').exists())

    def test_check_options_fail_before_loading_dictionary(self):
        for args in (('--sjekk', 'sol'), ('--sjekk',), ('--profil', 'sang', 'sol'),
                     ('--profil', 'hoggorm', 'sol'), ('--fasit', str(self.root), 'sol')):
            with self.subTest(args=args):
                result = self.cli(*args, wordlist=self.root / 'missing-words')
                self.assertEqual(result.returncode, 2)
                self.assertIn('krever', result.stderr)
                self.assertNotIn('Finner ikke ordlista', result.stderr)
        self.assertFalse((self.root / 'cache').exists())

    def test_missing_dictionary_has_working_recovery_hint(self):
        result = self.cli('sol', wordlist=self.root / 'missing-words')
        self.assertEqual(result.returncode, 1)
        self.assertIn('dicts/lag-ordliste.py', result.stderr)
        self.assertNotIn('install.sh', result.stderr)

    def test_default_data_path_is_local_even_without_dictionary(self):
        script = self.root / 'rim-bm'
        script.write_bytes((ROOT / 'rim-bm').read_bytes())
        env = {k: v for k, v in os.environ.items() if not k.startswith('RIM_BM_')}
        result = subprocess.run([sys.executable, str(script), 'sol'], env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn(str(self.root / 'norsk-ordbank-bm' / 'former-utf8.txt'), result.stderr)
        self.assertNotIn('music-projects', result.stderr)

    def test_markdown_identity_is_per_block(self):
        song = '[Verse 1]\nNøkkelen ligger under den røde stolen\nHun går gjennom døra\n'
        archive = self.root / 'archive'
        archive.mkdir()
        reference = archive / 'song.md'
        reference.write_text(f'```text\n{song}```\n```text\nDark pop, ninety BPM\n```\n', encoding='utf-8')
        findings = rb.sjekk_tekst(self.data, song, [archive], 'sang')
        self.assertFalse(any(f['type'] == 'gjenbruk' for f in findings))
        # En annen låt i samme fil skal fremdeles sammenlignes.
        with reference.open('a', encoding='utf-8') as f:
            f.write('```text\nNøkkelen ligger under den røde stolen\nBussen kjører videre\n```\n')
        findings = rb.sjekk_tekst(self.data, song, [archive], 'sang')
        self.assertTrue(any(f['type'] == 'gjenbruk' for f in findings))

    def test_gjennom_has_normalized_sound_and_unchanged_key(self):
        info = self.data.info('gjennom')
        self.assertEqual((info.lyd, info.nokkel, info.stav, info.trykk), ('jennom', 'ennom', 2, 1))

    def test_prompt_examples_have_explicit_english_pronunciation(self):
        data = rb.Data(self.words, self.uttale, self.root / 'missing', False, False, ROOT / 'egne-ord.txt')
        self.assertEqual(data.info('way').lyd, 'wæi')
        for a, b in (('meg', 'way'), ('cash', 'flash')):
            self.assertTrue(rb.check_pair(data, a, b)['treff'])
        self.assertFalse(rb.check_pair(data, 'natt', 'that')['treff'])
