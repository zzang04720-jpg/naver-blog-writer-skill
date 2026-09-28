"""Fictional fixtures only: no credentials, browser, uploads, or network."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def module(skill, script):
    spec = importlib.util.spec_from_file_location(script, ROOT / '.claude/skills' / skill / 'scripts' / (script + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class OfflineTests(unittest.TestCase):
    def test_score_fictional_candidates(self):
        score = module('keyword-scoring', 'score').score_candidate
        good = score(dict(keyword='FICTIONAL', monthly_total=1000, blog_total=5000), 1)
        self.assertEqual((good['passed'], good['saturation'], good['score']), (True, 5, 166.67))
        self.assertFalse(score(dict(monthly_total=1000, blog_total=20000), 1)['passed'])
        self.assertFalse(score(dict(monthly_total=1000), 1)['passed'])

    def test_escape_html(self):
        package = module('naver-packager', 'package')
        self.assertEqual(package.convert_inline('<script>x</script> **bold**'), '&lt;script&gt;x&lt;/script&gt; <b>bold</b>')

    def test_missing_image_fails_before_opening_browser(self):
        package = module('naver-packager', 'package')
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            (out / '02_draft.md').write_text('FICTIONAL\n[[IMG-01: missing]]', encoding='utf-8')
            (out / '02_meta.json').write_text('{}', encoding='utf-8')
            (out / 'images.json').write_text('[]', encoding='utf-8')
            with patch.object(sys, 'argv', ['package.py', folder]), patch.object(package.webbrowser, 'open') as browser:
                with self.assertRaises(SystemExit) as failure:
                    package.main()
                self.assertNotEqual(failure.exception.code, 0)
                browser.assert_not_called()

    def test_unsafe_image_url_is_rejected(self):
        package = module('naver-packager', 'package')
        with self.assertRaises(ValueError):
            package.build_image_map([dict(position=1, public_url='javascript:alert(1)')])

    def test_clean_clone_root_is_local(self):
        for skill, script in [('naver-keyword-api', 'keywordstool'), ('naver-serp-collector', 'serp'), ('image-uploader', 'upload_images')]:
            with self.subTest(skill=skill):
                mod = module(skill, script)
                self.assertEqual(mod.find_project_root(ROOT / '.claude/skills' / skill / 'scripts'), ROOT)

    def test_thumbnail_is_position_zero(self):
        uploader = module('image-uploader', 'upload_images')
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            for name in ['fictional-02.jpg', 'thumbnail.jpg', 'ignore.txt']:
                (out / name).write_bytes(b'fictional')
            entries = uploader.load_or_build_entries(out, out / 'images.json')
            self.assertEqual([(e['filename'], e['position']) for e in entries], [('thumbnail.jpg', 0), ('fictional-02.jpg', 1)])

    def test_upload_uses_configured_branch_and_encoded_path(self):
        uploader = module('image-uploader', 'upload_images')
        requests = []
        def fake_request(method, url, token, payload=None):
            requests.append((method, url, payload))
            return {'sha': 'fictional'} if method == 'GET' else {}
        with tempfile.TemporaryDirectory() as folder:
            image = Path(folder) / 'fictional.jpg'
            image.write_bytes(b'fictional')
            with patch.object(uploader, 'github_request', side_effect=fake_request):
                url = uploader.upload_file('example/images', 'FICTIONAL_TOKEN', 'date/post/space name.jpg', image, 'master')
            self.assertTrue(requests[0][1].endswith('space%20name.jpg?ref=master'))
            self.assertEqual(requests[1][2]['branch'], 'master')
            self.assertEqual(url, 'https://raw.githubusercontent.com/example/images/master/date/post/space%20name.jpg')

    def test_packaging_cli_no_browser(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            (out / '02_draft.md').write_text('# Fictional\n## Example\n**Demo** only.\n[[IMG-01: sample]]', encoding='utf-8')
            (out / '02_meta.json').write_text(json.dumps({'titles': ['Fictional sample'], 'hashtags': ['demo']}), encoding='utf-8')
            (out / 'images.json').write_text(json.dumps([{'position': 1, 'public_url': 'https://example.invalid/sample.jpg', 'alt': '"<fictional>"'}]), encoding='utf-8')
            run = subprocess.run([sys.executable, str(ROOT / '.claude/skills/naver-packager/scripts/package.py'), str(out), '--no-open'], capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr.decode('utf-8', errors='replace'))
            html = (out / 'post.html').read_text(encoding='utf-8')
            self.assertIn('<meta charset="utf-8">', html)
            self.assertIn('&quot;&lt;fictional&gt;&quot;', html)
            self.assertNotIn('[[IMG-', html)
            self.assertTrue((out / 'publish.md').exists())


if __name__ == '__main__':
    unittest.main()
