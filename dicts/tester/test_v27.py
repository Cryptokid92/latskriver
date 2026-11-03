"""Flowplan og ordrette låser med isolert ordliste."""
import json
import subprocess
import sys
import unittest
from pathlib import Path
import test_v26
from test_v26 import rb, ROOT


class Plan(unittest.TestCase):
    setUpClass = classmethod(test_v26.Kontroll.setUpClass.__func__)

    def test_flow_switch(self):
        plan = {'versjon': 1, 'flow': [dict(seksjon=1, fra=1, til=2, stavelser=1), dict(seksjon=1, fra=3, til=4, stavelser=2)]}
        self.assertEqual(rb.check_plan(self.data, '[Verse]\nsol\nstol\nsol stol\nher ser', plan), [])

    def test_flow_location_and_adlibs(self):
        plan = {'versjon': 1, 'flow': [dict(seksjon=1, fra=1, til=2, stavelser=1)]}
        result = rb.check_plan(self.data, '[Verse]\nsol (her ser)\nsol stol', plan)
        self.assertEqual(len(result), 1)
        self.assertEqual((result[0]['seksjon'], result[0]['linje']), (1, 2))

    def test_tolerance(self):
        plan = {'versjon': 1, 'flow': [dict(seksjon=1, fra=1, til=1, stavelser=1, toleranse=1)]}
        self.assertEqual(rb.check_plan(self.data, 'sol stol', plan), [])

    def test_missing_flow_target(self):
        plan = {'versjon': 1, 'flow': [dict(seksjon=1, fra=1, til=1, stavelser=1)]}
        self.assertEqual(rb.check_plan(self.data, '[Verse]', plan)[0]['type'], 'flow')

    def test_invalid_plans(self):
        block = dict(seksjon=1, fra=1, til=2, stavelser=1)
        for plan in ([], {'versjon': True}, {'versjon': 1, 'flow': [block, block]}, {'versjon': 1, 'las': [dict(seksjon=1, linjer=[])]}, {'versjon': 1, 'flow': [dict(block, toleranse=-1)]}, {'versjon': 1, 'flow': [dict(block, stavelser=True)]}, {'versjon': 1, 'typo': []}):
            with self.subTest(plan=plan), self.assertRaises(ValueError):
                rb.validate_plan(plan)

    def test_locked_line_is_verbatim(self):
        plan = {'versjon': 1, 'las': [dict(seksjon=1, linjer=[1])]}
        original = '[Verse]\nSol! (yeah)\nstol'
        self.assertEqual(rb.check_plan(self.data, original.replace('stol', 'her'), plan, original), [])
        for changed in ('sol! (yeah)', 'Sol (yeah)', 'Sol! (ah)', ' Sol! (yeah)'):
            self.assertTrue(rb.check_plan(self.data, '[Verse]\n'+changed+'\nstol', plan, original))

    def test_full_section_and_empty_hook(self):
        plan = {'versjon': 1, 'las': [dict(seksjon=2)]}
        original = '[Chorus]\nsol\n[Chorus]\nstol'
        for text in ('[Chorus]\nsol\n[Chorus]', '[Chorus]\nsol', original+'\nher'):
            self.assertTrue(rb.check_plan(self.data, text, plan, original))
        self.assertEqual(rb.check_plan(self.data, original, plan, original), [])

    def test_invalid_lock_source(self):
        for plan in ({'versjon': 1, 'las': [dict(seksjon=2)]}, {'versjon': 1, 'las': [dict(seksjon=1, linjer=[2])]}):
            with self.assertRaises(ValueError):
                rb.check_plan(self.data, 'sol', plan, 'sol')
        with self.assertRaises(ValueError):
            rb.check_plan(self.data, 'sol', {'versjon': 1, 'las': [dict(seksjon=1)]})

    def test_cli_strict_and_json(self):
        directory = Path(self.tmp.name)
        song = directory / 'song.txt'; song.write_text('[Chorus]\nsol stol', encoding='utf-8')
        plan = directory / 'plan.json'; plan.write_text(json.dumps({'versjon': 1, 'flow': [dict(seksjon=1, fra=1, til=1, stavelser=1)]}))
        args = [sys.executable, str(ROOT / 'rim-bm'), '--wordlist', str(self.words), '--ingen-cache', '--tekst', str(song), '--sjekk', '--plan', str(plan), '--json']
        result = subprocess.run(args + ['--streng'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertTrue(any(f['type'] == 'flow' for f in json.loads(result.stdout)['sjekk']))
        self.assertEqual(subprocess.run(args, capture_output=True).returncode, 0)
        plan.write_text('{broken')
        result = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn('Traceback', result.stderr)
