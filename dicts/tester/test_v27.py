"""Krokverksted (--krok) med små, midlertidige data uten private referanser."""
import importlib.machinery
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader('rim_bm_v27', str(ROOT / 'rim-bm'))
spec = importlib.util.spec_from_loader(loader.name, loader)
rb = importlib.util.module_from_spec(spec)
sys.modules[loader.name] = rb
loader.exec_module(rb)

KROK = 'Jeg retter én feil om gangen'
GAMMEL = 'Hodet er klart, jeg tar min fart'


class Krokverksted(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.root = Path(cls.tmp.name)
        cls.words = cls.root / 'ord.txt'
        cls.words.write_text('gangen\nfangen\nsangen\nklart\nfart\nsvart\nsol\n', encoding='utf-8')
        cls.frekvens = cls.root / 'frekvens.txt'
        cls.frekvens.write_text('fangen 10\nsol 5\n', encoding='utf-8')
        cls.egne = cls.root / 'egne.txt'
        cls.egne.write_text('', encoding='utf-8')
        cls.uttale = cls.root / 'uttale.txt'
        cls.data = rb.Data(cls.words, cls.uttale, cls.frekvens, False, False, cls.egne)
        cls.arkiv = cls.root / 'arkiv'
        cls.arkiv.mkdir()
        (cls.arkiv / '05-svarer-ikke.md').write_text(
            '# Svarer ikke\n\n```\n[Chorus]\nSvarer ikke, hodet er klart (yeah)\n'
            f'{GAMMEL} (skrr)\nNummeret ditt får ligge, jeg har satt\n```\n', encoding='utf-8')
        (cls.arkiv / '08-lomma-full.txt').write_text('[Chorus]\nLomma er full (yeah)\nJeg er her\n',
                                                      encoding='utf-8')

    def analyse(self, *kandidater, fasit=None):
        return rb.krok_analyse(self.data, list(kandidater), [self.arkiv] if fasit is None else fasit)

    def cli(self, *args, env=None):
        return subprocess.run([sys.executable, str(ROOT / 'rim-bm'), '--wordlist', str(self.words),
                               '--uttale', str(self.uttale), '--egne', str(self.egne),
                               '--frekvens', str(self.frekvens), '--ingen-cache', *args],
                              capture_output=True, text=True, env=env)

    def test_stavelser_og_grensen_fem_til_ni(self):
        kort, krok, lang = self.analyse('Gangen', KROK, 'Jeg retter alle mine feil i hele gamle gangen')
        self.assertEqual((kort['stav'], kort['innenfor']), (2, False))
        self.assertEqual((krok['stav'], krok['innenfor']), (8, True))
        self.assertEqual((lang['stav'], lang['innenfor']), (15, False))

    def test_adlibs_teller_ikke_med(self):
        self.assertEqual(self.analyse(KROK + ' (ey, yeah)')[0]['stav'], 8)

    def test_sluttord_rimmuligheter_og_multi(self):
        krok, gammel = self.analyse(KROK, GAMMEL)
        self.assertEqual((krok['sluttord'], krok['nokkel'], krok['multi']), ('gangen', 'angen', True))
        self.assertEqual((krok['rim'], krok['rim_vanlige']), (2, 1))  # fangen, sangen; bare fangen er vanlig
        self.assertEqual((gammel['nokkel'], gammel['multi']), ('art', False))
        self.assertEqual((gammel['rim'], gammel['rim_vanlige']), (2, 0))  # klart, svart

    def test_klisje_merkes(self):
        self.assertEqual(self.analyse('Ingen stopper meg')[0]['klisje'], ['ingen stopper meg'])
        self.assertEqual(self.analyse(KROK)[0]['klisje'], [])

    def test_tidligere_krok_merkes_med_fil(self):
        ny, gammel = self.analyse(KROK, GAMMEL)
        self.assertEqual(ny['brukt_for'], [])
        self.assertEqual(gammel['brukt_for'], ['05-svarer-ikke.md'])

    def test_delvis_gjenbruk_merkes(self):
        cases = {
            'Hodet er klart': ['05-svarer-ikke.md'],             # kandidaten står inni en gammel linje
            'Lomma er full i natt': ['08-lomma-full.txt'],      # en gammel linje står inni kandidaten
            'Nummeret ditt får ligge i natt': ['05-svarer-ikke.md'],  # fire ord på rad
            'Jeg er her': [],                                    # bare småord teller ikke
        }
        for kandidat, filer in cases.items():
            with self.subTest(kandidat=kandidat):
                self.assertEqual(self.analyse(kandidat)[0]['brukt_for'], filer)

    def test_uten_arkiv_ingen_gjenbrukssjekk(self):
        self.assertEqual(self.analyse(GAMMEL, fasit=[])[0]['brukt_for'], [])

    def test_cli_json(self):
        result = self.cli('--krok', KROK, GAMMEL, '--fasit', str(self.arkiv), '--json')
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual([d['tekst'] for d in data], [KROK, GAMMEL])
        self.assertEqual([d['brukt_for'] for d in data], [[], ['05-svarer-ikke.md']])

    def test_cli_tekst_viser_tidligere_bruk(self):
        result = self.cli('--krok', KROK, GAMMEL, '--fasit', str(self.arkiv))
        self.assertEqual(result.returncode, 0, result.stderr)
        linje_ny = next(l for l in result.stdout.splitlines() if KROK in l)
        linje_gammel = next(l for l in result.stdout.splitlines() if GAMMEL in l)
        self.assertIn('05-svarer-ikke.md', linje_gammel)
        self.assertNotIn('05-svarer-ikke.md', linje_ny)

    def test_hoggorm_bruker_standardarkivet_men_sang_gjor_ikke(self):
        env = dict(os.environ, RIM_BM_FASIT=str(self.arkiv))
        hoggorm = self.cli('--krok', GAMMEL, '--json', env=env)
        sang = self.cli('--krok', GAMMEL, '--profil', 'sang', '--json', env=env)
        self.assertEqual(hoggorm.returncode, 0, hoggorm.stderr)
        self.assertEqual(sang.returncode, 0, sang.stderr)
        self.assertEqual(json.loads(hoggorm.stdout)[0]['brukt_for'], ['05-svarer-ikke.md'])
        self.assertEqual(json.loads(sang.stdout)[0]['brukt_for'], [])

    def test_krok_krever_kandidat(self):
        result = self.cli('--krok')
        self.assertEqual(result.returncode, 2)
        self.assertIn('kandidat', result.stderr)

    def test_krok_kan_ikke_kombineres_med_par(self):
        result = self.cli('--krok', '--par', 'sol', 'stol')
        self.assertEqual(result.returncode, 2)
        self.assertNotIn('unrecognized', result.stderr)  # flagget finnes, men modusene utelukker hverandre

    def test_fasit_uten_sjekk_eller_krok_avvises_fortsatt(self):
        self.assertEqual(self.cli('sol', '--fasit', str(self.arkiv)).returncode, 2)

    # Seksjonsmerker: første versjon har rene merker; beskrivelser legges til etter lytting.
    def merkefunn(self, tekst, profil):
        return [f['melding'] for f in rb.sjekk_tekst(self.data, tekst, [], profil) if f['type'] == 'merke']

    def test_rent_versmerke_gir_ikke_rapvarsel(self):
        for profil in ('sang', 'rap', 'hoggorm'):
            for merke in ('[Verse 1]', '[Verse]', '[Vers 2]'):
                with self.subTest(profil=profil, merke=merke):
                    self.assertEqual(self.merkefunn(f'{merke}\nsol\n', profil), [])

    def test_beskrevet_versmerke_uten_rap_varsles_i_rap_og_hoggorm(self):
        tekst = '[Verse 1 - cold flow]\nsol\n'
        for profil in ('rap', 'hoggorm'):
            with self.subTest(profil=profil):
                self.assertTrue(any('sier ikke rap' in m for m in self.merkefunn(tekst, profil)))
        self.assertEqual(self.merkefunn(tekst, 'sang'), [])
        self.assertEqual(self.merkefunn('[Verse 1 - cold rap]\nsol\n', 'hoggorm'), [])


if __name__ == '__main__':
    unittest.main()
